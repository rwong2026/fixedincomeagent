"""Shape debate researchers: steepener vs flattener (Task 4.2).

Run after the direction debate; the direction outcome is provided as context
via ShapeDebateState.direction_outcome.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from fixedincomeagent.agents.researchers.flattener_researcher import (
    create_flattener_researcher,
)
from fixedincomeagent.agents.researchers.steepener_researcher import (
    create_steepener_researcher,
)

_FI_REPORTS = {
    "macro_policy_report": "MACRO",
    "curve_technicals_report": "CURVE",
    "fed_speak_report": "FED",
    "macro_calendar_report": "CALENDAR",
}


def _capturing_llm(captured: dict):
    llm = MagicMock()
    llm.invoke.side_effect = lambda prompt: (
        captured.__setitem__("prompt", prompt) or MagicMock(content="my case")
    )
    return llm


def _shape_state(current_response="", count=0, direction_outcome="Yields biased higher", **overrides):
    debate = {
        "history": "",
        "steepener_history": "",
        "flattener_history": "",
        "current_response": current_response,
        "direction_outcome": direction_outcome,
        "judge_decision": "",
        "count": count,
    }
    debate.update(overrides)
    return {**_FI_REPORTS, "shape_debate_state": debate}


# --- steepener ---------------------------------------------------------------


@pytest.mark.unit
def test_steepener_updates_state():
    out = create_steepener_researcher(MagicMock())(
        _shape_state(current_response="Flattener Analyst: belly leads")
    )["shape_debate_state"]
    assert out["count"] == 1
    assert out["current_response"].startswith("Steepener Analyst: ")
    assert "Steepener Analyst:" in out["steepener_history"]
    assert out["flattener_history"] == ""
    assert out["history"].endswith(out["current_response"])
    assert out["direction_outcome"] == "Yields biased higher"


@pytest.mark.unit
def test_steepener_prompt_includes_reports_direction_outcome_and_opponent():
    captured = {}
    create_steepener_researcher(_capturing_llm(captured))(
        _shape_state(current_response="Flattener Analyst: bull flattening")
    )
    prompt = captured["prompt"]
    for report in ("MACRO", "CURVE", "FED", "CALENDAR"):
        assert report in prompt
    assert "Yields biased higher" in prompt
    assert "bull flattening" in prompt


@pytest.mark.unit
def test_steepener_opening_has_no_phantom_opponent():
    captured = {}
    create_steepener_researcher(_capturing_llm(captured))(_shape_state())
    assert "flattener analyst has not spoken yet" in captured["prompt"]


# --- flattener ---------------------------------------------------------------


@pytest.mark.unit
def test_flattener_updates_state():
    out = create_flattener_researcher(MagicMock())(
        _shape_state(
            current_response="Steepener Analyst: term premium rebuild",
            steepener_history="Steepener Analyst: prior",
        )
    )["shape_debate_state"]
    assert out["count"] == 1
    assert out["current_response"].startswith("Flattener Analyst: ")
    assert "Flattener Analyst:" in out["flattener_history"]
    assert out["steepener_history"] == "Steepener Analyst: prior"


@pytest.mark.unit
def test_flattener_prompt_includes_reports_direction_outcome_and_opponent():
    captured = {}
    create_flattener_researcher(_capturing_llm(captured))(
        _shape_state(current_response="Steepener Analyst: supply steepens")
    )
    prompt = captured["prompt"]
    for report in ("MACRO", "CURVE", "FED", "CALENDAR"):
        assert report in prompt
    assert "Yields biased higher" in prompt
    assert "supply steepens" in prompt


@pytest.mark.unit
def test_flattener_opening_has_no_phantom_opponent():
    captured = {}
    create_flattener_researcher(_capturing_llm(captured))(_shape_state())
    assert "steepener analyst has not spoken yet" in captured["prompt"]
