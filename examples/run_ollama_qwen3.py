"""Run TradingAgents locally with Ollama's Qwen3:4b Instruct model."""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
from datetime import date
from pathlib import Path
from time import monotonic, sleep
from urllib.parse import urlsplit

from langchain_core.callbacks import BaseCallbackHandler

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

TICKERS = ("PLTR", "LMT", "NVDA", "MSFT", "AVGO")
ANALYSTS = ("market", "social", "news", "fundamentals")
MODEL = "qwen3:4b-tradingagents"
OLLAMA_URL = "http://127.0.0.1:11434/v1"


def ensure_runtime(config: dict, output_dir: Path) -> None:
    """Start a loopback-only Ollama server when needed and check model availability."""
    import requests

    base = config["backend_url"].rstrip("/").removesuffix("/v1")
    executable = shutil.which("ollama")
    if not executable and Path("/opt/homebrew/bin/ollama").exists():
        executable = "/opt/homebrew/bin/ollama"

    def available_models():
        response = requests.get(base + "/api/tags", timeout=5)
        response.raise_for_status()
        return {m["name"] for m in response.json()["models"]}

    try:
        models = available_models()
    except requests.ConnectionError:
        parts = urlsplit(base)
        if parts.hostname not in ("localhost", "127.0.0.1") or not executable:
            raise RuntimeError("Start Ollama at the configured OLLAMA_BASE_URL before running") from None
        output_dir.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, OLLAMA_HOST=f"127.0.0.1:{parts.port or 11434}",
                   OLLAMA_NO_CLOUD="1", OLLAMA_CONTEXT_LENGTH="32768",
                   OLLAMA_NUM_PARALLEL="1", OLLAMA_MAX_LOADED_MODELS="1",
                   OLLAMA_FLASH_ATTENTION="1", OLLAMA_KV_CACHE_TYPE="q8_0")
        with (output_dir / "ollama-server.log").open("ab") as log:
            process = subprocess.Popen([executable, "serve"], env=env, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
        print("Starting local Ollama server...", flush=True)
        for _ in range(30):
            try:
                models = available_models()
                break
            except requests.ConnectionError:
                if process.poll() is not None:
                    raise RuntimeError("Ollama could not start; see ollama-server.log") from None
                sleep(1)
        else:
            raise RuntimeError("Ollama did not become ready within 30 seconds")

    wanted = {config["deep_think_llm"], config["quick_think_llm"]}
    if MODEL in wanted and MODEL not in models and executable and urlsplit(base).hostname in ("localhost", "127.0.0.1"):
        env = dict(os.environ, OLLAMA_HOST=base)
        if "qwen3:4b-instruct" not in models:
            print("Downloading local Qwen3:4b Instruct (about 2.5 GB)...", flush=True)
            subprocess.run([executable, "pull", "qwen3:4b-instruct"], env=env, check=True)
        subprocess.run([executable, "create", MODEL, "-f",
                        str(Path(__file__).parent / "ollama" / "Qwen3.Modelfile")], env=env, check=True)
        models = available_models()
    missing = wanted - models
    if missing:
        raise RuntimeError("Pull the configured Ollama models first: " + ", ".join(sorted(missing)))


def build_config(output_dir: Path) -> dict:
    config = copy.deepcopy(DEFAULT_CONFIG)
    config.update({
        "llm_provider": "ollama",
        "backend_url": os.getenv("OLLAMA_BASE_URL", OLLAMA_URL),
        "deep_think_llm": os.getenv("TRADINGAGENTS_DEEP_THINK_LLM") or MODEL,
        "quick_think_llm": os.getenv("TRADINGAGENTS_QUICK_THINK_LLM") or MODEL,
        "max_debate_rounds": 2,
        "max_risk_discuss_rounds": 2,
        "checkpoint_enabled": True,
        "max_tokens": int(os.getenv("TRADINGAGENTS_MAX_TOKENS", "1536")),
        "llm_max_retries": int(os.getenv("TRADINGAGENTS_LLM_MAX_RETRIES", "2")),
        "results_dir": str(output_dir),
        "data_cache_dir": str(output_dir / "cache"),
        "memory_log_path": str(output_dir / "memory" / "trading_memory.md"),
    })
    return config


class Progress(BaseCallbackHandler):
    """Show progress without printing prompts, tool data, or credentials."""

    def __init__(self):
        self.started = monotonic()

    def on_chat_model_start(self, serialized, messages, *, metadata=None, **kwargs):
        node = (metadata or {}).get("langgraph_node", "LLM")
        print(f"[{monotonic() - self.started:.0f}s] {node}: generating", flush=True)

    def on_llm_end(self, response, **kwargs):
        generation = response.generations[0][0]
        message = generation.message
        calls = getattr(message, "tool_calls", [])
        detail = ", ".join(call["name"] for call in calls) or "report"
        finish = (generation.generation_info or {}).get("finish_reason", "unknown")
        print(f"[{monotonic() - self.started:.0f}s] Received {detail} ({finish})", flush=True)


def verify_complete(final_state: dict, decision: str) -> None:
    from tradingagents.agents.schemas import PortfolioRating

    reports = [final_state.get(key) for key in (
        "market_report", "sentiment_report", "news_report", "fundamentals_report",
        "investment_plan", "trader_investment_plan", "final_trade_decision",
    )]
    research = final_state.get("investment_debate_state", {})
    risk = final_state.get("risk_debate_state", {})
    reports += [research.get(key) for key in ("bull_history", "bear_history", "judge_decision")]
    reports += [risk.get(key) for key in (
        "aggressive_history", "neutral_history", "conservative_history", "judge_decision",
    )]
    if not all(reports) or risk["judge_decision"] != final_state["final_trade_decision"]:
        raise RuntimeError("Ollama graph did not complete all agents through Portfolio Manager")
    if research.get("count") != 4 or risk.get("count") != 6:
        raise RuntimeError("Ollama graph did not complete both debate and risk rounds")
    if decision not in {rating.value for rating in PortfolioRating}:
        raise RuntimeError("Ollama graph completed without a machine-readable Portfolio rating")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickers", nargs="+", choices=TICKERS, default=list(TICKERS))
    parser.add_argument("--date", default=os.getenv("TRADINGAGENTS_ANALYSIS_DATE") or date.today().isoformat())
    parser.add_argument("--output-dir", type=Path, default=Path("results/ollama_qwen3/local-v1"))
    args = parser.parse_args(argv)
    try:
        analysis_date = date.fromisoformat(args.date)
        if analysis_date > date.today():
            raise ValueError
    except ValueError:
        parser.error("--date must be YYYY-MM-DD and not in the future")

    config = build_config(args.output_dir)
    ensure_runtime(config, args.output_dir)
    graph = TradingAgentsGraph(selected_analysts=ANALYSTS, config=config, debug=False, callbacks=[Progress()])
    summary = []
    for ticker in args.tickers:
        print(f"{'=' * 50}\n{ticker}\n{'=' * 50}", flush=True)
        final_state, decision = graph.propagate(ticker, analysis_date.isoformat())
        verify_complete(final_state, decision)
        report_path = args.output_dir / ticker / analysis_date.isoformat()
        graph.save_reports(final_state, ticker, report_path)
        summary.append({"ticker": ticker, "date": analysis_date.isoformat(), "rating": decision,
                        "model": config["deep_think_llm"], "reports": str(report_path)})
        (args.output_dir / "run_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(final_state["final_trade_decision"])
        print(f"\nPortfolio Manager completed: {decision}\nReports: {report_path}\n", flush=True)


if __name__ == "__main__":
    main()
