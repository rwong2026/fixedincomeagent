"""Direction and shape research managers: the FI debate judges (Task 4.3).

Parallel structure to the equity research manager, but the direction manager
renders a per-tenor DirectionOutlook and the shape manager a per-spread
ShapeOutlook conditioned on the direction debate's outcome.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from fixedincomeagent.agents.managers.direction_research_manager import (
    create_direction_research_manager,
)
from fixedincomeagent.agents.managers.shape_research_manager import (
    create_shape_research_manager,
)
from fixedincomeagent.agents.schemas import (
    DirectionCall,
    DirectionOutlook,
    ShapeCall,
    ShapeOutlook,
)

_TENORS = ("2Y", "5Y", "10Y", "30Y")
_SPREADS = ("2s10s", "5s30s", "2s5s10s_fly")


def _free_text_llm(captured: dict):
    """LLM without structured-output support, forcing the free-text path."""
    llm = MagicMock()
    llm.with_structured_output.side_effect = NotImplementedError("unsupported")
    llm.invoke.side_effect = lambda prompt: (
        captured.__setitem__("prompt", prompt) or MagicMock(content="judge prose")
    )
    return llm


def _structured_llm(captured: dict, outlook):
    """LLM whose structured binding returns a real outlook instance."""
    structured = MagicMock()
    structured.invoke.side_effect = lambda prompt: (
        captured.__setitem__("prompt", prompt) or outlook
    )
    llm = MagicMock()
    llm.with_structured_output.return_value = structured
    return llm


def _direction_state(**overrides):
    debate = {
        "history": "Higher Yields Analyst: supply flood\nLower Yields Analyst: recession",
        "higher_yields_history": "Higher Yields Analyst: supply flood",
        "lower_yields_history": "Lower Yields Analyst: recession",
        "current_response": "Lower Yields Analyst: recession",
        "judge_decision": "",
        "count": 2,
    }
    debate.update(overrides)
    return {"direction_debate_state": debate}


def _shape_state(**overrides):
    debate = {
        "history": "Steepener Analyst: cuts pull front end down\nFlattener Analyst: term premium fades",
        "steepener_history": "Steepener Analyst: cuts pull front end down",
        "flattener_history": "Flattener Analyst: term premium fades",
        "current_response": "Flattener Analyst: term premium fades",
        "direction_outcome": "DIRECTION OUTCOME MARKER",
        "judge_decision": "",
        "count": 2,
    }
    debate.update(overrides)
    return {"shape_debate_state": debate}


# --- direction research manager --------------------------------------------


@pytest.mark.unit
def test_direction_manager_writes_judge_decision_freetext_fallback():
    out = create_direction_research_manager(_free_text_llm({}))(_direction_state())[
        "direction_debate_state"
    ]
    assert out["judge_decision"] == "judge prose"
    assert out["current_response"] == "judge prose"
    assert out["history"] == _direction_state()["direction_debate_state"]["history"]
    assert out["higher_yields_history"].startswith("Higher Yields Analyst:")
    assert out["lower_yields_history"].startswith("Lower Yields Analyst:")
    assert out["count"] == 2


@pytest.mark.unit
def test_direction_manager_prompt_covers_configured_tenors():
    captured = {}
    create_direction_research_manager(_free_text_llm(captured))(_direction_state())
    for tenor in _TENORS:
        assert tenor in captured["prompt"]
    assert "supply flood" in captured["prompt"]  # debate history included


@pytest.mark.unit
def test_direction_manager_renders_structured_outlook():
    outlook = DirectionOutlook(
        calls=[
            DirectionCall(
                tenor="10Y",
                direction="up",
                magnitude_bucket="10-25bp",
                confidence=0.7,
                rationale="Supply and term premium",
            )
        ],
        summary="Higher-yields case carried the long end.",
    )
    captured = {}
    out = create_direction_research_manager(_structured_llm(captured, outlook))(
        _direction_state()
    )["direction_debate_state"]
    assert "**10Y**: up (10-25bp)" in out["judge_decision"]
    assert "Supply and term premium" in out["judge_decision"]
    assert "Higher-yields case carried" in out["judge_decision"]


# --- shape research manager ------------------------------------------------


@pytest.mark.unit
def test_shape_manager_writes_judge_decision_freetext_fallback():
    state = _shape_state()
    out = create_shape_research_manager(_free_text_llm({}))(state)["shape_debate_state"]
    assert out["judge_decision"] == "judge prose"
    assert out["current_response"] == "judge prose"
    assert out["direction_outcome"] == "DIRECTION OUTCOME MARKER"
    assert out["steepener_history"].startswith("Steepener Analyst:")
    assert out["flattener_history"].startswith("Flattener Analyst:")
    assert out["count"] == 2


@pytest.mark.unit
def test_shape_manager_prompt_covers_spreads_and_direction_outcome():
    captured = {}
    create_shape_research_manager(_free_text_llm(captured))(_shape_state())
    prompt = captured["prompt"]
    for spread in _SPREADS:
        assert spread in prompt
    assert "DIRECTION OUTCOME MARKER" in prompt
    assert "term premium fades" in prompt  # debate history included


@pytest.mark.unit
def test_shape_manager_renders_structured_outlook():
    outlook = ShapeOutlook(
        calls=[
            ShapeCall(
                spread="2s10s",
                shape="steepen",
                confidence=0.65,
                rationale="Front end rallies on cuts",
            )
        ],
        summary="Steepener case won on the policy path.",
    )
    captured = {}
    out = create_shape_research_manager(_structured_llm(captured, outlook))(
        _shape_state()
    )["shape_debate_state"]
    assert "**2s10s**: steepen" in out["judge_decision"]
    assert "Front end rallies on cuts" in out["judge_decision"]
    assert "Steepener case won" in out["judge_decision"]
