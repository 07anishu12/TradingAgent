"""Unit coverage for the optional Bytez provider boundary."""

import json
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel

from tradingagents.llm_clients.api_key_env import get_api_key_env
from tradingagents.llm_clients.bytez_client import (
    BytezClient,
    BytezError,
    BytezStructuredRunnable,
    BytezToolRunnable,
    _CompatibleBytezChatModel,
)
from tradingagents.llm_clients.errors import RequiredStructuredOutputError
from tradingagents.llm_clients.factory import create_llm_client


@pytest.mark.unit
def test_bytez_is_registered_and_uses_its_key(monkeypatch):
    monkeypatch.setenv("BYTEZ_API_KEY", "test-key-not-a-real-credential")
    assert get_api_key_env("bytez") == "BYTEZ_API_KEY"
    client = create_llm_client("bytez", "zai-org/GLM-4.7")
    llm = client.get_llm()
    assert llm._model.model_id == "zai-org/GLM-4.7"
    key = llm._model.api_key
    assert (key.get_secret_value() if hasattr(key, "get_secret_value") else key) == "test-key-not-a-real-credential"
    assert llm.max_retries == 2


@pytest.mark.unit
def test_bytez_missing_key_fails_without_echoing_secret(monkeypatch):
    monkeypatch.delenv("BYTEZ_API_KEY", raising=False)
    with pytest.raises(ValueError, match="BYTEZ_API_KEY") as exc:
        BytezClient().get_llm()
    assert "test-key" not in str(exc.value)


@pytest.mark.unit
def test_structured_json_is_validated_and_retried():
    class Decision(BaseModel):
        ok: bool

    llm = MagicMock()
    llm.invoke.side_effect = [AIMessage(content="not json"), AIMessage(content='{"ok": true}')]
    result = BytezStructuredRunnable(llm, Decision, max_retries=1).invoke([HumanMessage(content="x")])
    assert isinstance(result, Decision)
    assert result.ok
    assert llm.invoke.call_count == 2


@pytest.mark.unit
def test_tool_intent_becomes_langchain_tool_call():
    llm = MagicMock()
    llm.max_retries = 1
    llm.invoke.return_value = AIMessage(content='{"tool":"get_stock_data","arguments":{"ticker":"PLTR"}}')
    result = BytezToolRunnable(llm, [{"function": {"name": "get_stock_data"}}]).invoke("prompt")
    assert result.tool_calls[0]["name"] == "get_stock_data"
    assert result.tool_calls[0]["args"] == {"ticker": "PLTR"}


@pytest.mark.unit
def test_bytez_does_not_use_openai_endpoint(monkeypatch):
    monkeypatch.setenv("BYTEZ_API_KEY", "test-key-not-a-real-credential")
    llm = BytezClient("zai-org/GLM-4.7").get_llm()
    assert not hasattr(llm._model, "base_url")


@pytest.mark.parametrize("answer", ['{"ok":', '{"ok": "invalid bool"}'])
def test_exhausted_structured_json_never_becomes_freetext(answer):
    from tradingagents.agents.utils.structured import invoke_structured_or_freetext

    class Decision(BaseModel):
        ok: bool

    raw = MagicMock()
    raw.invoke.return_value = AIMessage(content=answer)
    plain = MagicMock()
    structured = BytezStructuredRunnable(raw, Decision, max_retries=1)
    with pytest.raises(RequiredStructuredOutputError, match="after 1 retries"):
        invoke_structured_or_freetext(structured, plain, "prompt", str, "Portfolio Manager")
    plain.invoke.assert_not_called()
    assert raw.invoke.call_count == 2
    assert '"properties"' in raw.invoke.call_args_list[0].args[0]


def test_transport_failure_is_not_retried_as_json():
    from tradingagents.agents.schemas import PortfolioDecision

    raw = MagicMock()
    raw.invoke.side_effect = BytezError("Bytez authentication failed")
    with pytest.raises(RequiredStructuredOutputError, match="authentication"):
        BytezStructuredRunnable(raw, PortfolioDecision, max_retries=3).invoke("prompt")
    assert raw.invoke.call_count == 1


@pytest.mark.parametrize("bad", [
    '{"tool": "unknown", "arguments": {}}',
    '{"tool": "get_stock_data", "arguments": "PLTR"}',
    '{"tool": "get_stock_data", "arguments": {',
])
def test_invalid_tool_calls_are_retried_not_saved_as_reports(bad):
    raw = MagicMock(max_retries=1)
    raw.invoke.side_effect = [AIMessage(content=bad), AIMessage(content='{"tool":"get_stock_data","arguments":{"ticker":"PLTR"}}')]
    result = BytezToolRunnable(raw, [{"function": {"name": "get_stock_data"}}]).invoke("prompt")
    assert result.tool_calls[0]["args"] == {"ticker": "PLTR"}
    assert raw.invoke.call_count == 2


