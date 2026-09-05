# FixedIncomeAgent/graph/setup.py

from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from fixedincomeagent.agents import (
    create_aggressive_debator,
    create_bear_researcher,
    create_bull_researcher,
    create_conservative_debator,
    create_curve_technicals_analyst,
    create_direction_research_manager,
    create_fed_speak_analyst,
    create_fi_trader,
    create_flattener_researcher,
    create_fundamentals_analyst,
    create_higher_yields_researcher,
    create_lower_yields_researcher,
    create_macro_calendar_analyst,
    create_macro_policy_analyst,
    create_market_analyst,
    create_msg_delete,
    create_neutral_debator,
    create_news_analyst,
    create_portfolio_manager,
    create_research_manager,
    create_sentiment_analyst,
    create_shape_research_manager,
    create_steepener_researcher,
    create_trader,
)
from fixedincomeagent.agents.utils.agent_states import AgentState

from .analyst_execution import FI_ANALYST_KEYS, build_analyst_execution_plan
from .conditional_logic import ConditionalLogic

# Every target a shared conditional router can return. Each edge driven by the
# router maps all of them, so a fall-through return (e.g. under prompt/i18n/
# refactor drift in the speaker labels) can never hit a missing path_map entry
# and crash LangGraph mid-run (#1088).
DEBATE_PATH_MAP = {
    "Bull Researcher": "Bull Researcher",
    "Bear Researcher": "Bear Researcher",
    "Research Manager": "Research Manager",
}
RISK_ANALYSIS_PATH_MAP = {
    "Aggressive Analyst": "Aggressive Analyst",
    "Conservative Analyst": "Conservative Analyst",
    "Neutral Analyst": "Neutral Analyst",
    "Portfolio Manager": "Portfolio Manager",
}
# FI dual-track debate maps — same complete-map rule as DEBATE_PATH_MAP (#1088).
DIRECTION_DEBATE_PATH_MAP = {
    "Higher Yields Researcher": "Higher Yields Researcher",
    "Lower Yields Researcher": "Lower Yields Researcher",
    "Direction Research Manager": "Direction Research Manager",
}
SHAPE_DEBATE_PATH_MAP = {
    "Steepener Researcher": "Steepener Researcher",
    "Flattener Researcher": "Flattener Researcher",
    "Shape Research Manager": "Shape Research Manager",
}


