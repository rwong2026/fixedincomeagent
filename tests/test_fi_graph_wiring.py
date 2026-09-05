"""Task 4.5: wire the FI dual-track debate (direction -> shape) into the graph.

FI mode activates when every selected analyst is an FI analyst; the graph then
runs analysts -> Higher/Lower Yields debate -> Direction Research Manager ->
Steepener/Flattener debate -> Shape Research Manager -> FI Trader (Task 5.1;
risk / PM follow in Tasks 5.2/5.3).

Offline: structure is inspected via the compiled graph's edge list, and the
full path is invoked with a stub LLM (no network, no tool calls).
"""

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, START

from fixedincomeagent.agents.managers.direction_research_manager import (
    create_direction_research_manager,
)
from fixedincomeagent.graph.conditional_logic import ConditionalLogic
from fixedincomeagent.graph.propagation import Propagator
from fixedincomeagent.graph.setup import (
    DIRECTION_DEBATE_PATH_MAP,
    SHAPE_DEBATE_PATH_MAP,
    GraphSetup,
)
from fixedincomeagent.graph.trading_graph import TradingAgentsGraph

FI_KEYS = ["macro_policy", "curve_technicals", "fed_speak", "macro_calendar"]

DIRECTION_NODES = {
    "Higher Yields Researcher",
    "Lower Yields Researcher",
    "Direction Research Manager",
}
SHAPE_NODES = {
    "Steepener Researcher",
    "Flattener Researcher",
    "Shape Research Manager",
}
EQUITY_ONLY_NODES = {
    "Bull Researcher",
    "Bear Researcher",
    "Research Manager",
    "Trader",
    "Aggressive Analyst",
    "Neutral Analyst",
    "Conservative Analyst",
    "Portfolio Manager",
}


class _StubLLM(RunnableLambda):
    """Offline LLM: answers every prompt with a fixed AIMessage, never calls
    tools, and lacks structured output (managers take the free-text path)."""

    def __init__(self, content="stub response"):
        super().__init__(lambda _prompt: AIMessage(content=content))

    def bind_tools(self, tools, **kwargs):
        return self

    def with_structured_output(self, schema, **kwargs):
        raise AttributeError("stub: structured output unsupported")


def _setup(selected, llm=None):
    llm = llm or MagicMock()
    return GraphSetup(
        llm,
        llm,
        TradingAgentsGraph._create_tool_nodes(None),
        ConditionalLogic(max_direction_debate_rounds=1, max_shape_debate_rounds=1),
    )


def _edges(selected):
    graph = _setup(selected).setup_graph(selected).compile().get_graph()
    return {(e.source, e.target) for e in graph.edges}


def _nodes(selected):
    graph = _setup(selected).setup_graph(selected).compile().get_graph()
    return set(graph.nodes)


@pytest.mark.unit
def test_fi_mode_registers_dual_track_nodes():
    nodes = _nodes(FI_KEYS)
    assert nodes >= DIRECTION_NODES | SHAPE_NODES
    assert EQUITY_ONLY_NODES.isdisjoint(nodes)


@pytest.mark.unit
def test_equity_mode_unchanged():
    nodes = _nodes(["market", "social", "news", "fundamentals"])
    assert "Bull Researcher" in nodes
    assert (DIRECTION_NODES | SHAPE_NODES).isdisjoint(nodes)


@pytest.mark.unit
def test_mixed_selection_stays_on_equity_track():
    assert "Bull Researcher" in _nodes(["macro_policy", "market"])


@pytest.mark.unit
def test_fi_analyst_chain_feeds_direction_debate():
    edges = _edges(FI_KEYS)
    assert (START, "Macro Policy Analyst") in edges
    # Last analyst's clear node opens the direction debate.
    assert ("Msg Clear Macro Calendar", "Higher Yields Researcher") in edges


@pytest.mark.unit
def test_direction_manager_hands_off_to_shape_debate():
    assert ("Direction Research Manager", "Steepener Researcher") in _edges(FI_KEYS)


