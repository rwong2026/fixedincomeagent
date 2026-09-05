"""Argument tagging scaffold for credit assignment (Phase 6, Task 6.1).

SCAFFOLDING ONLY — INERT. Nothing in the live graph path calls this module,
and tagged arguments are never injected into debate prompts. It is activated
only after Phase 7's backtest establishes a working baseline; activating an
unvalidated reinforcement signal risks calcifying noise.
"""

from typing import Any, Literal

from pydantic import BaseModel

from .structured import bind_structured

AGENT_NAME = "ArgumentTagger"


class TaggedArgument(BaseModel):
    """A debate argument tagged for credit assignment (scaffolding only)."""

    argument_text: str
    argument_type: Literal[
        "macro_regime", "inflation_component", "policy_expectation",
        "technical_pattern", "positioning", "supply_demand", "other",
    ]
    regime_tags: list[str]  # e.g. ["hiking_cycle", "disinflation"]
    speaker: str  # "higher_yields" or "lower_yields" or "steepener" or "flattener"
    outcome_correct: bool | None = None  # populated after resolution


class _TaggedArgumentList(BaseModel):
    """Wrapper so with_structured_output can return a list of tags."""

    arguments: list[TaggedArgument]


_TAG_PROMPT = (
    "Tag each argument in this rates debate transcript with its type, regime "
    "tags, and speaker (higher_yields, lower_yields, steepener, or flattener).\n\n"
    "Transcript:\n{debate_history}"
)


def tag_debate_arguments(llm: Any, debate_history: str) -> list[TaggedArgument]:
    """Tag individual debate arguments via one structured LLM call.

    Returns an empty list if the provider does not support structured output.
    """
    structured = bind_structured(llm, _TaggedArgumentList, AGENT_NAME)
    if structured is None:
        return []
    result = structured.invoke(_TAG_PROMPT.format(debate_history=debate_history))
    return result.arguments
