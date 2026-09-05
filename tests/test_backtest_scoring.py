"""Backtest scoring (Task 7.3): hit rates, calibration, magnitude accuracy.

All synthetic: hand-built BacktestRun lists with exact expected rates. Pure
python, no network, no LLM.
"""
from __future__ import annotations

import pytest

from fixedincomeagent.agents.schemas import DirectionCall, ShapeCall
from fixedincomeagent.backtest.runner import BacktestRun
from fixedincomeagent.backtest.scoring import (
    _bucketize_change,
    render,
    score_backtest,
)


def _dcall(tenor, direction, bucket="<10bp", conf=0.5):
    return DirectionCall(
        tenor=tenor, direction=direction, magnitude_bucket=bucket,
        confidence=conf, rationale="r",
    )


def _scall(spread, shape, conf=0.5):
    return ShapeCall(spread=spread, shape=shape, confidence=conf, rationale="r")


def _run(dcalls=(), scalls=(), actual_dir=None, actual_shape=None,
         changes=None, date="2025-01-10"):
    return BacktestRun(
        test_date=date,
        direction_calls=list(dcalls),
        shape_calls=list(scalls),
        actual_direction=dict(actual_dir or {}),
        actual_shape=dict(actual_shape or {}),
        actual_yield_changes_bp=dict(changes or {}),
        horizon_end_date="2025-02-07",
    )


# ---------------------------------------------------------------------------
# Directional hit rate per tenor
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_direction_hit_rate_per_tenor_exact():
    runs = [
        _run(
            dcalls=[
                _dcall("2Y", "up"), _dcall("10Y", "up"), _dcall("30Y", "down"),
            ],
            actual_dir={"2Y": "up", "10Y": "up", "30Y": "up"},
            changes={"2Y": 5.0, "10Y": 5.0, "30Y": 5.0},
        ),
        _run(
            dcalls=[_dcall("2Y", "up"), _dcall("10Y", "neutral")],
            actual_dir={"2Y": "down", "10Y": "neutral"},
            changes={"2Y": -5.0, "10Y": 1.0},
        ),
    ]
    sc = score_backtest(runs)
    assert sc.n_runs == 2
    assert sc.n_direction_calls == 5
    assert sc.n_direction_hits == 3
    assert sc.per_tenor_calls == {"2Y": 2, "10Y": 2, "30Y": 1}
    assert sc.per_tenor_hit_rate == {"2Y": 0.5, "10Y": 1.0, "30Y": 0.0}


@pytest.mark.unit
def test_neutral_semantics_exact_equality_both_ways():
    runs = [
        _run(
            dcalls=[
                _dcall("2Y", "up"),       # actual neutral -> MISS
                _dcall("5Y", "neutral"),  # actual neutral -> HIT
                _dcall("10Y", "neutral"),  # actual up -> MISS (symmetric)
                _dcall("30Y", "down"),    # actual neutral -> MISS
            ],
            actual_dir={"2Y": "neutral", "5Y": "neutral",
                        "10Y": "up", "30Y": "neutral"},
            changes={"2Y": 1.0, "5Y": 1.0, "10Y": 8.0, "30Y": -1.0},
        ),
    ]
    sc = score_backtest(runs)
    assert sc.n_direction_calls == 4
    assert sc.n_direction_hits == 1
    assert sc.per_tenor_hit_rate == {
        "2Y": 0.0, "5Y": 1.0, "10Y": 0.0, "30Y": 0.0,
    }


# ---------------------------------------------------------------------------
# Curve-shape hit rate per spread
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_shape_hit_rate_per_spread_and_unchanged_semantics():
    runs = [
        _run(
            scalls=[
                _scall("2s10s", "steepen"),      # hit
                _scall("5s30s", "flatten"),      # miss (actual steepen)
                _scall("2s5s10s_fly", "unchanged"),  # hit
            ],
            actual_shape={"2s10s": "steepen", "5s30s": "steepen",
                          "2s5s10s_fly": "unchanged"},
        ),
        _run(
            scalls=[
                _scall("2s10s", "steepen"),     # miss: actual unchanged
                _scall("5s30s", "unchanged"),   # miss: actual flatten (symmetric)
            ],
            actual_shape={"2s10s": "unchanged", "5s30s": "flatten"},
        ),
    ]
    sc = score_backtest(runs)
    assert sc.n_shape_calls == 5
    assert sc.n_shape_hits == 2
    assert sc.per_spread_calls == {"2s10s": 2, "5s30s": 2, "2s5s10s_fly": 1}
    assert sc.per_spread_hit_rate == {
        "2s10s": 0.5, "5s30s": 0.0, "2s5s10s_fly": 1.0,
    }