def test_tools_include_argument_schemas_and_preserve_observation_roundtrip():
    from langchain_core.tools import tool

    from tradingagents.llm_clients.bytez_client import BytezChatModelAdapter

    @tool
    def quote(ticker: str, days: int) -> str:
        """Retrieve a quote history."""
        return "quote"

    raw = MagicMock()
    raw.invoke.return_value = AIMessage(content="Report", response_metadata={"marker": "kept"})
    llm = BytezChatModelAdapter(raw)
    result = llm.bind_tools([quote]).invoke([
        HumanMessage(content="Analyze PLTR"),
        AIMessage(content="", tool_calls=[{"id": "call-1", "name": "quote", "args": {"ticker": "PLTR", "days": 2}}]),
        ToolMessage(content="Two observations", tool_call_id="call-1"),
    ])
    messages = raw.invoke.call_args.args[0]
    assert "days" in messages[-1].content and "integer" in messages[-1].content
    assert "quote" in messages[1].content and "PLTR" in messages[1].content
    assert "Two observations" in messages[2].content and "call-1" in messages[2].content
    assert not any(isinstance(message, ToolMessage) for message in messages)
    assert result.response_metadata == {"marker": "kept"}


class CaptureCallbacks(BaseCallbackHandler):
    def __init__(self):
        self.records = []

    def on_chat_model_start(self, serialized, messages, **kwargs):
        self.records.append((serialized, kwargs))

    def on_llm_error(self, error, **kwargs):
        self.records.append(str(error))


def test_http_normalization_callbacks_and_credential_serialization():
    callback = CaptureCallbacks()
    key = "synthetic-secret-for-regression-test"
    model = _CompatibleBytezChatModel(model_id="zai-org/GLM-4.7", api_key=key, callbacks=[callback], streaming=True)
    with patch("requests.post") as post:
        response = post.return_value.__enter__.return_value
        response.status_code = 200
        response.json.return_value = {"error": None, "output": {"content": [
            {"type": "text", "text": "One"}, {"type": "text", "text": "Two"},
        ]}}
        answer = model.invoke("Hello")
    assert answer.content == "One\nTwo"
    assert post.call_args.kwargs["headers"]["Authorization"] == key
    assert post.call_args.kwargs["json"]["stream"] is False
    assert callback.records
    assert key not in repr(callback.records)
    assert key not in repr(model)
    assert key not in json.dumps(model.model_dump())


@pytest.mark.parametrize("status,expected_calls", [(401, 1), (404, 1), (429, 2), (503, 2)])
def test_transport_retries_only_transient_failures(status, expected_calls):
    from tradingagents.llm_clients.bytez_client import BytezChatModelAdapter

    callback = CaptureCallbacks()
    key = "synthetic-secret-for-regression-test"
    model = _CompatibleBytezChatModel(model_id="zai-org/GLM-4.7", api_key=key, callbacks=[callback])
    llm = BytezChatModelAdapter(model, max_retries=1)
    with patch("requests.post") as post:
        response = post.return_value.__enter__.return_value
        response.status_code = status
        response.json.return_value = {"error": key, "output": None}
        with pytest.raises(BytezError) as exc:
            llm.invoke("hello")
    assert post.call_count == expected_calls
    assert key not in str(exc.value)
    assert key not in repr(callback.records)


def test_bytez_provider_only_environment_defaults(monkeypatch):
    from tradingagents.default_config import (
        DEFAULT_CONFIG,
        _apply_env_overrides,
        _apply_provider_defaults,
    )

    monkeypatch.setenv("TRADINGAGENTS_LLM_PROVIDER", "bytez")
    monkeypatch.delenv("TRADINGAGENTS_DEEP_THINK_LLM", raising=False)
    monkeypatch.delenv("TRADINGAGENTS_QUICK_THINK_LLM", raising=False)
    config = _apply_provider_defaults(_apply_env_overrides(DEFAULT_CONFIG.copy()))
    assert config["quick_think_llm"] == "zai-org/GLM-4.7"
    assert config["deep_think_llm"] == "zai-org/GLM-4.7"
    monkeypatch.setenv("TRADINGAGENTS_QUICK_THINK_LLM", "custom/model")
    config = _apply_provider_defaults(_apply_env_overrides(DEFAULT_CONFIG.copy()))
    assert config["quick_think_llm"] == "custom/model"


def test_bytez_key_skips_cli_prompt(monkeypatch):
    from cli.utils import ensure_api_key

    monkeypatch.setenv("BYTEZ_API_KEY", "synthetic-key")
    with patch("cli.utils.questionary.password") as prompt:
        assert ensure_api_key("bytez") == "synthetic-key"
    prompt.assert_not_called()
