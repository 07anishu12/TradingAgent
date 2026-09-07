"""The smoke runner must honor ticker selection and reject incomplete graphs."""

from unittest.mock import MagicMock

import pytest

from examples import run_bytez_glm47 as runner


def complete_state():
    decision = "**Rating**: Hold\n**Executive Summary**: Insufficient evidence."
    return {
        **dict.fromkeys((
            "market_report", "sentiment_report", "news_report", "fundamentals_report",
            "investment_plan", "trader_investment_plan",
        ), "Test report"),
        "final_trade_decision": decision,
        "investment_debate_state": dict.fromkeys(("bull_history", "bear_history", "judge_decision"), "Test report"),
        "risk_debate_state": {
            **dict.fromkeys(("aggressive_history", "neutral_history", "conservative_history"), "Test report"),
            "judge_decision": decision,
        },
    }


def test_pltr_only_runner_keeps_full_team_and_custom_model(monkeypatch, tmp_path):
    monkeypatch.setenv("BYTEZ_API_KEY", "synthetic-key")
    monkeypatch.setenv("TRADINGAGENTS_QUICK_THINK_LLM", "custom/quick")
    graph = MagicMock()
    graph.propagate.return_value = complete_state(), "Hold"
    factory = MagicMock(return_value=graph)
    monkeypatch.setattr(runner, "TradingAgentsGraph", factory)
    runner.main(["--tickers", "PLTR", "--date", "2026-01-15", "--output-dir", str(tmp_path)])
    graph.propagate.assert_called_once_with("PLTR", "2026-01-15")
    assert factory.call_args.kwargs["selected_analysts"] == runner.ANALYSTS
    cfg = factory.call_args.kwargs["config"]
    assert cfg["quick_think_llm"] == "custom/quick"
    assert cfg["max_debate_rounds"] == cfg["max_risk_discuss_rounds"] == 2
    graph.save_reports.assert_called_once()


def test_five_ticker_runner_invokes_all_tickers(monkeypatch, tmp_path):
    monkeypatch.setenv("BYTEZ_API_KEY", "synthetic-key")
    graph = MagicMock()
    graph.propagate.return_value = complete_state(), "Hold"
    monkeypatch.setattr(runner, "TradingAgentsGraph", MagicMock(return_value=graph))
    runner.main(["--date", "2026-01-15", "--output-dir", str(tmp_path)])
    assert [call.args[0] for call in graph.propagate.call_args_list] == list(runner.TICKERS)


def test_completion_guard_rejects_missing_agent():
    state = complete_state()
    state["risk_debate_state"]["neutral_history"] = ""
    with pytest.raises(RuntimeError, match="all agents"):
        runner.verify_complete(state, "Hold")


def test_completion_guard_rejects_unparseable_portfolio_decision():
    with pytest.raises(RuntimeError, match="machine-readable"):
        runner.verify_complete(complete_state(), "REVIEW")
