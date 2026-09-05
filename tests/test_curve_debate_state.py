from typing import get_type_hints

from fixedincomeagent.agents.utils.agent_states import (
    AgentState,
    DirectionDebateState,
    ShapeDebateState,
)


def test_direction_debate_state_keys():
    expected = {
        "higher_yields_history",
        "lower_yields_history",
        "history",
        "current_response",
        "judge_decision",
        "count",
    }
    assert set(DirectionDebateState.__annotations__) == expected


def test_shape_debate_state_keys():
    expected = {
        "steepener_history",
        "flattener_history",
        "history",
        "current_response",
        "direction_outcome",
        "judge_decision",
        "count",
    }
    assert set(ShapeDebateState.__annotations__) == expected


def test_agent_state_has_fi_report_fields():
    hints = get_type_hints(AgentState, include_extras=True)
    for field in (
        "macro_policy_report",
        "curve_technicals_report",
        "fed_speak_report",
        "macro_calendar_report",
    ):
        assert field in hints
        assert hints[field].__metadata__  # Annotated with description


def test_agent_state_has_fi_debate_fields():
    hints = get_type_hints(AgentState, include_extras=True)
    assert hints["direction_debate_state"].__args__[0] is DirectionDebateState
    assert hints["shape_debate_state"].__args__[0] is ShapeDebateState
