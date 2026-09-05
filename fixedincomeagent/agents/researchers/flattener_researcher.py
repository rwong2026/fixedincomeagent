from fixedincomeagent.agents.utils.agent_utils import (
    get_language_instruction,
    opponent_argument_or_opening,
)


def create_flattener_researcher(llm):
    def flattener_node(state) -> dict:
        shape_debate_state = state["shape_debate_state"]
        history = shape_debate_state.get("history", "")
        flattener_history = shape_debate_state.get("flattener_history", "")
        direction_outcome = shape_debate_state.get("direction_outcome", "")

        current_response = opponent_argument_or_opening(
            shape_debate_state.get("current_response", ""), "steepener analyst"
        )
        macro_policy_report = state["macro_policy_report"]
        curve_technicals_report = state["curve_technicals_report"]
        fed_speak_report = state["fed_speak_report"]
        macro_calendar_report = state["macro_calendar_report"]

        prompt = f"""You are a Flattener Analyst arguing that the US Treasury yield curve will FLATTEN. Your task is to build a strong, evidence-based case for flattening — for example, front-end selling on a hawkish hold while the long end rallies on recession fears, or long-end outperformance as growth slows. Leverage the provided research and the direction debate's outcome to counter the steepener case effectively.

Key points to focus on:
- Front-End Pressure: Highlight hawkish Fed holds, sticky near-term inflation, or repricing that lifts short yields relative to the long end.
- Long-End Rally: Emphasize recession fears, flight-to-quality demand, or falling term premium pulling long yields down.
- Policy Path: Use Fed communications showing a path that favors flattening (higher-for-longer, or cuts coming too late).
- Curve Technicals: Point to positioning, supply skewed to the front end, and curve levels that favor a flatter curve.
- Steepener Counterpoints: Critically analyze the steepener argument with specific data and sound reasoning, exposing weaknesses.
- Engagement: Present your argument in a conversational style, engaging directly with the steepener analyst's points and debating effectively rather than just listing data.

Resources available:
Direction debate outcome (context): {direction_outcome}
Macro/policy report: {macro_policy_report}
Curve technicals report: {curve_technicals_report}
Fed speak report: {fed_speak_report}
Macro calendar report: {macro_calendar_report}
Conversation history of the debate: {history}
Last steepener argument: {current_response}
Use this information to deliver a compelling case for curve flattening, refute the steepener's claims, and engage in a dynamic debate.
""" + get_language_instruction()

        response = llm.invoke(prompt)

        argument = f"Flattener Analyst: {response.content}"

        new_shape_debate_state = {
            "history": history + "\n" + argument,
            "flattener_history": flattener_history + "\n" + argument,
            "steepener_history": shape_debate_state.get("steepener_history", ""),
            "direction_outcome": direction_outcome,
            "current_response": argument,
            "count": shape_debate_state["count"] + 1,
        }

        return {"shape_debate_state": new_shape_debate_state}

    return flattener_node
