"""Task 3.5: register the four fixed-income analysts in the graph setup.

Offline: a stub LLM object satisfies GraphSetup (the llm is only captured
inside node factories); ToolNodes are built from the real tool functions via
TradingAgentsGraph._create_tool_nodes.
"""

from unittest.mock import MagicMock

import pytest

from fixedincomeagent.agents import (
    create_curve_technicals_analyst,
    create_fed_speak_analyst,
    create_macro_calendar_analyst,
    create_macro_policy_analyst,
)
from fixedincomeagent.graph.analyst_execution import build_analyst_execution_plan
from fixedincomeagent.graph.conditional_logic import ConditionalLogic
from fixedincomeagent.graph.setup import GraphSetup
from fixedincomeagent.graph.trading_graph import TradingAgentsGraph

FI_KEYS = ["macro_policy", "curve_technicals", "fed_speak", "macro_calendar"]
FI_FACTORIES = [
    create_macro_policy_analyst,
    create_curve_technicals_analyst,
    create_fed_speak_analyst,
    create_macro_calendar_analyst,
]
EXPECTED_LABELS = {
    "macro_policy": "Macro Policy Analyst",
    "curve_technicals": "Curve Technicals Analyst",
    "fed_speak": "Fed Speak Analyst",
    "macro_calendar": "Macro Calendar Analyst",
}


def _compile(selected):
    setup = GraphSetup(
        MagicMock(),
        MagicMock(),
        TradingAgentsGraph._create_tool_nodes(None),
        ConditionalLogic(),
    )
    return setup.setup_graph(selected).compile()


@pytest.mark.unit
def test_fi_factories_exported_from_agents_package():
    import fixedincomeagent.agents as agents

    for factory in FI_FACTORIES:
        assert factory.__name__ in agents.__all__


@pytest.mark.unit
def test_plan_includes_all_four_fi_keys():
    plan = build_analyst_execution_plan(FI_KEYS)
    assert [spec.key for spec in plan.specs] == FI_KEYS


@pytest.mark.unit
@pytest.mark.parametrize("key", FI_KEYS)
def test_builds_and_compiles_with_fi_analyst(key):
    _compile([key])  # must not raise


@pytest.mark.unit
def test_equity_keys_still_compile():
    _compile(["market", "social", "news", "fundamentals"])


@pytest.mark.unit
def test_fi_and_equity_keys_can_be_mixed():
    _compile(["macro_policy", "market"])


EXPECTED_TOOL_NAMES = {
    "macro_policy": {
        "get_fred_series",
        "get_alfred_vintage",
        "get_inflation_breakevens",
        "get_inflation_nowcast",
        "get_shelter_rents",
        "get_used_vehicle_index",
        "get_supply_chain_pressure",
        "get_ism_prices_paid",
        "get_consumer_inflation_expectations",
        "get_fomc_calendar",
        "get_fed_speeches",
    },
    "curve_technicals": {"get_fred_series", "get_treasury_par_yields"},
    "fed_speak": {"get_fed_speeches", "get_fomc_calendar", "get_cot_data"},
    "macro_calendar": {"get_fomc_calendar", "get_fred_series", "get_auction_results"},
}


@pytest.mark.unit
@pytest.mark.parametrize("key", FI_KEYS)
def test_fi_tool_nodes_register_bound_tools(key):
    # Each FI analyst binds its tools via llm.bind_tools; the executor
    # ToolNode must register the same set or calls fail at runtime
    # (same gap class as tests/test_market_toolnode.py).
    nodes = TradingAgentsGraph._create_tool_nodes(None)
    assert set(nodes[key].tools_by_name) == EXPECTED_TOOL_NAMES[key]


@pytest.mark.unit
def test_fi_specs_use_display_labels():
    plan = build_analyst_execution_plan(FI_KEYS)
    assert {spec.key: spec.agent_node for spec in plan.specs} == EXPECTED_LABELS
