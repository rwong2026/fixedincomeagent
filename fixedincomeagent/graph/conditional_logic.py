# FixedIncomeAgent/graph/conditional_logic.py

from fixedincomeagent.agents.utils.agent_states import AgentState


class ConditionalLogic:
    """Handles conditional logic for determining graph flow."""

    def __init__(
        self,
        max_debate_rounds=1,
        max_risk_discuss_rounds=1,
        max_direction_debate_rounds=1,
        max_shape_debate_rounds=1,
    ):
        """Initialize with configuration parameters."""
        self.max_debate_rounds = max_debate_rounds
        self.max_risk_discuss_rounds = max_risk_discuss_rounds
        self.max_direction_debate_rounds = max_direction_debate_rounds
        self.max_shape_debate_rounds = max_shape_debate_rounds

    def should_continue_market(self, state: AgentState):
        """Determine if market analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_market"
        return "Msg Clear Market"

    def should_continue_social(self, state: AgentState):
        """Determine if sentiment-analyst tool round should continue.

        Method name keeps the legacy ``social`` suffix to match the
        ``AnalystType.SOCIAL = "social"`` wire value (saved-config
        back-compat); the returned ``clear_node`` label uses the v0.2.5
        rename so it matches the node registered by the execution plan.
        """
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_social"
        return "Msg Clear Sentiment"

    def should_continue_news(self, state: AgentState):
        """Determine if news analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_news"
        return "Msg Clear News"

    def should_continue_fundamentals(self, state: AgentState):
        """Determine if fundamentals analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_fundamentals"
        return "Msg Clear Fundamentals"

    def _should_continue_analyst(self, state: AgentState, tool_node: str, clear_node: str):
        """Shared analyst loop: route to the tool node while the model is
        calling tools, else to the clear node to advance the sequence."""
        if state["messages"][-1].tool_calls:
            return tool_node
        return clear_node

    def should_continue_macro_policy(self, state: AgentState):
        """Determine if macro-policy analysis should continue."""
        return self._should_continue_analyst(state, "tools_macro_policy", "Msg Clear Macro Policy")

    def should_continue_curve_technicals(self, state: AgentState):
        """Determine if curve-technicals analysis should continue."""
        return self._should_continue_analyst(state, "tools_curve_technicals", "Msg Clear Curve Technicals")

    def should_continue_fed_speak(self, state: AgentState):
        """Determine if fed-speak analysis should continue."""
        return self._should_continue_analyst(state, "tools_fed_speak", "Msg Clear Fed Speak")

    def should_continue_macro_calendar(self, state: AgentState):
        """Determine if macro-calendar analysis should continue."""
        return self._should_continue_analyst(state, "tools_macro_calendar", "Msg Clear Macro Calendar")

    def should_continue_debate(self, state: AgentState) -> str:
        """Determine if debate should continue."""

        if (
            state["investment_debate_state"]["count"] >= 2 * self.max_debate_rounds
        ):  # 3 rounds of back-and-forth between 2 agents
            return "Research Manager"
        if state["investment_debate_state"]["current_response"].startswith("Bull"):
            return "Bear Researcher"
        return "Bull Researcher"

    def should_continue_direction_debate(self, state: AgentState) -> str:
        """Route the higher/lower yields debate; hand to the Direction
        Research Manager once the round limit is reached."""
        if (
            state["direction_debate_state"]["count"]
            >= 2 * self.max_direction_debate_rounds
        ):  # rounds of back-and-forth between 2 agents
            return "Direction Research Manager"
        if state["direction_debate_state"]["current_response"].startswith(
            "Higher Yields"
        ):
            return "Lower Yields Researcher"
        return "Higher Yields Researcher"

    def should_continue_shape_debate(self, state: AgentState) -> str:
        """Route the steepener/flattener debate; hand to the Shape
        Research Manager once the round limit is reached."""
        if (
            state["shape_debate_state"]["count"] >= 2 * self.max_shape_debate_rounds
        ):  # rounds of back-and-forth between 2 agents
            return "Shape Research Manager"
        if state["shape_debate_state"]["current_response"].startswith("Steepener"):
            return "Flattener Researcher"
        return "Steepener Researcher"

    def should_continue_risk_analysis(self, state: AgentState) -> str:
        """Determine if risk analysis should continue."""
        if (
            state["risk_debate_state"]["count"] >= 3 * self.max_risk_discuss_rounds
        ):  # 3 rounds of back-and-forth between 3 agents
            return "Portfolio Manager"
        if state["risk_debate_state"]["latest_speaker"].startswith("Aggressive"):
            return "Conservative Analyst"
        if state["risk_debate_state"]["latest_speaker"].startswith("Conservative"):
            return "Neutral Analyst"
        return "Aggressive Analyst"
