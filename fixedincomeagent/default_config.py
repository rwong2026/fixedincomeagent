import os

# ponytail: TRADINGAGENTS_* fallback for 1 release, drop after migration
for _k, _v in list(os.environ.items()):
    if _k.startswith("TRADINGAGENTS_"):
        os.environ.setdefault("FIXEDINCOMEAGENT_" + _k[len("TRADINGAGENTS_"):], _v)

_FIXEDINCOMEAGENT_HOME = os.path.join(os.path.expanduser("~"), ".fixedincomeagent")

# Single source of truth for env-var → config-key overrides. To expose
# a new config key for environment-based override, add a row here — no
# entry-point script changes required. Coercion is driven by the type
# of the existing default, so users can keep writing plain strings in
# their .env file.
_ENV_OVERRIDES = {
    "FIXEDINCOMEAGENT_LLM_PROVIDER":         "llm_provider",
    "FIXEDINCOMEAGENT_DEEP_THINK_LLM":       "deep_think_llm",
    "FIXEDINCOMEAGENT_QUICK_THINK_LLM":      "quick_think_llm",
    "FIXEDINCOMEAGENT_LLM_BACKEND_URL":      "backend_url",
    "FIXEDINCOMEAGENT_OUTPUT_LANGUAGE":      "output_language",
    "FIXEDINCOMEAGENT_MAX_DEBATE_ROUNDS":    "max_debate_rounds",
    "FIXEDINCOMEAGENT_MAX_RISK_ROUNDS":      "max_risk_discuss_rounds",
    "FIXEDINCOMEAGENT_CHECKPOINT_ENABLED":   "checkpoint_enabled",
    "FIXEDINCOMEAGENT_BENCHMARK_TICKER":     "benchmark_ticker",
    "FIXEDINCOMEAGENT_TEMPERATURE":          "temperature",
    "FIXEDINCOMEAGENT_LLM_MAX_RETRIES":      "llm_max_retries",
    "FIXEDINCOMEAGENT_MAX_TOKENS":           "max_tokens",
    # Provider-specific reasoning/thinking knobs (None = each provider's own
    # default). Settable here for non-interactive runs; the CLI also offers an
    # interactive choice, which is skipped when the matching var is set.
    "FIXEDINCOMEAGENT_GOOGLE_THINKING_LEVEL":   "google_thinking_level",
    "FIXEDINCOMEAGENT_OPENAI_REASONING_EFFORT": "openai_reasoning_effort",
    "FIXEDINCOMEAGENT_ANTHROPIC_EFFORT":        "anthropic_effort",
}


_BOOL_TRUE = ("true", "1", "yes", "on")
_BOOL_FALSE = ("false", "0", "no", "off")


def _coerce(value: str, reference):
    """Coerce env-var string to the type of the existing default value.

    Invalid values raise ``ValueError`` rather than silently falling back to a
    default — a misspelled boolean (e.g. ``treu``) or non-numeric int should fail
    loudly at startup, not quietly misconfigure an unattended run.
    """
    if isinstance(reference, bool):
        normalized = value.strip().lower()
        if normalized in _BOOL_TRUE:
            return True
        if normalized in _BOOL_FALSE:
            return False
        raise ValueError(
            f"expected a boolean ({'/'.join(_BOOL_TRUE + _BOOL_FALSE)}), got {value!r}"
        )
    if isinstance(reference, int) and not isinstance(reference, bool):
        return int(value)
    if isinstance(reference, float):
        return float(value)
    return value


def _apply_env_overrides(config: dict) -> dict:
    """Apply FIXEDINCOMEAGENT_* env vars to the config dict in-place."""
    for env_var, key in _ENV_OVERRIDES.items():
        raw = os.environ.get(env_var)
        if raw is None or raw == "":
            continue
        try:
            config[key] = _coerce(raw, config.get(key))
        except ValueError as exc:
            raise ValueError(f"Invalid value for {env_var}: {exc}") from exc
    return config


