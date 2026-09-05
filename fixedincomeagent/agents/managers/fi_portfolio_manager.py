"""Fixed-Income Portfolio Manager: final synthesis of the desk's curve calls.

Terminal node of the FI track. Consumes the consistency-checked FI trader
plan (``trader_investment_plan``, possibly annotated with CONSISTENCY
WARNINGs by the risk checker) plus the direction and shape research managers'
judge decisions, then confirms or adjusts each call, noting adjustments in
the affected rationale. Uses the same ``TraderDecision`` schema as the FI
trader so the final output keeps the DirectionCall[]/ShapeCall[] shape;
the rendered markdown is stored under ``final_trade_decision`` — the same
state key the equity portfolio manager writes — so propagate()'s logging,
memory, and signal path work unchanged for FI runs.
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


def create_fi_portfolio_manager(llm):
    structured_llm = bind_structured(llm, TraderDecision, "FI Portfolio Manager")

    def fi_portfolio_manager_node(state) -> dict:
        direction_outlook = state["direction_debate_state"]["judge_decision"]
        shape_outlook = state["shape_debate_state"]["judge_decision"]
        trader_plan = state["trader_investment_plan"]
        config = get_config()
        tenors = ", ".join(config.get("fi_tenors", []))
        spreads = ", ".join(config.get("fi_spreads", []))

        prompt = f"""As the Fixed-Income Portfolio Manager, deliver the desk's final US Treasury yield-curve calls.

Review the trader's per-tenor direction calls and per-spread shape calls below. The risk consistency checker may have attached CONSISTENCY WARNING notes flagging direction/shape contradictions. Confirm each call or adjust it; when you adjust, say so explicitly in the affected call's rationale. Do not silently drop a call: produce exactly one direction call for each configured tenor ({tenors}) and one shape call for each configured spread/butterfly ({spreads}).

---

**Trader's Calls (risk-checked):**
{trader_plan}

**Direction Outlook (Direction Research Manager):**
{direction_outlook}

**Shape Outlook (Shape Research Manager):**
{shape_outlook}

{NO_EXTERNAL_TOOLS}""" + get_language_instruction()

        final_decision = invoke_structured_or_freetext(
            structured_llm,
            llm,
            prompt,
            render_trader_decision,
            "FI Portfolio Manager",
        )

        return {
            "messages": [AIMessage(content=final_decision)],
            "final_trade_decision": final_decision,
            "sender": "FI Portfolio Manager",
        }

    return fi_portfolio_manager_node
