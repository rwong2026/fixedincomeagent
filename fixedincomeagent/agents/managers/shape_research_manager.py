"""Shape Research Manager: judges the steepener/flattener debate into a per-spread outlook."""

from __future__ import annotations

from fixedincomeagent.agents.schemas import ShapeOutlook, render_shape_outlook
from fixedincomeagent.agents.utils.agent_utils import get_language_instruction
from fixedincomeagent.agents.utils.structured import (
    NO_EXTERNAL_TOOLS,
    bind_structured,
    invoke_structured_or_freetext,
)
from fixedincomeagent.dataflows.config import get_config


def create_shape_research_manager(llm):
    structured_llm = bind_structured(llm, ShapeOutlook, "Shape Research Manager")

    def shape_research_manager_node(state) -> dict:
        shape_debate_state = state["shape_debate_state"]
        history = shape_debate_state.get("history", "")
        direction_outcome = shape_debate_state.get("direction_outcome", "")
        spreads = ", ".join(get_config().get("fi_spreads", []))

        prompt = f"""As the Shape Research Manager and debate facilitator, your role is to critically evaluate this round of the curve-shape debate and deliver a clear, per-spread shape outlook for the US Treasury yield curve.

Produce exactly one shape call for each configured spread/butterfly: {spreads}.

**Shape scale** (use exactly one per spread):
- **steepen**: the spread is expected to widen (for the butterfly: belly outperforms wings)
- **flatten**: the spread is expected to narrow (for the butterfly: wings outperform belly)
- **unchanged**: no meaningful move expected over the prediction horizon

Condition your judgment on the direction debate's outcome below — a curve view that contradicts the resolved direction view needs explicit justification. Commit to steepen or flatten only when the debate's strongest arguments clearly warrant it for that spread. Choose unchanged when the evidence is balanced, materially conflicting, ambiguous, or insufficient; do not manufacture a shape view merely to appear decisive. Weigh the steepener and flattener cases on their merits, independent of which side spoke first or last. Spreads may diverge — judge each on its own evidence rather than forcing a uniform call across the curve.

---

**Direction Debate Outcome (context):**
{direction_outcome}

**Debate History:**
{history}

{NO_EXTERNAL_TOOLS}""" + get_language_instruction()

        outlook = invoke_structured_or_freetext(
            structured_llm,
            llm,
            prompt,
            render_shape_outlook,
            "Shape Research Manager",
        )

        new_shape_debate_state = {
            "judge_decision": outlook,
            "history": shape_debate_state.get("history", ""),
            "steepener_history": shape_debate_state.get("steepener_history", ""),
            "flattener_history": shape_debate_state.get("flattener_history", ""),
            "direction_outcome": direction_outcome,
            "current_response": outlook,
            "count": shape_debate_state["count"],
        }

        return {"shape_debate_state": new_shape_debate_state}

    return shape_research_manager_node
