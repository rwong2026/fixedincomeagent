from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from fixedincomeagent.agents.utils.agent_utils import (
    get_fred_series,
    get_language_instruction,
    get_treasury_par_yields,
)
from fixedincomeagent.dataflows.config import get_config


def _configured_spread_text() -> str:
    """Describe the configured spread set so the prompt tracks config."""
    cfg = get_config()
    definitions = cfg.get("fi_spread_definitions", {})
    parts = []
    for name, legs in definitions.items():
        if len(legs) == 2:
            parts.append(f"{name} ({legs[0]} vs {legs[1]})")
        else:
            belly = legs[1]
            wings = f"{legs[0]}/{legs[2]}"
            parts.append(f"{name} butterfly (2x{belly} minus {wings} wings)")
    return ", ".join(parts)


def create_curve_technicals_analyst(llm):
    spread_text = _configured_spread_text()
    tenors = ", ".join(get_config().get("fi_tenors", []))

    def curve_technicals_analyst_node(state):
        current_date = state["trade_date"]

        tools = [
            get_fred_series,
            get_treasury_par_yields,
        ]

        system_message = (
            "You are a curve-technicals analyst covering the US Treasury "
            "yield curve. Your job is to describe WHERE the curve sits and "
            "HOW it is moving, not why. Use the available tools to gather "
            "evidence: get_treasury_par_yields(curr_date, look_back_days) "
            "for the full daily par curve, and get_fred_series(indicator, "
            "curr_date, look_back_days) for individual constant-maturity "
            f"tenors ({tenors}) when you need a longer history than the par "
            "yield tool provides."
            " Analyze the configured spread set: "
            f"{spread_text}."
            " Structure your final report as markdown with these sections, in "
            "order: (1) **Curve Shape** — current level of each configured "
            "spread in bp, and whether the curve is upward-sloping, flat, or "
            "inverted at each segment; (2) **Historical Percentiles** — the "
            "approximate historical percentile of each key spread (2s10s, "
            "5s30s, and the butterfly) over the look-back window, flagging "
            "anything beyond the 10th/90th percentile; (3) **Momentum** — is "
            "the curve steepening or flattening on trend, and is the move "
            "accelerating or fading; (4) **Rate-of-Change** — the 1-week, "
            "1-month, and 3-month change in yield at each configured tenor, "
            "identifying which tenor is leading the move; (5) **Distance "
            "from Extremes** — how far each configured tenor sits from its "
            "recent highs/lows over the window, in bp; (6) **Overall "
            "Summary** — written LAST, synthesizing the sections above."
            " Report levels in basis points and round to whole bp. Distinguish "
            "bear-steepening from bull-steepening (and bear- vs "
            "bull-flattening) by whether yields are rising or falling as the "
            "curve moves — the direction of rates matters as much as the "
            "slope."
            + get_language_instruction()
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}."
                    " Today's date is {current_date}; treat it as 'now' for all analysis and tool-call date ranges.\n"
                    "{system_message}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "curve_technicals_report": report,
        }

    return curve_technicals_analyst_node
