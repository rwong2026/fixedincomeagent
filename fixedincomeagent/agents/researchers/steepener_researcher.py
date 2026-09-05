from fixedincomeagent.agents.utils.agent_utils import (
    get_language_instruction,
    opponent_argument_or_opening,
)


def create_steepener_researcher(llm):
    def steepener_node(state) -> dict:
        shape_debate_state = state["shape_debate_state"]
        history = shape_debate_state.get("history", "")
        steepener_history = shape_debate_state.get("steepener_history", "")
        direction_outcome = shape_debate_state.get("direction_outcome", "")

        current_response = opponent_argument_or_opening(
            shape_debate_state.get("current_response", ""), "flattener analyst"
        )
        macro_policy_report = state["macro_policy_report"]
        curve_technicals_report = state["curve_technicals_report"]
        fed_speak_report = state["fed_speak_report"]
        macro_calendar_report = state["macro_calendar_report"]

        prompt = f"""You are a Steepener Analyst arguing that the US Treasury yield curve will STEEPEN. Your task is to build a strong, evidence-based case for steepening — for example, a front-end rally on expected rate cuts while the long end stays bid on term premium, or long-end selling on supply while the front end stays anchored. Leverage the provided research and the direction debate's outcome to counter the flattener case effectively.

Key points to focus on:
- Front-End Dynamics: Highlight Fed easing expectations or policy repricing that pull short yields down faster than long yields.
- Long-End Pressure: Emphasize term-premium rebuild, heavy issuance, or inflation risk lifting long yields relative to the front end.
- Policy Path: Use Fed communications showing an asymmetric path that favors steepening.
- Curve Technicals: Point to positioning, supply calendar, and curve levels that favor a steeper curve.
- Flattener Counterpoints: Critically analyze the flattener argument with specific data and sound reasoning, exposing weaknesses.
- Engagement: Present your argument in a conversational style, engaging directly with the flattener analyst's points and debating effectively rather than just listing data.

Resources available:
Direction debate outcome (context): {direction_outcome}
Macro/policy report: {macro_policy_report}
Curve technicals report: {curve_technicals_report}
Fed speak report: {fed_speak_report}
Macro calendar report: {macro_calendar_report}
Conversation history of the debate: {history}
Last flattener argument: {current_response}
Use this information to deliver a compelling case for curve steepening, refute the flattener's concerns, and engage in a dynamic debate.
""" + get_language_instruction()

        response = llm.invoke(prompt)

        argument = f"Steepener Analyst: {response.content}"

        new_shape_debate_state = {
            "history": history + "\n" + argument,
            "steepener_history": steepener_history + "\n" + argument,
            "flattener_history": shape_debate_state.get("flattener_history", ""),
            "direction_outcome": direction_outcome,
            "current_response": argument,
            "count": shape_debate_state["count"] + 1,
        }

        return {"shape_debate_state": new_shape_debate_state}

    return steepener_node
