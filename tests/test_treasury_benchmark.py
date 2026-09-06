"""Unit tests for Treasury curve benchmark calculation."""

from unittest.mock import patch

import pytest

from fixedincomeagent.dataflows.fred import FredNotConfiguredError
from fixedincomeagent.dataflows.treasury_benchmark import (
    DEFAULT_FI_TENOR_SERIES,
    calculate_treasury_curve_benchmark,
    evaluate_directional_hit,
    parse_direction_calls,
)

# ---------------------------------------------------------------------------
# Helpers & Fixtures
# ---------------------------------------------------------------------------

SAMPLE_FI_DECISION_MD = """
## Direction Calls

**2Y**: up (<10bp) [confidence: 80%]
Rationale: Front-end easing expectations will moderate.

**5Y**: down (10-25bp) [confidence: 75%]
Rationale: Belly yields will rally on flight to quality.

**10Y**: neutral (<10bp) [confidence: 60%]
Rationale: Balanced growth and inflation dynamics.

**30Y**: up (25bp+) [confidence: 70%]
Rationale: Term premium expansion and supply concessions.

## Shape Calls

**2s10s**: steepen [confidence: 80%]
Rationale: Bull steepening pressure.
"""


def _make_mock_observations(start_yields: dict[str, float], end_yields: dict[str, float]):
    """Generate mock FRED observations for 2Y, 5Y, 10Y, 30Y across 6 dates."""
    dates = [
        "2026-09-01",  # Day 0 (trade date)
        "2026-09-02",  # Day 1
        "2026-09-03",  # Day 2
        "2026-09-04",  # Day 3
        "2026-09-07",  # Holiday (missing/dot)
        "2026-09-08",  # Day 4
        "2026-09-09",  # Day 5 (resolution date for holding_days=5)
    ]

    def mock_request(path: str, params: dict):
        series_id = params.get("series_id")
        # Reverse lookup series_id -> tenor
        tenor = None
        for t, s in DEFAULT_FI_TENOR_SERIES.items():
            if s == series_id:
                tenor = t
                break

        if tenor is None:
            return {"observations": []}

        y_start = start_yields[tenor]
        y_end = end_yields[tenor]

        # Interpolate across dates
        obs = [
            {"date": dates[0], "value": f"{y_start:.2f}"},
            {"date": dates[1], "value": f"{y_start + 0.01:.2f}"},
            {"date": dates[2], "value": f"{y_start + 0.02:.2f}"},
            {"date": dates[3], "value": f"{y_start + 0.03:.2f}"},
            {"date": dates[4], "value": "."},  # holiday
            {"date": dates[5], "value": f"{y_end - 0.01:.2f}"},
            {"date": dates[6], "value": f"{y_end:.2f}"},
        ]
        return {"observations": obs}

    return mock_request


# ---------------------------------------------------------------------------
# Test parse_direction_calls
# ---------------------------------------------------------------------------

def test_parse_direction_calls_from_markdown():
    calls = parse_direction_calls(SAMPLE_FI_DECISION_MD)
    assert calls == {
        "2Y": "up",
        "5Y": "down",
        "10Y": "neutral",
        "30Y": "up",
    }


def test_parse_direction_calls_from_dict():
    raw_dict = {"2Y": "UP", "5Y": "lower", "10Y": "FLAT", "30Y": "higher"}
    calls = parse_direction_calls(raw_dict)
    assert calls == {
        "2Y": "up",
        "5Y": "down",
        "10Y": "neutral",
        "30Y": "up",
    }


def test_parse_direction_calls_empty():
    assert parse_direction_calls("") == {}
    assert parse_direction_calls(None) == {}
    assert parse_direction_calls("Some unrelated equity report") == {}


# ---------------------------------------------------------------------------
# Test evaluate_directional_hit
# ---------------------------------------------------------------------------

def test_evaluate_directional_hit():
    threshold = 5.0  # bp
    # Up calls
    assert evaluate_directional_hit("up", 10.0, threshold) is True
    assert evaluate_directional_hit("up", 5.5, threshold) is True
    assert evaluate_directional_hit("up", 2.0, threshold) is False
    assert evaluate_directional_hit("up", -10.0, threshold) is False

    # Down calls
    assert evaluate_directional_hit("down", -12.0, threshold) is True
    assert evaluate_directional_hit("down", -5.5, threshold) is True
    assert evaluate_directional_hit("down", -2.0, threshold) is False
    assert evaluate_directional_hit("down", 10.0, threshold) is False

    # Neutral calls
    assert evaluate_directional_hit("neutral", 0.0, threshold) is True
    assert evaluate_directional_hit("neutral", 3.0, threshold) is True
    assert evaluate_directional_hit("neutral", -4.0, threshold) is True
    assert evaluate_directional_hit("neutral", 6.0, threshold) is False
    assert evaluate_directional_hit("neutral", -7.0, threshold) is False


# ---------------------------------------------------------------------------
# Test calculate_treasury_curve_benchmark
# ---------------------------------------------------------------------------