DEFAULT_CONFIG = _apply_env_overrides({
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("FIXEDINCOMEAGENT_RESULTS_DIR", os.path.join(_FIXEDINCOMEAGENT_HOME, "logs")),
    "data_cache_dir": os.getenv("FIXEDINCOMEAGENT_CACHE_DIR", os.path.join(_FIXEDINCOMEAGENT_HOME, "cache")),
    "memory_log_path": os.getenv("FIXEDINCOMEAGENT_MEMORY_LOG_PATH", os.path.join(_FIXEDINCOMEAGENT_HOME, "memory", "trading_memory.md")),
    # Optional cap on the number of resolved memory log entries. When set,
    # the oldest resolved entries are pruned once this limit is exceeded.
    # Pending entries are never pruned. None disables rotation entirely.
    "memory_log_max_entries": None,
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "gpt-5.6",
    "quick_think_llm": "gpt-5.6-luna",
    # When None, each provider's client falls back to its own default endpoint
    # (api.openai.com for OpenAI, generativelanguage.googleapis.com for Gemini, ...).
    # The CLI overrides this per provider when the user picks one. Keeping a
    # provider-specific URL here would leak (e.g. OpenAI's /v1 was previously
    # being forwarded to Gemini, producing malformed request URLs).
    "backend_url": None,
    # Provider-specific thinking configuration
    "google_thinking_level": None,      # "high", "minimal", etc.
    "openai_reasoning_effort": None,    # "medium", "high", "low"
    "anthropic_effort": None,           # "high", "medium", "low"
    # Sampling temperature, forwarded to every provider when set. None leaves
    # each provider at its own default. Lower values reduce run-to-run
    # variation on models that honor it; reasoning models largely ignore it
    # and no setting makes LLM output bit-identical across runs (see README).
    "temperature": None,
    # SDK retry budget forwarded to every provider chat client. None leaves each
    # provider/SDK at its own default (usually 2). Raise it to ride out bursty
    # 429 throttling on rate-limited deployments instead of aborting a run (#1091).
    "llm_max_retries": None,
    # Cap on output tokens forwarded to every provider chat client. None leaves
    # each provider at its own default. Set it to bound a model that emits
    # unbounded reasoning/output and hangs or trips a gateway idle timeout
    # (e.g. some deepseek-v4-flash deployments, #1204).
    "max_tokens": None,
    # Checkpoint/resume: when True, LangGraph saves state after each node
    # so a crashed run can resume from the last successful step.
    "checkpoint_enabled": False,
    # Output language for analyst reports and final decision
    # Internal agent debate stays in English for reasoning quality
    "output_language": "English",
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # News / data fetching parameters
    # Increase for longer lookback strategies or to broaden macro coverage;
    # decrease to reduce token usage in agent prompts.
    "news_article_limit": 20,             # max articles per ticker (ticker-news)
    "global_news_article_limit": 10,      # max articles for global/macro news
    "global_news_lookback_days": 7,       # macro news lookback window
    # Search queries used by get_global_news for macro headlines. Extend or
    # replace to broaden geographic / sector coverage.
    "global_news_queries": [
        "Federal Reserve interest rates inflation",
        "S&P 500 earnings GDP economic outlook",
        "geopolitical risk trade war sanctions",
        "ECB Bank of England BOJ central bank policy",
        "oil commodities supply chain energy",
    ],
    # Data vendor configuration
    # Category-level configuration (default for all tools in category).
    # The configured value is the exact vendor chain — requests are NOT silently
    # routed to vendors you didn't choose. For ordered fallback, list several,
    # e.g. "yfinance,alpha_vantage". "default" uses all available vendors.
    "data_vendors": {
        "core_stock_apis": "yfinance",       # Options: alpha_vantage, yfinance
        "technical_indicators": "yfinance",  # Options: alpha_vantage, yfinance
        "fundamental_data": "yfinance",      # Options: alpha_vantage, yfinance
        "news_data": "yfinance",             # Options: alpha_vantage, yfinance
        "macro_data": "fred",                # Options: fred (needs FRED_API_KEY)
        "prediction_markets": "polymarket",  # Options: polymarket (keyless)
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        # Example: "get_stock_data": "alpha_vantage",  # Override category default
    },
    # Benchmark for alpha calculation in the reflection layer.
    # ``benchmark_ticker`` (when set) overrides the suffix map for all
    # tickers; leave it None to use ``benchmark_map`` for auto-detection
    # based on the ticker's exchange suffix. SPY remains the US default
    # so the reflection label keeps reading "Alpha vs SPY" for US tickers
    # while non-US tickers get their regional index automatically.
    "benchmark_ticker": None,
    "benchmark_map": {
        ".NS":  "^NSEI",       # NSE India (Nifty 50)
        ".BO":  "^BSESN",      # BSE India (Sensex)
        ".T":   "^N225",       # Tokyo (Nikkei 225)
        ".HK":  "^HSI",        # Hong Kong (Hang Seng)
        ".L":   "^FTSE",       # London (FTSE 100)
        ".TO":  "^GSPTSE",     # Toronto (TSX Composite)
        ".AX":  "^AXJO",       # Australia (ASX 200)
        ".SS":  "000001.SS",   # Shanghai (SSE Composite)
        ".SZ":  "399001.SZ",   # Shenzhen (SZSE Component)
        "":     "SPY",         # default for US-listed tickers (no suffix)
    },
    # --- Fixed-Income (UST Rates & Curve) Configuration ---
    # Tenors to generate DirectionCalls for
    "fi_tenors": ["2Y", "5Y", "10Y", "30Y"],
    # Spreads/butterflies to generate ShapeCalls for
    "fi_spreads": ["2s10s", "5s30s", "2s5s10s_fly"],
    # Prediction horizon in trading days (not calendar days)
    "fi_horizon_days": 20,
    # Neutral threshold: yield moves below this (in bp) are classified
    # as "neutral" rather than directional. Documented tunable — not a
    # magic number. Calibrate via Phase 7 backtest.
    "fi_neutral_threshold_bp": 5,
    # FRED series IDs for key tenors (constant maturity yields)
    "fi_tenor_series": {
        "2Y": "DGS2",
        "5Y": "DGS5",
        "10Y": "DGS10",
        "30Y": "DGS30",
    },
    # FRED series for policy/funding rates
    "fi_rate_series": {
        "SOFR": "SOFR",
        "EFFR": "EFFR",
    },
    # FRED series for inflation breakevens
    "fi_breakeven_series": {
        "5Y_breakeven": "T5YIE",
        "10Y_breakeven": "T10YIE",
        "5Y5Y_forward": "T5YIFR",
    },
    # Spread definitions: maps spread name → (short_tenor, long_tenor)
    "fi_spread_definitions": {
        "2s10s": ("2Y", "10Y"),
        "5s30s": ("5Y", "30Y"),
        "2s5s10s_fly": ("2Y", "5Y", "10Y"),  # butterfly: 2×belly − wings
    },
    # Debate configuration for fixed-income dual-track debate
    "max_direction_debate_rounds": 1,
    "max_shape_debate_rounds": 1,
})
