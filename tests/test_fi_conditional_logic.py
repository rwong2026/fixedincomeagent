"""Dual-track FI debate routing (Task 4.4).

`should_continue_direction_debate` alternates Higher/Lower Yields Researchers
and hands off to the Direction Research Manager at the round limit;
`should_continue_shape_debate` does the same for Steepener/Flattener and the
Shape Research Manager. Count semantics mirror the equity debate
(`count >= 2 * max_rounds` ends the debate).
"""
import pytest

from fixedincomeagent.graph.conditional_logic import ConditionalLogic


def _direction_state(current_response, count=0):
    return {
        "direction_debate_state": {
            "current_response": current_response,
            "count": count,
        }
    }


def _shape_state(current_response, count=0):
    return {
        "shape_debate_state": {
            "current_response": current_response,
            "count": count,
        }
    }


@pytest.mark.unit
def test_direction_debate_alternates_speakers():
    logic = ConditionalLogic()
    assert (
        logic.should_continue_direction_debate(
            _direction_state("Higher Yields Analyst: supply flood")
        )
        == "Lower Yields Researcher"
    )
    assert (
        logic.should_continue_direction_debate(
            _direction_state("Lower Yields Analyst: recession")
        )
        == "Higher Yields Researcher"
    )


@pytest.mark.unit
def test_direction_debate_opens_with_higher_yields():
    logic = ConditionalLogic()
    # Empty current_response (debate start) -> Higher Yields opens, like Bull.
    assert (
        logic.should_continue_direction_debate(_direction_state(""))
        == "Higher Yields Researcher"
    )


@pytest.mark.unit
def test_direction_debate_continues_below_limit():
    logic = ConditionalLogic()  # default max_direction_debate_rounds=1 -> limit at 2
    assert (
        logic.should_continue_direction_debate(
            _direction_state("Higher Yields Analyst: x", count=1)
        )
        == "Lower Yields Researcher"
    )


@pytest.mark.unit
def test_direction_debate_routes_to_manager_at_default_limit():
    logic = ConditionalLogic()
    assert (
        logic.should_continue_direction_debate(
            _direction_state("Higher Yields Analyst: x", count=2)
        )
        == "Direction Research Manager"
    )


@pytest.mark.unit
def test_direction_debate_round_limit_from_config():
    logic = ConditionalLogic(max_direction_debate_rounds=3)  # limit at 6 turns
    assert (
        logic.should_continue_direction_debate(
            _direction_state("Higher Yields Analyst: x", count=5)
        )
        == "Lower Yields Researcher"
    )
    assert (
        logic.should_continue_direction_debate(
            _direction_state("Higher Yields Analyst: x", count=6)
        )
        == "Direction Research Manager"
    )


@pytest.mark.unit
def test_shape_debate_alternates_speakers():
    logic = ConditionalLogic()
    assert (
        logic.should_continue_shape_debate(
            _shape_state("Steepener Analyst: term premium rebuild")
        )
        == "Flattener Researcher"
    )
    assert (
        logic.should_continue_shape_debate(
            _shape_state("Flattener Analyst: belly leads")
        )
        == "Steepener Researcher"
    )


@pytest.mark.unit
def test_shape_debate_opens_with_steepener():
    logic = ConditionalLogic()
    assert (
        logic.should_continue_shape_debate(_shape_state(""))
        == "Steepener Researcher"
    )


@pytest.mark.unit
def test_shape_debate_continues_below_limit():
    logic = ConditionalLogic()  # default max_shape_debate_rounds=1 -> limit at 2
    assert (
        logic.should_continue_shape_debate(
            _shape_state("Steepener Analyst: x", count=1)
        )
        == "Flattener Researcher"
    )


@pytest.mark.unit
def test_shape_debate_routes_to_manager_at_default_limit():
    logic = ConditionalLogic()
    assert (
        logic.should_continue_shape_debate(
            _shape_state("Steepener Analyst: x", count=2)
        )
        == "Shape Research Manager"
    )


@pytest.mark.unit
def test_shape_debate_round_limit_from_config():
    logic = ConditionalLogic(max_shape_debate_rounds=2)  # limit at 4 turns
    assert (
        logic.should_continue_shape_debate(
            _shape_state("Steepener Analyst: x", count=3)
        )
        == "Flattener Researcher"
    )
    assert (
        logic.should_continue_shape_debate(
            _shape_state("Steepener Analyst: x", count=4)
        )
        == "Shape Research Manager"
    )
