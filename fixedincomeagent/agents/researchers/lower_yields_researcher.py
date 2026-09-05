from fixedincomeagent.agents.utils.agent_utils import (
    get_language_instruction,
    opponent_argument_or_opening,
)


def create_lower_yields_researcher(llm):
    def lower_yields_node(state) -> dict:
        direction_debate_state = state["direction_debate_state"]
        history = direction_debate_state.get("history", "")
        lower_yields_history = direction_debate_state.get("lower_yields_history", "")

        current_response = opponent_argument_or_opening(
            direction_debate_state.get("current_response", ""), "higher yields analyst"
        )
        macro_policy_report = state["macro_policy_report"]
        curve_technicals_report = state["curve_technicals_report"]
        fed_speak_report = state["fed_speak_report"]
        macro_calendar_report = state["macro_calendar_report"]

        prompt = f"""You are a Lower Yields Analyst arguing that US Treasury yields will move LOWER. Your task is to build a strong, evidence-based case emphasizing an economic slowdown, disinflation, a dovish Fed pivot, and flight-to-quality demand. Leverage the provided research to counter the case for higher yields effectively.

Key points to focus on:
- Economic Slowdown: Highlight weakening growth, labor market cooling, and fading consumer demand that pull yields down.
- Disinflation: Emphasize improving inflation trends that open the door to policy easing.
- Dovish Pivot: Use Fed communications and policy signals showing openness to cuts or an end to tightening.
- Flight to Quality: Point to risk-off dynamics and safe-haven demand for Treasuries pushing yields lower.
- Higher-Yields Counterpoints: Critically analyze the higher yields argument with specific data and sound reasoning, exposing weaknesses.
- Engagement: Present your argument in a conversational style, engaging directly with the higher yields analyst's points and debating effectively rather than just listing data.

Resources available:
Macro/policy report: {macro_policy_report}
Curve technicals report: {curve_technicals_report}
Fed speak report: {fed_speak_report}
Macro calendar report: {macro_calendar_report}
Conversation history of the debate: {history}
Last higher yields argument: {current_response}
Use this information to deliver a compelling case for lower yields, refute the higher yields analyst's claims, and engage in a dynamic debate.
""" + get_language_instruction()

        response = llm.invoke(prompt)

        argument = f"Lower Yields Analyst: {response.content}"

        new_direction_debate_state = {
            "history": history + "\n" + argument,
            "lower_yields_history": lower_yields_history + "\n" + argument,
            "higher_yields_history": direction_debate_state.get("higher_yields_history", ""),
            "current_response": argument,
            "count": direction_debate_state["count"] + 1,
        }

        return {"direction_debate_state": new_direction_debate_state}

    return lower_yields_node
