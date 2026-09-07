"""Regression checks for Ollama's wire format; opt-in local inference smoke test."""

import os

import pytest

from tradingagents.llm_clients.factory import create_llm_client


def test_ollama_token_budget_uses_supported_wire_field():
    llm = create_llm_client("ollama", "qwen3:4b", max_tokens=64).get_llm()
    payload = llm._get_request_payload("Hi")
    assert payload["max_tokens"] == 64
    assert "max_completion_tokens" not in payload
    assert llm._get_request_payload("Hi", max_tokens=16)["max_tokens"] == 16


def test_openai_token_budget_mapping_is_unchanged(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-test-key")
    llm = create_llm_client("openai", "gpt-4.1", base_url="http://example.invalid/v1", max_tokens=64).get_llm()
    payload = llm._get_request_payload("Hi")
    assert payload["max_completion_tokens"] == 64


def test_ollama_retries_invalid_typed_output_and_never_returns_freetext(monkeypatch):
    from langchain_core.exceptions import OutputParserException
    from langchain_core.runnables import RunnableLambda

    from tradingagents.agents.schemas import PortfolioDecision
    from tradingagents.llm_clients.errors import RequiredStructuredOutputError
    from tradingagents.llm_clients.openai_client import NormalizedChatOpenAI

    attempts = []

    def invalid(messages):
        attempts.append(messages)
        raise OutputParserException("Synthetic malformed response")

    monkeypatch.setattr(NormalizedChatOpenAI, "with_structured_output",
                        lambda *args, **kwargs: RunnableLambda(invalid))
    llm = create_llm_client("ollama", "qwen3:4b", max_retries=1).get_llm()
    with pytest.raises(RequiredStructuredOutputError, match="retry budget"):
        llm.with_structured_output(PortfolioDecision).invoke("Synthetic evidence")
    assert len(attempts) == 2
    assert "investment_thesis" in attempts[0][-1].content


@pytest.mark.skipif(os.getenv("OLLAMA_LIVE_TEST") != "1", reason="Set OLLAMA_LIVE_TEST=1 for local inference")
def test_local_chat_tools_schema_stream_and_budget():
    from langchain_core.tools import tool
    from langgraph.graph import END, START, MessagesState, StateGraph
    from langgraph.prebuilt import ToolNode

    from tradingagents.agents.schemas import PortfolioDecision

    llm = create_llm_client(
        "ollama", "qwen3:4b-tradingagents", base_url="http://127.0.0.1:11434/v1",
        max_tokens=1024, max_retries=0, timeout=120,
    ).get_llm()
    assert llm.invoke("Reply exactly LOCAL_OK.").content.strip() == "LOCAL_OK"

    @tool
    def echo(ticker: str) -> str:
        """Return a synthetic observation for a ticker."""
        return f"Synthetic observation for {ticker}"

    bound = llm.bind_tools([echo])
    prompt = "Call echo with ticker PLTR. After receiving its observation, summarize it without more tools."
    call = bound.invoke(prompt)
    assert call.tool_calls[0]["name"] == "echo"
    assert call.tool_calls[0]["args"] == {"ticker": "PLTR"}
    workflow = StateGraph(MessagesState)
    workflow.add_node("tools", ToolNode([echo]))
    workflow.add_edge(START, "tools")
    workflow.add_edge("tools", END)
    messages = workflow.compile().invoke({"messages": [("human", prompt), call]})["messages"]
    answer = bound.invoke(messages)
    assert not answer.tool_calls and "PLTR" in answer.content
    decision = llm.with_structured_output(PortfolioDecision).invoke(
        "Synthetic test with no market evidence: set rating Hold, use short strings and null optional prices."
    )
    assert isinstance(decision, PortfolioDecision) and decision.rating.value == "Hold"
    assert "".join(c.content for c in llm.stream("Reply exactly STREAM_OK.")).strip() == "STREAM_OK"
    capped = llm.invoke("Write a very long story.", max_tokens=16)
    assert capped.usage_metadata["output_tokens"] <= 16