class GraphSetup:
    """Handles the setup and configuration of the agent graph."""

    def __init__(
        self,
        quick_thinking_llm: Any,
        deep_thinking_llm: Any,
        tool_nodes: dict[str, ToolNode],
        conditional_logic: ConditionalLogic,
    ):
        """Initialize with required components."""
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.tool_nodes = tool_nodes
        self.conditional_logic = conditional_logic

    def setup_graph(
        self, selected_analysts=("market", "social", "news", "fundamentals")
    ):
        """Set up and compile the agent workflow graph.

        Args:
            selected_analysts (list): List of analyst types to include. Equity options:
                - "market": Market analyst
                - "social": Social media analyst
                - "news": News analyst
                - "fundamentals": Fundamentals analyst
            Fixed-income options (opt-in, not part of any default):
                - "macro_policy": Macro/policy analyst
                - "curve_technicals": Curve technicals analyst
                - "fed_speak": Fed speak analyst
                - "macro_calendar": Macro calendar analyst

        When every selected analyst is a fixed-income analyst, the graph wires
        the FI dual-track debate (direction -> shape) after the analyst chain
        instead of the equity bull/bear -> trader -> risk pipeline. Mixed
        selections keep the equity track.
        """
        plan = build_analyst_execution_plan(selected_analysts)

        analyst_factories = {
            "market": lambda: create_market_analyst(self.quick_thinking_llm),
            "social": lambda: create_sentiment_analyst(self.quick_thinking_llm),
            "news": lambda: create_news_analyst(self.quick_thinking_llm),
            "fundamentals": lambda: create_fundamentals_analyst(self.quick_thinking_llm),
            "macro_policy": lambda: create_macro_policy_analyst(self.quick_thinking_llm),
            "curve_technicals": lambda: create_curve_technicals_analyst(self.quick_thinking_llm),
            "fed_speak": lambda: create_fed_speak_analyst(self.quick_thinking_llm),
            "macro_calendar": lambda: create_macro_calendar_analyst(self.quick_thinking_llm),
        }

        fi_mode = set(selected_analysts) <= FI_ANALYST_KEYS

        # Create workflow and wire the analyst chain; the last analyst hands
        # off to the track's opening debater.
        workflow = StateGraph(AgentState)
        self._wire_analyst_chain(
            workflow,
            plan,
            analyst_factories,
            last_target="Higher Yields Researcher" if fi_mode else "Bull Researcher",
        )

        if fi_mode:
            self._wire_fi_debate_track(workflow)
            return workflow

        # Create researcher and manager nodes
        bull_researcher_node = create_bull_researcher(self.quick_thinking_llm)
        bear_researcher_node = create_bear_researcher(self.quick_thinking_llm)
        research_manager_node = create_research_manager(self.deep_thinking_llm)
        trader_node = create_trader(self.quick_thinking_llm)

        # Create risk analysis nodes
        aggressive_analyst = create_aggressive_debator(self.quick_thinking_llm)
        neutral_analyst = create_neutral_debator(self.quick_thinking_llm)
        conservative_analyst = create_conservative_debator(self.quick_thinking_llm)
        portfolio_manager_node = create_portfolio_manager(self.deep_thinking_llm)

        # Add other nodes
        workflow.add_node("Bull Researcher", bull_researcher_node)
        workflow.add_node("Bear Researcher", bear_researcher_node)
        workflow.add_node("Research Manager", research_manager_node)
        workflow.add_node("Trader", trader_node)
        workflow.add_node("Aggressive Analyst", aggressive_analyst)
        workflow.add_node("Neutral Analyst", neutral_analyst)
        workflow.add_node("Conservative Analyst", conservative_analyst)
        workflow.add_node("Portfolio Manager", portfolio_manager_node)

        # Both research-debate edges share the complete DEBATE_PATH_MAP (#1088).
        for debate_node in ("Bull Researcher", "Bear Researcher"):
            workflow.add_conditional_edges(
                debate_node,
                self.conditional_logic.should_continue_debate,
                DEBATE_PATH_MAP,
            )
        workflow.add_edge("Research Manager", "Trader")
        workflow.add_edge("Trader", "Aggressive Analyst")
        # All three risk edges share the complete RISK_ANALYSIS_PATH_MAP (#1088).
        for risk_node in ("Aggressive Analyst", "Conservative Analyst", "Neutral Analyst"):
            workflow.add_conditional_edges(
                risk_node,
                self.conditional_logic.should_continue_risk_analysis,
                RISK_ANALYSIS_PATH_MAP,
            )

        workflow.add_edge("Portfolio Manager", END)

        return workflow

    def _wire_analyst_chain(self, workflow, plan, analyst_factories, last_target):
        """Add analyst/tool/clear nodes and chain them START -> ... -> last_target."""
        for spec in plan.specs:
            workflow.add_node(spec.agent_node, analyst_factories[spec.key]())
            workflow.add_node(spec.clear_node, create_msg_delete())
            workflow.add_node(spec.tool_node, self.tool_nodes[spec.key])

        workflow.add_edge(START, plan.specs[0].agent_node)

        for i, spec in enumerate(plan.specs):
            current_analyst = spec.agent_node
            current_tools = spec.tool_node
            current_clear = spec.clear_node

            # Add conditional edges for current analyst
            workflow.add_conditional_edges(
                current_analyst,
                getattr(self.conditional_logic, f"should_continue_{spec.key}"),
                [current_tools, current_clear],
            )
            workflow.add_edge(current_tools, current_analyst)

            # Connect to next analyst, or to the track's opening debater.
            if i < len(plan.specs) - 1:
                workflow.add_edge(current_clear, plan.specs[i + 1].agent_node)
            else:
                workflow.add_edge(current_clear, last_target)

    def _wire_fi_debate_track(self, workflow):
        """Wire the FI dual-track debate after the analyst chain.

        Higher Yields <-> Lower Yields (direction debate) -> Direction
        Research Manager -> Steepener <-> Flattener (shape debate) -> Shape
        Research Manager -> FI Trader.
        """
        workflow.add_node(
            "Higher Yields Researcher",
            create_higher_yields_researcher(self.quick_thinking_llm),
        )
        workflow.add_node(
            "Lower Yields Researcher",
            create_lower_yields_researcher(self.quick_thinking_llm),
        )
        workflow.add_node(
            "Direction Research Manager",
            create_direction_research_manager(self.deep_thinking_llm),
        )
        workflow.add_node(
            "Steepener Researcher",
            create_steepener_researcher(self.quick_thinking_llm),
        )
        workflow.add_node(
            "Flattener Researcher",
            create_flattener_researcher(self.quick_thinking_llm),
        )
        workflow.add_node(
            "Shape Research Manager",
            create_shape_research_manager(self.deep_thinking_llm),
        )

        for debate_node in ("Higher Yields Researcher", "Lower Yields Researcher"):
            workflow.add_conditional_edges(
                debate_node,
                self.conditional_logic.should_continue_direction_debate,
                DIRECTION_DEBATE_PATH_MAP,
            )
        workflow.add_edge("Direction Research Manager", "Steepener Researcher")
        for debate_node in ("Steepener Researcher", "Flattener Researcher"):
            workflow.add_conditional_edges(
                debate_node,
                self.conditional_logic.should_continue_shape_debate,
                SHAPE_DEBATE_PATH_MAP,
            )
        # PHASE 5 CUT POINT: FI Trader is wired (Task 5.1); the risk check and
        # FI Portfolio Manager extend the graph here in Tasks 5.2/5.3. Until
        # then the FI Trader is the terminal node.
        workflow.add_node("FI Trader", create_fi_trader(self.quick_thinking_llm))
        workflow.add_edge("Shape Research Manager", "FI Trader")
        workflow.add_edge("FI Trader", END)