def test_calculate_treasury_curve_benchmark_success():
    # 2Y: 4.00 -> 4.15 (+15bp) -> call was 'up' -> Hit
    # 5Y: 4.10 -> 4.02 (-8bp)  -> call was 'down' -> Hit
    # 10Y: 4.20 -> 4.23 (+3bp) -> call was 'neutral' -> Hit
    # 30Y: 4.40 -> 4.38 (-2bp) -> call was 'up' -> Miss (moved down)
    start_yields = {"2Y": 4.00, "5Y": 4.10, "10Y": 4.20, "30Y": 4.40}
    end_yields = {"2Y": 4.15, "5Y": 4.02, "10Y": 4.23, "30Y": 4.38}

    mock_req = _make_mock_observations(start_yields, end_yields)

    with patch("fixedincomeagent.dataflows.treasury_benchmark._request", side_effect=mock_req):
        res = calculate_treasury_curve_benchmark(
            trade_date="2026-09-01",
            holding_days=5,
            decisions=SAMPLE_FI_DECISION_MD,
            neutral_threshold_bp=5.0,
        )

    assert res is not None
    assert res["trade_date"] == "2026-09-01"
    assert res["resolution_date"] == "2026-09-09"
    assert res["holding_days"] == 5

    # Check tenor changes in bp
    # 2Y: (4.15 - 4.00)*100 = +15.0
    # 5Y: (4.02 - 4.10)*100 = -8.0
    # 10Y: (4.23 - 4.20)*100 = +3.0
    # 30Y: (4.38 - 4.40)*100 = -2.0
    assert pytest.approx(res["tenor_changes"]["2Y"]["delta_bp"]) == 15.0
    assert pytest.approx(res["tenor_changes"]["5Y"]["delta_bp"]) == -8.0
    assert pytest.approx(res["tenor_changes"]["10Y"]["delta_bp"]) == 3.0
    assert pytest.approx(res["tenor_changes"]["30Y"]["delta_bp"]) == -2.0

    # Benchmark is average change: (15.0 - 8.0 + 3.0 - 2.0) / 4 = 8.0 / 4 = +2.0 bp
    assert pytest.approx(res["benchmark_bp"]) == 2.0

    # Hits: 2Y (hit), 5Y (hit), 10Y (hit), 30Y (miss) => 3/4
    assert res["hit_rate"] == "hit:3/4"
    assert res["hits"] == {"2Y": True, "5Y": True, "10Y": True, "30Y": False}

    # Strategy capture:
    # 2Y: +1 * 15 = 15
    # 5Y: -1 * -8 = 8
    # 10Y: 0 * 3 = 0
    # 30Y: +1 * -2 = -2
    # sum = 21, mean = 21 / 4 = 5.25 bp
    # alpha = strategy - benchmark = 5.25 - 2.0 = +3.25 bp
    assert pytest.approx(res["strategy_bp"]) == 5.25
    assert pytest.approx(res["alpha_bp"]) == 3.25


def test_calculate_treasury_curve_benchmark_insufficient_history():
    """If holding window has not elapsed, return None so it retries later."""
    obs = {
        "observations": [
            {"date": "2026-09-01", "value": "4.20"},
            {"date": "2026-09-02", "value": "4.22"},
        ]
    }
    with patch("fixedincomeagent.dataflows.treasury_benchmark._request", return_value=obs):
        res = calculate_treasury_curve_benchmark(
            trade_date="2026-09-01",
            holding_days=5,
            decisions=SAMPLE_FI_DECISION_MD,
        )
    assert res is None


def test_calculate_treasury_curve_benchmark_missing_api_key():
    """If FRED is not configured, fail open with None and do not crash."""
    with patch(
        "fixedincomeagent.dataflows.treasury_benchmark._request",
        side_effect=FredNotConfiguredError("FRED_API_KEY unset"),
    ):
        res = calculate_treasury_curve_benchmark(
            trade_date="2026-09-01",
            holding_days=5,
            decisions=SAMPLE_FI_DECISION_MD,
        )
    assert res is None


def test_calculate_treasury_curve_benchmark_handles_no_decisions():
    """Can calculate benchmark yield movement even without decision calls."""
    start_yields = {"2Y": 4.00, "5Y": 4.10, "10Y": 4.20, "30Y": 4.40}
    end_yields = {"2Y": 4.10, "5Y": 4.15, "10Y": 4.20, "30Y": 4.30}

    mock_req = _make_mock_observations(start_yields, end_yields)

    with patch("fixedincomeagent.dataflows.treasury_benchmark._request", side_effect=mock_req):
        res = calculate_treasury_curve_benchmark(
            trade_date="2026-09-01",
            holding_days=5,
            decisions=None,
        )

    assert res is not None
    assert res["hit_rate"] == "n/a"
    assert res["alpha_bp"] == 0.0
    assert pytest.approx(res["benchmark_bp"]) == (10.0 + 5.0 + 0.0 - 10.0) / 4  # 1.25 bp
