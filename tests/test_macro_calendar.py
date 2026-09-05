"""Tests for the Macro Calendar Analyst (Task 3.4).

Offline: a fake LLM captures the bound tools and rendered prompt; we assert
the state-key contract, forward-calendar/auction prompt content, and the
shared stop-signal preamble.
"""

from langchain_core.messages import AIMessage, HumanMessage

from fixedincomeagent.agents.analysts.macro_calendar_analyst import (
    create_macro_calendar_analyst,
)

EXPECTED_TOOL_NAMES = {"get_fomc_calendar", "get_fred_series", "get_auction_results"}


class _FakeLLM:
    """Captures the bound tools and rendered prompt; returns a canned report."""

    def __init__(self, content="macro calendar report body"):
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
        "messages": [HumanMessage(content="Run the macro calendar analysis.")],
    }


def test_node_returns_macro_calendar_report_state_key():
    llm = _FakeLLM()
    node = create_macro_calendar_analyst(llm)
    result = node(_state())
    assert result["macro_calendar_report"] == "macro calendar report body"
    assert len(result["messages"]) == 1
    assert result["messages"][0].content == "macro calendar report body"


def test_binds_expected_tool_set():
    llm = _FakeLLM()
    create_macro_calendar_analyst(llm)(_state())
    assert {tool.name for tool in llm.bound_tools} == EXPECTED_TOOL_NAMES


def test_prompt_covers_releases_surprises_and_supply():
    llm = _FakeLLM()
    create_macro_calendar_analyst(llm)(_state())
    prompt = llm.seen_prompt
    for cue in (
        "CPI",
        "NFP",
        "GDP",
        "FOMC",
        "consensus",
        "surprise",
        "auction",
    ):
        assert cue in prompt, f"prompt missing cue: {cue}"


def test_preamble_carries_final_transaction_proposal_stop_signal():
    llm = _FakeLLM()
    create_macro_calendar_analyst(llm)(_state())
    assert "FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**" in llm.seen_prompt


def test_tool_call_response_leaves_report_empty():
    llm = _FakeLLM()

    def _with_tool_calls(prompt_value):
        llm.seen_prompt = prompt_value.to_string()
        return AIMessage(
            content="",
            tool_calls=[{"name": "get_fomc_calendar", "args": {}, "id": "call_1"}],
        )

    llm.bind_tools = lambda tools: _with_tool_calls
    result = create_macro_calendar_analyst(llm)(_state())
    assert result["macro_calendar_report"] == ""
    assert len(result["messages"]) == 1
