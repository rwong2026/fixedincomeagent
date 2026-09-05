"""Baseline comparisons (Task 7.4): no-change and forwards-implied bars.

Offline: the Treasury.gov par-curve CSV fetch is mocked at the
``treasury._request`` boundary (same pattern as test_treasury.py) and the
cache dir is redirected via ``set_config`` (conftest restores global config).

Expected forward-implied values are hand-computed from the front-of-curve
no-arbitrage formula, with h = 20/252 and y_h the curve yield at maturity h
(the 1 Mo point, the shortest available tenor):

    f(h->P) = (P*y_P - h*y_h)/(P-h),   implied change = f - y_P

For a linear curve y(t) = y0 + s*t this collapses to h*(y_P - y_h)/(P-h) =
s*h*(P-m)/(P-h) (m = 1/12y), i.e. ~s*h and tenor-independent (the
horizon-scaled bar). Reference values:

- Linear curve y(t) = 2.0 + 0.1*t  -> +0.792149 (2Y), +0.793065 (5Y),
  +0.793360 (10Y), +0.793554bp (30Y); all well inside the 5bp neutral band.
- Flat curve y(t) = 4.0            -> 0bp everywhere.
- Inverted curve y(t) = 5.0 - 0.1*t -> -0.792149 (2Y), -0.793065 (5Y),
  -0.793360 (10Y), -0.793554bp (30Y); negative long-end implication.
- y(t) = 4.0 + 0.63*t -> 2Y implied +4.989669bp (just below the 5bp neutral
  threshold -> neutral); y(t) = 4.0 + 0.65*t -> +5.147934bp (-> up).
"""
from __future__ import annotations

from unittest import mock

import pytest

from fixedincomeagent.agents.schemas import DirectionCall, ShapeCall
from fixedincomeagent.backtest.baselines import (
    BaselineRun,
    forwards_implied_baseline,
    no_change_baseline,
    with_actuals,
)
from fixedincomeagent.backtest.runner import BacktestRun
from fixedincomeagent.backtest.scoring import score_backtest
from fixedincomeagent.dataflows import treasury
from fixedincomeagent.dataflows.config import set_config

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

_HEADER = (
    'Date,"1 Mo","2 Mo","3 Mo","4 Mo","6 Mo","1 Yr","2 Yr","3 Yr","5 Yr",'
    '"7 Yr","10 Yr","20 Yr","30 Yr"'
)
_TENOR_YEARS = [1 / 12, 2 / 12, 0.25, 4 / 12, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0,
                10.0, 20.0, 30.0]


def _curve_csv(rows: list[tuple[str, callable]]) -> str:
    """Build a par-yield CSV body; each row is (MM/DD/YYYY, t_years -> pct)."""
    lines = [_HEADER]
    for d, yfn in rows:
        lines.append(d + "," + ",".join(f"{yfn(t):.4f}" for t in _TENOR_YEARS))
    return "\n".join(lines) + "\n"


def _treasury_stub(csv: str):
    """treasury._request replacement serving the same CSV for any year.

    Rows inside the CSV carry full dates, so the point-in-time filtering
    under test is unaffected; the lookback may legitimately cross a year
    boundary for January test dates.
    """
    def _impl(url, params=None):
        assert "daily-treasury-rates.csv" in url
        return csv
    return _impl


@pytest.fixture()
def _tmp_cache(tmp_path):
    set_config({"data_cache_dir": str(tmp_path)})


# ---------------------------------------------------------------------------
# No-change baseline
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_no_change_neutral_calls_for_every_configured_tenor_and_spread():
    runs = no_change_baseline(["2025-01-10", "2025-01-13"], config=_CONFIG)

    assert [r.test_date for r in runs] == ["2025-01-10", "2025-01-13"]
    for run in runs:
        assert isinstance(run, BaselineRun)
        assert [c.tenor for c in run.direction_calls] == ["2Y", "5Y", "10Y", "30Y"]
        for call in run.direction_calls:
            assert isinstance(call, DirectionCall)
            assert call.direction == "neutral"
            assert call.magnitude_bucket == "<10bp"
            assert call.confidence == 0.5
        assert [c.spread for c in run.shape_calls] == [
            "2s10s", "5s30s", "2s5s10s_fly",
        ]
        for call in run.shape_calls:
            assert isinstance(call, ShapeCall)
            assert call.shape == "unchanged"
            assert call.confidence == 0.5
        # A no-change prediction is literally an implied change of zero.
        assert run.implied_changes_bp == {
            "2Y": 0.0, "5Y": 0.0, "10Y": 0.0, "30Y": 0.0
        }


