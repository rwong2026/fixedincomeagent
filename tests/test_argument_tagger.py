"""Tests for the inert argument-tagging scaffold (Task 6.1).

The tagger is scaffolding only: it must not be wired into any live graph
path, and the Reflector's default behaviour must be unchanged.
"""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from fixedincomeagent.agents.utils.argument_tagger import (
    TaggedArgument,
    _TaggedArgumentList,
    tag_debate_arguments,
)
from fixedincomeagent.graph.reflection import Reflector


def _valid_kwargs(**overrides):
    kwargs = {
        "argument_text": "Disinflation momentum favours lower yields.",
        "argument_type": "inflation_component",
        "regime_tags": ["disinflation"],
        "speaker": "lower_yields",
    }
    kwargs.update(overrides)
    return kwargs


class TestTaggedArgumentSchema:
    def test_valid_construction(self):
        tag = TaggedArgument(**_valid_kwargs())
        assert tag.argument_type == "inflation_component"
        assert tag.regime_tags == ["disinflation"]
        assert tag.speaker == "lower_yields"
        assert tag.outcome_correct is None  # default until resolution

    def test_all_argument_types_accepted(self):
        for at in (
            "macro_regime", "inflation_component", "policy_expectation",
            "technical_pattern", "positioning", "supply_demand", "other",
        ):
            assert TaggedArgument(**_valid_kwargs(argument_type=at)).argument_type == at

    def test_bad_argument_type_rejected(self):
        with pytest.raises(ValidationError):
            TaggedArgument(**_valid_kwargs(argument_type="vibes"))

    def test_outcome_correct_optional_bool(self):
        assert TaggedArgument(**_valid_kwargs(outcome_correct=True)).outcome_correct is True


class TestTagDebateArguments:
    def _stub_llm(self, arguments):
        """LLM stub whose structured binding returns a fixed wrapper."""
        structured = MagicMock()
        structured.invoke.return_value = _TaggedArgumentList(arguments=arguments)
        llm = MagicMock()
        llm.with_structured_output.return_value = structured
        return llm, structured

    def test_returns_parsed_list(self):
        args = [
            TaggedArgument(**_valid_kwargs()),
            TaggedArgument(**_valid_kwargs(
                argument_text="Curve supply pressure steepens the long end.",
                argument_type="supply_demand",
                regime_tags=["heavy_issuance"],
                speaker="steepener",
            )),
        ]
        llm, structured = self._stub_llm(args)
        result = tag_debate_arguments(llm, "debate transcript")
        assert result == args
        structured.invoke.assert_called_once()
        # Debate history must reach the LLM prompt.
        prompt = structured.invoke.call_args[0][0]
        assert "debate transcript" in prompt

    def test_empty_list(self):
        llm, _ = self._stub_llm([])
        assert tag_debate_arguments(llm, "nothing tagged") == []


class TestReflectorInertness:
    def test_default_path_does_not_touch_tagger(self):
        """reflect_on_final_decision never invokes structured tagging."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "Directionally correct."
        reflector = Reflector(mock_llm)
        result = reflector.reflect_on_final_decision(
            final_decision="Hold.", raw_return=0.01, alpha_return=0.005
        )
        assert result == "Directionally correct."
        mock_llm.with_structured_output.assert_not_called()

    def test_opt_in_uses_tagger(self):
        mock_llm = MagicMock()
        reflector = Reflector(mock_llm)
        expected = [TaggedArgument(**_valid_kwargs())]
        with patch(
            "fixedincomeagent.graph.reflection.tag_debate_arguments",
            return_value=expected,
        ) as mock_tag:
            result = reflector.tag_debate_arguments("debate transcript")
        assert result == expected
        mock_tag.assert_called_once_with(mock_llm, "debate transcript")
