"""Tests for the Macro/Policy Analyst (Task 3.1).

Covers the MacroPolicyReport component schemas and the analyst node itself:
state-key contract, mandatory no-averaging prompt language, and the bound
tool set. All offline — a fake LLM captures the prompt and tools.
"""

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import ValidationError

from fixedincomeagent.agents.analysts.macro_policy_analyst import create_macro_policy_analyst
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


# ---------------------------------------------------------------------------
# Analyst node
# ---------------------------------------------------------------------------

EXPECTED_TOOL_NAMES = {
    "get_fred_series",
    "get_alfred_vintage",
    "get_inflation_breakevens",
    "get_inflation_nowcast",
    "get_shelter_rents",
    "get_used_vehicle_index",
    "get_supply_chain_pressure",
    "get_ism_prices_paid",
    "get_consumer_inflation_expectations",
    "get_fomc_calendar",
    "get_fed_speeches",
}

NO_AVERAGING_LANGUAGE = (
    "Do not average these signals into a single inflation call. Identify "
    "which components are diverging and explain the mechanism. If shelter and "
    "services point in different directions, say so explicitly rather than "
    "netting them out. Breakevens reflect market-implied expectations but "
    "also carry liquidity and inflation-risk premia — never present them as "
    "a pure expectations reading."
)


class _FakeLLM:
    """Captures the bound tools and rendered prompt; returns a canned report."""

    def __init__(self, content="macro report body"):
        self.bound_tools = None
        self.seen_prompt = None
        self._content = content

    def bind_tools(self, tools):
        self.bound_tools = list(tools)

        def _respond(prompt_value):
            self.seen_prompt = prompt_value.to_string()
            return AIMessage(content=self._content)

        return _respond


def _state():
    return {
        "trade_date": "2026-01-15",
        "messages": [HumanMessage(content="Run the macro/policy analysis.")],
    }


def test_node_returns_macro_policy_report_state_key():
    llm = _FakeLLM()
    node = create_macro_policy_analyst(llm)
    result = node(_state())
    assert result["macro_policy_report"] == "macro report body"
    assert len(result["messages"]) == 1
    assert result["messages"][0].content == "macro report body"


def test_system_prompt_contains_no_averaging_language():
    llm = _FakeLLM()
    create_macro_policy_analyst(llm)(_state())
    assert NO_AVERAGING_LANGUAGE in llm.seen_prompt


def test_binds_expected_tool_set():
    llm = _FakeLLM()
    create_macro_policy_analyst(llm)(_state())
    assert {tool.name for tool in llm.bound_tools} == EXPECTED_TOOL_NAMES


def test_prompt_directs_component_level_report_structure():
    llm = _FakeLLM()
    create_macro_policy_analyst(llm)(_state())
    prompt = llm.seen_prompt
    for section in (
        "Shelter",
        "Supply-Chain",
        "Services",
        "Market-Implied Expectations",
        "Survey Expectations",
        "Divergence",
        "Fed Policy",
        "Overall Summary",
    ):
        assert section in prompt, f"prompt missing section cue: {section}"
