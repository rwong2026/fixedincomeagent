# Graph Report - fixedincomeagent  (2026-09-06)

## Corpus Check
- 228 files · ~283,433 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3016 nodes · 6423 edges · 162 communities (128 shown, 30 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 309 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2d2421c4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_ablation.py
- test_vendor_errors.py
- _request_stub
- agent_utils.py
- _stub
- SignalProcessor
- cot_data.py
- test_backtest_runner.py
- AzureOpenAIClient
- agents/__init__.py
- cli/main.py
- FixedIncomeAnalysis
- get_capabilities
- test_consumer_expectations.py
- DeepSeekChatOpenAI
- _stub
- test_baselines.py
- schemas.py
- _stub
- make_log
- patch
- test_reddit_fallback.py
- invoke_structured_or_freetext
- test_ollama_base_url.py
- FedSpeechesTests
- Propagator
- normalize_symbol
- cli/utils.py
- test_backtest_scoring.py
- FomcCalendarTests
- TestDeferredReflection
- test_structured_agent_prompts.py
- OpenAIClient
- sentiment_analyst.py
- shelter_rents.py
- interface.py
- test_checkpoint_resume.py
- ConditionalLogic
- test_fi_graph_setup.py
- test_fi_graph_wiring.py
- test_llm_max_tokens.py
- TradingMemoryLog
- in_window
- test_treasury_benchmark.py
- TaggedArgument
- market_data_validator.py
- create_llm_client
- test_fi_research_managers.py
- get_alfred_vintage
- test_social_lookahead.py
- test_fi_portfolio_manager.py
- test_api_key_env.py
- _select_model
- test_env_overrides.py
- openai_client.py
- FredFormattingTests
- ._write_csv
- ._write_csv
- treasury.py
- reddit.py
- stockstats_utils.py
- test_openrouter_model_select.py
- VendorRoutingTests
- set_config
- build_analyst_execution_plan
- ._run_graph
- test_llm_max_retries.py
- test_polymarket.py
- StatsCallbackHandler
- provider_default_url
- test_shape_debate.py
- DirectionCall
- _assert_ohlcv_not_stale
- _ohlcv
- TestProviderKwargsTemperature
- test_cli_symbol_handling.py
- news_data_tools.py
- BaseLLMClient
- TestEffortGate
- test_memory_log.py
- TestMinimaxStructuredOutputDispatch
- create_curve_technicals_analyst
- test_direction_debate.py
- test_fi_trader.py
- test_fi_interface.py
- safe_ticker_component
- write_report_tree
- AnthropicClient
- DummyLLMClient
- fred.py
- ._fetch_returns
- test_checkpoint_lifecycle.py
- test_structured_agents.py
- test_memory_pointintime.py
- fed_speeches.py
- test_ohlcv_cache_freshness.py
- used_vehicle_index.py
- BreakevensFetchTests
- checkpointer.py
- ism_prices_paid.py
- test_fi_config_models.py
- TestLegacyRemoval
- test_risk_router_path_map.py
- _build_run_config
- test_cli_fi_reskin.py
- polymarket.py
- AgentState
- _make_api_request
- TestLoadOhlcvNoPoison
- test_stocktwits_resilience.py
- fomc_calendar.py
- .__init__
- create_sentiment_analyst
- announcements.py
- TraderProposal
- Any
- _stub
- System Architecture Schema
- test_regime_dates.py
- _FakeResponse
- TradingAgentsGraph
- test_cli_no_console.py
- PortfolioDecision
- create_macro_calendar_analyst
- CotCacheTests
- CI Workflow
- Docker Configuration
- Project Dependencies
- CLI Initialization Screenshot
- CLI News Analysis Screenshot
- CLI Technical Analysis Screenshot
- CLI Transaction Decision Screenshot
- Tauric Research Logo
- Changelog
- Enum
- str
- ToolNode
- Handoff: fixedincomeagent — UST Rates & Curve System
- fixedincomeagent
- README
- BaseModel
- thread_id
- CotFormatErrorTests
- HTTPError
- test_i18n_coverage.py
- TestTraderAgent
- .__init__
- inflation_breakevens.py
- Any
- dataflows/utils.py
- FomcDateListIntegrityTests
- TestCryptoSearchTerm
- .get_completed_reports_count
- _clean_identity_value
- .get_llm
- date
- ValueError
- Path

## God Nodes (most connected - your core abstractions)
1. `TradingAgentsGraph` - 77 edges
2. `set_config()` - 54 edges
3. `get_language_instruction()` - 54 edges
4. `get_config()` - 53 edges
5. `ConditionalLogic` - 50 edges
6. `make_log()` - 41 edges
7. `route_to_vendor()` - 39 edges
8. `TradingMemoryLog` - 36 edges
9. `DirectionCall` - 34 edges
10. `get_capabilities()` - 34 edges

## Surprising Connections (you probably didn't know these)
- `test_direction_debate_state_keys()` --uses--> `DirectionDebateState`  [INFERRED]
  tests/test_curve_debate_state.py → fixedincomeagent/agents/utils/agent_states.py
- `test_shape_debate_state_keys()` --uses--> `ShapeDebateState`  [INFERRED]
  tests/test_curve_debate_state.py → fixedincomeagent/agents/utils/agent_states.py
- `HierarchyTests` --uses--> `FredNotConfiguredError`  [INFERRED]
  tests/test_vendor_errors.py → fixedincomeagent/dataflows/fred.py
- `test_graph_setup_threads_disabled_tools_to_analysts()` --uses--> `TradingAgentsGraph`  [INFERRED]
  tests/test_ablation.py → fixedincomeagent/graph/trading_graph.py
- `test_tool_nodes_filtered_by_disabled_tools()` --uses--> `TradingAgentsGraph`  [INFERRED]
  tests/test_ablation.py → fixedincomeagent/graph/trading_graph.py

## Import Cycles
- None detected.

## Communities (162 total, 30 thin omitted)

### Community 0 - "test_ablation.py"
Cohesion: 0.06
Nodes (65): create_fed_speak_analyst(), create_macro_policy_analyst(), MacroPolicyReport, MarketImpliedExpectations, Market-based inflation expectations from TIPS breakevens., Component-level inflation and macro analysis. CRITICAL: Do NOT average these…, ablation_disabled_tools(), AblationConfig (+57 more)

### Community 1 - "test_vendor_errors.py"
Cohesion: 0.10
Nodes (15): Exception, AlphaVantageNotConfiguredError, get_api_key(), Raised when Alpha Vantage is selected but no API key is configured. A…, Retrieve the API key for Alpha Vantage from environment variables., ValueError, Vendor data-error taxonomy. A single hierarchy so the routing layer reacts by…, Base for any condition where a vendor could not return usable data. (+7 more)

### Community 2 - "_request_stub"
Cohesion: 0.12
Nodes (8): AuctionResultsTests, ParYieldFetchingTests, ParYieldFormattingTests, unit, Treasury.gov vendor: par yield curve and auction results. All HTTP is mocked at…, Build a treasury._request replacement dispatching on the URL., _request_stub(), _TreasuryTestCase

### Community 3 - "agent_utils.py"
Cohesion: 0.07
Nodes (55): get_stock_data(), tool, Retrieve stock price data (OHLCV) for a given ticker symbol. Uses the…, get_alfred_vintage(), get_auction_results(), get_consumer_inflation_expectations(), get_cot_data(), get_fed_speeches() (+47 more)

### Community 4 - "_stub"
Cohesion: 0.12
Nodes (12): _apartment_list_csv(), ApartmentListIngestTests, _month_seq(), unit, Shelter & rents vendor (Zillow ZORI + Apartment List rent estimates). All HTTP…, Yield (year, month) for ``count`` consecutive months., ShelterReportTests, _ShelterTestCase (+4 more)

### Community 5 - "SignalProcessor"
Cohesion: 0.08
Nodes (20): extract_rating(), is_review(), parse_rating(), Shared 5-tier rating vocabulary and a deterministic heuristic parser. The same…, Extract a 5-tier rating from prose, or ``None`` if none is present. Two-pass…, Extract a 5-tier rating, falling back to ``default`` when none is found. Legacy…, Whether a signal is the non-tradeable REVIEW sentinel (#1170)., Any (+12 more)

### Community 6 - "cot_data.py"
Cohesion: 0.20
Nodes (15): _cache_path(), CotFormatError, _fmt(), get_cot_data(), _load_rows(), _parse_rows(), date, ValueError (+7 more)

### Community 7 - "test_backtest_runner.py"
Cohesion: 0.09
Nodes (39): BacktestResults, BacktestRunner, _classify_direction(), _classify_shape(), _entry_and_exit(), Point-in-time backtest replay harness for the UST rates/curve pipeline. For…, Ordered container returned by ``BacktestRunner.run``., up/down/neutral. Moves *below* the threshold are neutral (config semantics), so… (+31 more)

### Community 8 - "AzureOpenAIClient"
Cohesion: 0.17
Nodes (8): AzureChatOpenAI, AzureOpenAIClient, NormalizedAzureChatOpenAI, Any, AzureChatOpenAI with normalized content output., Client for Azure OpenAI deployments. Requires environment variables:…, Return configured AzureChatOpenAI instance., Azure accepts any deployed model name.

### Community 9 - "agents/__init__.py"
Cohesion: 0.15
Nodes (28): create_fundamentals_analyst(), create_market_analyst(), create_news_analyst(), create_research_manager(), create_bear_researcher(), create_bull_researcher(), create_aggressive_debator(), create_conservative_debator() (+20 more)

### Community 10 - "cli/main.py"
Cohesion: 0.06
Nodes (47): CLI Welcome Screen, analyze(), classify_message_type(), create_layout(), display_complete_report(), extract_content_string(), format_tokens(), format_tool_args() (+39 more)

### Community 11 - "FixedIncomeAnalysis"
Cohesion: 0.15
Nodes (16): FixedIncomeAnalysis, Any, Path, Public programmatic API for FixedIncomeAgent. Allows running Fixed Income (or…, Write report markdown tree to disk., High-level API for orchestrating fixed-income (and dual-track) analysis., Initialize the analysis orchestration. Args: config: Configuration dictionary…, Run complete analysis synchronously to completion. Returns a dictionary… (+8 more)

### Community 12 - "get_capabilities"
Cohesion: 0.07
Nodes (19): get_capabilities(), ModelCapabilities, Declarative per-model capability table for OpenAI-compatible providers. This is…, Resolve capabilities by exact ID, then pattern, then default., What an OpenAI-compatible model accepts at the API level., unit, Unit tests for the LLM capability table., deepseek-chat must NOT match the v\\d regex. (+11 more)

### Community 13 - "test_consumer_expectations.py"
Cohesion: 0.13
Nodes (9): _build_xlsx(), unit, NY Fed Survey of Consumer Expectations: median inflation expectations vendor.…, SceCacheTests, SceFormatErrorTests, SceParsingTests, _SceTestCase, _sheet() (+1 more)

### Community 14 - "DeepSeekChatOpenAI"
Cohesion: 0.07
Nodes (26): DeepSeekChatOpenAI, _input_to_messages(), Normalise a langchain LLM input to a list of message objects. Accepts a list of…, DeepSeek-specific overrides on top of the OpenAI-compatible client. Thinking-…, integration, skipif, _bound_kwargs(), _Pick (+18 more)

### Community 15 - "_stub"
Cohesion: 0.08
Nodes (24): _cache_path(), ClevelandFedFormatError, get_inflation_nowcast(), _load_rows(), _parse_nowcasts(), date, ValueError, Cleveland Fed Inflation Nowcasting: daily CPI/PCE nowcasts. Source verified… (+16 more)

### Community 16 - "test_baselines.py"
Cohesion: 0.20
Nodes (26): callable, forwards_implied_baseline(), Forward-curve-implied moves over the horizon (see module docstring)., Re-skin baseline predictions as BacktestRuns scored by score_backtest. Realized…, with_actuals(), BacktestRun, One replayed test date: predicted calls vs. realized outcomes., _actual_run() (+18 more)

### Community 17 - "schemas.py"
Cohesion: 0.12
Nodes (43): _annotate(), check_consistency(), ConsistencyWarning, fi_consistency_check_node(), _is_directional(), parse_trader_decision(), Fixed-Income Risk Consistency Check: pure-logic validator (no LLM). Sits…, Signed magnitude ordinal: up positive, down negative, neutral zero. (+35 more)

### Community 18 - "_stub"
Cohesion: 0.06
Nodes (36): _cache_path(), get_consumer_inflation_expectations(), _load_rows(), _month_end(), _parse_rows(), date, ValueError, NY Fed Survey of Consumer Expectations: median inflation expectations. Source… (+28 more)

### Community 19 - "make_log"
Cohesion: 0.08
Nodes (15): make_log(), Calling store_decision twice with same (ticker, date) stores only one entry., batch_update_with_outcomes resolves multiple pending entries in one write., Rating: X' label wins even when an opposing rating word appears earlier in…, LLM decision containing '---' must not corrupt the entry., Only the n_same most recent same-ticker entries are included., Only the n_cross most recent cross-ticker entries are included., Without max_entries, all resolved entries are kept. (+7 more)

### Community 20 - "patch"
Cohesion: 0.07
Nodes (23): build_fi_instrument_context(), build_instrument_context(), Resolve deterministic identity metadata (company name, sector, …) for a ticker.…, Describe the exact instrument so agents preserve identity and ticker. When…, Instrument context for fixed-income (rates/curve) runs. FI mode analyzes a…, resolve_instrument_identity(), Resolve ticker identity once and return the full instrument context.…, patch (+15 more)

### Community 21 - "test_reddit_fallback.py"
Cohesion: 0.10
Nodes (15): unit, _raise(), Tests for the RSS-first Reddit fetcher, its 429 backoff, the opt-in JSON path's…, The opt-in JSON path still degrades to RSS on a 403 (kept for #862)., IncompleteRead/RemoteDisconnected come from http.client and are NOT OSErrors,…, A minimal context-manager response whose read() runs ``read_fn``., The default per-subreddit fetch goes straight to RSS — it must not hit the WAF-…, _resp() (+7 more)

### Community 22 - "invoke_structured_or_freetext"
Cohesion: 0.15
Nodes (20): create_portfolio_manager(), Portfolio Manager: synthesises the risk-analyst debate into the final decision.…, Research Manager: turns the bull/bear debate into a structured investment plan…, Shape Research Manager: judges the steepener/flattener debate into a per-spread…, Fixed-Income Trader: turns the direction/shape outlooks into the desk's calls.…, create_trader(), Trader: turns the Research Manager's investment plan into a concrete…, bind_structured() (+12 more)

### Community 23 - "test_ollama_base_url.py"
Cohesion: 0.08
Nodes (37): get_model_options(), Return shared model options for a provider and selection mode., ModelOption, cli_utils(), fixture, Import cli.utils with a fresh environment so module-level state is consistent., _base_url(), fixture (+29 more)

### Community 25 - "Propagator"
Cohesion: 0.22
Nodes (12): DirectionDebateState, InvestDebateState, TypedDict, State for the yield-direction debate (higher vs lower yields)., State for the curve-shape debate (steepener vs flattener). Runs second,…, RiskDebateState, ShapeDebateState, Propagator (+4 more)

### Community 26 - "normalize_symbol"
Cohesion: 0.11
Nodes (15): crypto_base(), is_yahoo_safe(), _normalize_crypto(), normalize_symbol(), Symbol normalization and market-data error types for vendor calls. Yahoo…, Map a user/broker symbol to its canonical Yahoo Finance symbol. Resolution…, True when ``symbol`` only contains characters Yahoo symbols use., Return the crypto base (e.g. ``BTC``) for a known USD/USDT/USDC-quoted crypto… (+7 more)

### Community 27 - "cli/utils.py"
Cohesion: 0.17
Nodes (16): AnalystType, AssetType, detect_asset_type(), filter_analysts_for_asset_type(), get_analysis_date(), _llm_provider_table(), Prompt the user to enter a date in YYYY-MM-DD format., Select analysts using an interactive checkbox. (+8 more)

### Community 28 - "test_backtest_scoring.py"
Cohesion: 0.15
Nodes (30): Backtesting harness: point-in-time replay of the FI pipeline., BacktestScorecard, _bucketize_change(), _cal_bin_index(), CalibrationBin, _rate(), Backtest scoring (Task 7.3): score predicted calls against realized outcomes.…, Markdown summary of a scorecard. (+22 more)

### Community 29 - "FomcCalendarTests"
Cohesion: 0.14
Nodes (3): Redirect the data cache to a temp dir so tests never touch the real one., FomcCalendarTests, _FomcTestCase

### Community 30 - "TestDeferredReflection"
Cohesion: 0.05
Nodes (28): Any, SCAFFOLDING ONLY — opt-in, not called from any live graph path. Thin delegate…, Initialize the reflector with an LLM., Concise prompt for reflect_on_final_decision (Phase B log entries). Produces…, Concise prompt for reflect_on_fi_decision (Fixed Income Treasury curve).…, Single reflection call on the final trade decision with outcome context. Used…, Single reflection call on an FI yield-curve decision with benchmark metrics., Handles reflection on trading decisions. (+20 more)

### Community 31 - "test_structured_agent_prompts.py"
Cohesion: 0.20
Nodes (20): PortfolioRating, Enum, str, Discrete sentiment direction produced by the Sentiment Analyst. Six tiers keep…, 5-tier rating used by the Research Manager and Portfolio Manager., 3-tier transaction direction used by the Trader. The Trader's job is to…, SentimentBand, TraderAction (+12 more)

### Community 32 - "OpenAIClient"
Cohesion: 0.10
Nodes (19): _is_native_openai_base_url(), OpenAIClient, Any, Whether the (native OpenAI) model accepts ``reasoning_effort``., True when ``base_url`` is unset or points at api.openai.com. The Responses API…, Client for OpenAI, Ollama, OpenRouter, and xAI providers. For native OpenAI…, Return a configured ChatOpenAI instance, driven by the provider registry., Validate model for the provider. (+11 more)

### Community 33 - "sentiment_analyst.py"
Cohesion: 0.23
Nodes (8): _build_system_message(), Sentiment analyst — multi-source sentiment analysis for a target ticker.…, Assemble the sentiment-analyst system message with structured data blocks., Structured sentiment report produced by the Sentiment Analyst. Replaces the…, Render a SentimentReport to the markdown shape the rest of the system expects.…, render_sentiment_report(), SentimentReport, TestRenderSentimentReport

### Community 34 - "shelter_rents.py"
Cohesion: 0.12
Nodes (27): _apartment_list_path(), ApartmentListFormatError, _by_month(), _dollars(), get_shelter_rents(), _load_apartment_list(), _load_zillow(), _parse_apartment_list() (+19 more)

### Community 35 - "interface.py"
Cohesion: 0.15
Nodes (22): NoMarketDataError, A vendor returned no usable rows for a symbol (empty result or stale data).…, filter_financials_by_date(), Drop financial statement columns (fiscal period timestamps) after curr_date.…, Execute a yfinance call with exponential backoff on rate limits. yfinance…, StockstatsUtils, yf_retry(), get_balance_sheet() (+14 more)

### Community 36 - "test_checkpoint_resume.py"
Cohesion: 0.18
Nodes (13): has_checkpoint(), Check whether a resumable checkpoint exists for ticker+date., _build_graph(), _node_a(), _node_b(), StateGraph, TypedDict, Test checkpoint resume: crash mid-analysis, re-run resumes from last node. (+5 more)

### Community 37 - "ConditionalLogic"
Cohesion: 0.33
Nodes (16): ConditionalLogic, Handles conditional logic for determining graph flow., _direction_state(), unit, Dual-track FI debate routing (Task 4.4). `should_continue_direction_debate`…, _shape_state(), test_direction_debate_alternates_speakers(), test_direction_debate_continues_below_limit() (+8 more)

### Community 38 - "test_fi_graph_setup.py"
Cohesion: 0.16
Nodes (16): GraphSetup, Add analyst/tool/clear nodes and chain them START -> ... -> last_target., Handles the setup and configuration of the agent graph., Initialize the trading agents graph and components. Args: selected_analysts:…, Get provider-specific kwargs for LLM client creation., _compile(), parametrize, unit (+8 more)

### Community 39 - "test_fi_graph_wiring.py"
Cohesion: 0.15
Nodes (23): _edges(), _nodes(), parametrize, RunnableLambda, unit, Task 4.5: wire the FI dual-track debate (direction -> shape) into the graph. FI…, Regression: an all-FI *subset* (e.g. only macro_policy) still wires the full FI…, Offline LLM: answers every prompt with a fixed AIMessage, never calls tools,… (+15 more)

### Community 40 - "test_llm_max_tokens.py"
Cohesion: 0.06
Nodes (47): Any, AsyncCallbackManagerForLLMRun, BaseLLMClient, BaseMessage, CallbackManagerForLLMRun, ChatGoogleGenerativeAI, ChatResult, _coerce_max_tokens() (+39 more)

### Community 41 - "TradingMemoryLog"
Cohesion: 0.10
Nodes (12): Append-only markdown log of trading decisions and reflections., Replace pending tag and append REFLECTION section using atomic write. Finds the…, Apply multiple outcome updates in a single read + atomic write. Each element of…, Build a resolved entry tag, recording the outcome's known-by date.…, Drop oldest resolved blocks when their count exceeds max_entries. Pending…, Append pending entry at end of propagate(). No LLM call., Parse all entries from log. Returns list of dicts., Return entries with outcome:pending (for Phase B). (+4 more)

### Community 42 - "in_window"
Cohesion: 0.12
Nodes (28): in_window(), datetime, Shared look-ahead-safe date-window filtering for dated content. News,…, Normalize a datetime to UTC-aware; a naive value is assumed to be UTC., Whether an item belongs in the half-open window ``[start, end + 1 day)``.…, to_utc(), StockTwits public symbol-stream fetcher. StockTwits exposes a per-symbol…, Keep only messages published in [start_date, end_date] (look-ahead safe). No… (+20 more)

### Community 43 - "test_treasury_benchmark.py"
Cohesion: 0.11
Nodes (25): calculate_treasury_curve_benchmark(), evaluate_directional_hit(), _fetch_tenor_observations(), parse_direction_calls(), Any, Treasury curve equal-weight benchmark calculation for Fixed Income reflection.…, Calculate Treasury curve benchmark yield changes and decision hit-rate. Args:…, Extract normalized per-tenor direction calls from markdown or a dictionary. (+17 more)

### Community 44 - "TaggedArgument"
Cohesion: 0.16
Nodes (15): Any, BaseModel, Argument tagging scaffold for credit assignment (Phase 6, Task 6.1).…, A debate argument tagged for credit assignment (scaffolding only)., Wrapper so with_structured_output can return a list of tags., Tag individual debate arguments via one structured LLM call. Returns an empty…, tag_debate_arguments(), TaggedArgument (+7 more)

### Community 45 - "market_data_validator.py"
Cohesion: 0.12
Nodes (16): get_verified_market_snapshot(), tool, Deterministic verification snapshot for exact market-data claims. Returns the…, build_verified_market_snapshot(), _fmt(), DataFrame, Deterministic market-data verification snapshot. The market analyst is an LLM…, OHLCV on or before curr_date, date-sorted. Raises if nothing usable.… (+8 more)

### Community 46 - "create_llm_client"
Cohesion: 0.16
Nodes (23): Resolve the backend URL with the correct precedence. An explicit env override…, resolve_backend_url(), create_llm_client(), Create an LLM client for the specified provider. Provider modules are imported…, _capture_kwargs(), unit, Amazon Bedrock — first-class native client via the optional langchain-aws…, Stub _bedrock_class so the constructor kwargs are testable without the optional… (+15 more)

### Community 47 - "test_fi_research_managers.py"
Cohesion: 0.21
Nodes (20): create_direction_research_manager(), Direction Research Manager: judges the higher/lower yields debate into a per-…, create_shape_research_manager(), DirectionOutlook, Per-tenor direction outlook produced by the Direction Research Manager. The…, Render a DirectionOutlook to markdown for the trader's prompt context., render_direction_outlook(), _direction_state() (+12 more)

### Community 48 - "get_alfred_vintage"
Cohesion: 0.14
Nodes (16): get_alfred_vintage(), get_vintage_dates(), Return available vintage dates for a FRED series (ALFRED). Args: series_id:…, Fetch a FRED series as it was known on vintage_date (ALFRED). Args: series_id:…, _needs_key, AlfredMockedTests, unit, Tests for ALFRED point-in-time vintage fetcher. The three live-key tests are… (+8 more)

### Community 49 - "test_social_lookahead.py"
Cohesion: 0.14
Nodes (19): fetch_reddit_posts(), Fetch recent Reddit posts mentioning ``ticker`` across finance subreddits and…, fetch_stocktwits_messages(), Map a crypto pair to StockTwits' ``<BASE>.X`` convention. StockTwits lists…, Fetch recent StockTwits messages for ``ticker`` and return them as a formatted…, _stocktwits_symbol(), _epoch(), _JsonResp (+11 more)

### Community 50 - "test_fi_portfolio_manager.py"
Cohesion: 0.15
Nodes (19): create_fi_portfolio_manager(), Fixed-Income Portfolio Manager: final synthesis of the desk's curve calls.…, _decision(), _free_text_llm(), _graph(), RunnableLambda, unit, Fixed-Income Portfolio Manager (Task 5.3) and the completed FI graph wiring.… (+11 more)

### Community 51 - "test_api_key_env.py"
Cohesion: 0.11
Nodes (17): get_api_key_env(), Canonical provider -> API-key env-var mapping. A single source of truth for…, Return the env var name for `provider`'s API key, or None if not applicable.…, parametrize, Tests for the canonical provider->env-var mapping and the CLI key-prompt helper., When key is missing, user-pasted value must be written to .env AND os.environ., Empty prompt response (user cancelled) must not write to .env., An existing .env with other keys must be preserved on writeback. (+9 more)

### Community 52 - "_select_model"
Cohesion: 0.16
Nodes (14): _fetch_openrouter_models(), _prompt_custom_model_id(), Fetch available models from the OpenRouter API., Prompt for a required value; exit cleanly if the user cancels.…, Select an OpenRouter model from the newest available, or enter a custom ID.…, Prompt user to type a custom model ID., Select a model for the given provider and mode (quick/deep)., Select shallow thinking llm engine using an interactive selection. (+6 more)

### Community 53 - "test_env_overrides.py"
Cohesion: 0.14
Nodes (20): parametrize, Tests for FIXEDINCOMEAGENT_* env-var overlay onto DEFAULT_CONFIG., Garbage int values should surface a ValueError at import, not silently…, A misspelled boolean must fail loudly (like ints) instead of silently False., Env vars outside _ENV_OVERRIDES must not bleed into DEFAULT_CONFIG., Set/clear env vars then reload default_config to re-evaluate DEFAULT_CONFIG., The provider reasoning/thinking knobs are env-configurable (non-interactive…, Unset reasoning/thinking knobs stay None so each provider uses its own default. (+12 more)

### Community 54 - "openai_client.py"
Cohesion: 0.14
Nodes (17): ChatOpenAI, is_openai_compatible(), LocalCompatibleChatOpenAI, MinimaxChatOpenAI, NormalizedChatOpenAI, ProviderSpec, MiniMax-specific overrides on top of the OpenAI-compatible client. M2.x…, ChatOpenAI with normalized content output and capability-aware binding. The… (+9 more)

### Community 55 - "FredFormattingTests"
Cohesion: 0.08
Nodes (8): FredConfigTests, FredFormattingTests, FredResolutionTests, FredRoutingTests, unit, FRED macro vendor: alias resolution, configuration errors, output formatting,…, Build a _request replacement that dispatches on the endpoint path., _request_stub()

### Community 56 - "._write_csv"
Cohesion: 0.16
Nodes (5): IsmIngestTests, IsmReportTests, _IsmTestCase, unit, ISM Manufacturing Prices Index ("prices paid") — manual local-CSV ingest. The…

### Community 57 - "._write_csv"
Cohesion: 0.19
Nodes (4): unit, UsedVehicleIngestTests, UsedVehicleReportTests, _UsedVehicleTestCase

### Community 58 - "treasury.py"
Cohesion: 0.12
Nodes (23): date, Par curve as of test_date: maturity (years) -> yield (decimal). Point-in-time:…, _spot_curve(), get_auction_results(), _get_session(), get_treasury_par_yields(), _is_priced(), _load_yield_csv() (+15 more)

### Community 59 - "reddit.py"
Cohesion: 0.14
Nodes (20): _fetch_subreddit(), _fetch_subreddit_json(), _fetch_subreddit_rss(), _iso_to_timestamp(), _jitter(), Reddit search fetcher for ticker-specific discussion posts. Default path is…, Return ``seconds`` with +/-``frac`` random jitter, to desynchronize concurrent…, Seconds to wait from a 429's ``Retry-After`` header, capped at 30s. Returns… (+12 more)

### Community 60 - "stockstats_utils.py"
Cohesion: 0.10
Nodes (34): _clean_dataframe(), _coerce_ohlcv_dates(), _ensure_date_column(), _fill_price_gaps(), load_ohlcv(), _local_midnight(), _normalize_dates(), DataFrame (+26 more)

### Community 61 - "test_openrouter_model_select.py"
Cohesion: 0.16
Nodes (9): _asks(), parametrize, unit, OpenRouter model selection: prompts are labeled by mode (#1000); required…, TestCancelExitsCleanly, TestLanguageDefaultsToEnglish, TestMainstreamFilter, TestOpenRouterLatestFirst (+1 more)

### Community 62 - "VendorRoutingTests"
Cohesion: 0.21
Nodes (7): _no_data(), unit, _raises(), Vendor router must respect the configured chain and never silently hide a…, _reset_config(), _returns(), VendorRoutingTests

### Community 63 - "set_config"
Cohesion: 0.09
Nodes (20): get_config(), initialize_config(), Initialize the configuration with default values., Update the configuration with custom values. Dict-valued keys (e.g.…, Get the current configuration., set_config(), _apply_env_overrides(), _coerce() (+12 more)

### Community 64 - "build_analyst_execution_plan"
Cohesion: 0.18
Nodes (8): AnalystExecutionPlan, AnalystNodeSpec, AnalystWallTimeTracker, build_analyst_execution_plan(), get_initial_analyst_node(), sync_analyst_tracker_from_chunk(), AnalystExecutionPlanTests, AnalystWallTimeTrackerTests

### Community 65 - "._run_graph"
Cohesion: 0.10
Nodes (11): Point-in-time cutoff for past-context lessons (#1251). A historical/backtest…, Graph-shape inputs that must invalidate a checkpoint if changed. Keyed into the…, Run the trading agents graph for a company on a specific date. ``asset_type``…, The value to stream/invoke: ``None`` to resume an existing checkpoint, else the…, Restore the plain uncheckpointed graph after a checkpointed run., Context-manager form of begin/end_checkpoint for the propagate path., Drop a completed run's checkpoint so a later run starts fresh (#1249)., Execute the graph and write the resulting state to disk and memory log. (+3 more)

### Community 66 - "test_llm_max_retries.py"
Cohesion: 0.27
Nodes (17): _coerce_max_retries(), Validate an ``llm_max_retries`` value to a non-negative int. Accepts an int or…, _bare_graph(), parametrize, unit, Configurable LLM SDK retry budget (#1090/#1091). A single transient 429 burst…, _reload_with_env(), test_coerce_accepts_non_negative_ints_and_numeric_strings() (+9 more)

### Community 67 - "test_polymarket.py"
Cohesion: 0.13
Nodes (6): PolymarketFilterTests, PolymarketFormatTests, PolymarketResilienceTests, PolymarketRoutingTests, unit, Polymarket prediction-market vendor: forward-looking filtering, volume ranking,…

### Community 68 - "StatsCallbackHandler"
Cohesion: 0.15
Nodes (10): BaseCallbackHandler, Any, Callback handler that tracks LLM calls, tool calls, and token usage., Increment LLM call counter when an LLM starts., Increment LLM call counter when a chat model starts., Extract token usage from LLM response., Increment tool call counter when a tool starts., Return current statistics. (+2 more)

### Community 69 - "provider_default_url"
Cohesion: 0.19
Nodes (8): provider_default_url(), Return the default backend URL for a provider key, or None if unknown., unit, Tests for env-driven CLI behavior (#897, #873). The config-layer override…, TestCliSkipsPromptsFromEnv, TestProviderDefaultUrl, TestReasoningEffortSkippedFromEnv, TestResearchDepthSkippedFromEnv

### Community 70 - "test_shape_debate.py"
Cohesion: 0.35
Nodes (12): create_flattener_researcher(), create_steepener_researcher(), _capturing_llm(), unit, Shape debate researchers: steepener vs flattener (Task 4.2). Run after the…, _shape_state(), test_flattener_opening_has_no_phantom_opponent(), test_flattener_prompt_includes_reports_direction_outcome_and_opponent() (+4 more)

### Community 71 - "DirectionCall"
Cohesion: 0.12
Nodes (28): DirectionCall, Structured yield-direction prediction for a single tenor., Render a DirectionCall to markdown., Structured curve-shape prediction for a single spread., Render a ShapeCall to markdown., render_direction_call(), render_shape_call(), ShapeCall (+20 more)

### Community 72 - "_assert_ohlcv_not_stale"
Cohesion: 0.18
Nodes (8): _assert_ohlcv_not_stale(), Reject OHLCV whose latest row is far older than curr_date. Raises…, _frame(), unit, Stale OHLCV guard (#1021): a vendor returning a year-old partial frame must be…, StaleGuardPropagationTests, StaleGuardRoutingTests, StaleGuardUnitTests

### Community 73 - "_ohlcv"
Cohesion: 0.17
Nodes (9): _ohlcv(), DataFrame, unit, Tests for tolerating a non-`Date` index column in stockstats_utils (#890).…, OHLCV frame whose date column is named `date_col`., A frame with `index` instead of `Date` must still clean to a usable, date-…, stockstats must compute indicators on a frame whose date column arrived as…, TestCleanDataframeAcrossVersions (+1 more)

### Community 74 - "TestProviderKwargsTemperature"
Cohesion: 0.16
Nodes (7): parametrize, unit, Tests for the configurable sampling temperature (#178/#168). Temperature is a…, _get_provider_kwargs float-coerces and forwards temperature, or omits it., TestProviderKwargsTemperature, TestTemperatureEnvOverlay, TestTemperatureForwarding

### Community 75 - "test_cli_symbol_handling.py"
Cohesion: 0.15
Nodes (12): is_valid_ticker_input(), normalize_ticker_symbol(), Whether a ticker entry is acceptable (charset + length). Allows the characters…, Resolve user input to its canonical Yahoo symbol (single source of truth).…, parametrize, CLI symbol validation/classification must agree with the data path. Regressions…, test_cli_normalize_delegates_to_data_layer(), test_detect_asset_type() (+4 more)

### Community 76 - "news_data_tools.py"
Cohesion: 0.21
Nodes (11): get_global_news(), get_insider_transactions(), get_news(), tool, Retrieve news data for a given ticker symbol. Uses the configured news_data…, Retrieve global news data. Uses the configured news_data vendor. Defaults for…, Retrieve insider transaction information about a company. Uses the configured…, unit (+3 more)

### Community 77 - "BaseLLMClient"
Cohesion: 0.10
Nodes (21): ABC, BaseLLMClient, normalize_content(), Abstract base class for LLM clients., Return the provider name used in warning messages., Warn when the model is outside the known list for the provider., Validate that the model is supported by this client., Normalize LLM response content to a plain string. Multiple providers (OpenAI… (+13 more)

### Community 78 - "TestEffortGate"
Cohesion: 0.21
Nodes (8): _capture_kwargs(), parametrize, unit, Tests for Anthropic effort-parameter gating (#831). Haiku (any version) and…, Forward-compat: new Opus/Sonnet versions don't need a code change., Default is conservative — unknown models don't get effort to avoid 400s., Skipping effort must not break other passthrough kwargs., TestEffortGate

### Community 79 - "test_memory_log.py"
Cohesion: 0.08
Nodes (19): Append-only markdown decision log for FixedIncomeAgent., _make_pm_state(), _price_df(), Tests for TradingMemoryLog — storage, deferred reflection, PM injection, legacy…, When max_entries is set and exceeded, oldest resolved entries are pruned., Pending entries (unresolved) are kept regardless of the cap., No rotation when resolved count <= max_entries., Store a decision then immediately resolve it via the API. (+11 more)

### Community 80 - "TestMinimaxStructuredOutputDispatch"
Cohesion: 0.20
Nodes (9): _client(), _Pick, BaseModel, unit, Tests for MinimaxChatOpenAI quirks. Verifies the subclass injects…, Coding Plan / MiniMax-Text-01 / any non-M2-prefixed model must NOT receive…, M2.x models route through the capability table — tool_choice is suppressed but…, TestMinimaxReasoningSplit (+1 more)

### Community 81 - "create_curve_technicals_analyst"
Cohesion: 0.31
Nodes (11): _configured_spread_text(), create_curve_technicals_analyst(), Describe the configured spread set so the prompt tracks config., _FakeLLM, Tests for the Curve Technicals Analyst (Task 3.2). Offline: a fake LLM captures…, _state(), test_binds_expected_tool_set(), test_node_returns_curve_technicals_report_state_key() (+3 more)

### Community 82 - "test_direction_debate.py"
Cohesion: 0.29
Nodes (13): create_higher_yields_researcher(), create_lower_yields_researcher(), Wire the FI dual-track debate after the analyst chain. Higher Yields <-> Lower…, _capturing_llm(), _direction_state(), unit, Direction debate researchers: higher vs lower yields (Task 4.1). Parallel…, test_higher_yields_opening_has_no_phantom_opponent() (+5 more)

### Community 83 - "test_fi_trader.py"
Cohesion: 0.32
Nodes (14): create_fi_trader(), _free_text_llm(), _full_coverage_decision(), unit, Fixed-Income Trader (Task 5.1): emits DirectionCall[]/ShapeCall[]. Consumes the…, LLM without structured-output support, forcing the free-text path., LLM whose structured binding returns a real TraderDecision instance., _state() (+6 more)

### Community 84 - "test_fi_interface.py"
Cohesion: 0.14
Nodes (13): get_category_for_method(), Get the category that contains the specified method., fixture, parametrize, Task 1.12: all Phase 1 fixed-income data tools are registered in the interface…, Each @tool wrapper must invoke its registered dataflows function., All new FI data tools should be importable and invocable. LangChain…, Docstrings are what the LLM sees — every tool must have one. (+5 more)

### Community 85 - "safe_ticker_component"
Cohesion: 0.21
Nodes (6): Validate ``value`` is safe to interpolate into a filesystem path. Tickers come…, safe_ticker_component(), unit, Tests for the ticker path-component validator that blocks directory traversal., Sanity: sanitized values stay within base when joined., TestSafeTickerComponent

### Community 86 - "write_report_tree"
Cohesion: 0.24
Nodes (11): Write the markdown report tree for a completed run, like the CLI does.…, Path, Reusable report-tree writer shared by the CLI and the programmatic API. Writes…, Save a completed run's reports to ``save_path``; return the complete-report…, write_report_tree(), unit, Report parity: the shared writer produces the report tree for the CLI and the…, _state() (+3 more)

### Community 87 - "AnthropicClient"
Cohesion: 0.14
Nodes (10): ChatAnthropic, AnthropicClient, NormalizedChatAnthropic, Any, Whether Anthropic accepts the ``effort`` parameter for this model., ChatAnthropic with normalized content output. Claude models with extended…, Client for Anthropic Claude models., Return configured ChatAnthropic instance. (+2 more)

### Community 88 - "DummyLLMClient"
Cohesion: 0.28
Nodes (3): DummyLLMClient, ModelValidationTests, unit

### Community 89 - "fred.py"
Cohesion: 0.15
Nodes (18): ALFRED (Archival FRED) point-in-time vintage fetcher. Returns economic data as…, _fred_today(), FredNotConfiguredError, get_api_key(), get_macro_data(), _get_session(), Session, FRED (Federal Reserve Economic Data) macro vendor. Fetches macroeconomic time… (+10 more)

### Community 90 - "._fetch_returns"
Cohesion: 0.11
Nodes (9): Fetch raw and alpha return for ticker over holding_days from trade_date.…, Resolve pending log entries for ticker at the start of a new run. Fetches…, Only 1 data point available → returns all-None, no crash., Empty DataFrame → returns all-None, no crash., SPY having fewer rows than the stock (but still a full window) must not raise…, #1169: a rerun before the full holding window has traded returns unavailable…, Pending AAPL entry is not resolved when the run is for NVDA., After resolve, get_pending_entries() is empty and the entry has a REFLECTION. (+1 more)

### Community 91 - "test_checkpoint_lifecycle.py"
Cohesion: 0.27
Nodes (13): _bare_graph(), _node_a(), _node_b(), StateGraph, TypedDict, unit, The checkpoint lifecycle is reusable so --checkpoint works on the CLI path…, _State (+5 more)

### Community 92 - "test_structured_agents.py"
Cohesion: 0.22
Nodes (12): Render a ResearchPlan to markdown for storage and the trader's prompt context., Structured investment plan produced by the Research Manager. Hand-off to the…, render_research_plan(), ResearchPlan, _make_rm_state(), unit, Tests for structured-output agents (Trader, Research Manager, Sentiment…, The RM prompt must list all five tiers so the schema enum matches user… (+4 more)

### Community 93 - "test_memory_pointintime.py"
Cohesion: 0.44
Nodes (10): _log(), unit, Memory-log lessons must be point-in-time safe in a backtest (#1251).…, _resolve(), test_as_of_excludes_lessons_resolved_after_the_run_date(), test_cross_ticker_lessons_are_also_gated(), test_legacy_entry_without_resolution_date_excluded_in_backtest(), test_memory_as_of_gates_historical_but_not_live() (+2 more)

### Community 94 - "fed_speeches.py"
Cohesion: 0.21
Nodes (12): _fallback(), _FeedShapeError, get_fed_speeches(), _parse_items(), date, ValueError, Fed speeches vendor: recent speeches by Federal Reserve officials. Source: the…, GET the RSS feed and return the raw response body. (+4 more)

### Community 95 - "test_ohlcv_cache_freshness.py"
Cohesion: 0.31
Nodes (12): _needs_same_day_refresh(), Whether a cached frame must be refetched to reflect the requested day. The…, unit, Same-day OHLCV cache must not serve a stale snapshot all day (#1150). The cache…, End-to-end: the helper is actually wired into load_ohlcv's cache branch.…, test_current_day_cache_past_ttl_is_refreshed(), test_historical_request_always_uses_cache(), test_load_ohlcv_refetches_stale_same_day_cache() (+4 more)

### Community 96 - "used_vehicle_index.py"
Cohesion: 0.23
Nodes (12): _by_month(), _csv_path(), get_used_vehicle_index(), ManheimFormatError, _parse(), _pct(), date, ValueError (+4 more)

### Community 98 - "BreakevensFetchTests"
Cohesion: 0.23
Nodes (4): BreakevensFetchTests, unit, Build a fred._request replacement dispatching on series_id., _request_stub()

### Community 99 - "checkpointer.py"
Cohesion: 0.20
Nodes (14): checkpoint_step(), clear_all_checkpoints(), clear_checkpoint(), _db_path(), get_checkpointer(), Path, LangGraph checkpoint support for resumable analysis runs. Per-ticker SQLite…, Return the SQLite checkpoint DB path for a ticker. (+6 more)

### Community 100 - "ism_prices_paid.py"
Cohesion: 0.23
Nodes (11): _csv_path(), get_ism_prices_paid(), ISMFormatError, _mom(), _parse(), date, ValueError, ISM Manufacturing Prices Index ("prices paid"): input-cost pressure. LIMITATION… (+3 more)

### Community 101 - "test_fi_config_models.py"
Cohesion: 0.27
Nodes (10): CentralBank, Curve, BaseModel, Currency-agnostic configuration models for rates analysis. Populated for…, Configuration for a sovereign yield curve., Configuration for a central bank's data sources., test_central_bank_requires_all_fields(), test_config_central_banks_parse_into_model() (+2 more)

### Community 102 - "TestLegacyRemoval"
Cohesion: 0.18
Nodes (6): FinancialSituationMemory must not be importable from the memory module., rank_bm25 must not be present in the memory module namespace., TradingAgentsGraph must not expose reflect_and_remember., create_portfolio_manager accepts only llm; passing memory= raises TypeError., propagate() completes and stores the decision after the redesign., TestLegacyRemoval

### Community 103 - "test_risk_router_path_map.py"
Cohesion: 0.36
Nodes (10): _debate_state(), parametrize, unit, Shared-router / path_map completeness (#1088). Both…, _state(), test_debate_path_map_covers_full_router_range(), test_debate_router_return_always_routable(), test_path_map_covers_full_router_range() (+2 more)

### Community 104 - "_build_run_config"
Cohesion: 0.29
Nodes (9): _build_run_config(), Assemble the run config from interactive selections, honoring env precedence.…, parametrize, CLI config precedence (#976, #977). An explicit environment override for the…, test_checkpoint_flag_overrides_env(), test_checkpoint_none_preserves_env_default(), test_env_round_counts_win_over_selection(), test_partial_env_only_overrides_that_count() (+1 more)

### Community 105 - "test_cli_fi_reskin.py"
Cohesion: 0.13
Nodes (15): MessageBuffer, Update analyst statuses based on accumulated report state. Logic: - Store new…, Initialize agent status and report sections based on selected analysts. Args:…, update_analyst_statuses(), get_ticker(), Prompt the user to enter a curve or ticker symbol, preserving exchange…, unit, Tests for FI CLI re-skinning and dual-track support in CLI. (+7 more)

### Community 106 - "polymarket.py"
Cohesion: 0.31
Nodes (9): get_prediction_markets(), _is_forward_looking(), _parse_json_list(), datetime, Polymarket prediction-market vendor. Surfaces live, market-implied…, Gamma encodes ``outcomes``/``outcomePrices`` as JSON-string arrays., Keep only open markets that resolve in the future. ``closed`` is the reliable…, Return live prediction-market probabilities for an event topic. Args: topic:… (+1 more)

### Community 107 - "AgentState"
Cohesion: 0.07
Nodes (19): AgentState, Route the steepener/flattener debate; hand to the Shape Research Manager once…, Determine if risk analysis should continue., Determine if market analysis should continue., Determine if sentiment-analyst tool round should continue. Method name keeps…, Determine if news analysis should continue., Determine if fundamentals analysis should continue., Shared analyst loop: route to the tool node while the model is calling tools,… (+11 more)

### Community 108 - "_make_api_request"
Cohesion: 0.10
Nodes (38): AlphaVantageRateLimitError, _filter_csv_by_date_range(), format_datetime_for_api(), _make_api_request(), Filter CSV data to include only rows within the specified date range. Args:…, Convert various date formats to YYYYMMDDTHHMM format required by Alpha Vantage…, Raised when the Alpha Vantage API rate limit is exceeded., Helper function to make API requests and handle responses. Raises:… (+30 more)

### Community 109 - "TestLoadOhlcvNoPoison"
Cohesion: 0.25
Nodes (3): unit, TestLoadOhlcvNoPoison, TestRouteToVendorSentinel

### Community 110 - "test_stocktwits_resilience.py"
Cohesion: 0.27
Nodes (6): parametrize, unit, _raise(), StockTwits fetch: transport-error resilience (#1024) and crypto symbol mapping…, TestStockTwitsCryptoSymbols, TestStockTwitsResilience

### Community 111 - "fomc_calendar.py"
Cohesion: 0.31
Nodes (8): _fmt_meeting(), get_fomc_calendar(), Meeting, date, FOMC meeting calendar and statement text (local files). Reports the FOMC…, Report the FOMC meetings bracketing ``curr_date`` as markdown. Args: curr_date:…, An FOMC meeting. ``end`` is the decision day (statement release)., _statement_path()

### Community 113 - "create_sentiment_analyst"
Cohesion: 0.24
Nodes (9): create_sentiment_analyst(), create_social_media_analyst(), Deprecated alias for :func:`create_sentiment_analyst`. Kept so existing code…, Create a sentiment analyst node for the trading graph. Pre-fetches news +…, Backwards-compatibility shim for the renamed module. The agent is now…, _make_sentiment_state(), MagicMock LLM whose structured binding captures the prompt and returns a real…, _structured_sentiment_llm() (+1 more)

### Community 114 - "announcements.py"
Cohesion: 0.29
Nodes (5): display_announcements(), fetch_announcements(), Fetch announcements from endpoint. Returns dict with announcements and settings., Display announcements panel. Prompts for Enter if require_attention is True., Console

### Community 115 - "TraderProposal"
Cohesion: 0.29
Nodes (7): Structured transaction proposal produced by the Trader. The trader reads the…, Render a TraderProposal to markdown. The trailing ``FINAL TRANSACTION PROPOSAL:…, render_trader_proposal(), TraderProposal, A weak LLM may write "None"/"N/A" into an optional float field (#1058); coerce…, TestNullishFloatCoercion, TestRenderTraderProposal

### Community 118 - "System Architecture Schema"
Cohesion: 0.40
Nodes (5): Analyst Team Diagram, Researcher Team Diagram, Risk Management Diagram, System Architecture Schema, Trader Agent Diagram

### Community 119 - "test_regime_dates.py"
Cohesion: 0.24
Nodes (11): all_dates(), Curated backtest test dates spanning distinct rate regimes (Task 7.2). Each…, Every regime test date flattened into one sorted, de-duplicated list., unit, Regime test dates (Task 7.2): curated test-date set spanning regimes., test_all_dates_flattened_sorted_unique(), test_dates_are_strict_iso_sorted_and_unique(), test_dates_fall_inside_named_regime_window() (+3 more)

### Community 121 - "TradingAgentsGraph"
Cohesion: 0.10
Nodes (22): True when only fixed-income analysts are active., Main class that orchestrates the trading agents framework., TradingAgentsGraph, Path, Verify fixed-income state keys are persisted in run logs without KeyError., Verify equity mode states continue to log correctly., test_equity_state_logging(), test_fi_state_logging() (+14 more)

### Community 123 - "PortfolioDecision"
Cohesion: 0.18
Nodes (9): field_validator, _coerce_optional_float(), PortfolioDecision, Structured output produced by the Portfolio Manager. The model fills every…, Render a PortfolioDecision back to the markdown shape the rest of the system…, render_pm_decision(), The structured PortfolioDecision is rendered to markdown that downstream…, Build a MagicMock LLM whose with_structured_output binding captures the prompt… (+1 more)

### Community 124 - "create_macro_calendar_analyst"
Cohesion: 0.36
Nodes (9): create_macro_calendar_analyst(), _FakeLLM, Tests for the Macro Calendar Analyst (Task 3.4). Offline: a fake LLM captures…, _state(), test_binds_expected_tool_set(), test_node_returns_macro_calendar_report_state_key(), test_preamble_carries_final_transaction_proposal_stop_signal(), test_prompt_covers_releases_surprises_and_supply() (+1 more)

### Community 125 - "CotCacheTests"
Cohesion: 0.27
Nodes (3): CotCacheTests, _CotTestCase, unit

### Community 144 - "BaseModel"
Cohesion: 0.22
Nodes (9): InflationComponentTrajectory, BaseModel, Per-spread shape outlook produced by the Shape Research Manager. One ShapeCall…, Render a ShapeOutlook to markdown for the trader's prompt context., Trajectory assessment for a single inflation component., Survey-based inflation expectations., render_shape_outlook(), ShapeOutlook (+1 more)

### Community 145 - "thread_id"
Cohesion: 0.28
Nodes (4): Deterministic thread ID for a ticker+date pair. ``signature`` folds in graph-…, thread_id(), A different graph shape (analyst selection / depth / asset mode) must not…, TestCheckpointSignature

### Community 147 - "HTTPError"
Cohesion: 0.50
Nodes (3): HTTPError, _atom_resp(), TestRss429Backoff

### Community 148 - "test_i18n_coverage.py"
Cohesion: 0.29
Nodes (5): parametrize, unit, Every report-producing agent must apply the configured output language…, test_report_agent_applies_language_instruction(), TestLanguageInstruction

### Community 149 - "TestTraderAgent"
Cohesion: 0.50
Nodes (3): _make_trader_state(), _structured_trader_llm(), TestTraderAgent

### Community 150 - ".__init__"
Cohesion: 0.50
Nodes (3): Any, ToolNode, Initialize with required components. ``disabled_tools`` (tool names) is…

### Community 151 - "inflation_breakevens.py"
Cohesion: 0.33
Nodes (5): _fetch_points(), get_inflation_breakevens(), Inflation breakevens (FRED): TIPS-implied inflation compensation. Fetches the…, Fetch one series' in-window observations, skipping FRED's '.' missings., Fetch the configured inflation breakeven series as one markdown report. Args:…

### Community 153 - "dataflows/utils.py"
Cohesion: 0.29
Nodes (3): DataFrame, save_output(), SavePathType

### Community 157 - "_clean_identity_value"
Cohesion: 0.67
Nodes (3): _clean_identity_value(), Any, Return a trimmed string, or None for empty / placeholder-ish values.

## Knowledge Gaps
- **18 isolated node(s):** `AnalystNodeSpec`, `fixedincomeagent`, `Analyst Team Diagram`, `Researcher Team Diagram`, `Risk Management Diagram` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1000 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TradingAgentsGraph` connect `TradingAgentsGraph` to `test_ablation.py`, `SignalProcessor`, `test_backtest_runner.py`, `FixedIncomeAnalysis`, `thread_id`, `patch`, `TestDeferredReflection`, `test_checkpoint_resume.py`, `test_fi_graph_setup.py`, `test_fi_graph_wiring.py`, `test_llm_max_tokens.py`, `test_treasury_benchmark.py`, `test_fi_portfolio_manager.py`, `._run_graph`, `test_llm_max_retries.py`, `TestProviderKwargsTemperature`, `test_memory_log.py`, `write_report_tree`, `._fetch_returns`, `test_checkpoint_lifecycle.py`, `test_memory_pointintime.py`, `checkpointer.py`, `TestLegacyRemoval`?**
  _High betweenness centrality (0.163) - this node is a cross-community bridge._
- **Why does `set_config()` connect `set_config` to `test_vendor_errors.py`, `_request_stub`, `_stub`, `test_consumer_expectations.py`, `_stub`, `test_baselines.py`, `_stub`, `test_i18n_coverage.py`, `FomcCalendarTests`, `test_fi_graph_setup.py`, `FredFormattingTests`, `._write_csv`, `._write_csv`, `stockstats_utils.py`, `VendorRoutingTests`, `test_polymarket.py`, `_assert_ohlcv_not_stale`, `TestLoadOhlcvNoPoison`, `CotCacheTests`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Why does `get_config()` connect `set_config` to `test_ablation.py`, `agent_utils.py`, `cot_data.py`, `test_backtest_runner.py`, `agents/__init__.py`, `_stub`, `test_baselines.py`, `_stub`, `invoke_structured_or_freetext`, `inflation_breakevens.py`, `shelter_rents.py`, `interface.py`, `in_window`, `test_fi_research_managers.py`, `test_fi_portfolio_manager.py`, `treasury.py`, `stockstats_utils.py`, `DirectionCall`, `create_curve_technicals_analyst`, `test_fi_trader.py`, `used_vehicle_index.py`, `ism_prices_paid.py`, `fomc_calendar.py`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `TradingAgentsGraph` (e.g. with `FixedIncomeAnalysis` and `BacktestRunner`) actually correct?**
  _`TradingAgentsGraph` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `ConditionalLogic` (e.g. with `AgentState` and `GraphSetup`) actually correct?**
  _`ConditionalLogic` has 21 INFERRED edges - model-reasoned connections that need verification._
- **What connects `AnalystNodeSpec`, `fixedincomeagent`, `Analyst Team Diagram` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_ablation.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06004543979227524 - nodes in this community are weakly interconnected._