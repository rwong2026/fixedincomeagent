"""Ablation support (Task 7.5): run the pipeline with data sources removed.

Ablation removes DATA, not agents — every analyst still runs, with fewer
tools bound (and the matching ToolNode executors trimmed to the same set, so
the bound/executable invariant in trading_graph._create_tool_nodes holds).
Offline: fake-LLM capture of the bound tool lists, same pattern as the
analyst tests; no network, no LLM, no FRED calls.
"""
from __future__ import annotations

from unittest import mock

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableLambda

from fixedincomeagent.agents.analysts.fed_speak_analyst import (
    create_fed_speak_analyst,
)
from fixedincomeagent.agents.analysts.macro_policy_analyst import (
    create_macro_policy_analyst,
)
from fixedincomeagent.backtest.runner import (
    AblationConfig,
    BacktestRunner,
    ablation_disabled_tools,
)
from fixedincomeagent.graph.conditional_logic import ConditionalLogic
from fixedincomeagent.graph.propagation import Propagator
from fixedincomeagent.graph.setup import GraphSetup
from fixedincomeagent.graph.trading_graph import TradingAgentsGraph

MACRO_POLICY_FULL = {
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
}
FED_SPEAK_FULL = {"get_fed_speeches", "get_fomc_calendar", "get_cot_data"}

INFLATION_COMPONENT_TOOLS = {
    "get_inflation_nowcast",
    "get_shelter_rents",
    "get_used_vehicle_index",
    "get_supply_chain_pressure",
    "get_ism_prices_paid",
    "get_consumer_inflation_expectations",
}

FI_KEYS = ["macro_policy", "curve_technicals", "fed_speak", "macro_calendar"]


class _FakeLLM:
    """Captures the bound tools and rendered prompt; returns a canned report."""

    def __init__(self, content="ablation report body"):
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
        "messages": [HumanMessage(content="Run the analysis.")],
    }


def _bound_names(factory, disabled=None):
    llm = _FakeLLM()
    factory(llm, disabled_tools=disabled)(_state())
    return {tool.name for tool in llm.bound_tools}, llm


# ---------------------------------------------------------------------------
# AblationConfig + the flag -> tool-name mapping
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ablation_config_defaults():
    config = AblationConfig()
    assert config.disable_inflation_components is False
    assert config.disable_positioning is False
    assert config.disable_fed_speak is False
    assert config.label == "full"


@pytest.mark.unit
def test_disabled_tools_no_flags_is_empty():
    assert ablation_disabled_tools(AblationConfig()) == frozenset()
    assert ablation_disabled_tools(None) == frozenset()


@pytest.mark.unit
def test_disabled_tools_inflation_components_flag():
    config = AblationConfig(disable_inflation_components=True)
    assert ablation_disabled_tools(config) == frozenset(INFLATION_COMPONENT_TOOLS)


@pytest.mark.unit
def test_disabled_tools_positioning_flag():
    assert ablation_disabled_tools(AblationConfig(disable_positioning=True)) == frozenset(
        {"get_cot_data"}
    )


@pytest.mark.unit
def test_disabled_tools_fed_speak_flag():
    assert ablation_disabled_tools(AblationConfig(disable_fed_speak=True)) == frozenset(
        {"get_fed_speeches"}
    )


@pytest.mark.unit
def test_disabled_tools_flags_combine():
    config = AblationConfig(disable_positioning=True, disable_fed_speak=True)
    assert ablation_disabled_tools(config) == frozenset(
        {"get_cot_data", "get_fed_speeches"}
    )


# ---------------------------------------------------------------------------
# Analyst binding: the filtered tool set is what the LLM actually gets
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_macro_policy_binds_full_set_by_default():
    names, _ = _bound_names(create_macro_policy_analyst)
    assert names == MACRO_POLICY_FULL


@pytest.mark.unit
def test_macro_policy_drops_inflation_component_tools():
    disabled = ablation_disabled_tools(AblationConfig(disable_inflation_components=True))
    names, llm = _bound_names(create_macro_policy_analyst, disabled)
    assert names == MACRO_POLICY_FULL - INFLATION_COMPONENT_TOOLS
    # The prompt's tool_names line reflects the filtered set.
    tools_line = next(
        line for line in llm.seen_prompt.splitlines() if "following tools:" in line
    )
    assert "get_shelter_rents" not in tools_line
    assert "get_fred_series" in tools_line


@pytest.mark.unit
def test_macro_policy_drops_fed_speeches_tool():
    disabled = ablation_disabled_tools(AblationConfig(disable_fed_speak=True))
    names, _ = _bound_names(create_macro_policy_analyst, disabled)
    assert names == MACRO_POLICY_FULL - {"get_fed_speeches"}


@pytest.mark.unit
def test_fed_speak_binds_full_set_by_default():
    names, _ = _bound_names(create_fed_speak_analyst)
    assert names == FED_SPEAK_FULL


@pytest.mark.unit
def test_fed_speak_drops_cot_tool():
    disabled = ablation_disabled_tools(AblationConfig(disable_positioning=True))
    names, _ = _bound_names(create_fed_speak_analyst, disabled)
    assert names == FED_SPEAK_FULL - {"get_cot_data"}


