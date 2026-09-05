"""Tests for the Curve Technicals Analyst (Task 3.2).

Offline: a fake LLM captures the bound tools and rendered prompt; we assert
the state-key contract, the configured spread/tenor set in the prompt, and
the shared stop-signal preamble.
"""

from langchain_core.messages import AIMessage, HumanMessage

from fixedincomeagent.agents.analysts.curve_technicals_analyst import (
    create_curve_technicals_analyst,
)

EXPECTED_TOOL_NAMES = {"get_fred_series", "get_treasury_par_yields"}


class _FakeLLM:
    """Captures the bound tools and rendered prompt; returns a canned report."""

    def __init__(self, content="curve technicals report body"):
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
        "messages": [HumanMessage(content="Run the curve technicals analysis.")],
    }


def test_node_returns_curve_technicals_report_state_key():
    llm = _FakeLLM()
    node = create_curve_technicals_analyst(llm)
    result = node(_state())
    assert result["curve_technicals_report"] == "curve technicals report body"
    assert len(result["messages"]) == 1
    assert result["messages"][0].content == "curve technicals report body"


def test_binds_expected_tool_set():
    llm = _FakeLLM()
    create_curve_technicals_analyst(llm)(_state())
    assert {tool.name for tool in llm.bound_tools} == EXPECTED_TOOL_NAMES


def test_prompt_references_configured_spreads_and_technicals():
    llm = _FakeLLM()
    create_curve_technicals_analyst(llm)(_state())
    prompt = llm.seen_prompt.lower()
    for cue in (
        "2s10s",
        "5s30s",
        "butterfly",
        "percentile",
        "steepening",
        "flattening",
        "rate-of-change",
        "recent highs/lows",
    ):
        assert cue in prompt, f"prompt missing cue: {cue}"


def test_preamble_carries_final_transaction_proposal_stop_signal():
    llm = _FakeLLM()
    create_curve_technicals_analyst(llm)(_state())
    assert "FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**" in llm.seen_prompt


def test_tool_call_response_leaves_report_empty():
    llm = _FakeLLM()

    def _with_tool_calls(prompt_value):
        llm.seen_prompt = prompt_value.to_string()
        return AIMessage(
            content="",
            tool_calls=[{"name": "get_fred_series", "args": {}, "id": "call_1"}],
        )

    llm.bind_tools = lambda tools: _with_tool_calls
    result = create_curve_technicals_analyst(llm)(_state())
    assert result["curve_technicals_report"] == ""
    assert len(result["messages"]) == 1
