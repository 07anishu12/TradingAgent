"""Paid/external Bytez checks, disabled unless BYTEZ_LIVE_TEST=1.

The PLTR graph costs many more calls and additionally requires
BYTEZ_PLTR_LIVE_TEST=1. Override the model with BYTEZ_LIVE_MODEL.
Never insert a key here; use BYTEZ_API_KEY.
"""

from __future__ import annotations

import json
import os
from datetime import date
from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from tradingagents.agents.schemas import PortfolioDecision, PortfolioRating
from tradingagents.llm_clients.bytez_client import BytezError
from tradingagents.llm_clients.errors import RequiredStructuredOutputError
from tradingagents.llm_clients.factory import create_llm_client
from tradingagents.llm_clients.model_catalog import DEFAULT_BYTEZ_MODEL

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.getenv("BYTEZ_LIVE_TEST") != "1", reason="Set BYTEZ_LIVE_TEST=1 to call Bytez"),
]


@pytest.fixture
def live_llm():
    __tracebackhide__ = True
    if not os.getenv("BYTEZ_API_KEY", "").strip():
        pytest.fail("BYTEZ_LIVE_TEST=1 requires BYTEZ_API_KEY in the environment or local .env", pytrace=False)
    return create_llm_client(
        "bytez", os.getenv("BYTEZ_LIVE_MODEL") or DEFAULT_BYTEZ_MODEL,
        max_retries=int(os.getenv("TRADINGAGENTS_LLM_MAX_RETRIES") or "1"),
        max_tokens=int(os.getenv("TRADINGAGENTS_MAX_TOKENS") or "2048"),
        http_timeout_s=120,
    ).get_llm()


def _live_call(runnable, prompt):
    """Report safe provider diagnostics without dumping SDK frames or locals."""
    __tracebackhide__ = True
    try:
        return runnable.invoke(prompt)
    except (BytezError, RequiredStructuredOutputError) as exc:
        pytest.fail(str(exc), pytrace=False)
    except Exception:
        pytest.fail("Unexpected Bytez live-test failure; inspect the provider adapter locally", pytrace=False)


def test_live_auth_model_resolution_and_chat(live_llm):
    # A completed inference on the exact model ID validates both auth and
    # resolution. A local constructor alone does not establish either.
    response = _live_call(live_llm, "Reply with exactly BYTEZ_SMOKE_OK. Do not include reasoning.")
    assert isinstance(response, AIMessage)
    assert "BYTEZ_SMOKE_OK" in response.content


def test_live_json_response(live_llm):
    response = _live_call(live_llm, 'Return only this JSON object: {"ok": true}. No reasoning or Markdown.')
    assert json.loads(response.content.strip()) == {"ok": True}


def test_live_structured_decision_and_injected_parse_retry(live_llm):
    # Deterministically inject one malformed answer, then request a REAL
    # correction from the model. This tests our parse retry, not API throttling.
    live_invoke = live_llm.invoke
    attempts = 0

    def malformed_once(input, config=None, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return AIMessage(content="deliberately malformed JSON for retry test")
        return live_invoke(input, config=config, **kwargs)

    # The parse-retry budget is deliberately one for this controlled test.
    structured = live_llm.with_structured_output(PortfolioDecision)
    structured.max_retries = 1
    with patch.object(live_llm, "invoke", side_effect=malformed_once):
        result = _live_call(
            structured,
            "This is a synthetic test with no market evidence. Set rating to Hold. "
            "Use one short sentence each for executive_summary and investment_thesis; "
            "leave optional fields null. Do not invent prices or include reasoning outside JSON.",
        )
    assert attempts == 2
    assert isinstance(result, PortfolioDecision)
    assert result.rating == PortfolioRating.HOLD


def test_live_tool_intent_and_observation(live_llm):
    @tool
    def smoke_echo(ticker: str) -> str:
        """Return a synthetic observation for a ticker; no market data request."""
        return f"Synthetic observation received for {ticker}"

    from langgraph.prebuilt import ToolNode

    bound = live_llm.bind_tools([smoke_echo])
    request = "Call smoke_echo with ticker PLTR once. After its result, summarize the observation without more tools."
    call = _live_call(bound, request)
    assert len(call.tool_calls) == 1
    assert call.tool_calls[0]["name"] == "smoke_echo"
    assert call.tool_calls[0]["args"] == {"ticker": "PLTR"}
    observations = ToolNode([smoke_echo]).invoke({"messages": [call]})["messages"]
    answer = _live_call(bound, [("human", request), call, *observations])
    assert not answer.tool_calls
    assert "PLTR" in answer.content


@pytest.mark.skipif(os.getenv("BYTEZ_PLTR_LIVE_TEST") != "1", reason="Set BYTEZ_PLTR_LIVE_TEST=1 for the full PLTR graph")
def test_live_pltr_reaches_portfolio_manager(live_llm, tmp_path):
    from examples.run_bytez_glm47 import ANALYSTS, build_config, verify_complete
    from tradingagents.graph.trading_graph import TradingAgentsGraph

    config = build_config(tmp_path)
    model = os.getenv("BYTEZ_LIVE_MODEL") or DEFAULT_BYTEZ_MODEL
    config.update(deep_think_llm=model, quick_think_llm=model)
    graph = TradingAgentsGraph(selected_analysts=ANALYSTS, config=config)
    analysis_date = os.getenv("TRADINGAGENTS_ANALYSIS_DATE") or date.today().isoformat()
    state, signal = graph.propagate("PLTR", analysis_date)
    verify_complete(state, signal)
    graph.save_reports(state, "PLTR", tmp_path / "reports")
