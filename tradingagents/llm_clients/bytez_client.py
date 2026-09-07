"""Bytez chat client and LangChain compatibility adapters.

Bytez's official LangChain integration is a native chat model.  The current
package supports chat and streaming, but does not advertise native tool
calling or structured-output bindings.  TradingAgents therefore keeps those
two contracts at this boundary: tool intents are represented as JSON in the
prompt and converted into normal LangChain ``AIMessage.tool_calls``; typed
agent outputs are parsed and validated against their existing Pydantic schema.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    ToolMessage,
    convert_to_messages,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import BaseModel, Field, SecretStr

from .api_key_env import get_api_key_env
from .base_client import BaseLLMClient, normalize_content
from .errors import RequiredStructuredOutputError
from .model_catalog import DEFAULT_BYTEZ_MODEL
from .validators import validate_model


class BytezError(RuntimeError):
    """A safe diagnostic that never includes a response body or credentials."""


class BytezTransientError(BytezError):
    """A timeout, throttling, or temporary server error that may be retried."""


def _http_error(status: int) -> BytezError:
    if status in (408, 429) or status >= 500:
        return BytezTransientError(f"Bytez temporary inference failure (HTTP {status})")
    if status in (401, 403):
        return BytezError(f"Bytez authentication/access failure (HTTP {status}); check BYTEZ_API_KEY")
    if status == 404:
        return BytezError("Bytez model resolution failed (HTTP 404); check the model ID and availability")
    return BytezError(f"Bytez inference request rejected (HTTP {status})")


def _content_text(response: Any) -> str:
    """Extract text without exposing provider metadata or credentials."""
    response = normalize_content(response)
    content = getattr(response, "content", response)
    if isinstance(content, dict):
        content = content.get("text", content.get("content", ""))
    return str(content or "").strip()


def _json_value(text: str) -> Any:
    """Parse complete JSON, allowing a code fence or a closed thinking block."""
    candidate = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if candidate.startswith("```"):
        candidate = candidate.split("\n", 1)[1] if "\n" in candidate else candidate
        candidate = candidate.rsplit("```", 1)[0].strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
    raise ValueError("Bytez returned content that is not valid JSON")


class BytezStructuredRunnable(Runnable):
    """Bounded JSON/Pydantic structured-output compatibility layer."""

    def __init__(self, llm: Any, schema: type, max_retries: int = 2):
        self.llm = llm
        self.schema = schema
        self.max_retries = max(0, int(max_retries))

    def invoke(self, input: Any, config: dict | None = None, **kwargs: Any) -> Any:
        prompt = _append_correction(input, self.schema, None)
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            if attempt:
                prompt = _append_correction(input, self.schema, last_error)
            try:
                raw = self.llm.invoke(prompt, config=config, **kwargs)
                return self.schema.model_validate(_json_value(_content_text(raw)))
            except BytezError as exc:
                # Transport retries happen on the plain runnable. Do not
                # multiply that budget by retrying them again as parse errors.
                raise RequiredStructuredOutputError(str(exc)) from None
            except ValueError as exc:
                last_error = exc
        raise RequiredStructuredOutputError(
            f"Bytez structured output failed validation for {self.schema.__name__} "
            f"after {self.max_retries} retries"
        ) from None


def _append_correction(input_: Any, schema: type, error: Exception | None) -> Any:
    instruction = (
        f"Return only one valid JSON object matching this schema: "
        f"{json.dumps(schema.model_json_schema(), ensure_ascii=True)}. "
        "Do not use Markdown fences or explanatory text."
    )
    if error:
        instruction += " The previous response failed validation; correct it."
    if hasattr(input_, "to_messages"):
        return input_.to_messages() + [HumanMessage(content=instruction)]
    if isinstance(input_, list):
        return input_ + [HumanMessage(content=instruction)]
    return f"{input_}\n\n{instruction}"


class BytezToolRunnable(Runnable):
    """Turn JSON tool intents into standard LangChain AIMessage tool calls."""

    def __init__(self, llm: Any, tools: list[Any], schemas: dict | None = None):
        self.llm = llm
        self.tools = tools
        self.tool_names = {tool.get("function", {}).get("name") for tool in tools}
        self.schemas = schemas or {}

    def invoke(self, input: Any, config: dict | None = None, **kwargs: Any) -> AIMessage:
        prompt = _append_tool_instruction(input, self.tools)
        for attempt in range(self.llm.max_retries + 1):
            response = self.llm.invoke(prompt, config=config, **kwargs)
            text = _content_text(response)
            try:
                call = _parse_tool_intent(text, self.tool_names)
                if call and call[0] in self.schemas:
                    self.schemas[call[0]].model_validate(call[1])
                break
            except ValueError:
                if attempt == self.llm.max_retries:
                    raise BytezError("Bytez tool intent failed validation after the retry budget") from None
                prompt = _append_tool_instruction(input, self.tools)
                prompt.append(HumanMessage(content="The previous tool intent was invalid. Use a listed name and its exact argument schema."))
        if call is None:
            return response.model_copy(update={"content": text})
        name, args = call
        return response.model_copy(update={
            "content": "",
            "tool_calls": [{
                "name": name,
                "args": args,
                "id": f"bytez_{uuid.uuid4().hex}",
                "type": "tool_call",
            }],
        })


def _append_tool_instruction(input_: Any, tools: list[dict]) -> Any:
    instruction = (
        "Available tool descriptions and argument schemas: " + json.dumps(tools) + ". If a tool is needed, "
        "return only JSON in the form {\"tool\": \"name\", \"arguments\": {}}. "
        "If no tool is needed, return the final answer as plain text."
    )
    messages = input_.to_messages() if hasattr(input_, "to_messages") else (
        [HumanMessage(content=input_)] if isinstance(input_, str) else convert_to_messages(input_)
    )
    return messages + [HumanMessage(content=instruction)]


def _parse_tool_intent(text: str, allowed: set[str]) -> tuple[str, dict] | None:
    try:
        value = _json_value(text)
    except ValueError:
        if re.search(r'"(?:tool|arguments|tool_calls)"\s*:', text):
            raise ValueError("Malformed tool intent") from None
        return None
    if not isinstance(value, dict):
        return None
    name = value.get("tool") or value.get("name")
    args = value.get("arguments", value.get("args", {}))
    if not any(key in value for key in ("tool", "name", "tool_calls")):
        return None
    if not isinstance(name, str) or name not in allowed or not isinstance(args, dict):
        raise ValueError("Invalid tool name or arguments")
    return name, args


class BytezChatModelAdapter(Runnable):
    """Small facade adding TradingAgents contracts to ``BytezChatModel``."""

    def __init__(self, model: Any, max_retries: int = 2):
        self._model = model
        self.max_retries = int(max_retries)
        if isinstance(max_retries, bool) or self.max_retries < 0:
            raise ValueError("Bytez max_retries must be a non-negative integer")
        self._retrying_model = RunnableLambda(self._invoke_once).with_retry(
            retry_if_exception_type=(BytezTransientError,),
            stop_after_attempt=self.max_retries + 1,
        )

    def _invoke_once(self, input, config=None, **kwargs):
        # The JSON bridge has no native tool role. Carry the tool IDs, names,
        # arguments and observations as ordinary conversational messages.
        messages = input.to_messages() if hasattr(input, "to_messages") else (
            [HumanMessage(content=input)] if isinstance(input, str) else convert_to_messages(input)
        )
        normalized = []
        for message in messages:
            if isinstance(message, ToolMessage):
                normalized.append(HumanMessage(content=f"Tool result for {message.tool_call_id}:\n{message.content}"))
            elif isinstance(message, AIMessage) and message.tool_calls:
                normalized.append(AIMessage(content=json.dumps({"tool_calls": message.tool_calls})))
            else:
                normalized.append(message)
        return normalize_content(self._model.invoke(normalized, config=config, **kwargs))

    def invoke(self, input, config=None, **kwargs):
        return self._retrying_model.invoke(input, config=config, **kwargs)

    def stream(self, input, config=None, **kwargs):
        # Buffer a complete response so retries cannot duplicate partial output.
        response = self.invoke(input, config=config, **kwargs)
        yield AIMessageChunk(content=response.content, response_metadata=response.response_metadata)

    def with_structured_output(self, schema: type, **kwargs: Any) -> BytezStructuredRunnable:
        if not isinstance(schema, type) or not issubclass(schema, BaseModel):
            raise TypeError("Bytez structured output requires a Pydantic model schema")
        if kwargs:
            raise ValueError("Bytez supports validated JSON only; native structured-output options are unavailable")
        return BytezStructuredRunnable(self, schema, self.max_retries)

    def bind_tools(self, tools: list[Any], **kwargs: Any) -> BytezToolRunnable:
        if kwargs:
            raise ValueError("Bytez JSON tools do not support native tool_choice options")
        schemas = {tool.name: tool.get_input_schema() for tool in tools if hasattr(tool, "get_input_schema")}
        return BytezToolRunnable(self, [convert_to_openai_tool(tool) for tool in tools], schemas)


class _CompatibleBytezChatModel(BaseChatModel):
    """Small modern-LangChain fallback for Bytez package 0.0.7.

    ``langchain-bytez==0.0.7`` currently imports legacy LangChain modules.  On
    installations using LangChain 1.x those imports fail, although the Bytez
    HTTP contract itself is unchanged.  This fallback keeps the optional
    provider usable while the official package remains the first choice.
    """

    model_id: str
    api_key: SecretStr = Field(exclude=True, repr=False)
    params: dict = Field(default_factory=dict)
    streaming: bool = False
    http_timeout_s: float = 300.0

    @property
    def _llm_type(self) -> str:
        return "bytez"

    def _payload(self, messages: list[Any], stream: bool = False) -> dict:
        return {
            "messages": [
                {
                    "role": {"human": "user", "ai": "assistant"}.get(
                        getattr(message, "type", "user"), getattr(message, "type", "user")
                    ),
                    "content": _content_text(message),
                }
                for message in messages
            ],
            "params": self.params,
            "stream": stream,
        }

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        import requests

        try:
            with requests.post(
                f"https://api.bytez.com/models/v2/{self.model_id}",
                headers={"Authorization": self.api_key.get_secret_value()},
                json=self._payload(messages, False),
                timeout=self.http_timeout_s,
                allow_redirects=False,
            ) as response:
                if response.status_code >= 300:
                    raise _http_error(response.status_code)
                body = response.json()
        except (requests.Timeout, requests.ConnectionError):
            raise BytezTransientError("Bytez inference timed out or could not connect") from None
        except (requests.RequestException, ValueError):
            raise BytezError("Bytez returned an invalid HTTP/JSON response") from None
        if not isinstance(body, dict):
            raise BytezError("Bytez returned an invalid response envelope")
        if body.get("error"):
            # Error bodies are untrusted and may echo authorization. Classify
            # known transient failures without forwarding the original text.
            error = str(body["error"]).lower()
            if any(term in error for term in ("rate limit", "timeout", "loading", "starting", "unavailable")):
                raise BytezTransientError("Bytez reported temporary inference unavailability")
            if any(term in error for term in ("unauthorized", "api key", "authentication")):
                raise BytezError("Bytez authentication failed; check BYTEZ_API_KEY")
            raise BytezError("Bytez inference failed; check model access and quota")
        output = body.get("output")
        text = output.get("content", output) if isinstance(output, dict) else output
        if not isinstance(text, (str, list)):
            raise BytezError("Bytez returned no chat content")
        try:
            message = normalize_content(AIMessage(content=text))
        except ValueError:
            raise BytezError("Bytez returned invalid chat content") from None
        if not message.content.strip():
            raise BytezError("Bytez returned empty chat content")
        return ChatResult(generations=[ChatGeneration(message=message)])

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        # The compatibility adapter intentionally buffers one normal request.
        result = self._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
        yield ChatGenerationChunk(message=AIMessageChunk(content=result.generations[0].text))


class BytezClient(BaseLLMClient):
    """TradingAgents client for Bytez's native LangChain chat integration."""

    provider = "bytez"

    def __init__(self, model: str = DEFAULT_BYTEZ_MODEL, base_url: str | None = None, **kwargs):
        super().__init__(model or DEFAULT_BYTEZ_MODEL, base_url, **kwargs)

    def get_llm(self) -> BytezChatModelAdapter:
        self.warn_if_unknown_model()
        api_env = get_api_key_env(self.provider)
        api_key = os.environ.get(api_env) if api_env else None
        if not api_key:
            raise ValueError(
                f"API key for provider 'bytez' is not set. Set the {api_env} "
                "environment variable."
            )

        # Bytez calls generation controls ``params``; do not pass OpenAI-only
        # kwargs into its Pydantic model.
        params = dict(self.kwargs.get("params") or {})
        if self.kwargs.get("temperature") is not None:
            params.setdefault("temperature", self.kwargs["temperature"])
        if self.kwargs.get("max_tokens") is not None:
            params.setdefault("max_new_tokens", self.kwargs["max_tokens"])
        model_kwargs = {
            "model_id": self.model,
            "api_key": api_key,
            "params": params,
            "streaming": bool(self.kwargs.get("streaming", False)),
        }
        for key in ("callbacks", "http_timeout_s", "capacity", "timeout"):
            if self.kwargs.get(key) is not None:
                model_kwargs[key] = self.kwargs[key]
        try:
            from langchain_bytez import BytezChatModel
        except (ImportError, ModuleNotFoundError):
            # The published integration currently pins legacy LangChain
            # modules. Use the same documented Bytez endpoint under modern
            # LangChain rather than making Bytez users downgrade all providers.
            bytez_model = _CompatibleBytezChatModel(
                model_id=self.model,
                api_key=api_key,
                params=params,
                streaming=model_kwargs["streaming"],
                http_timeout_s=model_kwargs.get("http_timeout_s", 300.0),
                callbacks=model_kwargs.get("callbacks"),
            )
        else:
            class SafeBytezChatModel(BytezChatModel):
                # Upstream 0.0.7 includes api_key AND headers in identifying
                # params. Remove both before LangChain callbacks/traces run.
                api_key: str = Field(exclude=True, repr=False)
                headers: dict = Field(default_factory=dict, exclude=True, repr=False)

                @property
                def _identifying_params(self):
                    return {"model_id": self.model_id}

                def _generate(self, messages, stop=None, run_manager=None, **kwargs):
                    import requests

                    try:
                        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
                    except (requests.Timeout, requests.ConnectionError):
                        raise BytezTransientError("Bytez inference timed out or could not connect") from None
                    except Exception:
                        raise BytezError("Bytez native inference failed; check model access and quota") from None

            # Keep native and compatibility paths buffered while validation and
            # retrying are active. Upstream's HTTP timeout is in seconds.
            model_kwargs["streaming"] = False
            model_kwargs["headers"] = {"Authorization": api_key}
            bytez_model = SafeBytezChatModel(**model_kwargs)

        return BytezChatModelAdapter(
            bytez_model,
            max_retries=self.kwargs.get("max_retries") if self.kwargs.get("max_retries") is not None else 2,
        )

    def validate_model(self) -> bool:
        return validate_model(self.provider, self.model)
