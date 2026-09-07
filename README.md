<p align="center">
  <img src="assets/TauricResearch.png" style="width: 60%; height: auto;">
</p>

<div align="center" style="line-height: 1;">
  <a href="https://arxiv.org/abs/2412.20138" target="_blank"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2412.20138-B31B1B?logo=arxiv"/></a>
  <a href="https://discord.com/invite/hk9PGKShPK" target="_blank"><img alt="Discord" src="https://img.shields.io/badge/Discord-TradingResearch-7289da?logo=discord&logoColor=white&color=7289da"/></a>
  <a href="https://x.com/TauricResearch" target="_blank"><img alt="X Follow" src="https://img.shields.io/badge/X-TauricResearch-white?logo=x&logoColor=white"/></a>
  <a href="https://github.com/TauricResearch/" target="_blank"><img alt="Community" src="https://img.shields.io/badge/GitHub_Community-TauricResearch-14C290?logo=discourse"/></a>
</div>
<br>
<div align="center">
  <a href="https://github.com/TauricResearch" target="_blank"><img alt="TradingAgents #1 Repository of the Day" src="https://trendshift.io/api/badge/repositories/16192" width="250" height="55"/></a>
</div>
<br>
<div align="center">
  <!-- Keep these links. Translations will automatically update with the README. -->
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=de">Deutsch</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=es">Español</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=fr">français</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=ja">日本語</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=ko">한국어</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=pt">Português</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=ru">Русский</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=zh">中文</a>
</div>

---

# TradingAgents: Multi-Agents LLM Financial Trading Framework

