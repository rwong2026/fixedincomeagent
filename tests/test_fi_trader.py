"""Fixed-Income Trader (Task 5.1): emits DirectionCall[]/ShapeCall[].

Consumes the direction and shape research managers' judge decisions plus the
curve technicals report, and produces the desk's per-tenor direction calls and
per-spread shape calls, rendered to markdown under the equity trader's state
key (``trader_investment_plan``) so downstream plumbing works unchanged.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from fixedincomeagent.agents.schemas import DirectionCall, ShapeCall, TraderDecision
from fixedincomeagent.agents.trader.fi_trader import create_fi_trader

_TENORS = ("2Y", "5Y", "10Y", "30Y")
_SPREADS = ("2s10s", "5s30s", "2s5s10s_fly")


def _free_text_llm(captured: dict):
    """LLM without structured-output support, forcing the free-text path."""
    llm = MagicMock()
    llm.with_structured_output.side_effect = NotImplementedError("unsupported")
    llm.invoke.side_effect = lambda prompt: (
        captured.__setitem__("prompt", prompt) or MagicMock(content="trader prose")
    )
    return llm


def _structured_llm(captured: dict, decision):
    """LLM whose structured binding returns a real TraderDecision instance."""
    structured = MagicMock()
    structured.invoke.side_effect = lambda prompt: (
        captured.__setitem__("prompt", prompt) or decision
    )
    llm = MagicMock()
    llm.with_structured_output.return_value = structured
    return llm


def _state(**overrides):
    state = {
        "direction_debate_state": {"judge_decision": "DIRECTION OUTLOOK MARKER"},
        "shape_debate_state": {"judge_decision": "SHAPE OUTLOOK MARKER"},
        "curve_technicals_report": "TECHNICALS MARKER",
    }
    state.update(overrides)
    return state


def _full_coverage_decision():
    return TraderDecision(
        direction_calls=[
            DirectionCall(
                tenor=tenor,
                direction="up",
                magnitude_bucket="10-25bp",
                confidence=0.6,
                rationale=f"{tenor} rationale",
            )
            for tenor in _TENORS
        ],
        shape_calls=[
            ShapeCall(
                spread=spread,
                shape="steepen",
                confidence=0.55,
                rationale=f"{spread} rationale",
            )
            for spread in _SPREADS
        ],
    )


@pytest.mark.unit
def test_fi_trader_writes_trader_investment_plan_freetext_fallback():
    out = create_fi_trader(_free_text_llm({}))(_state())
    assert out["trader_investment_plan"] == "trader prose"
    assert out["sender"] == "FI Trader"
    assert out["messages"][0].content == "trader prose"


@pytest.mark.unit
def test_fi_trader_prompt_includes_manager_outputs_and_technicals():
    captured = {}
    create_fi_trader(_free_text_llm(captured))(_state())
    prompt = captured["prompt"]
    assert "DIRECTION OUTLOOK MARKER" in prompt
    assert "SHAPE OUTLOOK MARKER" in prompt
    assert "TECHNICALS MARKER" in prompt


@pytest.mark.unit
def test_fi_trader_prompt_lists_full_tenor_and_spread_coverage():
    captured = {}
    create_fi_trader(_free_text_llm(captured))(_state())
    prompt = captured["prompt"]
    for tenor in _TENORS:
        assert tenor in prompt
    for spread in _SPREADS:
        assert spread in prompt


@pytest.mark.unit
def test_fi_trader_prompt_omits_technicals_section_when_report_empty():
    captured = {}
    create_fi_trader(_free_text_llm(captured))(_state(curve_technicals_report=""))
    assert "TECHNICALS MARKER" not in captured["prompt"]
    assert "Curve Technicals Report" not in captured["prompt"]


@pytest.mark.unit
def test_fi_trader_renders_structured_decision_with_full_coverage():
    captured = {}
    out = create_fi_trader(_structured_llm(captured, _full_coverage_decision()))(
        _state()
    )
    plan = out["trader_investment_plan"]
    assert "Direction Calls" in plan
    assert "Shape Calls" in plan
    for tenor in _TENORS:
        assert f"**{tenor}**: up (10-25bp)" in plan
        assert f"{tenor} rationale" in plan
    for spread in _SPREADS:
        assert f"**{spread}**: steepen" in plan
        assert f"{spread} rationale" in plan
