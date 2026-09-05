"""Direction Research Manager: judges the higher/lower yields debate into a per-tenor outlook."""

from __future__ import annotations

from fixedincomeagent.agents.schemas import DirectionOutlook, render_direction_outlook
from fixedincomeagent.agents.utils.agent_utils import get_language_instruction
from fixedincomeagent.agents.utils.structured import (
    NO_EXTERNAL_TOOLS,
    bind_structured,
    invoke_structured_or_freetext,
)
from fixedincomeagent.dataflows.config import get_config


def create_direction_research_manager(llm):
    structured_llm = bind_structured(llm, DirectionOutlook, "Direction Research Manager")

    def direction_research_manager_node(state) -> dict:
        direction_debate_state = state["direction_debate_state"]
        history = direction_debate_state.get("history", "")
        tenors = ", ".join(get_config().get("fi_tenors", []))

        prompt = f"""As the Direction Research Manager and debate facilitator, your role is to critically evaluate this round of the yield-direction debate and deliver a clear, per-tenor direction outlook for US Treasury yields.

Produce exactly one direction call for each configured tenor: {tenors}.

**Direction scale** (use exactly one per tenor):
- **up**: yields expected to move higher over the prediction horizon
- **down**: yields expected to move lower over the prediction horizon
- **neutral**: expected move below the neutral threshold (default <5bp)

Commit to up or down only when the debate's strongest arguments clearly warrant it for that tenor. Choose neutral when the evidence is balanced, materially conflicting, ambiguous, or insufficient; do not manufacture a direction merely to appear decisive. Weigh the higher-yields and lower-yields cases on their merits, independent of which side spoke first or last. Tenors may diverge — judge each on its own evidence rather than forcing a uniform call across the curve.

---

**Debate History:**
{history}

{NO_EXTERNAL_TOOLS}""" + get_language_instruction()

        outlook = invoke_structured_or_freetext(
            structured_llm,
            llm,
            prompt,
            render_direction_outlook,
            "Direction Research Manager",
        )

        new_direction_debate_state = {
            "judge_decision": outlook,
            "history": direction_debate_state.get("history", ""),
            "higher_yields_history": direction_debate_state.get("higher_yields_history", ""),
            "lower_yields_history": direction_debate_state.get("lower_yields_history", ""),
            "current_response": outlook,
            "count": direction_debate_state["count"],
        }

        # Hand off to the shape debate: seed its direction_outcome with the
        # judged direction outlook so steepener/flattener researchers argue
        # conditioned on it. Other shape fields pass through untouched.
        shape_debate_state = state.get("shape_debate_state", {})

        return {
            "direction_debate_state": new_direction_debate_state,
            "shape_debate_state": {
                "steepener_history": shape_debate_state.get("steepener_history", ""),
                "flattener_history": shape_debate_state.get("flattener_history", ""),
                "history": shape_debate_state.get("history", ""),
                "current_response": shape_debate_state.get("current_response", ""),
                "direction_outcome": outlook,
                "judge_decision": shape_debate_state.get("judge_decision", ""),
                "count": shape_debate_state.get("count", 0),
            },
        }

    return direction_research_manager_node