## News
- [2026-08] **TradingAgents v0.4.0** released with look-ahead / point-in-time fixes across FRED macro, social sentiment, and the decision-log memory; clearer decision signals; working CLI checkpoint resume; Trader price grounding; and the GPT-5.6 and GLM-5.3 models. See [CHANGELOG.md](CHANGELOG.md) for the full list.
- [2026-07] **TradingAgents v0.3.1** released with correctness and stability fixes: Alpha Vantage look-ahead filtering, graph-router crash-safety, graph-shape-aware checkpoint resume, working crypto sentiment sources, a configurable LLM retry budget, Bedrock API-key auth, and Claude Sonnet 5 / Fable 5 support.
- [2026-06] **TradingAgents v0.3.0** released with a verified data-access contract, an expanded provider registry (NVIDIA, Kimi, Groq, Mistral, Bedrock, and any OpenAI-compatible endpoint), FRED and Polymarket data vendors, a current-generation model catalog, and a CI gate.
- [2026-05] **TradingAgents v0.2.5** released with the grounded Sentiment Analyst, GPT-5.5 etc. model coverage, Qwen/GLM/MiniMax dual-region support, `TRADINGAGENTS_*` env-var configurability with API-key auto-detection, remote Ollama support, non-US alpha benchmarks, and ticker path-traversal hardening.
- [2026-04] **TradingAgents v0.2.4** released with structured-output agents (Research Manager, Trader, Portfolio Manager), LangGraph checkpoint resume, persistent decision log, DeepSeek/Qwen/GLM/Azure provider support, Docker, and a Windows UTF-8 encoding fix.
- [2026-03] **TradingAgents v0.2.3** released with multi-language support, GPT-5.4 family models, unified model catalog, backtesting date fidelity, and proxy support.
- [2026-03] **TradingAgents v0.2.2** released with GPT-5.4/Gemini 3.1/Claude 4.6 model coverage, five-tier rating scale, OpenAI Responses API, Anthropic effort control, and cross-platform stability.
- [2026-02] **TradingAgents v0.2.0** released with multi-provider LLM support (GPT-5.x, Gemini 3.x, Claude 4.x, Grok 4.x) and improved system architecture.
- [2026-01] **Trading-R1** [Technical Report](https://arxiv.org/abs/2509.11420) released, with [Terminal](https://github.com/TauricResearch/Trading-R1) expected to land soon.

<div align="center">

🚀 [TradingAgents](#tradingagents-framework) | ⚡ [Installation & CLI](#installation-and-cli) | 🎬 [Demo](https://www.youtube.com/watch?v=90gr5lwjIho) | 📦 [Package Usage](#tradingagents-package) | 🤝 [Contributing](#contributing) | 📄 [Citation](#citation)

</div>

> 🎉 **TradingAgents** officially released! We have received numerous inquiries about the work, and we would like to express our thanks for the enthusiasm in our community.
>
> So we decided to fully open-source the framework. Looking forward to building impactful projects with you!

## TradingAgents Framework

TradingAgents is a multi-agent trading framework that mirrors the dynamics of real-world trading firms. By deploying specialized LLM-powered agents: from fundamental analysts, sentiment experts, and technical analysts, to trader, risk management team, the platform collaboratively evaluates market conditions and informs trading decisions. Moreover, these agents engage in dynamic discussions to pinpoint the optimal strategy.

<p align="center">
  <img src="assets/schema.png" style="width: 100%; height: auto;">
</p>

> TradingAgents framework is designed for research purposes. Trading performance may vary based on many factors, including the chosen backbone language models, model temperature, trading periods, the quality of data, and other non-deterministic factors. [It is not intended as financial, investment, or trading advice.](https://tauric.ai/disclaimer/)

Our framework decomposes complex trading tasks into specialized roles.

### Analyst Team
- Fundamentals Analyst: Evaluates company financials and performance metrics, identifying intrinsic values and potential red flags.
- Sentiment Analyst: Aggregates news headlines, StockTwits, and Reddit chatter into a single sentiment read to gauge short-term market mood.
- News Analyst: Monitors global news and macroeconomic indicators, interpreting the impact of events on market conditions.
- Technical Analyst: Utilizes technical indicators (like MACD and RSI) to detect trading patterns and forecast price movements.

<p align="center">
  <img src="assets/analyst.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

### Researcher Team
- Comprises both bullish and bearish researchers who critically assess the insights provided by the Analyst Team. Through structured debates, they balance potential gains against inherent risks.

<p align="center">
  <img src="assets/researcher.png" width="70%" style="display: inline-block; margin: 0 2%;">
</p>

### Trader Agent
- Composes reports from the analysts and researchers to make informed trading decisions, determining the timing and magnitude of trades.

<p align="center">
  <img src="assets/trader.png" width="70%" style="display: inline-block; margin: 0 2%;">
</p>

### Risk Management and Portfolio Manager
- Continuously evaluates portfolio risk by assessing market volatility, liquidity, and other risk factors. The risk management team evaluates and adjusts trading strategies, providing assessment reports to the Portfolio Manager for final decision.
- The Portfolio Manager approves/rejects the transaction proposal. If approved, the order will be sent to the simulated exchange and executed.

<p align="center">
  <img src="assets/risk.png" width="70%" style="display: inline-block; margin: 0 2%;">
</p>

## Installation and CLI

### Installation

Clone TradingAgents:
```bash
git clone https://github.com/TauricResearch/TradingAgents.git
cd TradingAgents
```

Create a virtual environment in any of your favorite environment managers:
```bash
conda create -n tradingagents python=3.12
conda activate tradingagents
```

Install the package and its dependencies:
```bash
pip install .
```

### Docker

Alternatively, run with Docker:
```bash
cp .env.example .env  # add your API keys
docker compose run --rm tradingagents
```

For local models with Ollama:
```bash
docker compose --profile ollama run --rm tradingagents-ollama
```

### Required APIs

TradingAgents supports multiple LLM providers. Set the API key for your chosen provider:

```bash
export OPENAI_API_KEY=...          # OpenAI (GPT)
export GOOGLE_API_KEY=...          # Google (Gemini)
export ANTHROPIC_API_KEY=...       # Anthropic (Claude)
export XAI_API_KEY=...             # xAI (Grok)
export DEEPSEEK_API_KEY=...        # DeepSeek
export DASHSCOPE_API_KEY=...       # Qwen — International (dashscope-intl.aliyuncs.com)
export DASHSCOPE_CN_API_KEY=...    # Qwen — China (dashscope.aliyuncs.com)
export ZHIPU_API_KEY=...           # GLM via Z.AI (international)
export ZHIPU_CN_API_KEY=...        # GLM via BigModel (China, open.bigmodel.cn)
export MINIMAX_API_KEY=...         # MiniMax — Global (api.minimax.io)
export MINIMAX_CN_API_KEY=...      # MiniMax — China (api.minimaxi.com)
export BYTEZ_API_KEY=...           # Bytez (GLM-4.7 and other Bytez models)
export OPENROUTER_API_KEY=...      # OpenRouter
export ALPHA_VANTAGE_API_KEY=...   # Alpha Vantage
```

For Azure OpenAI, copy `.env.enterprise.example` to `.env.enterprise` and fill in your credentials.

For AWS Bedrock, install the extra with `pip install ".[bedrock]"`, set `llm_provider: "bedrock"`, configure AWS credentials (environment variables, `~/.aws/credentials`, or an IAM role) and `AWS_DEFAULT_REGION`, and use a Bedrock model ID, e.g. `us.anthropic.claude-opus-4-8-v1:0`.

For local models, configure Ollama with `llm_provider: "ollama"`. The default endpoint is `http://localhost:11434/v1`; set `OLLAMA_BASE_URL` to point at a remote `ollama-serve`. Pull models with `ollama pull <name>`, and pick "Custom model ID" in the CLI for any model not listed by default.

For any other OpenAI-compatible server (vLLM, LM Studio, llama.cpp, or a custom relay), use `llm_provider: "openai_compatible"` and set the endpoint via `backend_url` (or `TRADINGAGENTS_LLM_BACKEND_URL`), e.g. `http://localhost:8000/v1` for vLLM or `http://localhost:1234/v1` for LM Studio. The model is whatever your server serves. No key is needed for local servers; set `OPENAI_COMPATIBLE_API_KEY` when the endpoint requires one.

Alternatively, copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

## Bytez / GLM-4.7

TradingAgents has a Bytez provider for GLM-4.7. From this checkout, install
the project and test tools, then configure the environment:

```bash
python -m pip install -e ".[dev]"
```

The published `langchain-bytez==0.0.7` pins `langchain==0.3.17`, which
conflicts with the modern LangChain core required by the Google provider.
The `bytez` extra is therefore **not currently a validated installation
path**. Do not downgrade existing providers to satisfy that pin. When the
official package cannot import, the adapter uses a LangChain chat model
that calls Bytez's native [model API](https://docs.bytez.com/http-reference/model/run).
Live validation on 2026-09-06 reached Bytez, but inference for
`zai-org/GLM-4.7` returned HTTP 404: Bytez reported that the model does not
exist or has not yet been added to its catalog. Both the documented and
legacy SDK authentication formats returned that result. The documented
catalog endpoint also returned HTTP 500, so no alternative model ID was
verified. Authentication, successful inference, and the full PLTR graph
remain unverified; Bytez must make the requested model available before
this backend can pass the live gate.

```env
BYTEZ_API_KEY=...
TRADINGAGENTS_LLM_PROVIDER=bytez
TRADINGAGENTS_DEEP_THINK_LLM=zai-org/GLM-4.7
TRADINGAGENTS_QUICK_THINK_LLM=zai-org/GLM-4.7
TRADINGAGENTS_LLM_MAX_RETRIES=2
```

Start with the opt-in, small live test suite, then a PLTR-only analysis:

```bash
BYTEZ_LIVE_TEST=1 python -m pytest -q tests/test_bytez_live.py
python examples/run_bytez_glm47.py --tickers PLTR
```

The tests check authentication/model resolution via real chat, plain JSON,
a typed Portfolio decision, and a tool-call/observation round trip. The parse
retry test injects one malformed response, then requests a real correction;
it does not simulate or claim to reproduce real API rate limits. Transport
retry behavior is covered with mocked HTTP failures in the unit tests.
Live tests are skipped unless `BYTEZ_LIVE_TEST=1`. Opting in without
`BYTEZ_API_KEY` fails with a setup error and makes no request. Requests use
a 120-second HTTP timeout and 2,048 output-token cap by default; override the
cap with `TRADINGAGENTS_MAX_TOKENS` if GLM exhausts it on reasoning.
To test a different model without changing the GLM defaults:

```bash
BYTEZ_LIVE_TEST=1 BYTEZ_LIVE_MODEL=Qwen/Qwen3-4B python -m pytest -q -x tests/test_bytez_live.py -k 'not pltr'
```

Bytez's [free plan](https://docs.bytez.com/model-api/docs/billing) covers open
models up to 7B parameters, one concurrent request, and a limited credit
allowance refreshed every four weeks; this is not unlimited free inference.
Keep auto-reload disabled in your Bytez account if you require zero paid usage.
Sequential live probes on 2026-09-06 for `Qwen/Qwen3-4B`,
`Qwen/Qwen2.5-3B-Instruct`, `meta-llama/Llama-3.2-3B-Instruct`,
`microsoft/Phi-3.5-mini-instruct`, and `HuggingFaceTB/SmolLM2-1.7B-Instruct`
all returned HTTP 404 before inference. Qwen3 also returned 404 through Bytez's
documented OpenAI-compatible endpoint; the catalog request returned HTTP 500.
These are small-model candidates, **not verified working Bytez backends**.
The catalog failure prevents an exhaustive available-model check.
A full PLTR runner attempt with Qwen3-4B also stopped at the first LLM
request with HTTP 404; it did not reach Portfolio Manager.

After a candidate passes the live compatibility tests, use it for the full
runner through the existing model overrides:

```bash
TRADINGAGENTS_DEEP_THINK_LLM=Qwen/Qwen3-4B \
TRADINGAGENTS_QUICK_THINK_LLM=Qwen/Qwen3-4B \
python examples/run_bytez_glm47.py --tickers PLTR --output-dir results/bytez_glm47/qwen3-4b
```

The full PLTR test requires an additional explicit flag because it runs all
agents and real data sources:

```bash
BYTEZ_LIVE_TEST=1 BYTEZ_PLTR_LIVE_TEST=1 python -m pytest -q tests/test_bytez_live.py -k pltr
```

Once PLTR succeeds, run all five tickers (PLTR, LMT, NVDA, MSFT, AVGO):

```bash
python examples/run_bytez_glm47.py
# Shortcut (not an autonomous market scanner):
python autonomous_research.py --provider bytez
```

Both runners accept `--tickers PLTR` and `--date YYYY-MM-DD`, use two debate
and two risk rounds, retain all four analysts, and save reports, checkpoints,
and memory under the ignored `results/bytez_glm47/` directory. Model environment
overrides are honored. Completion requires every agent's report and a parseable
Portfolio Manager rating. See `.env.bytez.example` for the full configuration.

Bytez's [LangChain integration](https://github.com/Bytez-com/langchain_bytez)
provides chat and streaming, but lacks native tool binding. The adapter sends
JSON instructions with complete tool argument schemas and validates the
existing Pydantic decision schemas. Exhausted JSON retries stop the run;
they never turn into an untyped Portfolio decision. `stream()` currently
buffers the response into one chunk to avoid replaying partial output on
retry. Native JSON-schema/tool-choice options are not advertised. Configurable
transport retries cover timeouts, HTTP 429 and temporary server failures;
authentication errors are not retried by the HTTP fallback.

## Local Qwen3 / Ollama

Run the full team locally with Qwen3 4B Instruct. No LLM API key is required.
The current Ollama `qwen3:4b` tag resolves to the thinking-only 2507 variant;
use [`qwen3:4b-instruct`](https://ollama.com/library/qwen3:4b-instruct) for this
workflow. The `qwen3:4b-tradingagents` profile shares its weights and sets a
32K context and bounded output. Existing models and providers remain available.

From this checkout on macOS:

```bash
brew install ollama
python3.12 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python autonomous_research.py --tickers PLTR
# After PLTR, run the five-stock experiment:
.venv/bin/python autonomous_research.py
```

The runner starts a localhost-only Ollama server if needed, downloads Instruct
if missing (about 2.5 GB), and creates the local profile. Alternatively, prepare
it manually with `ollama pull qwen3:4b-instruct` and
`ollama create qwen3:4b-tradingagents -f examples/ollama/Qwen3.Modelfile`.
Use `.env.ollama.example` for environment overrides. A pre-existing Ollama
server is reused; its own settings remain in effect.

`examples/run_ollama_qwen3.py` is the dedicated entry point. Both entry points
accept `--tickers`, `--date YYYY-MM-DD`, and `--output-dir`. They retain all
four analysts and two research/risk rounds, print per-agent progress, and save
reports plus `run_summary.json` under `results/ollama_qwen3/local-v1/`.
An interrupted ticker resumes from its checkpoint on the same date. The root
shortcut researches the five configured stocks; it is not an autonomous market
scanner or an order-execution system.

Ollama uses its native JSON-schema output mode with schema instructions and
Pydantic validation. Invalid or truncated decisions retry within the configured
budget and then stop with a clear error. The output cap is translated to
Ollama's `max_tokens` wire field. Increase `TRADINGAGENTS_MAX_TOKENS` if required.
Run the opt-in local compatibility test with:

```bash
OLLAMA_LIVE_TEST=1 .venv/bin/python -m pytest -q tests/test_ollama_local.py
```

Small models can misinterpret data or tools. Market data still comes from the
existing Yahoo Finance, FRED, and Polymarket stack. FRED needs its own key;
unavailable sources and rate limits can reduce the evidence in a report.

### CLI Usage

Launch the interactive CLI:
```bash
tradingagents          # installed command
python -m cli.main     # alternative: run directly from source
```
You will see a screen where you can select your desired tickers, analysis date, LLM provider, research depth, and more.

### Markets and tickers

TradingAgents works with any market Yahoo Finance covers, using the exchange-suffixed ticker. Company identity and the alpha benchmark resolve automatically per market.

- US: `AAPL`, `SPY`
- Hong Kong: `0700.HK` · Tokyo: `7203.T` · London: `AZN.L`
- India: `RELIANCE.NS`, `.BO` · Canada: `.TO` · Australia: `.AX`
- China A-shares: Shanghai `.SS`, Shenzhen `.SZ` (e.g. `600519.SS` for Kweichow Moutai)
- Crypto: `BTC-USD`, `ETH-USD`

<p align="center">
  <img src="assets/cli/cli_init.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

An interface will appear showing results as they load, letting you track the agent's progress as it runs.

<p align="center">
  <img src="assets/cli/cli_news.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

<p align="center">
  <img src="assets/cli/cli_transaction.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

## TradingAgents Package

### Implementation Details

We built TradingAgents with LangGraph to ensure flexibility and modularity. The framework supports multiple LLM providers: OpenAI, Google, Anthropic, xAI, DeepSeek, Qwen (Alibaba DashScope, international and China endpoints), GLM (Zhipu), MiniMax (global + China), OpenRouter, Ollama for local models, and Azure OpenAI for enterprise.

### Python Usage

To use TradingAgents inside your code, you can import the `tradingagents` module and initialize a `TradingAgentsGraph()` object. The `.propagate()` function will return a decision. You can run `main.py`, here's also a quick example:

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

ta = TradingAgentsGraph(debug=True, config=DEFAULT_CONFIG.copy())

# forward propagate
_, decision = ta.propagate("NVDA", "2026-01-15")
print(decision)
```

You can also adjust the default configuration to set your own choice of LLMs, debate rounds, etc.

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "openai"        # e.g. openai, google, anthropic, deepseek, groq, ollama; openai_compatible covers any OpenAI-compatible endpoint (vLLM, LM Studio, llama.cpp, ...)
config["deep_think_llm"] = "gpt-5.6"      # Model for complex reasoning
config["quick_think_llm"] = "gpt-5.6-luna" # Model for quick tasks
config["max_debate_rounds"] = 2

ta = TradingAgentsGraph(debug=True, config=config)
_, decision = ta.propagate("NVDA", "2026-01-15")
print(decision)
```

See `tradingagents/default_config.py` for all configuration options.

## Persistence and Recovery

TradingAgents persists two kinds of state across runs.

### Decision log

The decision log is always on. Each completed run appends its decision to `~/.tradingagents/memory/trading_memory.md`. On the next run for the same ticker, TradingAgents fetches the realised return (raw and alpha vs SPY), generates a one-paragraph reflection, and injects the most recent same-ticker decisions plus recent cross-ticker lessons into the Portfolio Manager prompt, so each analysis carries forward what worked and what didn't.

Override the path with `TRADINGAGENTS_MEMORY_LOG_PATH`.

### Checkpoint resume

Checkpoint resume is opt-in via `--checkpoint`. When enabled, LangGraph saves state after each node so a crashed or interrupted run resumes from the last successful step instead of starting over. On a resume run you will see `Resuming from step N for <TICKER> on <date>` in the logs; on a new run you will see `Starting fresh`. Checkpoints are cleared automatically on successful completion.

Per-ticker SQLite databases live at `~/.tradingagents/cache/checkpoints/<TICKER>.db` (override the base with `TRADINGAGENTS_CACHE_DIR`). Use `--clear-checkpoints` to reset all of them before a run.

```bash
tradingagents analyze --checkpoint           # enable for this run
tradingagents analyze --clear-checkpoints    # reset before running
```

```python
config = DEFAULT_CONFIG.copy()
config["checkpoint_enabled"] = True
ta = TradingAgentsGraph(config=config)
_, decision = ta.propagate("NVDA", "2026-01-15")
```

## Reproducibility

TradingAgents is LLM-driven, so two runs of the same ticker and date can differ. This is expected for a research tool built on language models, not a defect. The variation comes from a few distinct sources, and it helps to separate them.

Language model sampling is non-deterministic. Even at a fixed temperature, providers do not guarantee byte-identical output across calls, and reasoning models (the default GPT-5.x family, and any thinking-mode model) vary the most because their internal reasoning is itself sampled.

Live data moves. News, StockTwits, and Reddit return different content as time passes, so a run today sees different inputs than a run last week even for the same historical trade date. Pin the analysis date to hold the price and indicator window fixed, but the social and news sources still reflect "now".

To reduce variation you can lower the sampling temperature. Set `temperature` in your config (or `TRADINGAGENTS_TEMPERATURE` in `.env`); lower values make models that honor it more repeatable. The current curated models are reasoning-first and largely ignore temperature, so for tighter reproducibility use a non-reasoning model, which you can set explicitly via the Custom model ID option.

```python
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "openai"
config["temperature"] = 0.0
# Reasoning models ignore temperature. For tighter reproducibility, set a
# non-reasoning deep/quick model explicitly (e.g. via the Custom model ID option).
```

What does not vary anymore: the analyzed company identity is resolved deterministically from the ticker before any agent runs, and the market analyst grounds exact price and indicator claims in a verified data snapshot. Earlier reports of "different companies" or fabricated price levels across runs are addressed by these two mechanisms.

Backtest results are not guaranteed to match any published figure. Returns depend on the model, the temperature, the date range, data quality, and the sampling above. Treat the framework as a research scaffold for studying multi-agent analysis, not as a strategy with a fixed, replicable return.

## Contributing

Contributions are welcome: bug fixes, documentation, and feature ideas; past contributions are credited per release in [`CHANGELOG.md`](CHANGELOG.md).

## Citation

Please reference our work if you find *TradingAgents* provides you with some help :)

```
@misc{xiao2025tradingagentsmultiagentsllmfinancial,
      title={TradingAgents: Multi-Agents LLM Financial Trading Framework}, 
      author={Yijia Xiao and Edward Sun and Di Luo and Wei Wang},
      year={2025},
      eprint={2412.20138},
      archivePrefix={arXiv},
      primaryClass={q-fin.TR},
      url={https://arxiv.org/abs/2412.20138}, 
}
```
