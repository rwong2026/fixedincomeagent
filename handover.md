# Handoff: fixedincomeagent — UST Rates & Curve System

## What this repo is
A fork of TradingAgents repurposed into a US Treasury rates/curve analysis system.
It predicts, over a 20-trading-day horizon: (1) yield direction per tenor
(2Y/5Y/10Y/30Y → up/down/neutral) and (2) curve shape per spread
(2s10s, 5s30s, 2s5s10s_fly → steepen/flatten/unchanged). The LangGraph pipeline
is: 4 FI analysts → direction debate (higher vs lower yields) → direction manager
→ shape debate (steepener vs flattener, conditioned on direction outcome) → shape
manager → FI trader → consistency checker → FI portfolio manager. A Phase 7
backtest harness (ALFRED point-in-time replay, scoring, baselines, ablation) lives
in fixedincomeagent/backtest/.

Repo: https://github.com/rwong2026/fixedincomeagent (branch: feat/fi-transition-dual-track, PR #4).
All planned phases and FI transition complete: 1101 tests passing, ruff clean.

## Setup (do this first)
1. Python 3.11+ (3.13 used in dev). Then:
   ```bash
   python3.13 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   .venv/bin/pip install ruff pytest
   ```
2. Create `.env` in the repo root (gitignored) with:
   ```
   FRED_API_KEY=<get free key at fred.stlouisfed.org/docs/api/api_key.html>
   GOOGLE_API_KEY=<your Google AI key>
   FIXEDINCOMEAGENT_LLM_PROVIDER=google
   FIXEDINCOMEAGENT_QUICK_THINK_LLM=gemini-3.1-flash-lite
   FIXEDINCOMEAGENT_DEEP_THINK_LLM=gemini-3.1-flash-lite
   ```
   (Use cheap models for plumbing tests; ~15-25 LLM calls per single-date run.)
3. Verify: `.venv/bin/python -m pytest tests/ -q` → expect 1101 passed, 2 skipped.
   (Without FRED_API_KEY: 1096 passed, 5 skipped — 3 live-key tests skip.)
4. Verify lint: `.venv/bin/ruff check .` → must be clean. CI gates on this;
   run ruff before EVERY commit.

