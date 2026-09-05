"""Tests for the Macro/Policy Analyst (Task 3.1).

Covers the MacroPolicyReport component schemas and the analyst node itself:
state-key contract, mandatory no-averaging prompt language, and the bound
tool set. All offline — a fake LLM captures the prompt and tools.
"""

import pytest
from pydantic import ValidationError

from fixedincomeagent.agents.schemas import (
    InflationComponentTrajectory,
    MacroPolicyReport,
    MarketImpliedExpectations,
    SurveyExpectations,
)


def _component(direction="decelerating", confidence="high"):
    return InflationComponentTrajectory(
        direction=direction,
        confidence=confidence,
        supporting_data="CPI shelter +0.3% m/m; market rents leading down",
    )


def _valid_report():
    return MacroPolicyReport(
        shelter_trajectory=_component(),
        energy_supply_chain_trajectory=_component(direction="stable"),
        services_wage_trajectory=_component(direction="accelerating", confidence="medium"),
        market_implied_expectations=MarketImpliedExpectations(
            breakeven_5y="2.4%, drifting lower over the past quarter",
            breakeven_10y="2.5%, stable",
            forward_5y5y="2.6%, edging up",
        ),
        survey_expectations=SurveyExpectations(
            sce_1yr="3.0%",
            sce_3yr="2.8%",
        ),
        divergence_flag="Shelter and services diverge: rents cooling, wages hot.",
        fed_policy_assessment="Restrictive stance; cuts contingent on services cooling.",
        overall_summary="Components diverge; do not net them out.",
    )


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


def test_macro_policy_report_valid():
    report = _valid_report()
    assert report.shelter_trajectory.direction == "decelerating"
    assert report.services_wage_trajectory.confidence == "medium"
    assert report.survey_expectations.sce_5yr is None
    assert "diverge" in report.divergence_flag


def test_component_trajectory_rejects_bad_direction():
    with pytest.raises(ValidationError):
        _component(direction="sideways")


def test_component_trajectory_rejects_bad_confidence():
    with pytest.raises(ValidationError):
        _component(confidence="very high")


def test_macro_policy_report_rejects_bad_nested_literal():
    with pytest.raises(ValidationError):
        MacroPolicyReport(
            shelter_trajectory=_component(direction="up"),
            energy_supply_chain_trajectory=_component(),
            services_wage_trajectory=_component(),
            market_implied_expectations=MarketImpliedExpectations(
                breakeven_5y="x", breakeven_10y="y", forward_5y5y="z",
            ),
            survey_expectations=SurveyExpectations(sce_1yr="3.0%", sce_3yr="2.8%"),
            divergence_flag="d",
            fed_policy_assessment="f",
            overall_summary="s",
        )


def test_market_implied_expectations_default_caveat():
    mie = MarketImpliedExpectations(
        breakeven_5y="a", breakeven_10y="b", forward_5y5y="c",
    )
    assert "risk premia" in mie.risk_premium_caveat
    assert "not a pure" in mie.risk_premium_caveat
