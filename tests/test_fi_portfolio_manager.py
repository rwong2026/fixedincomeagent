"""Fixed-Income Portfolio Manager (Task 5.3) and the completed FI graph wiring.

The FI PM is the terminal synthesis node: it reviews the consistency-checked
FI trader plan (rendered DirectionCall[]/ShapeCall[] markdown, possibly
annotated with CONSISTENCY WARNINGs by the risk checker), confirms or adjusts
each call with adjustments noted, and writes the final rendered TraderDecision
under ``final_trade_decision`` — the same key the equity PM writes — so
``propagate()``'s logging/memory/signal path closes over FI runs unchanged.

Graph: FI Trader -> FI Consistency Check -> FI Portfolio Manager -> END.

Offline: stub LLMs only (no network, no tool calls).
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END

from fixedincomeagent.agents.managers.fi_portfolio_manager import (
    create_fi_portfolio_manager,
)
from fixedincomeagent.agents.schemas import DirectionCall, ShapeCall, TraderDecision
from fixedincomeagent.agents.utils.memory import TradingMemoryLog
from fixedincomeagent.graph.conditional_logic import ConditionalLogic
from fixedincomeagent.graph.propagation import Propagator
from fixedincomeagent.graph.setup import GraphSetup
from fixedincomeagent.graph.signal_processing import SignalProcessor
from fixedincomeagent.graph.trading_graph import TradingAgentsGraph

FI_KEYS = ["macro_policy", "curve_technicals", "fed_speak", "macro_calendar"]


class _StubLLM(RunnableLambda):
    """Offline LLM: fixed AIMessage for every prompt, no structured output."""

    def __init__(self, content="stub response"):
        super().__init__(lambda _prompt: AIMessage(content=content))

    def bind_tools(self, tools, **kwargs):
        return self

    def with_structured_output(self, schema, **kwargs):
        raise AttributeError("stub: structured output unsupported")


def _free_text_llm(captured: dict):
    """LLM without structured-output support, forcing the free-text path."""
    llm = MagicMock()
    llm.with_structured_output.side_effect = NotImplementedError("unsupported")
    llm.invoke.side_effect = lambda prompt: (
        captured.__setitem__("prompt", prompt) or MagicMock(content="pm prose")
    )
    return llm


def _structured_llm(captured: dict, decision):
    structured = MagicMock()
    structured.invoke.side_effect = lambda prompt: (
        captured.__setitem__("prompt", prompt) or decision
    )
    llm = MagicMock()
    llm.with_structured_output.return_value = structured
    return llm


def _state(**overrides):
    state = {
        "direction_debate_state": {"judge_decision": "DIRECTION OUTLOOK MARKER"},
        "shape_debate_state": {"judge_decision": "SHAPE OUTLOOK MARKER"},
        "trader_investment_plan": (
            "ANNOTATED PLAN MARKER\n\n"
            "CONSISTENCY WARNING: 2Y leads 10Y but the 2s10s call is 'steepen'."
        ),
    }
    state.update(overrides)
    return state


def _decision():
    return TraderDecision(
        direction_calls=[
            DirectionCall(
                tenor="10Y",
                direction="up",
                magnitude_bucket="10-25bp",
                confidence=0.6,
                rationale="confirmed; adjusted 2Y instead",
            )
        ],
        shape_calls=[
            ShapeCall(
                spread="2s10s",
                shape="flatten",
                confidence=0.55,
                rationale="adjusted from steepen per consistency warning",
            )
        ],
    )


@pytest.mark.unit
def test_fi_pm_writes_final_trade_decision_freetext_fallback():
    out = create_fi_portfolio_manager(_free_text_llm({}))(_state())
    assert out["final_trade_decision"] == "pm prose"
    assert out["sender"] == "FI Portfolio Manager"
    assert out["messages"][0].content == "pm prose"


@pytest.mark.unit
def test_fi_pm_prompt_includes_annotated_plan_warnings_and_outlooks():
    captured = {}
    create_fi_portfolio_manager(_free_text_llm(captured))(_state())
    prompt = captured["prompt"]
    assert "ANNOTATED PLAN MARKER" in prompt
    assert "CONSISTENCY WARNING" in prompt
    assert "DIRECTION OUTLOOK MARKER" in prompt
    assert "SHAPE OUTLOOK MARKER" in prompt


@pytest.mark.unit
def test_fi_pm_renders_structured_decision():
    out = create_fi_portfolio_manager(_structured_llm({}, _decision()))(_state())
    decision = out["final_trade_decision"]
    assert "Direction Calls" in decision
    assert "Shape Calls" in decision
    assert "**10Y**: up (10-25bp)" in decision
    assert "**2s10s**: flatten" in decision
    assert "adjusted from steepen per consistency warning" in decision


# ---------------------------------------------------------------------------
# Graph wiring: FI Trader -> FI Consistency Check -> FI Portfolio Manager -> END
# ---------------------------------------------------------------------------


def _graph(selected, llm=None):
    llm = llm or MagicMock()
    setup = GraphSetup(
        llm,
        llm,
        TradingAgentsGraph._create_tool_nodes(None),
        ConditionalLogic(max_direction_debate_rounds=1, max_shape_debate_rounds=1),
    )
    return setup.setup_graph(selected).compile().get_graph()


@pytest.mark.unit
def test_fi_terminal_chain_edges():
    edges = {(e.source, e.target) for e in _graph(FI_KEYS).edges}
    assert ("Shape Research Manager", "FI Trader") in edges
    assert ("FI Trader", "FI Consistency Check") in edges
    assert ("FI Consistency Check", "FI Portfolio Manager") in edges
    assert ("FI Portfolio Manager", END) in edges
    assert ("FI Trader", END) not in edges


@pytest.mark.unit
def test_equity_mode_unaffected():
    graph = _graph(["market", "social", "news", "fundamentals"])
    edges = {(e.source, e.target) for e in graph.edges}
    assert ("Portfolio Manager", END) in edges
    assert {"FI Trader", "FI Consistency Check", "FI Portfolio Manager"}.isdisjoint(
        graph.nodes
    )


@pytest.mark.unit
def test_propagate_completes_in_fi_mode_without_keyerror(tmp_path):
    """Phase 5 carryover: _log_state reads final_trade_decision; the FI PM now
    writes it, so a full propagate() in FI mode no longer KeyErrors."""
    llm = _StubLLM()
    g = object.__new__(TradingAgentsGraph)
    g.debug = False
    g.callbacks = []
    g.config = {
        "results_dir": str(tmp_path),
        "data_cache_dir": str(tmp_path),
        "max_debate_rounds": 1,
        "max_risk_discuss_rounds": 1,
        "max_direction_debate_rounds": 1,
        "max_shape_debate_rounds": 1,
    }
    g.selected_analysts = tuple(FI_KEYS)
    g.memory_log = TradingMemoryLog({"memory_log_path": str(tmp_path / "mem.md")})
    g.log_states_dict = {}
    g.ticker = None
    g.curr_state = None
    g._checkpointer_ctx = None
    g._resuming = False
    g.tool_nodes = TradingAgentsGraph._create_tool_nodes(None)
    g.conditional_logic = ConditionalLogic(
        max_direction_debate_rounds=1, max_shape_debate_rounds=1
    )
    g.propagator = Propagator()
    g.signal_processor = SignalProcessor()
    g.reflector = None  # untouched: no pending memory entries in a fresh tmp log
    g.resolve_instrument_context = lambda *args, **kwargs: ""
    g.workflow = GraphSetup(
        llm, llm, g.tool_nodes, g.conditional_logic
    ).setup_graph(FI_KEYS)
    g.graph = g.workflow.compile()

    final_state, _signal = TradingAgentsGraph.propagate(g, "UST", "2026-09-04")

    assert final_state["final_trade_decision"] == "stub response"
    assert final_state["trader_investment_plan"] == "stub response"
    logged = g.log_states_dict["2026-09-04"]
    assert logged["final_trade_decision"] == "stub response"
    assert logged["investment_plan"] == ""
