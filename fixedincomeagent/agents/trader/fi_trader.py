"""Fixed-Income Trader: turns the direction/shape outlooks into the desk's calls.

Consumes the Direction Research Manager's judge decision (rendered
DirectionOutlook), the Shape Research Manager's judge decision (rendered
ShapeOutlook), and the curve technicals report, then emits one DirectionCall
per configured tenor and one ShapeCall per configured spread. The rendered
markdown is stored under ``trader_investment_plan`` — the same state key the
equity trader writes — so downstream plumbing works unchanged.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage

from fixedincomeagent.agents.schemas import TraderDecision, render_trader_decision
from fixedincomeagent.agents.utils.agent_utils import get_language_instruction
from fixedincomeagent.agents.utils.structured import (
    NO_EXTERNAL_TOOLS,
    bind_structured,
    invoke_structured_or_freetext,
)
from fixedincomeagent.dataflows.config import get_config


def create_fi_trader(llm):
    structured_llm = bind_structured(llm, TraderDecision, "FI Trader")

    def fi_trader_node(state) -> dict:
        direction_outlook = state["direction_debate_state"]["judge_decision"]
        shape_outlook = state["shape_debate_state"]["judge_decision"]
        config = get_config()
        tenors = ", ".join(config.get("fi_tenors", []))
        spreads = ", ".join(config.get("fi_spreads", []))
        # The report is empty when the curve technicals analyst was not
        # selected; only offer it (and the grounding instruction) when it has
        # content — mirrors the equity trader's market-report handling.
        technicals = (state.get("curve_technicals_report") or "").strip()

        if technicals:
            grounding = (
                "Ground concrete yield and spread levels in the curve "
                "technicals report's current levels, momentum, and "
                "support/resistance, and use the managers' outlooks for "
                "direction and shape conviction. "
            )
            technicals_section = f"**Curve Technicals Report:**\n{technicals}\n\n"
        else:
            grounding = ""
            technicals_section = ""

        prompt = f"""As the Fixed-Income Trader, your role is to turn the research team's direction and shape outlooks into the desk's concrete US Treasury yield-curve calls.

Produce exactly one direction call for each configured tenor: {tenors}.
Produce exactly one shape call for each configured spread/butterfly: {spreads}.

{grounding}Reconcile the two outlooks where they conflict and state explicitly when you defer to one over the other. Do not manufacture conviction: keep confidence low when the outlooks disagree or the evidence is thin.

---

**Direction Outlook (Direction Research Manager):**
{direction_outlook}

**Shape Outlook (Shape Research Manager):**
{shape_outlook}

{technicals_section}{NO_EXTERNAL_TOOLS}""" + get_language_instruction()

        plan = invoke_structured_or_freetext(
            structured_llm,
            llm,
            prompt,
            render_trader_decision,
            "FI Trader",
        )

        return {
            "messages": [AIMessage(content=plan)],
            "trader_investment_plan": plan,
            "sender": "FI Trader",
        }

    return fi_trader_node
