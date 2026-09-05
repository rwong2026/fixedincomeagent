"""Backtest runner (Task 7.1): point-in-time replay harness.

Actual-outcome logic (direction/shape classification, horizon trading-day
semantics) is pure and tested directly. The FRED boundary (``fred._request``)
and the agent graph are stubbed, so the whole suite runs offline with no API
key and no LLM.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest import mock

import pytest

from fixedincomeagent.agents.schemas import (
    DirectionCall,
    ShapeCall,
    TraderDecision,
    render_trader_decision,
)
from fixedincomeagent.backtest.runner import (
    BacktestRunner,
    _classify_direction,
    _classify_shape,
    _entry_and_exit,
)
from fixedincomeagent.dataflows import fred

_CONFIG = {
    "fi_tenor_series": {"2Y": "DGS2", "5Y": "DGS5", "10Y": "DGS10", "30Y": "DGS30"},
    "fi_spread_definitions": {
        "2s10s": ("2Y", "10Y"),
        "5s30s": ("5Y", "30Y"),
        "2s5s10s_fly": ("2Y", "5Y", "10Y"),
    },
    "fi_horizon_days": 20,
    "fi_neutral_threshold_bp": 5,
}


def _business_days(start: str, n: int) -> list[str]:
    """n consecutive weekday dates starting on/after start."""
    days, d = [], datetime.strptime(start, "%Y-%m-%d")
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=1)
    return days


def _series_obs(start: str, n: int, start_yield: float, daily_step: float):
    """Synthetic yield series: n business days on a linear path."""
    dates = _business_days(start, n)
    obs = [
        {"date": d, "value": f"{start_yield + i * daily_step:.4f}"}
        for i, d in enumerate(dates)
    ]
    return dates, obs


def _fred_stub(series_obs: dict[str, list[dict]], capture: dict | None = None):
    """Build a fred._request replacement keyed by series_id."""
    def _impl(path, params):
        assert path == "series/observations"
        if capture is not None:
            capture[params["series_id"]] = params
        return {"observations": series_obs[params["series_id"]]}
    return _impl


# ---------------------------------------------------------------------------
# Direction classification (fi_neutral_threshold_bp semantics)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_classify_direction_up_down_neutral():
    assert _classify_direction(7.0, 5) == "up"
    assert _classify_direction(-7.0, 5) == "down"
    assert _classify_direction(3.0, 5) == "neutral"
    assert _classify_direction(0.0, 5) == "neutral"


@pytest.mark.unit
def test_classify_direction_exactly_at_threshold_is_directional():
    # Config semantics: moves *below* the threshold are neutral, so a move of
    # exactly threshold bp is a real directional outcome.
    assert _classify_direction(5.0, 5) == "up"
    assert _classify_direction(-5.0, 5) == "down"


# ---------------------------------------------------------------------------
# Shape classification
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_classify_shape_steepen_flatten_unchanged():
    assert _classify_shape(8.0, 5) == "steepen"
    assert _classify_shape(-8.0, 5) == "flatten"
    assert _classify_shape(2.0, 5) == "unchanged"
    assert _classify_shape(5.0, 5) == "steepen"  # edge, mirrors direction rule
    assert _classify_shape(-5.0, 5) == "flatten"


# ---------------------------------------------------------------------------
# Horizon trading-day logic: Nth available observation after test_date
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_entry_and_exit_uses_nth_observation_after_test_date():
    dates, obs = _series_obs("2025-01-06", 30, 4.0, 0.01)  # Mon 2025-01-06
    series = [(o["date"], float(o["value"])) for o in obs]
    (d0, v0), (d1, v1) = _entry_and_exit(series, dates[4], 20)
    assert d0 == dates[4]          # baseline: the test_date observation itself
    assert d1 == dates[4 + 20]     # exit: 20th observation strictly after
    assert v1 - v0 == pytest.approx(0.20)


@pytest.mark.unit
def test_entry_and_exit_weekend_test_date_uses_prior_observation():
    dates, obs = _series_obs("2025-01-06", 30, 4.0, 0.0)
    series = [(o["date"], float(o["value"])) for o in obs]
    saturday = "2025-01-11"  # between dates[4] (Fri) and dates[5] (Mon)
    (d0, _), (d1, _) = _entry_and_exit(series, saturday, 20)
    assert d0 == dates[4]
    assert d1 == dates[5 + 19]  # 20th observation after the weekend date


@pytest.mark.unit
def test_entry_and_exit_raises_when_horizon_has_not_elapsed():
    dates, obs = _series_obs("2025-01-06", 10, 4.0, 0.0)
    series = [(o["date"], float(o["value"])) for o in obs]
    with pytest.raises(ValueError, match="horizon"):
        _entry_and_exit(series, dates[4], 20)


@pytest.mark.unit
def test_entry_and_exit_raises_without_baseline():
    _, obs = _series_obs("2025-01-06", 30, 4.0, 0.0)
    series = [(o["date"], float(o["value"])) for o in obs]
    with pytest.raises(ValueError, match="baseline"):
        _entry_and_exit(series, "2024-12-01", 20)


# ---------------------------------------------------------------------------
# _compute_actuals: full direction + shape computation over stub FRED data
# ---------------------------------------------------------------------------


def _four_tenor_stub(steps: dict[str, float]):
    """Observations per series_id for a shared business-day calendar."""
    dates = _business_days("2025-01-06", 30)
    obs = {}
    for tenor, sid in _CONFIG["fi_tenor_series"].items():
        obs[sid] = [
            {"date": d, "value": f"{4.0 + i * steps[tenor]:.4f}"}
            for i, d in enumerate(dates)
        ]
    return dates, obs


@pytest.mark.unit
def test_compute_actuals_direction_shape_and_horizon():
    test_date = "2025-01-10"  # dates[4], a Friday
    # Over the 20-observation horizon: 2Y 0bp, 5Y +2bp, 10Y +10bp, 30Y -10bp.
    dates, obs = _four_tenor_stub({"2Y": 0.0, "5Y": 0.001, "10Y": 0.005, "30Y": -0.005})
    runner = BacktestRunner(graph=object(), config=_CONFIG)
    with mock.patch.object(fred, "_request", side_effect=_fred_stub(obs)):
        direction, shape, changes, horizon_end = runner._compute_actuals(test_date)

    assert direction == {"2Y": "neutral", "5Y": "neutral", "10Y": "up", "30Y": "down"}
    assert changes["10Y"] == pytest.approx(10.0)
    assert changes["30Y"] == pytest.approx(-10.0)
    # 2s10s: +10 - 0 = +10bp -> steepen; 5s30s: -10 - 2 = -12bp -> flatten;
    # fly: 2 - (0 + 10)/2 = -3bp, inside threshold -> unchanged.
    assert shape == {"2s10s": "steepen", "5s30s": "flatten", "2s5s10s_fly": "unchanged"}
    assert horizon_end == dates[4 + 20]


@pytest.mark.unit
def test_compute_actuals_butterfly_steepen_and_flatten():
    test_date = "2025-01-10"
    runner = BacktestRunner(graph=object(), config=_CONFIG)

    # Belly (5Y) outperforms wings: 20 - (0 + 10)/2 = +15bp -> fly steepens.
    _, obs_up = _four_tenor_stub({"2Y": 0.0, "5Y": 0.01, "10Y": 0.005, "30Y": 0.0})
    with mock.patch.object(fred, "_request", side_effect=_fred_stub(obs_up)):
        _, shape, _, _ = runner._compute_actuals(test_date)
    assert shape["2s5s10s_fly"] == "steepen"

    # Belly underperforms wings: -20 - (0 + 10)/2 = -25bp -> fly flattens.
    _, obs_down = _four_tenor_stub({"2Y": 0.0, "5Y": -0.01, "10Y": 0.005, "30Y": 0.0})
    with mock.patch.object(fred, "_request", side_effect=_fred_stub(obs_down)):
        _, shape, _, _ = runner._compute_actuals(test_date)
    assert shape["2s5s10s_fly"] == "flatten"


@pytest.mark.unit
def test_fetch_series_skips_missing_values_and_pins_window():
    obs = {"DGS2": [
        {"date": "2025-01-06", "value": "4.10"},
        {"date": "2025-01-07", "value": "."},  # FRED missing marker -> skipped
        {"date": "2025-01-08", "value": "4.12"},
    ]}
    capture: dict = {}
    runner = BacktestRunner(graph=object(), config=_CONFIG)
    with mock.patch.object(fred, "_request", side_effect=_fred_stub(obs, capture)):
        series = runner._fetch_series("DGS2", "2025-01-10")
    assert series == [("2025-01-06", 4.10), ("2025-01-08", 4.12)]
    # Window starts ahead of test_date so a baseline exists even when
    # test_date itself is a weekend/holiday; no observation_end (latest data).
    assert capture["DGS2"]["observation_start"] == "2024-12-27"
    assert "observation_end" not in capture["DGS2"]


# ---------------------------------------------------------------------------
# Runner integration: stub graph + stub FRED, markdown round-trip
# ---------------------------------------------------------------------------


class _StubGraph:
    """Stands in for TradingAgentsGraph.propagate; no LLM, no network."""

    def __init__(self, decision_md: str):
        self._decision_md = decision_md
        self.propagate_calls: list[tuple[str, str]] = []

    def propagate(self, ticker, trade_date, **kwargs):
        self.propagate_calls.append((ticker, trade_date))
        return (
            {
                "final_trade_decision": self._decision_md,
                "market_report": "MARKET REPORT BODY",
                "trader_investment_plan": self._decision_md,
            },
            "REVIEW",
        )


def _decision() -> TraderDecision:
    return TraderDecision(
        direction_calls=[
            DirectionCall(tenor="2Y", direction="neutral", magnitude_bucket="<10bp",
                          confidence=0.5, rationale="front end pinned"),
            DirectionCall(tenor="5Y", direction="neutral", magnitude_bucket="<10bp",
                          confidence=0.5, rationale="belly quiet"),
            DirectionCall(tenor="10Y", direction="up", magnitude_bucket="10-25bp",
                          confidence=0.7, rationale="term premium rebuild"),
            DirectionCall(tenor="30Y", direction="down", magnitude_bucket="10-25bp",
                          confidence=0.6, rationale="duration bid"),
        ],
        shape_calls=[
            ShapeCall(spread="2s10s", shape="steepen", confidence=0.65,
                      rationale="long end leads"),
            ShapeCall(spread="5s30s", shape="flatten", confidence=0.6,
                      rationale="belly vs long bond"),
            ShapeCall(spread="2s5s10s_fly", shape="unchanged", confidence=0.5,
                      rationale="no fly edge"),
        ],
    )


@pytest.mark.unit
def test_run_replays_stub_graph_and_computes_actuals():
    test_date = "2025-01-10"
    dates, obs = _four_tenor_stub({"2Y": 0.0, "5Y": 0.001, "10Y": 0.005, "30Y": -0.005})
    decision = _decision()
    graph = _StubGraph(render_trader_decision(decision))
    runner = BacktestRunner(graph=graph, config=_CONFIG)

    with mock.patch.object(fred, "_request", side_effect=_fred_stub(obs)):
        results = runner.run([test_date])

    assert len(results.runs) == 1
    run = results.runs[0]
    assert run.test_date == test_date
    # The PM's rendered markdown round-trips through parse_trader_decision.
    assert run.direction_calls == decision.direction_calls
    assert run.shape_calls == decision.shape_calls
    assert run.actual_direction == {
        "2Y": "neutral", "5Y": "neutral", "10Y": "up", "30Y": "down"
    }
    assert run.actual_shape == {
        "2s10s": "steepen", "5s30s": "flatten", "2s5s10s_fly": "unchanged"
    }
    assert run.actual_yield_changes_bp["10Y"] == pytest.approx(10.0)
    assert run.horizon_end_date == dates[4 + 20]
    # Agent reports are recorded from the final state.
    assert run.agent_reports["market_report"] == "MARKET REPORT BODY"
    # The graph ran pinned to the test date with the UST ticker.
    assert graph.propagate_calls == [("UST", test_date)]


@pytest.mark.unit
def test_run_multiple_dates_in_order():
    _, obs = _four_tenor_stub({"2Y": 0.0, "5Y": 0.0, "10Y": 0.0, "30Y": 0.0})
    graph = _StubGraph(render_trader_decision(_decision()))
    runner = BacktestRunner(graph=graph, config=_CONFIG)

    with mock.patch.object(fred, "_request", side_effect=_fred_stub(obs)):
        results = runner.run(["2025-01-10", "2025-01-13"])

    assert [r.test_date for r in results.runs] == ["2025-01-10", "2025-01-13"]
    assert graph.propagate_calls == [("UST", "2025-01-10"), ("UST", "2025-01-13")]
