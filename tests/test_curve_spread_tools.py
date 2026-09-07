"""Tests for the pre-computed curve spreads tool (Issue 1 fix).

Verifies that butterfly and 2-leg spreads are computed in Python, not
delegated to the LLM. Uses a fake par-yield markdown table as input.
"""
from unittest.mock import patch

import pytest

# The function under test — will be created in the next step.
from fixedincomeagent.agents.utils.curve_spread_tools import get_curve_spreads


# Simulated markdown output from get_treasury_par_yields, with a known
# latest curve row: 2 Yr=4.37, 5 Yr=4.54, 10 Yr=4.78, 30 Yr=5.24.
FAKE_PAR_YIELD_REPORT = (
    "## Treasury Par Yield Curve (Daily CMT Rates)\n"
    "- Source: home.treasury.gov Daily Treasury Par Yield Curve Rates\n"
    "- Window: 2026-06-07 to 2026-09-04\n"
    "\n**Latest curve (2026-09-04):**\n\n"
    "| Tenor | Yield % |\n| --- | --- |\n"
    "| 1 Mo | 4.32 |\n"
    "| 2 Yr | 4.37 |\n"
    "| 5 Yr | 4.54 |\n"
    "| 10 Yr | 4.78 |\n"
    "| 30 Yr | 5.24 |\n"
)


def _mock_route(method, *args, **kwargs):
    """Intercept route_to_vendor and return fake par yields."""
    if method == "get_treasury_par_yields":
        return FAKE_PAR_YIELD_REPORT
    raise ValueError(f"Unexpected method: {method}")


@pytest.mark.unit
@patch(
    "fixedincomeagent.agents.utils.curve_spread_tools.route_to_vendor",
    side_effect=_mock_route,
)
def test_butterfly_is_minus_7_bp(mock_vendor):
    result = get_curve_spreads.invoke(
        {"curr_date": "2026-09-04", "look_back_days": 90}
    )
    # (4.54 * 2) - (4.37 + 4.78) = 9.08 - 9.15 = -0.07 = -7 bp
    assert "-7" in result
    assert "2s5s10s" in result.lower() or "butterfly" in result.lower()


@pytest.mark.unit
@patch(
    "fixedincomeagent.agents.utils.curve_spread_tools.route_to_vendor",
    side_effect=_mock_route,
)
def test_2s10s_spread_is_41_bp(mock_vendor):
    result = get_curve_spreads.invoke(
        {"curr_date": "2026-09-04", "look_back_days": 90}
    )
    # 4.78 - 4.37 = 0.41 = 41 bp
    assert "41" in result
    assert "2s10s" in result.lower()


@pytest.mark.unit
@patch(
    "fixedincomeagent.agents.utils.curve_spread_tools.route_to_vendor",
    side_effect=_mock_route,
)
def test_5s30s_spread_is_70_bp(mock_vendor):
    result = get_curve_spreads.invoke(
        {"curr_date": "2026-09-04", "look_back_days": 90}
    )
    # 5.24 - 4.54 = 0.70 = 70 bp
    assert "70" in result
    assert "5s30s" in result.lower()


@pytest.mark.unit
@patch(
    "fixedincomeagent.agents.utils.curve_spread_tools.route_to_vendor",
    side_effect=_mock_route,
)
def test_returns_error_when_par_yields_unavailable(mock_vendor):
    mock_vendor.side_effect = lambda method, *a, **kw: "ERROR: network failure"
    result = get_curve_spreads.invoke(
        {"curr_date": "2026-09-04", "look_back_days": 90}
    )
    assert "ERROR" in result or "unavailable" in result.lower()
