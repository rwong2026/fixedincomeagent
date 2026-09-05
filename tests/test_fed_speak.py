"""Tests for the Fed Speak Analyst (Task 3.3).

Offline: a fake LLM captures the bound tools and rendered prompt; we assert
the state-key contract, hawkish/dovish and positioning prompt content, and
the shared stop-signal preamble.
"""

from langchain_core.messages import AIMessage, HumanMessage

from fixedincomeagent.agents.analysts.fed_speak_analyst import (
    create_fed_speak_analyst,
)

EXPECTED_TOOL_NAMES = {"get_fed_speeches", "get_fomc_calendar", "get_cot_data"}


class _FakeLLM:
    """Captures the bound tools and rendered prompt; returns a canned report."""

    def __init__(self, content="fed speak report body"):
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
        "messages": [HumanMessage(content="Run the Fed speak analysis.")],
    }


def test_node_returns_fed_speak_report_state_key():
    llm = _FakeLLM()
    node = create_fed_speak_analyst(llm)
    result = node(_state())
    assert result["fed_speak_report"] == "fed speak report body"
    assert len(result["messages"]) == 1
    assert result["messages"][0].content == "fed speak report body"


def test_binds_expected_tool_set():
    llm = _FakeLLM()
    create_fed_speak_analyst(llm)(_state())
    assert {tool.name for tool in llm.bound_tools} == EXPECTED_TOOL_NAMES


def test_prompt_covers_sentiment_positioning_and_policy_path():
    llm = _FakeLLM()
    create_fed_speak_analyst(llm)(_state())
    prompt = llm.seen_prompt
    for cue in (
        "hawkish",
        "dovish",
        "speaker",
        "COT",
        "positioning",
        "policy path",
    ):
        assert cue in prompt, f"prompt missing cue: {cue}"


def test_preamble_carries_final_transaction_proposal_stop_signal():
    llm = _FakeLLM()
    create_fed_speak_analyst(llm)(_state())
    assert "FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**" in llm.seen_prompt


def test_tool_call_response_leaves_report_empty():
    llm = _FakeLLM()

    def _with_tool_calls(prompt_value):
        llm.seen_prompt = prompt_value.to_string()
        return AIMessage(
            content="",
            tool_calls=[{"name": "get_fed_speeches", "args": {}, "id": "call_1"}],
        )

    llm.bind_tools = lambda tools: _with_tool_calls
    result = create_fed_speak_analyst(llm)(_state())
    assert result["fed_speak_report"] == ""
    assert len(result["messages"]) == 1