## Architecture orientation (5 min)
- `fixedincomeagent/api.py` — `FixedIncomeAnalysis` programmatic interface exposing `.run()` and `.run_streaming()`, decoupled from the CLI for future web frontends.
- `fixedincomeagent/dataflows/` — 13 data modules (`treasury_benchmark.py` computes equal-weight 2Y/5Y/10Y/30Y curve benchmark, yield deltas, alpha, and hit rates; `fred.py` is the vendor template):
  - `treasury_benchmark.py` — Equal-weight Treasury curve benchmark across 2Y, 5Y, 10Y, 30Y yields from FRED (`DGS2`, `DGS5`, `DGS10`, `DGS30`), computing yield changes in bp, strategy yield capture, alpha vs curve, and directional hit-rate (`hit:X/Y`)
  - `alfred.py` — ALFRED point-in-time vintage fetcher (backtest backbone)
  - `treasury.py` — home.treasury.gov CMT CSV (par curve is NOT in the Fiscal Data API) + Fiscal Data auctions
  - `fomc_calendar.py`, `fed_speeches.py` — static verified meeting list (2019–2027, update annually) + Fed RSS with loud fallback
  - `inflation_breakevens.py` — T5YIE/T10YIE/T5YIFR via FRED
  - `inflation_nowcast.py` — Cleveland Fed chart JSON (no CSV/XLSX exists anymore)
  - `shelter_rents.py` — Zillow ZORI live; Apartment List is local-file ingest (no stable URL)
  - `used_vehicle_index.py` + `ism_prices_paid.py` — MANUAL local-CSV ingests, empty until a human maintains the CSVs (schemas in module docstrings)
  - `supply_chain_pressure.py` — GSCPI chart CSV (the page's XLSX is corrupt server-side)
  - `consumer_inflation_expectations.py` — NY Fed SCE XLSX
  - `cot_data.py` — CFTC Socrata dataset `gpe5-46if`; code 020601 = classic 30Y, 020604 = Ultra Bond
- `fixedincomeagent/agents/` — `analysts/` (4 FI analysts), `researchers/` (4 debate researchers), `managers/` (direction/shape research managers, `fi_portfolio_manager`), `trader/fi_trader.py`, `risk_mgmt/fi_consistency_checker.py` (pure logic — parses the trader's rendered markdown, flags contradictions, never overrides), `schemas.py` (DirectionCall, ShapeCall, TraderDecision, MacroPolicyReport)
- `fixedincomeagent/graph/` — `setup.py` wires the dual-track debate; FI mode activates when ALL selected analysts are FI keys. `trading_graph.py`: `fi_mode` property gates rates context identity and routes deferred memory resolution to `_resolve_fi_pending_entries()`. `reflection.py`: `reflect_on_fi_decision` produces 2-4 sentence rates/curve reflections reviewing yield shifts and alpha vs the equal-weight curve.
- `fixedincomeagent/agents/utils/memory.py` — `TradingMemoryLog` supports dual metric formatting for float (equity `%`) and string (FI `hit:X/Y | alpha:+Xbp`) outcome tags.
- `cli/` — Re-skinned to default to Fixed Income: `cli/models.py` defines FI analyst enum types; `cli/utils.py` defaults ticker to `"UST"` with FI analysts pre-selected; `cli/main.py` dynamically switches between FI teams (Direction Debate, Shape Debate, FI Trading) and equity teams.
- `fixedincomeagent/backtest/` — `runner.py`, `regime_dates.py`, `scoring.py`, `baselines.py`, ablation via `AblationConfig`
- `graphify-out/` & Antigravity rules — Persistent codebase intelligence knowledge graph (`graph.html`, `graph.json`, `GRAPH_REPORT.md`) updated via git post-commit hooks and tracked via `GEMINI.md` / `AGENTS.md`.
- Tunables live in `default_config.py` (`fi_tenors`, `fi_spreads`, `fi_horizon_days=20`, `fi_neutral_threshold_bp=5`, `fi_*_series`, debate rounds). Never hardcode.

## Test entry point (single-date live run)

Programmatic API (recommended):
```python
from fixedincomeagent.api import FixedIncomeAnalysis

analysis = FixedIncomeAnalysis()
state, signal = analysis.run("UST", "2026-09-04")
```

Or direct `TradingAgentsGraph`:
```python
from fixedincomeagent.default_config import DEFAULT_CONFIG
from fixedincomeagent.graph.trading_graph import TradingAgentsGraph

ta = TradingAgentsGraph(
    selected_analysts=["macro_policy", "curve_technicals", "fed_speak", "macro_calendar"],
    debug=True,
    config=dict(DEFAULT_CONFIG),
)
_, decision = ta.propagate("UST", "2026-09-04")
```
Expect: full DirectionCall (4 tenors) + ShapeCall (3 spreads) coverage, signal
"REVIEW" by design. First run is slow (cold data cache in
`~/.fixedincomeagent/cache`); warm reruns ~2 min.

Or CLI interactive run:
```bash
.venv/bin/python -m cli.main
```
(Defaults to ticker `UST` and the 4 FI analysts; switches dynamically to FI debate and trading display tables.)

## Your work: open issues
1. https://github.com/rwong2026/fixedincomeagent/issues/1 — FI analyst/debate
   content is missing from saved run logs. `full_states_log_*.json` only
   serializes equity-shaped state keys; the FI reports, both debate sub-states
   (histories + judge decisions), and `trader_investment_plan` are all dropped.
   Start at `TradingAgentsGraph._log_state` and the reporting layer. Acceptance:
   a live FI run's saved JSON contains non-empty FI reports, both debate
   histories, and both judge decisions. Add a regression test (offline, stub LLM).
2. https://github.com/rwong2026/fixedincomeagent/issues/2 — the Google LLM
   client (`fixedincomeagent/llm_clients/`) emits a stderr deprecation warning
   on every call: "Direct use of automatic function calling (AFC) in
   Models.generate_content is not recommended... use AFC in Chat.send_message".
   No functional impact today, but the path is deprecated. Migrate the
   google client's generate/tool-call path to the supported API and add a test
   asserting no AFC-deprecation warning on a mocked call.
3. https://github.com/rwong2026/fixedincomeagent/issues/3 — [Tech Debt / Migration]
   Study and migrate or extract equity-track agents, tools, and dataflows.
   Dual-track architecture is preserved so equity capabilities are retained,
   while ensuring FI runs do not execute equity tools. Future work will
   evaluate which equity components to retool for fixed income or cleanly extract.

## Conventions (violating these fails review)
- TDD: failing test first, then implement. All network mocked in tests —
  tests must pass offline with no keys (see `tests/test_fred.py` for the pattern).
- Tests verify real behavior, not mocks-of-mocks.
- `ruff check .` clean before every commit; no noqa bypasses.
- Data modules fail LOUDLY on vendor format changes (name the source), and
  never cache unvalidated bodies.
- Point-in-time discipline: no future data leakage; note that 4 sources leak
  revisions-only (documented in `backtest/runner.py` docstring — nowcast,
  Zillow/AL rents, GSCPI, SCE).
- Equity mode must stay untouched: node-disjointness and mixed-selection tests
  guard this (`tests/test_fi_graph_wiring.py`).

## Known limitations (do not "fix" without discussion)
- Manheim + ISM need monthly manual CSV appends (schemas in docstrings).
- Apartment List has no stable download URL (Cloudflare + rotating assets).
- `fi_tenors`/`fi_spreads` Literals in `schemas.py` are static; config is the
  tunable source — a consistency test guards drift.
- Dual-track codebase: equity agents, tools, and dataflows remain in the
  codebase alongside FI (tracked in Issue #3 for future evaluation/extraction).

