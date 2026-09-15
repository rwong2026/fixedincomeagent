# Graph Report - fixedincomeagent  (2026-09-07)

## Corpus Check
- 231 files · ~285,256 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3057 nodes · 6378 edges · 180 communities (143 shown, 34 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 282 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c5f6c81a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- _make_api_request
- _stub
- GoogleClient
- fi_data_tools.py
- _request_stub
- BaseLLMClient
- test_backtest_runner.py
- test_baselines.py
- TraderDecision
- make_log
- test_reddit_fallback.py
- TradingAgentsGraph
- TestDeferredReflection
- test_ollama_base_url.py
- get_capabilities
- agents/__init__.py
- _stub
- TaggedArgument
- cli/main.py
- baselines.py
- Propagator
- test_macro_policy_analyst.py
- schemas.py
- test_backtest_scoring.py
- test_consumer_expectations.py
- _stub
- normalize_symbol
- OpenAIClient
- FredFormattingTests
- build_instrument_context
- FixedIncomeAnalysis
- AssetType
- create_llm_client
- SignalProcessor
- reddit.py
- test_checkpoint_resume.py
- test_fi_graph_wiring.py
- y_finance.py
- DeepSeekChatOpenAI
- _sample_ohlcv
- fred.py
- get_api_key_env
- test_ablation.py
- TradingMemoryLog
- ism_prices_paid.py
- test_treasury_benchmark.py
- create_fed_speak_analyst
- consumer_inflation_expectations.py
- test_social_lookahead.py
- build_analyst_execution_plan
- test_fi_portfolio_manager.py
- test_structured_agent_prompts.py
- ._run_graph
- get_alfred_vintage
- test_env_overrides.py
- patch
- ._write_csv
- ._write_csv
- test_cli_symbol_handling.py
- in_window
- _local_midnight (test_ohlcv_latest_bar.py)
- test_openrouter_model_select.p (test_openrouter_model_select.py)
- openai_client.py
- invoke_structured_or_freetext
- test_llm_max_retries.py
- TestMinimaxStructuredOutputDispatch
- test_polymarket.py
- VendorRoutingTests
- BaseCallbackHandler (stats_handler.py)
- test_fi_consistency.py
- test_direction_debate.py
- shelter_rents.py
- test_instrument_identity.py
- _assert_ohlcv_not_stale
- ConditionalLogic
- _ohlcv
- TestProviderKwargsTemperature
- create_portfolio_manager
- resolve_instrument_identity
- validators.py
- TestEffortGate
- FedSpeechesTests
- test_memory_log.py
- _stub
- provider_default_url
- test_shape_debate.py
- thread_id
- test_stocktwits_resilience.py
- ContextAnchoredPlaceholderTests
- safe_ticker_component
- BreakevensFetchTests
- test_graph_setup_threads_disabled_tools_to_analysts
- _select_model
- test_fi_trader.py
- set_config
- unit
- checkpointer.py
- inflation_breakevens.py
- test_checkpoint_lifecycle.py
- FredNotConfiguredError
- news_data_tools.py
- test_regime_dates.py
- fed_speeches.py
- test_ohlcv_cache_freshness.py
- used_vehicle_index.py
- test_llm_max_tokens.py
- MessageBuffer
- create_macro_calendar_analyst
- .get_completed_reports_count
- treasury.py
- test_fi_interface.py
- test_fi_config_models.py
- interface.py
- test_structured_agents.py
- .__init__
- test_reporting.py
- GetInstrumentContextFromStateTests
- test_memory_pointintime.py
- test_risk_router_path_map.py
- _build_run_config
- create_curve_technicals_analyst
- memory.py
- polymarket.py
- test_fi_research_managers.py
- conftest.py
- .get_llm
- fundamental_data_tools.py
- Any
- TestLegacyRemoval
- ._should_continue_analyst
- TraderProposal
- Path
- dataflows/utils.py
- inflation_nowcast.py
- RunnableLambda
- unit
- stockstats_utils.py
- supply_chain_pressure.py
- test_equity_state_logging
- ._fetch_returns
- market_data_validator.py
- .__init__
- Q: what equity or single stock elements are in the code base?
- ._resolve_pending_entries
- Any
- test_i18n_coverage.py
- FixedIncomeAgent Multi-Agent Framework
- default_config.py
- get_curve_spreads
- Antigravity Project Instructions
- parametrize
- Antigravity Project Instructions
- cli/utils.py
- CI Workflow
- Docker Configuration
- Project Dependencies
- Analyst Team Diagram
- CLI Initialization Screenshot
- CLI News Analysis Screenshot
- CLI Technical Analysis Screenshot
- CLI Transaction Decision Screenshot
- Researcher Team Diagram
- Risk Management Diagram
- System Architecture Schema
- Tauric Research Logo
- Trader Agent Diagram
- date
- ValueError
- ToolNode
- fixedincomeagent
- unit
- date_window.py
- .__init__
- datetime
- unit
- date
- ValueError

## God Nodes (most connected - your core abstractions)
1. `TradingAgentsGraph` - 74 edges
2. `set_config()` - 52 edges
3. `get_config()` - 50 edges
4. `ConditionalLogic` - 48 edges
5. `get_language_instruction()` - 48 edges
6. `make_log()` - 41 edges
7. `route_to_vendor()` - 40 edges
8. `DirectionCall` - 34 edges
9. `get_capabilities()` - 34 edges
10. `ShapeCall` - 32 edges

## Surprising Connections (you probably didn't know these)
- `HierarchyTests` --uses--> `NoMarketDataError`  [INFERRED]
  tests/test_vendor_errors.py → fixedincomeagent/dataflows/errors.py
- `HierarchyTests` --uses--> `FredNotConfiguredError`  [INFERRED]
  tests/test_vendor_errors.py → fixedincomeagent/dataflows/fred.py
- `test_graph_setup_threads_disabled_tools_to_analysts()` --uses--> `TradingAgentsGraph`  [INFERRED]
  tests/test_ablation.py → fixedincomeagent/graph/trading_graph.py
- `test_tool_nodes_filtered_by_disabled_tools()` --uses--> `TradingAgentsGraph`  [INFERRED]
  tests/test_ablation.py → fixedincomeagent/graph/trading_graph.py
- `test_tool_nodes_unfiltered_by_default()` --uses--> `TradingAgentsGraph`  [INFERRED]
  tests/test_ablation.py → fixedincomeagent/graph/trading_graph.py

## Import Cycles
- None detected.

## Communities (180 total, 34 thin omitted)

### Community 0 - "_make_api_request"
Cohesion: 0.05
Nodes (54): Exception, AlphaVantageNotConfiguredError, AlphaVantageRateLimitError, _filter_csv_by_date_range(), format_datetime_for_api(), get_api_key(), _make_api_request(), Filter CSV data to include only rows within the specified date range. Args:… (+46 more)

### Community 1 - "_stub"
Cohesion: 0.12
Nodes (12): _apartment_list_csv(), ApartmentListIngestTests, _month_seq(), unit, Shelter & rents vendor (Zillow ZORI + Apartment List rent estimates). All HTTP…, Yield (year, month) for ``count`` consecutive months., ShelterReportTests, _ShelterTestCase (+4 more)

### Community 2 - "GoogleClient"
Cohesion: 0.07
Nodes (31): AsyncCallbackManagerForLLMRun, BaseLLMClient, BaseMessage, CallbackManagerForLLMRun, ChatGoogleGenerativeAI, ChatResult, _FeedShapeError, The RSS feed returned 200 with an unexpected structure. (+23 more)

### Community 3 - "fi_data_tools.py"
Cohesion: 0.10
Nodes (28): get_alfred_vintage(), get_auction_results(), get_consumer_inflation_expectations(), get_cot_data(), get_fed_speeches(), get_fomc_calendar(), get_inflation_breakevens(), get_inflation_nowcast() (+20 more)

### Community 4 - "_request_stub"
Cohesion: 0.12
Nodes (8): AuctionResultsTests, ParYieldFetchingTests, ParYieldFormattingTests, unit, Treasury.gov vendor: par yield curve and auction results. All HTTP is mocked at…, Build a treasury._request replacement dispatching on the URL., _request_stub(), _TreasuryTestCase

### Community 5 - "BaseLLMClient"
Cohesion: 0.06
Nodes (28): ABC, AzureChatOpenAI, AnthropicClient, Client for Anthropic Claude models., Validate model for Anthropic., AzureOpenAIClient, NormalizedAzureChatOpenAI, Any (+20 more)

### Community 6 - "test_backtest_runner.py"
Cohesion: 0.12
Nodes (30): BacktestRunner, _entry_and_exit(), Any, Baseline = last observation on/before test_date; exit = the ``horizon_days``-th…, Replays the FI pipeline over historical test dates and scores outcomes.…, _business_days(), _decision(), _four_tenor_stub() (+22 more)

### Community 7 - "test_baselines.py"
Cohesion: 0.15
Nodes (32): callable, BaselineRun, forwards_implied_baseline(), no_change_baseline(), Random-walk prior: "neutral"/"unchanged" everywhere, zero implied move. Uses no…, Forward-curve-implied moves over the horizon (see module docstring)., Re-skin baseline predictions as BacktestRuns scored by score_backtest. Realized…, One baseline's predictions for a test date (scorer-ready call lists). (+24 more)

### Community 8 - "TraderDecision"
Cohesion: 0.15
Nodes (21): _annotate(), ConsistencyWarning, fi_consistency_check_node(), _is_directional(), parse_trader_decision(), Fixed-Income Risk Consistency Check: pure-logic validator (no LLM). Sits…, Signed magnitude ordinal: up positive, down negative, neutral zero., Graph node: validate ``trader_investment_plan`` and flag conflicts. Parses the… (+13 more)

### Community 9 - "make_log"
Cohesion: 0.08
Nodes (15): make_log(), Calling store_decision twice with same (ticker, date) stores only one entry., batch_update_with_outcomes resolves multiple pending entries in one write., Rating: X' label wins even when an opposing rating word appears earlier in…, LLM decision containing '---' must not corrupt the entry., Only the n_same most recent same-ticker entries are included., Only the n_cross most recent cross-ticker entries are included., Without max_entries, all resolved entries are kept. (+7 more)

### Community 10 - "test_reddit_fallback.py"
Cohesion: 0.08
Nodes (20): HTTPError, _atom_resp(), unit, _raise(), Tests for the RSS-first Reddit fetcher, its 429 backoff, the opt-in JSON path's…, The opt-in JSON path still degrades to RSS on a 403 (kept for #862)., IncompleteRead/RemoteDisconnected come from http.client and are NOT OSErrors,…, A crypto pair (BTC-USD) barely matches Reddit text; search the base (#1113). (+12 more)

### Community 11 - "TradingAgentsGraph"
Cohesion: 0.10
Nodes (21): True when only fixed-income analysts are active., Run the trading agents graph for a company on a specific date. ``asset_type``…, Restore the plain uncheckpointed graph after a checkpointed run., Context-manager form of begin/end_checkpoint for the propagate path., Main class that orchestrates the trading agents framework., TradingAgentsGraph, unit, The market analyst is bound (and prompt-instructed) to call… (+13 more)

### Community 12 - "TestDeferredReflection"
Cohesion: 0.06
Nodes (21): Any, Initialize the reflector with an LLM., Concise prompt for reflect_on_final_decision (Phase B log entries). Produces…, Single reflection call on the final trade decision with outcome context. Used…, SCAFFOLDING ONLY — opt-in, not called from any live graph path. Thin delegate…, Handles reflection on trading decisions., Reflector, Pick the benchmark ticker for alpha calculation against ``ticker``.… (+13 more)

### Community 13 - "test_ollama_base_url.py"
Cohesion: 0.08
Nodes (37): get_model_options(), Return shared model options for a provider and selection mode., ModelOption, cli_utils(), fixture, Import cli.utils with a fresh environment so module-level state is consistent., _base_url(), fixture (+29 more)

### Community 14 - "get_capabilities"
Cohesion: 0.07
Nodes (19): get_capabilities(), ModelCapabilities, Declarative per-model capability table for OpenAI-compatible providers. This is…, Resolve capabilities by exact ID, then pattern, then default., What an OpenAI-compatible model accepts at the API level., unit, Unit tests for the LLM capability table., deepseek-chat must NOT match the v\\d regex. (+11 more)

### Community 15 - "agents/__init__.py"
Cohesion: 0.13
Nodes (30): create_fundamentals_analyst(), create_market_analyst(), create_news_analyst(), create_bear_researcher(), create_bull_researcher(), create_aggressive_debator(), create_conservative_debator(), create_neutral_debator() (+22 more)

### Community 16 - "_stub"
Cohesion: 0.07
Nodes (22): _cache_path(), CotFormatError, _fmt(), get_cot_data(), _load_rows(), _parse_rows(), date, ValueError (+14 more)

### Community 17 - "TaggedArgument"
Cohesion: 0.15
Nodes (16): Any, BaseModel, Argument tagging scaffold for credit assignment (Phase 6, Task 6.1).…, A debate argument tagged for credit assignment (scaffolding only)., Wrapper so with_structured_output can return a list of tags., Tag individual debate arguments via one structured LLM call. Returns an empty…, tag_debate_arguments(), TaggedArgument (+8 more)

### Community 18 - "cli/main.py"
Cohesion: 0.08
Nodes (31): CLI Welcome Screen, display_announcements(), fetch_announcements(), Fetch announcements from endpoint. Returns dict with announcements and settings., Display announcements panel. Prompts for Enter if require_attention is True., analyze(), classify_message_type(), create_layout() (+23 more)

### Community 19 - "baselines.py"
Cohesion: 0.08
Nodes (28): _direction_call(), _implied_change_bp(), Baseline comparisons (Task 7.4): the two bars every scorecard must beat. 1.…, Maturity in years of a configured tenor label like ``"10Y"``., Front-of-curve forward minus spot, in bp (see module docs)., Shape calls from per-tenor implied changes; runner spread semantics., _shape_calls(), _tenor_years() (+20 more)

### Community 20 - "Propagator"
Cohesion: 0.12
Nodes (20): AgentState, DirectionDebateState, InvestDebateState, TypedDict, State for the yield-direction debate (higher vs lower yields)., State for the curve-shape debate (steepener vs flattener). Runs second,…, RiskDebateState, ShapeDebateState (+12 more)

### Community 21 - "test_macro_policy_analyst.py"
Cohesion: 0.15
Nodes (26): create_macro_policy_analyst(), InflationComponentTrajectory, MacroPolicyReport, MarketImpliedExpectations, BaseModel, Trajectory assessment for a single inflation component., Market-based inflation expectations from TIPS breakevens., Survey-based inflation expectations. (+18 more)

### Community 22 - "schemas.py"
Cohesion: 0.14
Nodes (23): DirectionCall, Pydantic schemas used by agents that produce structured output. The framework's…, Structured yield-direction prediction for a single tenor., Render a DirectionCall to markdown., Structured curve-shape prediction for a single spread., Render a ShapeCall to markdown., Render a DirectionOutlook to markdown for the trader's prompt context., Per-spread shape outlook produced by the Shape Research Manager. One ShapeCall… (+15 more)

### Community 23 - "test_backtest_scoring.py"
Cohesion: 0.25
Nodes (21): BacktestScorecard, Markdown summary of a scorecard., Flat, printable aggregate over a list of BacktestRun., Score replayed runs into an aggregate BacktestScorecard., render(), score_backtest(), _dcall(), unit (+13 more)

### Community 24 - "test_consumer_expectations.py"
Cohesion: 0.13
Nodes (9): _build_xlsx(), unit, NY Fed Survey of Consumer Expectations: median inflation expectations vendor.…, SceCacheTests, SceFormatErrorTests, SceParsingTests, _SceTestCase, _sheet() (+1 more)

### Community 25 - "_stub"
Cohesion: 0.13
Nodes (10): _chart(), NowcastCacheTests, NowcastFormatErrorTests, NowcastParsingTests, _NowcastTestCase, _payload(), unit, Cleveland Fed inflation nowcast vendor. All HTTP is mocked at the module's… (+2 more)

### Community 26 - "normalize_symbol"
Cohesion: 0.11
Nodes (15): crypto_base(), is_yahoo_safe(), _normalize_crypto(), normalize_symbol(), Symbol normalization and market-data error types for vendor calls. Yahoo…, Map a user/broker symbol to its canonical Yahoo Finance symbol. Resolution…, True when ``symbol`` only contains characters Yahoo symbols use., Return the crypto base (e.g. ``BTC``) for a known USD/USDT/USDC-quoted crypto… (+7 more)

### Community 27 - "OpenAIClient"
Cohesion: 0.10
Nodes (19): _is_native_openai_base_url(), OpenAIClient, Any, Whether the (native OpenAI) model accepts ``reasoning_effort``., True when ``base_url`` is unset or points at api.openai.com. The Responses API…, Client for OpenAI, Ollama, OpenRouter, and xAI providers. For native OpenAI…, Return a configured ChatOpenAI instance, driven by the provider registry., Validate model for the provider. (+11 more)

### Community 28 - "FredFormattingTests"
Cohesion: 0.08
Nodes (8): FredConfigTests, FredFormattingTests, FredResolutionTests, FredRoutingTests, unit, FRED macro vendor: alias resolution, configuration errors, output formatting,…, Build a _request replacement that dispatches on the endpoint path., _request_stub()

### Community 29 - "build_instrument_context"
Cohesion: 0.28
Nodes (5): build_instrument_context(), Describe the exact instrument so agents preserve identity and ticker. When…, Resolve ticker identity once and return the full instrument context.…, BuildInstrumentContextTests, unit

### Community 30 - "FixedIncomeAnalysis"
Cohesion: 0.15
Nodes (16): FixedIncomeAnalysis, Any, Path, Public programmatic API for FixedIncomeAgent. Allows running Fixed Income (or…, Write report markdown tree to disk., High-level API for orchestrating fixed-income (and dual-track) analysis., Initialize the analysis orchestration. Args: config: Configuration dictionary…, Run complete analysis synchronously to completion. Returns a dictionary… (+8 more)

### Community 31 - "AssetType"
Cohesion: 0.24
Nodes (10): AnalystType, AssetType, Enum, str, detect_asset_type(), filter_analysts_for_asset_type(), Select analysts using an interactive checkbox., Classify on the canonical symbol so e.g. BTCUSD and BTC-USDT both read as… (+2 more)

### Community 32 - "create_llm_client"
Cohesion: 0.15
Nodes (25): Resolve the backend URL with the correct precedence. An explicit env override…, resolve_backend_url(), create_llm_client(), Create an LLM client for the specified provider. Provider modules are imported…, Check if model name is valid for the given provider. For ollama, openrouter,…, validate_model(), _capture_kwargs(), unit (+17 more)

### Community 33 - "SignalProcessor"
Cohesion: 0.08
Nodes (21): Append pending entry at end of propagate(). No LLM call., extract_rating(), is_review(), parse_rating(), Shared 5-tier rating vocabulary and a deterministic heuristic parser. The same…, Extract a 5-tier rating from prose, or ``None`` if none is present. Two-pass…, Extract a 5-tier rating, falling back to ``default`` when none is found. Legacy…, Whether a signal is the non-tradeable REVIEW sentinel (#1170). (+13 more)

### Community 34 - "reddit.py"
Cohesion: 0.14
Nodes (20): _fetch_subreddit(), _fetch_subreddit_json(), _fetch_subreddit_rss(), _iso_to_timestamp(), _jitter(), Reddit search fetcher for ticker-specific discussion posts. Default path is…, Return ``seconds`` with +/-``frac`` random jitter, to desynchronize concurrent…, Seconds to wait from a 429's ``Retry-After`` header, capped at 30s. Returns… (+12 more)

### Community 35 - "test_checkpoint_resume.py"
Cohesion: 0.18
Nodes (13): has_checkpoint(), Check whether a resumable checkpoint exists for ticker+date., _build_graph(), _node_a(), _node_b(), StateGraph, TypedDict, Test checkpoint resume: crash mid-analysis, re-run resumes from last node. (+5 more)

### Community 36 - "test_fi_graph_wiring.py"
Cohesion: 0.15
Nodes (23): _edges(), _nodes(), parametrize, RunnableLambda, unit, Task 4.5: wire the FI dual-track debate (direction -> shape) into the graph. FI…, Regression: an all-FI *subset* (e.g. only macro_policy) still wires the full FI…, Offline LLM: answers every prompt with a fixed AIMessage, never calls tools,… (+15 more)

### Community 37 - "y_finance.py"
Cohesion: 0.11
Nodes (24): NoMarketDataError, A vendor returned no usable rows for a symbol (empty result or stale data).…, Execute a yfinance call with exponential backoff on rate limits. yfinance…, StockstatsUtils, yf_retry(), get_balance_sheet(), get_cashflow(), get_fundamentals() (+16 more)

### Community 38 - "DeepSeekChatOpenAI"
Cohesion: 0.07
Nodes (26): DeepSeekChatOpenAI, _input_to_messages(), Normalise a langchain LLM input to a list of message objects. Accepts a list of…, DeepSeek-specific overrides on top of the OpenAI-compatible client. Thinking-…, integration, skipif, _bound_kwargs(), _Pick (+18 more)

### Community 39 - "_sample_ohlcv"
Cohesion: 0.23
Nodes (6): DataFrame, unit, Tests for the deterministic market-data verification snapshot (#830/#881)., _sample_ohlcv(), TestTool, TestVerifiedSnapshot

### Community 40 - "fred.py"
Cohesion: 0.17
Nodes (14): ALFRED (Archival FRED) point-in-time vintage fetcher. Returns economic data as…, _fred_today(), get_macro_data(), _get_session(), Session, FRED (Federal Reserve Economic Data) macro vendor. Fetches macroeconomic time…, Map a friendly alias to a FRED series ID, or pass a raw ID through. Raises…, FRED's current calendar date (US Central) as ``yyyy-mm-dd``. The vintage pin is… (+6 more)

### Community 41 - "get_api_key_env"
Cohesion: 0.10
Nodes (19): ensure_api_key(), Make sure the API key for `provider` is available in the environment. If the…, get_api_key_env(), Canonical provider -> API-key env-var mapping. A single source of truth for…, Return the env var name for `provider`'s API key, or None if not applicable.…, parametrize, Tests for the canonical provider->env-var mapping and the CLI key-prompt helper., When key is missing, user-pasted value must be written to .env AND os.environ. (+11 more)

### Community 42 - "test_ablation.py"
Cohesion: 0.18
Nodes (23): ablation_disabled_tools(), AblationConfig, Config for ablation testing., Map ablation flags to the tool names to drop. Ablation removes DATA, not agents…, _bound_names(), Ablation support (Task 7.5): run the pipeline with data sources removed.…, _state(), test_ablation_config_defaults() (+15 more)

### Community 43 - "TradingMemoryLog"
Cohesion: 0.13
Nodes (9): Append-only markdown log of trading decisions and reflections., Replace pending tag and append REFLECTION section using atomic write. Finds the…, Apply multiple outcome updates in a single read + atomic write. Each element of…, Build a resolved entry tag, recording the outcome's known-by date.…, Drop oldest resolved blocks when their count exceeds max_entries. Pending…, Parse all entries from log. Returns list of dicts., Return entries with outcome:pending (for Phase B)., Return formatted past context string for agent prompt injection. When ``as_of``… (+1 more)

### Community 44 - "ism_prices_paid.py"
Cohesion: 0.23
Nodes (11): _csv_path(), get_ism_prices_paid(), ISMFormatError, _mom(), _parse(), date, ValueError, ISM Manufacturing Prices Index ("prices paid"): input-cost pressure. LIMITATION… (+3 more)

### Community 45 - "test_treasury_benchmark.py"
Cohesion: 0.15
Nodes (20): calculate_treasury_curve_benchmark(), evaluate_directional_hit(), parse_direction_calls(), Any, Treasury curve equal-weight benchmark calculation for Fixed Income reflection.…, Calculate Treasury curve benchmark yield changes and decision hit-rate. Args:…, Extract normalized per-tenor direction calls from markdown or a dictionary., Evaluate whether an individual tenor direction prediction was correct. (+12 more)

### Community 46 - "create_fed_speak_analyst"
Cohesion: 0.31
Nodes (11): create_fed_speak_analyst(), _FakeLLM, Tests for the Fed Speak Analyst (Task 3.3). Offline: a fake LLM captures the…, Captures the bound tools and rendered prompt; returns a canned report., _state(), test_binds_expected_tool_set(), test_node_returns_fed_speak_report_state_key(), test_preamble_carries_final_transaction_proposal_stop_signal() (+3 more)

### Community 47 - "consumer_inflation_expectations.py"
Cohesion: 0.20
Nodes (15): _cache_path(), get_consumer_inflation_expectations(), _load_rows(), _month_end(), _parse_rows(), date, ValueError, NY Fed Survey of Consumer Expectations: median inflation expectations. Source… (+7 more)

### Community 48 - "test_social_lookahead.py"
Cohesion: 0.16
Nodes (17): fetch_reddit_posts(), Fetch recent Reddit posts mentioning ``ticker`` across finance subreddits and…, fetch_stocktwits_messages(), Fetch recent StockTwits messages for ``ticker`` and return them as a formatted…, _epoch(), _JsonResp, _msg(), unit (+9 more)

### Community 49 - "build_analyst_execution_plan"
Cohesion: 0.18
Nodes (8): AnalystExecutionPlan, AnalystNodeSpec, AnalystWallTimeTracker, build_analyst_execution_plan(), get_initial_analyst_node(), sync_analyst_tracker_from_chunk(), AnalystExecutionPlanTests, AnalystWallTimeTrackerTests

### Community 50 - "test_fi_portfolio_manager.py"
Cohesion: 0.17
Nodes (16): _free_text_llm(), _graph(), RunnableLambda, unit, Fixed-Income Portfolio Manager (Task 5.3) and the completed FI graph wiring.…, Phase 5 carryover: _log_state reads final_trade_decision; the FI PM now writes…, Offline LLM: fixed AIMessage for every prompt, no structured output., _state() (+8 more)

### Community 51 - "test_structured_agent_prompts.py"
Cohesion: 0.12
Nodes (24): field_validator, _coerce_optional_float(), PortfolioDecision, PortfolioRating, Enum, str, Structured output produced by the Portfolio Manager. The model fills every…, Render a PortfolioDecision back to the markdown shape the rest of the system… (+16 more)

### Community 52 - "._run_graph"
Cohesion: 0.13
Nodes (8): Point-in-time cutoff for past-context lessons (#1251). A historical/backtest…, Graph-shape inputs that must invalidate a checkpoint if changed. Keyed into the…, The value to stream/invoke: ``None`` to resume an existing checkpoint, else the…, Drop a completed run's checkpoint so a later run starts fresh (#1249)., Execute the graph and write the resulting state to disk and memory log., Log the final state to a JSON file., Process a signal to extract the core decision., Path

### Community 53 - "get_alfred_vintage"
Cohesion: 0.14
Nodes (16): get_alfred_vintage(), get_vintage_dates(), Return available vintage dates for a FRED series (ALFRED). Args: series_id:…, Fetch a FRED series as it was known on vintage_date (ALFRED). Args: series_id:…, _needs_key, AlfredMockedTests, unit, Tests for ALFRED point-in-time vintage fetcher. The three live-key tests are… (+8 more)

### Community 54 - "test_env_overrides.py"
Cohesion: 0.14
Nodes (20): parametrize, Tests for FIXEDINCOMEAGENT_* env-var overlay onto DEFAULT_CONFIG., Garbage int values should surface a ValueError at import, not silently…, A misspelled boolean must fail loudly (like ints) instead of silently False., Env vars outside _ENV_OVERRIDES must not bleed into DEFAULT_CONFIG., Set/clear env vars then reload default_config to re-evaluate DEFAULT_CONFIG., The provider reasoning/thinking knobs are env-configurable (non-interactive…, Unset reasoning/thinking knobs stay None so each provider uses its own default. (+12 more)

### Community 55 - "patch"
Cohesion: 0.31
Nodes (8): patch, _mock_route(), Tests for the pre-computed curve spreads tool (Issue 1 fix). Verifies that…, Intercept route_to_vendor and return fake par yields., test_2s10s_spread_is_41_bp(), test_5s30s_spread_is_70_bp(), test_butterfly_is_minus_7_bp(), test_returns_error_when_par_yields_unavailable()

### Community 56 - "._write_csv"
Cohesion: 0.16
Nodes (5): IsmIngestTests, IsmReportTests, _IsmTestCase, unit, ISM Manufacturing Prices Index ("prices paid") — manual local-CSV ingest. The…

### Community 57 - "._write_csv"
Cohesion: 0.16
Nodes (5): unit, Manheim Used Vehicle Value Index — manual local-CSV ingest. The module reads…, UsedVehicleIngestTests, UsedVehicleReportTests, _UsedVehicleTestCase

### Community 58 - "test_cli_symbol_handling.py"
Cohesion: 0.14
Nodes (14): get_ticker(), is_valid_ticker_input(), normalize_ticker_symbol(), Whether a ticker entry is acceptable (charset + length). Allows the characters…, Prompt the user to enter a ticker symbol, preserving exchange suffixes. Uses…, Resolve user input to its canonical Yahoo symbol (single source of truth).…, parametrize, CLI symbol validation/classification must agree with the data path. Regressions… (+6 more)

### Community 59 - "in_window"
Cohesion: 0.18
Nodes (20): in_window(), Whether an item belongs in the half-open window ``[start, end + 1 day)``.…, _extract_article_data(), get_global_news_yfinance(), get_news_yfinance(), yfinance-based news data fetching functions., Retrieve global/macro economic news using yfinance Search. Args: curr_date:…, Extract article data from yfinance news format (handles nested 'content'… (+12 more)

### Community 60 - "_local_midnight (test_ohlcv_latest_bar.py)"
Cohesion: 0.19
Nodes (18): _local_midnight(), _normalize_dates(), A single timestamp as its naive, midnight-normalized local date (or NaT)., Parse to naive, midnight-normalized dates so tz-aware or intraday timestamps…, unit, The latest trading day's bar must not silently vanish (#1201). yfinance can…, Drive load_ohlcv against a pre-seeded cache frame (no network)., _run_load() (+10 more)

### Community 61 - "test_openrouter_model_select.p (test_openrouter_model_select.py)"
Cohesion: 0.16
Nodes (9): _asks(), parametrize, unit, OpenRouter model selection: prompts are labeled by mode (#1000); required…, TestCancelExitsCleanly, TestLanguageDefaultsToEnglish, TestMainstreamFilter, TestOpenRouterLatestFirst (+1 more)

### Community 62 - "openai_client.py"
Cohesion: 0.15
Nodes (15): ChatOpenAI, is_openai_compatible(), LocalCompatibleChatOpenAI, NormalizedChatOpenAI, ProviderSpec, ChatOpenAI with normalized content output and capability-aware binding. The…, Declarative config for one OpenAI-compatible provider. The OpenAI-compatible…, Whether ``provider`` is served by the OpenAI-compatible registry. (+7 more)

### Community 63 - "invoke_structured_or_freetext"
Cohesion: 0.15
Nodes (18): create_direction_research_manager(), Direction Research Manager: judges the higher/lower yields debate into a per-…, create_fi_portfolio_manager(), Fixed-Income Portfolio Manager: final synthesis of the desk's curve calls.…, Portfolio Manager: synthesises the risk-analyst debate into the final decision.…, create_shape_research_manager(), Shape Research Manager: judges the steepener/flattener debate into a per-spread…, create_fi_trader() (+10 more)

### Community 64 - "test_llm_max_retries.py"
Cohesion: 0.27
Nodes (17): _coerce_max_retries(), Validate an ``llm_max_retries`` value to a non-negative int. Accepts an int or…, _bare_graph(), parametrize, unit, Configurable LLM SDK retry budget (#1090/#1091). A single transient 429 burst…, _reload_with_env(), test_coerce_accepts_non_negative_ints_and_numeric_strings() (+9 more)

### Community 65 - "TestMinimaxStructuredOutputDispatch"
Cohesion: 0.18
Nodes (11): MinimaxChatOpenAI, MiniMax-specific overrides on top of the OpenAI-compatible client. M2.x…, _client(), _Pick, BaseModel, unit, Tests for MinimaxChatOpenAI quirks. Verifies the subclass injects…, Coding Plan / MiniMax-Text-01 / any non-M2-prefixed model must NOT receive… (+3 more)

### Community 66 - "test_polymarket.py"
Cohesion: 0.13
Nodes (6): PolymarketFilterTests, PolymarketFormatTests, PolymarketResilienceTests, PolymarketRoutingTests, unit, Polymarket prediction-market vendor: forward-looking filtering, volume ranking,…

### Community 67 - "VendorRoutingTests"
Cohesion: 0.21
Nodes (7): _no_data(), unit, _raises(), Vendor router must respect the configured chain and never silently hide a…, _reset_config(), _returns(), VendorRoutingTests

### Community 68 - "BaseCallbackHandler (stats_handler.py)"
Cohesion: 0.15
Nodes (10): BaseCallbackHandler, Any, Callback handler that tracks LLM calls, tool calls, and token usage., Increment LLM call counter when an LLM starts., Increment LLM call counter when a chat model starts., Extract token usage from LLM response., Increment tool call counter when a tool starts., Return current statistics. (+2 more)

### Community 69 - "test_fi_consistency.py"
Cohesion: 0.28
Nodes (21): check_consistency(), Flag direction/shape contradictions. Never overrides a call. A rule only fires…, _dc(), Fixed-Income Risk Consistency Check (Task 5.2). Pure-logic validator between…, _sc(), test_belly_outperforms_and_fly_steepens_no_warning(), test_belly_outperforms_but_fly_flatten_flagged(), test_belly_underperforms_but_fly_steepen_flagged() (+13 more)

### Community 70 - "test_direction_debate.py"
Cohesion: 0.42
Nodes (12): create_higher_yields_researcher(), create_lower_yields_researcher(), _capturing_llm(), _direction_state(), unit, Direction debate researchers: higher vs lower yields (Task 4.1). Parallel…, test_higher_yields_opening_has_no_phantom_opponent(), test_higher_yields_prompt_includes_reports_and_opponent() (+4 more)

### Community 71 - "shelter_rents.py"
Cohesion: 0.12
Nodes (27): _apartment_list_path(), ApartmentListFormatError, _by_month(), _dollars(), get_shelter_rents(), _load_apartment_list(), _load_zillow(), _parse_apartment_list() (+19 more)

### Community 72 - "test_instrument_identity.py"
Cohesion: 0.25
Nodes (5): build_fi_instrument_context(), Instrument context for fixed-income (rates/curve) runs. FI mode analyzes a…, FIInstrumentContextTests, Tests for deterministic instrument-identity resolution (#814) and the context-…, FI mode must anchor agents to the yield curve, not resolve the ticker through…

### Community 73 - "_assert_ohlcv_not_stale"
Cohesion: 0.18
Nodes (8): _assert_ohlcv_not_stale(), Reject OHLCV whose latest row is far older than curr_date. Raises…, _frame(), unit, Stale OHLCV guard (#1021): a vendor returning a year-old partial frame must be…, StaleGuardPropagationTests, StaleGuardRoutingTests, StaleGuardUnitTests

### Community 74 - "ConditionalLogic"
Cohesion: 0.14
Nodes (22): ConditionalLogic, Route the steepener/flattener debate; hand to the Shape Research Manager once…, Determine if risk analysis should continue., Determine if market analysis should continue., Determine if sentiment-analyst tool round should continue. Method name keeps…, Determine if fundamentals analysis should continue., Handles conditional logic for determining graph flow., Determine if debate should continue. (+14 more)

### Community 75 - "_ohlcv"
Cohesion: 0.17
Nodes (9): _ohlcv(), DataFrame, unit, Tests for tolerating a non-`Date` index column in stockstats_utils (#890).…, OHLCV frame whose date column is named `date_col`., A frame with `index` instead of `Date` must still clean to a usable, date-…, stockstats must compute indicators on a frame whose date column arrived as…, TestCleanDataframeAcrossVersions (+1 more)

### Community 76 - "TestProviderKwargsTemperature"
Cohesion: 0.16
Nodes (7): parametrize, unit, Tests for the configurable sampling temperature (#178/#168). Temperature is a…, _get_provider_kwargs float-coerces and forwards temperature, or omits it., TestProviderKwargsTemperature, TestTemperatureEnvOverlay, TestTemperatureForwarding

### Community 77 - "create_portfolio_manager"
Cohesion: 0.15
Nodes (18): create_portfolio_manager(), create_research_manager(), Research Manager: turns the bull/bear debate into a structured investment plan…, Render a ResearchPlan to markdown for storage and the trader's prompt context., Structured investment plan produced by the Research Manager. Hand-off to the…, render_research_plan(), ResearchPlan, main() (+10 more)

### Community 78 - "resolve_instrument_identity"
Cohesion: 0.33
Nodes (3): Resolve deterministic identity metadata (company name, sector, …) for a ticker.…, resolve_instrument_identity(), ResolveInstrumentIdentityTests

### Community 79 - "validators.py"
Cohesion: 0.18
Nodes (7): get_known_models(), Shared model catalog for CLI selections and validation., Build known model names from the shared CLI catalog., Model name validators for each provider., DummyLLMClient, ModelValidationTests, unit

### Community 80 - "TestEffortGate"
Cohesion: 0.21
Nodes (8): _capture_kwargs(), parametrize, unit, Tests for Anthropic effort-parameter gating (#831). Haiku (any version) and…, Forward-compat: new Opus/Sonnet versions don't need a code change., Default is conservative — unknown models don't get effort to avoid 400s., Skipping effort must not break other passthrough kwargs., TestEffortGate

### Community 81 - "FedSpeechesTests"
Cohesion: 0.07
Nodes (6): FedSpeechesTests, FomcCalendarTests, FomcDateListIntegrityTests, _FomcTestCase, unit, Redirect the data cache to a temp dir so tests never touch the real one.

### Community 82 - "test_memory_log.py"
Cohesion: 0.08
Nodes (19): _make_pm_state(), Tests for TradingMemoryLog — storage, deferred reflection, PM injection, legacy…, When max_entries is set and exceeded, oldest resolved entries are pruned., Pending entries (unresolved) are kept regardless of the cap., No rotation when resolved count <= max_entries., Store a decision then immediately resolve it via the API., Minimal AgentState dict for portfolio_manager_node., PM prompt omits the lessons section entirely when past_context is empty. (+11 more)

### Community 83 - "_stub"
Cohesion: 0.13
Nodes (7): GscpiCacheTests, GscpiFormatErrorTests, GscpiParsingTests, _GscpiTestCase, unit, NY Fed GSCPI supply chain pressure vendor. All HTTP is mocked at the module's…, _stub()

### Community 84 - "provider_default_url"
Cohesion: 0.19
Nodes (8): provider_default_url(), Return the default backend URL for a provider key, or None if unknown., unit, Tests for env-driven CLI behavior (#897, #873). The config-layer override…, TestCliSkipsPromptsFromEnv, TestProviderDefaultUrl, TestReasoningEffortSkippedFromEnv, TestResearchDepthSkippedFromEnv

### Community 85 - "test_shape_debate.py"
Cohesion: 0.42
Nodes (12): create_flattener_researcher(), create_steepener_researcher(), _capturing_llm(), unit, Shape debate researchers: steepener vs flattener (Task 4.2). Run after the…, _shape_state(), test_flattener_opening_has_no_phantom_opponent(), test_flattener_prompt_includes_reports_direction_outcome_and_opponent() (+4 more)

### Community 86 - "thread_id"
Cohesion: 0.28
Nodes (4): Deterministic thread ID for a ticker+date pair. ``signature`` folds in graph-…, thread_id(), A different graph shape (analyst selection / depth / asset mode) must not…, TestCheckpointSignature

### Community 87 - "test_stocktwits_resilience.py"
Cohesion: 0.27
Nodes (6): parametrize, unit, _raise(), StockTwits fetch: transport-error resilience (#1024) and crypto symbol mapping…, TestStockTwitsCryptoSymbols, TestStockTwitsResilience

### Community 89 - "safe_ticker_component"
Cohesion: 0.21
Nodes (6): Validate ``value`` is safe to interpolate into a filesystem path. Tickers come…, safe_ticker_component(), unit, Tests for the ticker path-component validator that blocks directory traversal., Sanity: sanitized values stay within base when joined., TestSafeTickerComponent

### Community 90 - "BreakevensFetchTests"
Cohesion: 0.23
Nodes (4): BreakevensFetchTests, unit, Build a fred._request replacement dispatching on series_id., _request_stub()

### Community 91 - "test_graph_setup_threads_disabled_tools_to_analysts"
Cohesion: 0.29
Nodes (4): RunnableLambda, _CapturingStubLLM, Offline LLM recording every bind_tools list it receives., test_graph_setup_threads_disabled_tools_to_analysts()

### Community 92 - "_select_model"
Cohesion: 0.16
Nodes (14): _fetch_openrouter_models(), _prompt_custom_model_id(), Fetch available models from the OpenRouter API., Prompt for a required value; exit cleanly if the user cancels.…, Select an OpenRouter model from the newest available, or enter a custom ID.…, Prompt user to type a custom model ID., Select a model for the given provider and mode (quick/deep)., Select shallow thinking llm engine using an interactive selection. (+6 more)

### Community 93 - "test_fi_trader.py"
Cohesion: 0.31
Nodes (13): _free_text_llm(), _full_coverage_decision(), unit, Fixed-Income Trader (Task 5.1): emits DirectionCall[]/ShapeCall[]. Consumes the…, LLM without structured-output support, forcing the free-text path., LLM whose structured binding returns a real TraderDecision instance., _state(), _structured_llm() (+5 more)

### Community 94 - "set_config"
Cohesion: 0.09
Nodes (22): get_config(), initialize_config(), Initialize the configuration with default values., Update the configuration with custom values. Dict-valued keys (e.g.…, Get the current configuration., set_config(), _fmt_meeting(), get_fomc_calendar() (+14 more)

### Community 95 - "unit"
Cohesion: 0.15
Nodes (20): Create tool nodes for different data sources using abstract methods.…, parametrize, test_tool_nodes_filtered_by_disabled_tools(), test_tool_nodes_unfiltered_by_default(), _compile(), Task 3.5: register the four fixed-income analysts in the graph setup. Offline:…, test_builds_and_compiles_with_fi_analyst(), test_equity_keys_still_compile() (+12 more)

### Community 96 - "checkpointer.py"
Cohesion: 0.20
Nodes (14): checkpoint_step(), clear_all_checkpoints(), clear_checkpoint(), _db_path(), get_checkpointer(), Path, LangGraph checkpoint support for resumable analysis runs. Per-ticker SQLite…, Return the SQLite checkpoint DB path for a ticker. (+6 more)

### Community 97 - "inflation_breakevens.py"
Cohesion: 0.33
Nodes (5): _fetch_points(), get_inflation_breakevens(), Inflation breakevens (FRED): TIPS-implied inflation compensation. Fetches the…, Fetch one series' in-window observations, skipping FRED's '.' missings., Fetch the configured inflation breakeven series as one markdown report. Args:…

### Community 98 - "test_checkpoint_lifecycle.py"
Cohesion: 0.27
Nodes (13): _bare_graph(), _node_a(), _node_b(), StateGraph, TypedDict, unit, The checkpoint lifecycle is reusable so --checkpoint works on the CLI path…, _State (+5 more)

### Community 99 - "FredNotConfiguredError"
Cohesion: 0.29
Nodes (7): FredNotConfiguredError, get_api_key(), Raised when FRED is selected but no API key is configured. A…, Retrieve the FRED API key from the environment., If FRED is not configured, fail open with None and do not crash., test_calculate_treasury_curve_benchmark_missing_api_key(), VendorNotConfiguredError

### Community 100 - "news_data_tools.py"
Cohesion: 0.32
Nodes (7): get_global_news(), get_insider_transactions(), get_news(), tool, Retrieve news data for a given ticker symbol. Uses the configured news_data…, Retrieve global news data. Uses the configured news_data vendor. Defaults for…, Retrieve insider transaction information about a company. Uses the configured…

### Community 101 - "test_regime_dates.py"
Cohesion: 0.24
Nodes (11): all_dates(), Curated backtest test dates spanning distinct rate regimes (Task 7.2). Each…, Every regime test date flattened into one sorted, de-duplicated list., unit, Regime test dates (Task 7.2): curated test-date set spanning regimes., test_all_dates_flattened_sorted_unique(), test_dates_are_strict_iso_sorted_and_unique(), test_dates_fall_inside_named_regime_window() (+3 more)

### Community 102 - "fed_speeches.py"
Cohesion: 0.17
Nodes (18): date, _fallback(), get_fed_speeches(), _parse_items(), _parse_json_items(), Fed speeches vendor: recent speeches by Federal Reserve officials. Source: the…, Fetch recent Fed official speeches as a markdown report. Tries the RSS feed…, GET the RSS feed and return the raw response body. (+10 more)

### Community 103 - "test_ohlcv_cache_freshness.py"
Cohesion: 0.31
Nodes (12): _needs_same_day_refresh(), Whether a cached frame must be refetched to reflect the requested day. The…, unit, Same-day OHLCV cache must not serve a stale snapshot all day (#1150). The cache…, End-to-end: the helper is actually wired into load_ohlcv's cache branch.…, test_current_day_cache_past_ttl_is_refreshed(), test_historical_request_always_uses_cache(), test_load_ohlcv_refetches_stale_same_day_cache() (+4 more)

### Community 104 - "used_vehicle_index.py"
Cohesion: 0.23
Nodes (12): _by_month(), _csv_path(), get_used_vehicle_index(), ManheimFormatError, _parse(), _pct(), date, ValueError (+4 more)

### Community 105 - "test_llm_max_tokens.py"
Cohesion: 0.24
Nodes (19): _coerce_max_tokens(), Validate a ``max_tokens`` value to a positive int (env vars are strings)., _bare_graph(), parametrize, unit, Configurable output-token cap (#1204). Some model/gateway combinations (e.g.…, _reload_with_env(), test_coerce_accepts_positive_ints_and_numeric_strings() (+11 more)

### Community 106 - "MessageBuffer"
Cohesion: 0.14
Nodes (13): MessageBuffer, Update analyst statuses based on accumulated report state. Logic: - Store new…, Initialize agent status and report sections based on selected analysts. Args:…, update_analyst_statuses(), unit, Tests for FI CLI re-skinning and dual-track support in CLI., test_analyst_order_defaults_to_fi_first(), test_analyst_type_enum_has_fi_analysts() (+5 more)

### Community 107 - "create_macro_calendar_analyst"
Cohesion: 0.25
Nodes (11): create_macro_calendar_analyst(), _FakeLLM, Captures the bound tools and rendered prompt; returns a canned report., _FakeLLM, Tests for the Macro Calendar Analyst (Task 3.4). Offline: a fake LLM captures…, _state(), test_binds_expected_tool_set(), test_node_returns_macro_calendar_report_state_key() (+3 more)

### Community 109 - "treasury.py"
Cohesion: 0.13
Nodes (22): Par curve as of test_date: maturity (years) -> yield (decimal). Point-in-time:…, _spot_curve(), get_auction_results(), _get_session(), get_treasury_par_yields(), _is_priced(), _load_yield_csv(), _parse_yield_csv() (+14 more)

### Community 110 - "test_fi_interface.py"
Cohesion: 0.12
Nodes (15): get_fred_series(), Retrieve any FRED (Federal Reserve Economic Data) series: policy rates,…, get_category_for_method(), Get the category that contains the specified method., fixture, parametrize, Task 1.12: all Phase 1 fixed-income data tools are registered in the interface…, Each @tool wrapper must invoke its registered dataflows function. (+7 more)

### Community 111 - "test_fi_config_models.py"
Cohesion: 0.27
Nodes (10): CentralBank, Curve, BaseModel, Currency-agnostic configuration models for rates analysis. Populated for…, Configuration for a sovereign yield curve., Configuration for a central bank's data sources., test_central_bank_requires_all_fields(), test_config_central_banks_parse_into_model() (+2 more)

### Community 112 - "interface.py"
Cohesion: 0.14
Nodes (16): get_stock_data(), tool, Retrieve stock price data (OHLCV) for a given ticker symbol. Uses the…, get_macro_indicators(), tool, Retrieve a macroeconomic indicator time series from FRED (Federal Reserve…, get_prediction_markets(), tool (+8 more)

### Community 113 - "test_structured_agents.py"
Cohesion: 0.12
Nodes (20): _build_system_message(), create_sentiment_analyst(), create_social_media_analyst(), Sentiment analyst — multi-source sentiment analysis for a target ticker.…, Assemble the sentiment-analyst system message with structured data blocks., Deprecated alias for :func:`create_sentiment_analyst`. Kept so existing code…, Create a sentiment analyst node for the trading graph. Pre-fetches news +…, Backwards-compatibility shim for the renamed module. The agent is now… (+12 more)

### Community 114 - ".__init__"
Cohesion: 0.33
Nodes (5): Any, _clean_identity_value(), Return a trimmed string, or None for empty / placeholder-ish values., Initialize the trading agents graph and components. Args: selected_analysts:…, Get provider-specific kwargs for LLM client creation.

### Community 115 - "test_reporting.py"
Cohesion: 0.21
Nodes (13): Write the markdown report tree for a completed run, like the CLI does.…, Path, Reusable report-tree writer shared by the CLI and the programmatic API. Writes…, Save a completed run's reports to ``save_path``; return the complete-report…, write_report_tree(), unit, Report parity: the shared writer produces the report tree for the CLI and the…, _state() (+5 more)

### Community 117 - "test_memory_pointintime.py"
Cohesion: 0.44
Nodes (10): _log(), unit, Memory-log lessons must be point-in-time safe in a backtest (#1251).…, _resolve(), test_as_of_excludes_lessons_resolved_after_the_run_date(), test_cross_ticker_lessons_are_also_gated(), test_legacy_entry_without_resolution_date_excluded_in_backtest(), test_memory_as_of_gates_historical_but_not_live() (+2 more)

### Community 118 - "test_risk_router_path_map.py"
Cohesion: 0.36
Nodes (10): _debate_state(), parametrize, unit, Shared-router / path_map completeness (#1088). Both…, _state(), test_debate_path_map_covers_full_router_range(), test_debate_router_return_always_routable(), test_path_map_covers_full_router_range() (+2 more)

### Community 119 - "_build_run_config"
Cohesion: 0.29
Nodes (9): _build_run_config(), Assemble the run config from interactive selections, honoring env precedence.…, parametrize, CLI config precedence (#976, #977). An explicit environment override for the…, test_checkpoint_flag_overrides_env(), test_checkpoint_none_preserves_env_default(), test_env_round_counts_win_over_selection(), test_partial_env_only_overrides_that_count() (+1 more)

### Community 120 - "create_curve_technicals_analyst"
Cohesion: 0.27
Nodes (12): _configured_spread_text(), create_curve_technicals_analyst(), Describe the configured spread set so the prompt tracks config., _FakeLLM, Tests for the Curve Technicals Analyst (Task 3.2). Offline: a fake LLM captures…, Captures the bound tools and rendered prompt; returns a canned report., _state(), test_binds_expected_tool_set() (+4 more)

### Community 121 - "memory.py"
Cohesion: 0.20
Nodes (4): Append-only markdown decision log for FixedIncomeAgent., memory_log(), fixture, Unit tests for Fixed Income reflection and memory log updates.

### Community 122 - "polymarket.py"
Cohesion: 0.27
Nodes (10): datetime, get_prediction_markets(), _is_forward_looking(), _parse_json_list(), Polymarket prediction-market vendor. Surfaces live, market-implied…, # TODO: Issue 4 long-term fix — integrate CME FedWatch or OIS-implied rate, Gamma encodes ``outcomes``/``outcomePrices`` as JSON-string arrays., Keep only open markets that resolve in the future. ``closed`` is the reliable… (+2 more)

### Community 123 - "test_fi_research_managers.py"
Cohesion: 0.28
Nodes (15): DirectionOutlook, Per-tenor direction outlook produced by the Direction Research Manager. The…, _direction_state(), _free_text_llm(), unit, Direction and shape research managers: the FI debate judges (Task 4.3).…, LLM whose structured binding returns a real outlook instance., _shape_state() (+7 more)

### Community 124 - "conftest.py"
Cohesion: 0.32
Nodes (6): _dummy_api_keys(), _isolate_config(), mock_llm_client(), fixture, Shared pytest fixtures that prevent CI hangs when API keys are absent., Reset the global dataflows config before and after each test. ``set_config``…

### Community 125 - ".get_llm"
Cohesion: 0.22
Nodes (7): ChatAnthropic, NormalizedChatAnthropic, Any, Whether Anthropic accepts the ``effort`` parameter for this model., ChatAnthropic with normalized content output. Claude models with extended…, Return configured ChatAnthropic instance., _supports_effort()

### Community 126 - "fundamental_data_tools.py"
Cohesion: 0.27
Nodes (9): get_balance_sheet(), get_cashflow(), get_fundamentals(), get_income_statement(), tool, Retrieve comprehensive fundamental data for a given ticker symbol. Uses the…, Retrieve balance sheet data for a given ticker symbol. Uses the configured…, Retrieve cash flow statement data for a given ticker symbol. Uses the… (+1 more)

### Community 128 - "TestLegacyRemoval"
Cohesion: 0.18
Nodes (6): FinancialSituationMemory must not be importable from the memory module., rank_bm25 must not be present in the memory module namespace., TradingAgentsGraph must not expose reflect_and_remember., create_portfolio_manager accepts only llm; passing memory= raises TypeError., propagate() completes and stores the decision after the redesign., TestLegacyRemoval

### Community 129 - "._should_continue_analyst"
Cohesion: 0.20
Nodes (5): Shared analyst loop: route to the tool node while the model is calling tools,…, Determine if macro-policy analysis should continue., Determine if curve-technicals analysis should continue., Determine if fed-speak analysis should continue., Determine if macro-calendar analysis should continue.

### Community 130 - "TraderProposal"
Cohesion: 0.18
Nodes (13): Structured transaction proposal produced by the Trader. The trader reads the…, Render a TraderProposal to markdown. The trailing ``FINAL TRANSACTION PROPOSAL:…, render_trader_proposal(), TraderProposal, create_trader(), _make_trader_state(), unit, A weak LLM may write "None"/"N/A" into an optional float field (#1058); coerce… (+5 more)

### Community 132 - "dataflows/utils.py"
Cohesion: 0.29
Nodes (3): DataFrame, save_output(), SavePathType

### Community 133 - "inflation_nowcast.py"
Cohesion: 0.19
Nodes (14): _cache_path(), ClevelandFedFormatError, get_inflation_nowcast(), _load_rows(), _parse_nowcasts(), date, ValueError, Cleveland Fed Inflation Nowcasting: daily CPI/PCE nowcasts. Source verified… (+6 more)

### Community 136 - "stockstats_utils.py"
Cohesion: 0.22
Nodes (14): _clean_dataframe(), _coerce_ohlcv_dates(), _ensure_date_column(), _fill_price_gaps(), filter_financials_by_date(), load_ohlcv(), DataFrame, Drop rows with no close and forward/back-fill remaining price gaps so… (+6 more)

### Community 137 - "supply_chain_pressure.py"
Cohesion: 0.19
Nodes (14): _cache_path(), get_supply_chain_pressure(), GscpiFormatError, _load_rows(), _parse_rows(), date, ValueError, NY Fed Global Supply Chain Pressure Index (GSCPI): monthly index. Source… (+6 more)

### Community 138 - "test_equity_state_logging"
Cohesion: 0.38
Nodes (6): Path, unit, Verify fixed-income state keys are persisted in run logs without KeyError., Verify equity mode states continue to log correctly., test_equity_state_logging(), test_fi_state_logging()

### Community 139 - "._fetch_returns"
Cohesion: 0.15
Nodes (7): Fetch raw and alpha return for ticker over holding_days from trade_date.…, _price_df(), Only 1 data point available → returns all-None, no crash., Empty DataFrame → returns all-None, no crash., SPY having fewer rows than the stock (but still a full window) must not raise…, #1169: a rerun before the full holding window has traded returns unavailable…, Minimal DataFrame matching yfinance .history() output shape. Uses a…

### Community 140 - "market_data_validator.py"
Cohesion: 0.23
Nodes (10): get_verified_market_snapshot(), tool, Deterministic verification snapshot for exact market-data claims. Returns the…, build_verified_market_snapshot(), _fmt(), DataFrame, Deterministic market-data verification snapshot. The market analyst is an LLM…, OHLCV on or before curr_date, date-sorted. Raises if nothing usable.… (+2 more)

### Community 141 - ".__init__"
Cohesion: 0.50
Nodes (3): Any, ToolNode, Initialize with required components. ``disabled_tools`` (tool names) is…

### Community 142 - "Q: what equity or single stock elements are in the code base?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: what equity or single stock elements are in the code base?, Source Nodes

### Community 143 - "._resolve_pending_entries"
Cohesion: 0.20
Nodes (5): Resolve pending log entries for ticker at the start of a new run. Fetches…, Resolve pending log entries for fixed-income runs using Treasury curve…, Pending AAPL entry is not resolved when the run is for NVDA., After resolve, get_pending_entries() is empty and the entry has a REFLECTION., #1169: when the outcome can't be settled yet (_fetch_returns None), the entry…

### Community 145 - "test_i18n_coverage.py"
Cohesion: 0.29
Nodes (5): parametrize, unit, Every report-producing agent must apply the configured output language…, test_report_agent_applies_language_instruction(), TestLanguageInstruction

### Community 146 - "FixedIncomeAgent Multi-Agent Framework"
Cohesion: 0.50
Nodes (4): FixedIncomeAgent Multi-Agent Framework, FixedIncomeAgent Project Handover, FixedIncomeAgent v0.4.0 Release Notes, Codebase Intelligence with graphify

### Community 147 - "default_config.py"
Cohesion: 0.17
Nodes (5): _apply_env_overrides(), _coerce(), Coerce env-var string to the type of the existing default value. Invalid values…, Apply FIXEDINCOMEAGENT_* env vars to the config dict in-place., Inflation breakevens fetcher: config-driven series set, consolidated markdown…

### Community 148 - "get_curve_spreads"
Cohesion: 0.33
Nodes (6): get_curve_spreads(), _parse_latest_yields(), Pre-computed curve spreads tool. Eliminates LLM arithmetic hallucinations by…, Extract the latest-curve yields from a par-yield markdown report. Looks for the…, Compute Treasury yield-curve spreads and butterflies from the par yield curve.…, tool

### Community 152 - "cli/utils.py"
Cohesion: 0.08
Nodes (26): ask_anthropic_effort(), ask_gemini_thinking_config(), ask_glm_region(), ask_minimax_region(), ask_openai_reasoning_effort(), ask_output_language(), ask_qwen_region(), confirm_ollama_endpoint() (+18 more)

### Community 176 - "date_window.py"
Cohesion: 0.20
Nodes (9): datetime, Shared look-ahead-safe date-window filtering for dated content. News,…, Normalize a datetime to UTC-aware; a naive value is assumed to be UTC., to_utc(), StockTwits public symbol-stream fetcher. StockTwits exposes a per-symbol…, Keep only messages published in [start_date, end_date] (look-ahead safe). No…, Map a crypto pair to StockTwits' ``<BASE>.X`` convention. StockTwits lists…, _stocktwits_symbol() (+1 more)

## Knowledge Gaps
- **24 isolated node(s):** `AnalystNodeSpec`, `Answer`, `Outcome`, `Source Nodes`, `graphify Codebase Intelligence` (+19 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1029 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **34 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TradingAgentsGraph` connect `TradingAgentsGraph` to `TestLegacyRemoval`, `test_backtest_runner.py`, `test_equity_state_logging`, `._fetch_returns`, `TestDeferredReflection`, `._resolve_pending_entries`, `baselines.py`, `Propagator`, `build_instrument_context`, `FixedIncomeAnalysis`, `SignalProcessor`, `test_checkpoint_resume.py`, `test_fi_graph_wiring.py`, `test_ablation.py`, `test_fi_portfolio_manager.py`, `._run_graph`, `test_llm_max_retries.py`, `test_instrument_identity.py`, `TestProviderKwargsTemperature`, `test_memory_log.py`, `thread_id`, `test_graph_setup_threads_disabled_tools_to_analysts`, `unit`, `checkpointer.py`, `test_checkpoint_lifecycle.py`, `test_llm_max_tokens.py`, `.__init__`, `test_reporting.py`, `test_memory_pointintime.py`?**
  _High betweenness centrality (0.142) - this node is a cross-community bridge._
- **Why does `get_config()` connect `set_config` to `inflation_nowcast.py`, `test_backtest_runner.py`, `test_baselines.py`, `shelter_rents.py`, `stockstats_utils.py`, `supply_chain_pressure.py`, `used_vehicle_index.py`, `ism_prices_paid.py`, `agents/__init__.py`, `consumer_inflation_expectations.py`, `_stub`, `interface.py`, `baselines.py`, `get_curve_spreads`, `create_curve_technicals_analyst`, `in_window`, `invoke_structured_or_freetext`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `set_config()` connect `set_config` to `_make_api_request`, `_stub`, `test_polymarket.py`, `VendorRoutingTests`, `_request_stub`, `y_finance.py`, `test_baselines.py`, `_assert_ohlcv_not_stale`, `_stub`, `FedSpeechesTests`, `.__init__`, `test_i18n_coverage.py`, `_stub`, `test_consumer_expectations.py`, `_stub`, `._write_csv`, `._write_csv`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `TradingAgentsGraph` (e.g. with `FixedIncomeAnalysis` and `BacktestRunner`) actually correct?**
  _`TradingAgentsGraph` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `ConditionalLogic` (e.g. with `AgentState` and `GraphSetup`) actually correct?**
  _`ConditionalLogic` has 20 INFERRED edges - model-reasoned connections that need verification._
- **What connects `AnalystNodeSpec`, `Answer`, `Outcome` to the rest of the system?**
  _24 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `_make_api_request` be split into smaller, more focused modules?**
  _Cohesion score 0.0547945205479452 - nodes in this community are weakly interconnected._