@pytest.mark.unit
def test_no_change_uses_no_market_data_at_all():
    # Point-in-time trivially holds: the baseline touches no data boundary.
    with mock.patch.object(treasury, "_request", side_effect=AssertionError), mock.patch(
        "fixedincomeagent.dataflows.fred._request", side_effect=AssertionError
    ):
        runs = no_change_baseline(["2025-01-10"], config=_CONFIG)
    assert len(runs) == 1


# ---------------------------------------------------------------------------
# Forwards-implied baseline
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_forwards_flat_curve_implies_no_change(_tmp_cache):
    csv_text = _curve_csv([("01/10/2025", lambda t: 4.00)])
    with mock.patch.object(
        treasury, "_request", side_effect=_treasury_stub(csv_text)
    ):
        runs = forwards_implied_baseline(["2025-01-10"], config=_CONFIG)

    run = runs[0]
    for change in run.implied_changes_bp.values():
        assert change == pytest.approx(0.0, abs=1e-9)
    for call in run.direction_calls:
        assert call.direction == "neutral"
        assert call.magnitude_bucket == "<10bp"
    for call in run.shape_calls:
        assert call.shape == "unchanged"


@pytest.mark.unit
def test_forwards_upward_sloping_curve_implies_rises(_tmp_cache):
    # y(t) = 2.0 + 0.1*t percent: a mild +10bp/year slope.
    csv_text = _curve_csv([("01/10/2025", lambda t: 2.0 + 0.1 * t)])
    with mock.patch.object(
        treasury, "_request", side_effect=_treasury_stub(csv_text)
    ):
        runs = forwards_implied_baseline(["2025-01-10"], config=_CONFIG)

    run = runs[0]
    # Hand-computed from the front-of-curve formula (module docstring):
    # ~s*h and tenor-independent, far inside the 5bp neutral band.
    assert run.implied_changes_bp == pytest.approx(
        {"2Y": 0.792149, "5Y": 0.793065, "10Y": 0.793360, "30Y": 0.793554},
        rel=1e-6,
    )
    calls = {c.tenor: c for c in run.direction_calls}
    assert all(c.direction == "neutral" for c in calls.values())
    assert all(c.magnitude_bucket == "<10bp" for c in calls.values())
    # Shape deltas are sub-bp (+0.0013, +0.0005, +0.0003bp) -> unchanged.
    assert all(c.shape == "unchanged" for c in run.shape_calls)


@pytest.mark.unit
def test_forwards_inverted_curve_implies_negative_long_end(_tmp_cache):
    # y(t) = 5.0 - 0.1*t percent: a -10bp/year inversion.
    csv_text = _curve_csv([("01/10/2025", lambda t: 5.0 - 0.1 * t)])
    with mock.patch.object(
        treasury, "_request", side_effect=_treasury_stub(csv_text)
    ):
        runs = forwards_implied_baseline(["2025-01-10"], config=_CONFIG)

    run = runs[0]
    # Negative at every tenor, with the long-end implication most negative
    # (mirrors the upward-curve case): 30Y < 10Y < 5Y < 2Y < 0.
    assert run.implied_changes_bp == pytest.approx(
        {"2Y": -0.792149, "5Y": -0.793065, "10Y": -0.793360,
         "30Y": -0.793554},
        rel=1e-6,
    )
    calls = {c.tenor: c for c in run.direction_calls}
    # Sub-bp implied moves are inside the 5bp neutral band -> all neutral.
    assert all(c.direction == "neutral" for c in calls.values())
    assert all(c.shape == "unchanged" for c in run.shape_calls)


@pytest.mark.unit
def test_forwards_threshold_edge_cases(_tmp_cache):
    # Slopes bracketing the 5bp neutral threshold for the 2Y implied change:
    # +4.989669bp -> neutral; +5.147934bp -> up (exactly-at-or-above is
    # directional, mirroring runner._classify_direction semantics).
    csv_text = _curve_csv([
        ("01/09/2025", lambda t: 4.0 + 0.63 * t),
        ("01/10/2025", lambda t: 4.0 + 0.65 * t),
    ])
    with mock.patch.object(
        treasury, "_request", side_effect=_treasury_stub(csv_text)
    ):
        runs = forwards_implied_baseline(["2025-01-09", "2025-01-10"],
                                         config=_CONFIG)

    assert runs[0].implied_changes_bp["2Y"] == pytest.approx(4.989669, rel=1e-6)
    assert {c.tenor: c for c in runs[0].direction_calls}["2Y"].direction == "neutral"
    assert runs[1].implied_changes_bp["2Y"] == pytest.approx(5.147934, rel=1e-6)
    assert {c.tenor: c for c in runs[1].direction_calls}["2Y"].direction == "up"