@pytest.mark.unit
def test_fed_speak_drops_speeches_tool_keeps_cot():
    disabled = ablation_disabled_tools(AblationConfig(disable_fed_speak=True))
    names, _ = _bound_names(create_fed_speak_analyst, disabled)
    assert names == {"get_fomc_calendar", "get_cot_data"}


# ---------------------------------------------------------------------------
# ToolNode executors: same filter applied to the executable tool sets
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_tool_nodes_unfiltered_by_default():
    nodes = TradingAgentsGraph._create_tool_nodes(None)
    assert set(nodes["macro_policy"].tools_by_name) == MACRO_POLICY_FULL
    assert set(nodes["fed_speak"].tools_by_name) == FED_SPEAK_FULL


@pytest.mark.unit
def test_tool_nodes_filtered_by_disabled_tools():
    disabled = ablation_disabled_tools(
        AblationConfig(disable_inflation_components=True, disable_positioning=True)
    )
    nodes = TradingAgentsGraph._create_tool_nodes(disabled)
    assert set(nodes["macro_policy"].tools_by_name) == (
        MACRO_POLICY_FULL - INFLATION_COMPONENT_TOOLS
    )
    assert set(nodes["fed_speak"].tools_by_name) == {"get_fed_speeches", "get_fomc_calendar"}
    # Untouched analysts keep their full tool set.
    assert "get_treasury_par_yields" in nodes["curve_technicals"].tools_by_name


# ---------------------------------------------------------------------------
# GraphSetup plumbing: disabled_tools reach the analyst factories
# ---------------------------------------------------------------------------


class _CapturingStubLLM(RunnableLambda):
    """Offline LLM recording every bind_tools list it receives."""

    def __init__(self):
        self.captured: list[list[str]] = []
        super().__init__(lambda _prompt: AIMessage(content="stub response"))

    def bind_tools(self, tools, **kwargs):
        self.captured.append([tool.name for tool in tools])
        return self

    def with_structured_output(self, schema, **kwargs):
        raise AttributeError("stub: structured output unsupported")


@pytest.mark.unit
def test_graph_setup_threads_disabled_tools_to_analysts():
    llm = _CapturingStubLLM()
    disabled = ablation_disabled_tools(
        AblationConfig(disable_inflation_components=True, disable_positioning=True)
    )
    setup = GraphSetup(
        llm,
        llm,
        TradingAgentsGraph._create_tool_nodes(disabled),
        ConditionalLogic(max_direction_debate_rounds=1, max_shape_debate_rounds=1),
        disabled_tools=disabled,
    )
    graph = setup.setup_graph(FI_KEYS).compile()
    init = Propagator().create_initial_state("UST", "2026-09-04")
    final = graph.invoke(init, config={"recursion_limit": 100})

    assert final["macro_policy_report"] == "stub response"
    bound_sets = [set(names) for names in llm.captured]
    # No analyst anywhere in the run saw a disabled tool.
    for names in bound_sets:
        assert names.isdisjoint(disabled)
    # The macro policy analyst (the only list with ALFRED) ran reduced.
    assert MACRO_POLICY_FULL - INFLATION_COMPONENT_TOOLS in bound_sets
    # The fed speak analyst (fomc + speeches, no ALFRED) lost the COT tool.
    assert {"get_fed_speeches", "get_fomc_calendar"} in bound_sets


# ---------------------------------------------------------------------------
# BacktestRunner: accepts the config, labels runs, threads the filter
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_runner_defaults_to_full_ablation():
    runner = BacktestRunner(graph=object())
    assert runner.ablation_config == AblationConfig()
    assert runner.ablation_config.label == "full"


@pytest.mark.unit
def test_runner_stores_ablation_config_and_label():
    config = AblationConfig(disable_positioning=True, label="no-positioning")
    runner = BacktestRunner(graph=object(), ablation_config=config)
    assert runner.ablation_config is config
    assert runner.ablation_config.label == "no-positioning"


@pytest.mark.unit
def test_runner_constructs_graph_with_disabled_tools():
    config = AblationConfig(disable_inflation_components=True, label="no-inflation-detail")
    runner = BacktestRunner(graph=None, config={"fi_horizon_days": 20},
                            ablation_config=config)
    with mock.patch(
        "fixedincomeagent.graph.trading_graph.TradingAgentsGraph"
    ) as graph_cls:
        runner.graph  # noqa: B018 — triggers the lazy construction
    _, kwargs = graph_cls.call_args
    assert kwargs["disabled_tools"] == frozenset(INFLATION_COMPONENT_TOOLS)


@pytest.mark.unit
def test_runner_full_ablation_constructs_graph_with_no_filtering():
    runner = BacktestRunner(graph=None, config={"fi_horizon_days": 20})
    with mock.patch(
        "fixedincomeagent.graph.trading_graph.TradingAgentsGraph"
    ) as graph_cls:
        runner.graph  # noqa: B018
    _, kwargs = graph_cls.call_args
    assert kwargs["disabled_tools"] == frozenset()
