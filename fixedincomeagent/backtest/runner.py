"""Point-in-time backtest replay harness for the UST rates/curve pipeline.

For each test date the runner invokes the agent graph pinned to that date
(``TradingAgentsGraph.propagate`` — agent prompts request tools pinned to the
state trade_date, and revision-prone series are fetched as ALFRED vintages by
``alfred.py``), parses the FI portfolio manager's rendered
``final_trade_decision`` back into DirectionCall/ShapeCall objects via the
tolerant Task 5.2 parser, and scores them against ACTUAL outcomes computed
from realized DGS yields.

Yields are never revised by FRED, so the runner's own actual-outcome fetch
needs no realtime vintage pin: current DGS data equals point-in-time data for
these series. "Trading days" means the series' own observations — the horizon
end is the Nth available observation after the test date, which handles
weekends and holidays without a market-calendar dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from fixedincomeagent.agents.risk_mgmt.fi_consistency_checker import (
    parse_trader_decision,
)
from fixedincomeagent.agents.schemas import DirectionCall, ShapeCall
from fixedincomeagent.dataflows import fred
from fixedincomeagent.dataflows.config import get_config

# Analyst set that wires the FI dual-track pipeline (see graph/analyst_execution).
_FI_ANALYSTS = ["macro_policy", "curve_technicals", "fed_speak", "macro_calendar"]

# Buffer ahead of test_date so a baseline observation exists even when
# test_date falls on a weekend/holiday.
_BASELINE_LOOKBACK_DAYS = 14


@dataclass
class AblationConfig:
    """Config for ablation testing."""

    disable_inflation_components: bool = False  # skip shelter/vehicles/supply chain
    disable_positioning: bool = False  # skip COT data
    disable_fed_speak: bool = False  # skip speech analysis
    label: str = "full"  # human-readable ablation label


# Inflation-component detail tools dropped by disable_inflation_components.
_INFLATION_COMPONENT_TOOLS = frozenset({
    "get_shelter_rents",
    "get_used_vehicle_index",
    "get_supply_chain_pressure",
    "get_ism_prices_paid",
    "get_inflation_nowcast",
    "get_consumer_inflation_expectations",
})


def ablation_disabled_tools(config: AblationConfig | None) -> frozenset[str]:
    """Map ablation flags to the tool names to drop. Ablation removes DATA,
    not agents — every analyst still runs, with fewer tools bound."""
    if config is None:
        return frozenset()
    names = set()
    if config.disable_inflation_components:
        names |= _INFLATION_COMPONENT_TOOLS
    if config.disable_positioning:
        names.add("get_cot_data")
    if config.disable_fed_speak:
        names.add("get_fed_speeches")
    return frozenset(names)


@dataclass
class BacktestRun:
    """One replayed test date: predicted calls vs. realized outcomes."""

    test_date: str
    direction_calls: list[DirectionCall]
    shape_calls: list[ShapeCall]
    actual_direction: dict[str, str]  # tenor -> "up"/"down"/"neutral"
    actual_shape: dict[str, str]  # spread -> "steepen"/"flatten"/"unchanged"
    actual_yield_changes_bp: dict[str, float]  # tenor -> bp change
    horizon_end_date: str
    # All agent report strings from the final state, for downstream scoring
    # and audit (design: "record ... all agent reports").
    agent_reports: dict[str, str] = field(default_factory=dict)


@dataclass
class BacktestResults:
    """Ordered container returned by ``BacktestRunner.run``."""

    runs: list[BacktestRun] = field(default_factory=list)


def _classify_direction(change_bp: float, threshold_bp: float) -> str:
    """up/down/neutral. Moves *below* the threshold are neutral (config
    semantics), so exactly-at-threshold is directional."""
    if change_bp >= threshold_bp:
        return "up"
    if change_bp <= -threshold_bp:
        return "down"
    return "neutral"


def _classify_shape(change_bp: float, threshold_bp: float) -> str:
    """steepen/flatten/unchanged, same threshold semantics as direction."""
    if change_bp >= threshold_bp:
        return "steepen"
    if change_bp <= -threshold_bp:
        return "flatten"
    return "unchanged"


def _entry_and_exit(
    series: list[tuple[str, float]], test_date: str, horizon_days: int
) -> tuple[tuple[str, float], tuple[str, float]]:
    """Baseline = last observation on/before test_date; exit = the
    ``horizon_days``-th observation strictly after test_date (the series' own
    trading days). Raises ValueError when either side is unavailable — a test
    date whose horizon has not yet elapsed cannot be scored."""
    before = [p for p in series if p[0] <= test_date]
    after = [p for p in series if p[0] > test_date]
    if not before:
        raise ValueError(f"no baseline observation on/before {test_date}")
    if len(after) < horizon_days:
        raise ValueError(
            f"horizon of {horizon_days} trading days has not elapsed after "
            f"{test_date}: only {len(after)} observations available"
        )
    return before[-1], after[horizon_days - 1]


class BacktestRunner:
    """Replays the FI pipeline over historical test dates and scores outcomes.

    ``graph`` is injectable for tests/offline runs: anything exposing
    ``propagate(ticker, trade_date) -> (final_state, signal)``. When omitted, a
    real ``TradingAgentsGraph`` is built lazily with the FI analyst set.

    ``ablation_config`` drops data-source tools from the graph's analysts
    (e.g. run with vs. without the Phase 1b inflation-component detail) to
    test whether a source improves hit rate/calibration or just adds noise
    and cost. Ablation removes DATA, not agents — every analyst still runs
    with a reduced tool set.
    """

    def __init__(
        self,
        graph: Any | None = None,
        config: dict | None = None,
        ticker: str = "UST",
        ablation_config: AblationConfig | None = None,
    ):
        self._graph = graph
        self.config = config if config is not None else get_config()
        self.ticker = ticker
        self.ablation_config = ablation_config or AblationConfig()

    @property
    def graph(self):
        if self._graph is None:
            # Lazy: importing TradingAgentsGraph pulls in the whole LLM stack,
            # which offline scoring/tests never need.
            from fixedincomeagent.graph.trading_graph import TradingAgentsGraph

            self._graph = TradingAgentsGraph(
                selected_analysts=_FI_ANALYSTS,
                config=self.config,
                disabled_tools=ablation_disabled_tools(self.ablation_config),
            )
        return self._graph

    def run(self, test_dates: list[str]) -> BacktestResults:
        """Replay each test date in order and collect one BacktestRun per date."""
        return BacktestResults(runs=[self.run_date(d) for d in test_dates])

    def run_date(self, test_date: str) -> BacktestRun:
        final_state, _signal = self.graph.propagate(self.ticker, test_date)
        decision_md = final_state.get("final_trade_decision") or ""
        direction_calls, shape_calls = parse_trader_decision(decision_md)
        actual_direction, actual_shape, changes_bp, horizon_end = (
            self._compute_actuals(test_date)
        )
        agent_reports = {
            key: value
            for key, value in final_state.items()
            if isinstance(value, str)
            and value
            and (key.endswith("_report") or key == "trader_investment_plan")
        }
        return BacktestRun(
            test_date=test_date,
            direction_calls=direction_calls,
            shape_calls=shape_calls,
            actual_direction=actual_direction,
            actual_shape=actual_shape,
            actual_yield_changes_bp=changes_bp,
            horizon_end_date=horizon_end,
            agent_reports=agent_reports,
        )

    def _compute_actuals(
        self, test_date: str
    ) -> tuple[dict[str, str], dict[str, str], dict[str, float], str]:
        """Realized outcomes for a test date from the configured tenor series.

        Pure apart from the ``_fetch_series`` boundary (stub fred._request in
        tests). Returns (actual_direction, actual_shape, changes_bp,
        horizon_end_date). ``horizon_end_date`` is the latest per-tenor exit
        date — the day the full horizon had elapsed for every tenor.
        """
        horizon = int(self.config["fi_horizon_days"])
        threshold = float(self.config["fi_neutral_threshold_bp"])

        changes_bp: dict[str, float] = {}
        actual_direction: dict[str, str] = {}
        exit_dates: list[str] = []
        for tenor, series_id in self.config["fi_tenor_series"].items():
            series = self._fetch_series(series_id, test_date)
            (_, v0), (d1, v1) = _entry_and_exit(series, test_date, horizon)
            change = (v1 - v0) * 100
            changes_bp[tenor] = change
            actual_direction[tenor] = _classify_direction(change, threshold)
            exit_dates.append(d1)

        actual_shape: dict[str, str] = {}
        for name, legs in self.config["fi_spread_definitions"].items():
            if any(tenor not in changes_bp for tenor in legs):
                continue  # spread references a tenor outside fi_tenor_series
            if len(legs) == 2:
                short, long_ = legs
                delta = changes_bp[long_] - changes_bp[short]
            else:  # butterfly: belly vs wings average (Task 5.2 semantics)
                wing1, belly, wing2 = legs
                delta = changes_bp[belly] - (changes_bp[wing1] + changes_bp[wing2]) / 2
            actual_shape[name] = _classify_shape(delta, threshold)

        return actual_direction, actual_shape, changes_bp, max(exit_dates)

    def _fetch_series(self, series_id: str, test_date: str) -> list[tuple[str, float]]:
        """Raw (date, yield) observations for a FRED series, ascending.

        No realtime pin: DGS yields are not revised, so latest data is the
        point-in-time data. No observation_end: the window must extend past
        test_date + horizon to settle the outcome.
        """
        start = (
            datetime.strptime(test_date, "%Y-%m-%d")
            - timedelta(days=_BASELINE_LOOKBACK_DAYS)
        ).strftime("%Y-%m-%d")
        data = fred._request(
            "series/observations",
            {
                "series_id": series_id,
                "observation_start": start,
                "sort_order": "asc",
            },
        )
        return [
            (o["date"], float(o["value"]))
            for o in data.get("observations", [])
            if o.get("value") not in (".", None, "")
        ]
