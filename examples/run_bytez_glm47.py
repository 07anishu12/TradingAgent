"""Run the full TradingAgents workflow with Bytez; use --tickers PLTR first."""

from __future__ import annotations

import argparse
import copy
import os
from datetime import date
from pathlib import Path

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.llm_clients.model_catalog import DEFAULT_BYTEZ_MODEL

TICKERS = ("PLTR", "LMT", "NVDA", "MSFT", "AVGO")
ANALYSTS = ("market", "social", "news", "fundamentals")


def build_config(output_dir: Path) -> dict:
    config = copy.deepcopy(DEFAULT_CONFIG)
    config.update({
        "llm_provider": "bytez",
        "backend_url": None,
        "deep_think_llm": os.getenv("TRADINGAGENTS_DEEP_THINK_LLM") or DEFAULT_BYTEZ_MODEL,
        "quick_think_llm": os.getenv("TRADINGAGENTS_QUICK_THINK_LLM") or DEFAULT_BYTEZ_MODEL,
        "max_debate_rounds": 2,
        "max_risk_discuss_rounds": 2,
        "checkpoint_enabled": True,
        "results_dir": str(output_dir),
        "data_cache_dir": str(output_dir / "cache"),
        "memory_log_path": str(output_dir / "memory" / "trading_memory.md"),
    })
    return config


def verify_complete(final_state: dict, decision: str) -> None:
    """Require every agent's report and a parseable final Portfolio rating."""
    from tradingagents.agents.schemas import PortfolioRating

    reports = [
        final_state.get(key) for key in (
            "market_report", "sentiment_report", "news_report", "fundamentals_report",
            "investment_plan", "trader_investment_plan", "final_trade_decision",
        )
    ]
    research = final_state.get("investment_debate_state", {})
    risk = final_state.get("risk_debate_state", {})
    reports += [research.get(key) for key in ("bull_history", "bear_history", "judge_decision")]
    reports += [risk.get(key) for key in (
        "aggressive_history", "neutral_history", "conservative_history", "judge_decision",
    )]
    if not all(reports) or risk["judge_decision"] != final_state["final_trade_decision"]:
        raise RuntimeError("Bytez graph did not complete all agents through Portfolio Manager")
    if decision not in {rating.value for rating in PortfolioRating}:
        raise RuntimeError("Bytez graph completed without a machine-readable Portfolio rating")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickers", nargs="+", choices=TICKERS, default=list(TICKERS))
    parser.add_argument("--date", default=os.getenv("TRADINGAGENTS_ANALYSIS_DATE") or date.today().isoformat())
    parser.add_argument("--output-dir", type=Path, default=Path("results/bytez_glm47"))
    args = parser.parse_args(argv)
    try:
        analysis_date = date.fromisoformat(args.date)
        if analysis_date > date.today():
            raise ValueError
    except ValueError:
        parser.error("--date must be YYYY-MM-DD and not in the future")
    if not os.environ.get("BYTEZ_API_KEY"):
        raise SystemExit("Set BYTEZ_API_KEY before running this example.")

    config = build_config(args.output_dir)
    graph = TradingAgentsGraph(selected_analysts=ANALYSTS, config=config, debug=False)
    for ticker in args.tickers:
        print(f"{'=' * 50}\n{ticker}\n{'=' * 50}", flush=True)
        final_state, decision = graph.propagate(ticker, analysis_date.isoformat())
        verify_complete(final_state, decision)
        report_path = args.output_dir / ticker / analysis_date.isoformat()
        graph.save_reports(final_state, ticker, report_path)
        print(final_state["final_trade_decision"])
        print(f"\nPortfolio Manager completed: {decision}\nReports: {report_path}\n", flush=True)


if __name__ == "__main__":
    main()