# ---------------------------------------------------------------------------
# Confidence calibration bins (deciles, direction + shape calls pooled)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_calibration_bins_hand_computed():
    runs = [
        _run(
            dcalls=[
                _dcall("2Y", "up", conf=0.05),    # bin 0, hit
                _dcall("5Y", "up", conf=0.15),    # bin 1, miss
                _dcall("10Y", "up", conf=0.25),   # bin 2, hit
                _dcall("30Y", "up", conf=0.9),    # bin 9, hit
            ],
            scalls=[
                _scall("2s10s", "steepen", conf=1.0),  # bin 9, miss
            ],
            actual_dir={"2Y": "up", "5Y": "down", "10Y": "up", "30Y": "up"},
            actual_shape={"2s10s": "flatten"},
            changes={"2Y": 5.0, "5Y": -5.0, "10Y": 5.0, "30Y": 5.0},
        ),
    ]
    sc = score_backtest(runs)
    bins = sc.calibration_bins
    assert len(bins) == 10
    b0, b1, b2, b9 = bins[0], bins[1], bins[2], bins[9]
    assert (b0.count, b0.mean_confidence, b0.empirical_hit_rate) == (1, 0.05, 1.0)
    assert (b1.count, b1.mean_confidence, b1.empirical_hit_rate) == (1, 0.15, 0.0)
    assert (b2.count, b2.mean_confidence, b2.empirical_hit_rate) == (1, 0.25, 1.0)
    # confidence == 1.0 falls in the top bin; mean of {0.9, 1.0}, 1 hit of 2
    assert b9.count == 2
    assert b9.mean_confidence == pytest.approx(0.95)
    assert b9.empirical_hit_rate == 0.5
    for i in range(3, 9):
        assert (bins[i].count, bins[i].mean_confidence,
                bins[i].empirical_hit_rate) == (0, 0.0, 0.0)


@pytest.mark.unit
def test_calibration_bin_ranges_are_deciles():
    sc = score_backtest([])
    for i, b in enumerate(sc.calibration_bins):
        assert b.lower == pytest.approx(i / 10)
        assert b.upper == pytest.approx((i + 1) / 10)


# ---------------------------------------------------------------------------
# Magnitude accuracy (direction calls only; buckets on |actual bp change|)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_bucketize_change_boundaries():
    assert _bucketize_change(0.0) == "<10bp"
    assert _bucketize_change(9.99) == "<10bp"
    assert _bucketize_change(-9.99) == "<10bp"
    assert _bucketize_change(10.0) == "10-25bp"   # lower bound inclusive
    assert _bucketize_change(-24.99) == "10-25bp"
    assert _bucketize_change(25.0) == "25bp+"     # 25 goes to top bucket
    assert _bucketize_change(-40.0) == "25bp+"


@pytest.mark.unit
def test_magnitude_accuracy_exact():
    runs = [
        _run(
            dcalls=[
                _dcall("2Y", "up", "<10bp"),      # |+5| -> <10bp: hit
                _dcall("10Y", "up", "10-25bp"),   # |+10| -> 10-25bp: hit
                _dcall("30Y", "down", "25bp+"),   # |-30| -> 25bp+: hit
                _dcall("5Y", "up", "<10bp"),      # |+25| -> 25bp+: miss
            ],
            actual_dir={"2Y": "up", "10Y": "up", "30Y": "down", "5Y": "up"},
            changes={"2Y": 5.0, "10Y": 10.0, "30Y": -30.0, "5Y": 25.0},
        ),
    ]
    sc = score_backtest(runs)
    assert sc.n_magnitude_calls == 4
    assert sc.n_magnitude_hits == 3
    assert sc.magnitude_accuracy == 0.75


# ---------------------------------------------------------------------------
# Skips and empty input
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_calls_without_matching_actuals_are_skipped():
    runs = [
        _run(
            dcalls=[_dcall("2Y", "up"), _dcall("10Y", "up")],
            scalls=[_scall("2s10s", "steepen"), _scall("5s30s", "flatten")],
            # 10Y direction, 5s30s shape, and 2Y's change are unscorable.
            actual_dir={"2Y": "up"},
            actual_shape={"2s10s": "steepen"},
            changes={"10Y": 12.0},  # no 2Y change -> magnitude skipped
        ),
    ]
    sc = score_backtest(runs)
    assert sc.n_direction_calls == 1 and sc.n_direction_hits == 1
    assert sc.per_tenor_calls == {"2Y": 1}
    assert sc.n_shape_calls == 1 and sc.n_shape_hits == 1
    assert sc.per_spread_calls == {"2s10s": 1}
    assert sc.n_magnitude_calls == 0
    assert sc.magnitude_accuracy == 0.0
    # Only the two scored calls feed calibration.
    assert sum(b.count for b in sc.calibration_bins) == 2


@pytest.mark.unit
def test_empty_input_returns_zero_scorecard():
    sc = score_backtest([])
    assert sc.n_runs == 0
    assert sc.n_direction_calls == 0 and sc.n_direction_hits == 0
    assert sc.n_shape_calls == 0 and sc.n_shape_hits == 0
    assert sc.per_tenor_hit_rate == {} and sc.per_tenor_calls == {}
    assert sc.per_spread_hit_rate == {} and sc.per_spread_calls == {}
    assert sc.n_magnitude_calls == 0 and sc.n_magnitude_hits == 0
    assert sc.magnitude_accuracy == 0.0  # zero-division defined as 0.0
    assert len(sc.calibration_bins) == 10
    assert all(b.count == 0 and b.empirical_hit_rate == 0.0
               for b in sc.calibration_bins)


# ---------------------------------------------------------------------------
# render: markdown summary
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_render_markdown_summary():
    runs = [
        _run(
            dcalls=[_dcall("10Y", "up", "10-25bp", 0.7)],
            scalls=[_scall("2s10s", "steepen", 0.6)],
            actual_dir={"10Y": "up"},
            actual_shape={"2s10s": "flatten"},
            changes={"10Y": 12.0},
        ),
    ]
    md = render(score_backtest(runs))
    assert isinstance(md, str)
    assert "Direction" in md and "10Y" in md and "100.0%" in md
    assert "Shape" in md and "2s10s" in md and "0.0%" in md
    assert "Calibration" in md and "Magnitude" in md
