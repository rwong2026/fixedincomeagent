from fixedincomeagent.agents.utils.agent_utils import (
    get_language_instruction,
    opponent_argument_or_opening,
)


def create_higher_yields_researcher(llm):
    def higher_yields_node(state) -> dict:
        direction_debate_state = state["direction_debate_state"]
        history = direction_debate_state.get("history", "")
        higher_yields_history = direction_debate_state.get("higher_yields_history", "")

        current_response = opponent_argument_or_opening(
            direction_debate_state.get("current_response", ""), "lower yields analyst"
        )
        macro_policy_report = state["macro_policy_report"]
        curve_technicals_report = state["curve_technicals_report"]
        fed_speak_report = state["fed_speak_report"]
        macro_calendar_report = state["macro_calendar_report"]

        prompt = f"""You are a Higher Yields Analyst arguing that US Treasury yields will move HIGHER. Your task is to build a strong, evidence-based case emphasizing a strong economy, sticky inflation, a hawkish Fed, and increased Treasury supply. Leverage the provided research to counter the case for lower yields effectively.

Key points to focus on:
- Strong Economy: Highlight resilient growth, a firm labor market, and robust consumer demand that keep yields elevated.
- Sticky Inflation: Emphasize persistent price pressures (shelter, services, wages) that limit disinflation progress.
- Hawkish Fed: Use Fed communications and policy signals showing restraint on cuts or openness to further tightening.
- Increased Supply: Point to heavy Treasury issuance, widening deficits, and term-premium rebuild pushing yields up.
- Lower-Yields Counterpoints: Critically analyze the lower yields argument with specific data and sound reasoning, exposing weaknesses.
- Engagement: Present your argument in a conversational style, engaging directly with the lower yields analyst's points and debating effectively rather than just listing data.

Resources available:
Macro/policy report: {macro_policy_report}
Curve technicals report: {curve_technicals_report}
Fed speak report: {fed_speak_report}
Macro calendar report: {macro_calendar_report}
Conversation history of the debate: {history}
Last lower yields argument: {current_response}
Use this information to deliver a compelling case for higher yields, refute the lower yields analyst's concerns, and engage in a dynamic debate.
""" + get_language_instruction()

        response = llm.invoke(prompt)

        argument = f"Higher Yields Analyst: {response.content}"

        new_direction_debate_state = {
            "history": history + "\n" + argument,
            "higher_yields_history": higher_yields_history + "\n" + argument,
            "lower_yields_history": direction_debate_state.get("lower_yields_history", ""),
            "current_response": argument,
            "count": direction_debate_state["count"] + 1,
        }

        return {"direction_debate_state": new_direction_debate_state}

    return higher_yields_node
