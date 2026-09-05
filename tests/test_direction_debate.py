"""Direction debate researchers: higher vs lower yields (Task 4.1).

Parallel structure to bull/bear researchers, but reading the four FI analyst
reports and updating DirectionDebateState fields.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from fixedincomeagent.agents.researchers.higher_yields_researcher import (
    create_higher_yields_researcher,
)
from fixedincomeagent.agents.researchers.lower_yields_researcher import (
    create_lower_yields_researcher,
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


def _direction_state(current_response="", count=0, **overrides):
    debate = {
        "history": "",
        "higher_yields_history": "",
        "lower_yields_history": "",
        "current_response": current_response,
        "judge_decision": "",
        "count": count,
    }
    debate.update(overrides)
    return {**_FI_REPORTS, "direction_debate_state": debate}


# --- higher yields ----------------------------------------------------------


@pytest.mark.unit
def test_higher_yields_updates_state():
    out = create_higher_yields_researcher(MagicMock())(
        _direction_state(current_response="Lower Yields Analyst: cuts are coming")
    )["direction_debate_state"]
    assert out["count"] == 1
    assert out["current_response"].startswith("Higher Yields Analyst: ")
    assert "Higher Yields Analyst:" in out["higher_yields_history"]
    assert out["lower_yields_history"] == ""
    assert out["history"].endswith(out["current_response"])


@pytest.mark.unit
def test_higher_yields_prompt_includes_reports_and_opponent():
    captured = {}
    create_higher_yields_researcher(_capturing_llm(captured))(
        _direction_state(current_response="Lower Yields Analyst: recession")
    )
    prompt = captured["prompt"]
    for report in ("MACRO", "CURVE", "FED", "CALENDAR"):
        assert report in prompt
    assert "recession" in prompt


@pytest.mark.unit
def test_higher_yields_opening_has_no_phantom_opponent():
    captured = {}
    create_higher_yields_researcher(_capturing_llm(captured))(_direction_state())
    assert "lower yields analyst has not spoken yet" in captured["prompt"]


# --- lower yields -----------------------------------------------------------


@pytest.mark.unit
def test_lower_yields_updates_state():
    out = create_lower_yields_researcher(MagicMock())(
        _direction_state(
            current_response="Higher Yields Analyst: inflation is sticky",
            higher_yields_history="Higher Yields Analyst: prior",
        )
    )["direction_debate_state"]
    assert out["count"] == 1
    assert out["current_response"].startswith("Lower Yields Analyst: ")
    assert "Lower Yields Analyst:" in out["lower_yields_history"]
    assert out["higher_yields_history"] == "Higher Yields Analyst: prior"


@pytest.mark.unit
def test_lower_yields_prompt_includes_reports_and_opponent():
    captured = {}
    create_lower_yields_researcher(_capturing_llm(captured))(
        _direction_state(current_response="Higher Yields Analyst: supply flood")
    )
    prompt = captured["prompt"]
    for report in ("MACRO", "CURVE", "FED", "CALENDAR"):
        assert report in prompt
    assert "supply flood" in prompt


@pytest.mark.unit
def test_lower_yields_opening_has_no_phantom_opponent():
    captured = {}
    create_lower_yields_researcher(_capturing_llm(captured))(_direction_state())
    assert "higher yields analyst has not spoken yet" in captured["prompt"]