@pytest.mark.unit
def test_forwards_uses_latest_curve_on_or_before_test_date(_tmp_cache):
    # 01/03/2025 is a Friday; the Saturday test date must snap back to it and
    # must NOT see the (steep) Monday 01/06 curve.
    csv_text = _curve_csv([
        ("01/06/2025", lambda t: 2.0 + 0.1 * t),   # most recent first in feed
        ("01/03/2025", lambda t: 4.00),
    ])
    with mock.patch.object(
        treasury, "_request", side_effect=_treasury_stub(csv_text)
    ):
        runs = forwards_implied_baseline(["2025-01-04"], config=_CONFIG)

    assert runs[0].implied_changes_bp["10Y"] == pytest.approx(0.0, abs=1e-9)
    assert all(c.direction == "neutral" for c in runs[0].direction_calls)


@pytest.mark.unit
def test_forwards_raises_without_curve_on_or_before_test_date(_tmp_cache):
    csv_text = _curve_csv([("01/10/2025", lambda t: 4.00)])
    with mock.patch.object(
        treasury, "_request", side_effect=_treasury_stub(csv_text)
    ), pytest.raises(ValueError, match="no par curve observation"):
        forwards_implied_baseline(["2025-01-08"], config=_CONFIG)


@pytest.mark.unit
def test_forwards_multiple_dates_in_order(_tmp_cache):
    csv_text = _curve_csv([
        ("01/10/2025", lambda t: 4.00),
        ("01/09/2025", lambda t: 2.0 + 0.1 * t),
    ])
    with mock.patch.object(
        treasury, "_request", side_effect=_treasury_stub(csv_text)
    ):
        runs = forwards_implied_baseline(["2025-01-09", "2025-01-10"],
                                         config=_CONFIG)
    assert [r.test_date for r in runs] == ["2025-01-09", "2025-01-10"]
    assert runs[0].implied_changes_bp["10Y"] == pytest.approx(0.793360, rel=1e-6)
    assert runs[1].implied_changes_bp["10Y"] == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# with_actuals: re-skin baseline predictions as scorer-ready BacktestRuns
# ---------------------------------------------------------------------------


def _actual_run(test_date: str, direction: str, shape: str) -> BacktestRun:
    return BacktestRun(
        test_date=test_date,
        direction_calls=[],
        shape_calls=[],
        actual_direction=dict.fromkeys(_CONFIG["fi_tenor_series"], direction),
        actual_shape=dict.fromkeys(_CONFIG["fi_spread_definitions"], shape),
        actual_yield_changes_bp=dict.fromkeys(_CONFIG["fi_tenor_series"], 0.0),
        horizon_end_date="2025-02-10",
    )


@pytest.mark.unit
def test_with_actuals_makes_baseline_scorable_by_score_backtest():
    baselines = no_change_baseline(["2025-01-10"], config=_CONFIG)
    actuals = [_actual_run("2025-01-10", "neutral", "unchanged")]

    runs = with_actuals(baselines, actuals)

    assert len(runs) == 1
    assert isinstance(runs[0], BacktestRun)
    assert runs[0].direction_calls == baselines[0].direction_calls
    assert runs[0].actual_direction == actuals[0].actual_direction
    sc = score_backtest(runs)
    assert sc.n_runs == 1
    assert sc.n_direction_calls == 4
    assert sc.n_direction_hits == 4   # neutral vs neutral hits everywhere
    assert sc.n_shape_calls == 3
    assert sc.n_shape_hits == 3
    assert sc.n_magnitude_calls == 4
    assert sc.n_magnitude_hits == 4   # 0bp realized -> "<10bp" bucket hit


@pytest.mark.unit
def test_with_actuals_scores_baseline_misses():
    baselines = no_change_baseline(["2025-01-10"], config=_CONFIG)
    actuals = [_actual_run("2025-01-10", "up", "steepen")]

    sc = score_backtest(with_actuals(baselines, actuals))
    assert sc.n_direction_hits == 0
    assert sc.n_shape_hits == 0


@pytest.mark.unit
def test_with_actuals_raises_when_actuals_missing_a_test_date():
    baselines = no_change_baseline(["2025-01-10"], config=_CONFIG)
    with pytest.raises(KeyError):
        with_actuals(baselines, [])