@pytest.mark.unit
def test_shape_manager_routes_to_fi_trader():
    # Task 5.1 wired the FI Trader; Tasks 5.2/5.3 extend past it (risk, PM).
    edges = _edges(FI_KEYS)
    assert ("Shape Research Manager", "FI Trader") in edges
    # PHASE 5 CUT POINT: ("FI Trader", END) becomes FI Trader -> risk check.
    assert ("FI Trader", END) in edges


@pytest.mark.unit
def test_debate_edges_use_complete_path_maps():
    edges = _edges(FI_KEYS)
    for debater in ("Higher Yields Researcher", "Lower Yields Researcher"):
        for target in DIRECTION_DEBATE_PATH_MAP.values():
            assert (debater, target) in edges
    for debater in ("Steepener Researcher", "Flattener Researcher"):
        for target in SHAPE_DEBATE_PATH_MAP.values():
            assert (debater, target) in edges


@pytest.mark.unit
@pytest.mark.parametrize("response", ["Higher Yields", "Lower", "", "drift"])
def test_direction_router_return_always_routable(response):
    logic = ConditionalLogic(max_direction_debate_rounds=1)
    for count in (0, 99):
        target = logic.should_continue_direction_debate(
            {"direction_debate_state": {"current_response": response, "count": count}}
        )
        assert target in DIRECTION_DEBATE_PATH_MAP


@pytest.mark.unit
@pytest.mark.parametrize("response", ["Steepener", "Flattener", "", "drift"])
def test_shape_router_return_always_routable(response):
    logic = ConditionalLogic(max_shape_debate_rounds=1)
    for count in (0, 99):
        target = logic.should_continue_shape_debate(
            {"shape_debate_state": {"current_response": response, "count": count}}
        )
        assert target in SHAPE_DEBATE_PATH_MAP


@pytest.mark.unit
def test_initial_state_has_both_fi_debate_states():
    state = Propagator().create_initial_state("UST", "2026-09-04")
    direction = state["direction_debate_state"]
    assert direction["count"] == 0
    assert direction["history"] == ""
    assert direction["higher_yields_history"] == ""
    assert direction["lower_yields_history"] == ""
    shape = state["shape_debate_state"]
    assert shape["count"] == 0
    assert shape["history"] == ""
    assert shape["direction_outcome"] == ""


@pytest.mark.unit
def test_direction_manager_seeds_shape_direction_outcome():
    llm = _StubLLM(content="direction verdict")
    state = {
        "direction_debate_state": {
            "history": "Higher Yields Analyst: up\nLower Yields Analyst: down",
            "higher_yields_history": "Higher Yields Analyst: up",
            "lower_yields_history": "Lower Yields Analyst: down",
            "current_response": "Lower Yields Analyst: down",
            "judge_decision": "",
            "count": 2,
        },
        "shape_debate_state": {
            "steepener_history": "",
            "flattener_history": "",
            "history": "",
            "current_response": "",
            "direction_outcome": "",
            "judge_decision": "",
            "count": 0,
        },
    }
    out = create_direction_research_manager(llm)(state)
    assert out["direction_debate_state"]["judge_decision"] == "direction verdict"
    assert out["shape_debate_state"]["direction_outcome"] == "direction verdict"
    assert out["shape_debate_state"]["count"] == 0


@pytest.mark.unit
def test_fi_graph_invokes_end_to_end_offline():
    setup = _setup(FI_KEYS, llm=_StubLLM())
    graph = setup.setup_graph(FI_KEYS).compile()
    init = Propagator().create_initial_state("UST", "2026-09-04")
    final = graph.invoke(init, config={"recursion_limit": 100})

    assert final["macro_policy_report"] == "stub response"
    assert final["macro_calendar_report"] == "stub response"
    direction = final["direction_debate_state"]
    assert direction["judge_decision"] == "stub response"
    assert direction["count"] == 2  # 1 round = 2 speeches
    shape = final["shape_debate_state"]
    assert shape["judge_decision"] == "stub response"
    assert shape["direction_outcome"] == "stub response"  # manager hand-off
    assert shape["count"] == 2
    # FI Trader runs last (free-text stub path).
    assert final["trader_investment_plan"] == "stub response"
