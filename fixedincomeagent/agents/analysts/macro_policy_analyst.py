from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from fixedincomeagent.agents.utils.agent_utils import (
    get_alfred_vintage,
    get_consumer_inflation_expectations,
    get_fed_speeches,
    get_fomc_calendar,
    get_fred_series,
    get_inflation_breakevens,
    get_inflation_nowcast,
    get_ism_prices_paid,
    get_language_instruction,
    get_shelter_rents,
    get_supply_chain_pressure,
    get_used_vehicle_index,
)


def create_macro_policy_analyst(llm, disabled_tools=None):
    def macro_policy_analyst_node(state):
        current_date = state["trade_date"]

        tools = [
            get_fred_series,
            get_alfred_vintage,
            get_inflation_breakevens,
            get_inflation_nowcast,
            get_shelter_rents,
            get_used_vehicle_index,
            get_supply_chain_pressure,
            get_ism_prices_paid,
            get_consumer_inflation_expectations,
            get_fomc_calendar,
            get_fed_speeches,
        ]
        if disabled_tools:
            tools = [t for t in tools if t.name not in disabled_tools]

        system_message = (
            "You are a macro and monetary-policy analyst covering US inflation "
            "dynamics and the Federal Reserve's likely policy path — the primary "
            "driver of the Treasury rates and curve outlook. Use the available "
            "tools to gather evidence: get_fred_series(indicator, curr_date, "
            "look_back_days) for inflation, labor, and rates series (e.g. 'cpi', "
            "'core_pce', 'unemployment', 'fed_funds_rate'), "
            "get_alfred_vintage(series_id, vintage_date) for point-in-time data "
            "as it was known on a given day (no revision lookahead), "
            "get_inflation_nowcast(curr_date) for the Cleveland Fed inflation "
            "nowcast, get_shelter_rents(curr_date) for market-rent trends that "
            "lead CPI shelter, get_used_vehicle_index(curr_date) for goods "
            "price pressure, get_supply_chain_pressure(curr_date) and "
            "get_ism_prices_paid(curr_date) for pipeline price pressure, "
            "get_inflation_breakevens(curr_date, look_back_days) for 5Y/10Y "
            "breakevens and the 5Y5Y forward, "
            "get_consumer_inflation_expectations(curr_date) for NY Fed SCE "
            "survey expectations, and get_fomc_calendar(curr_date) plus "
            "get_fed_speeches(curr_date, look_back_days) for the policy "
            "calendar and Fed communication."
            " Structure your final report as markdown with these sections, in "
            "order: (1) **Shelter Trajectory** — direction (accelerating / "
            "decelerating / stable), confidence (low / medium / high), and the "
            "specific data points behind the call; (2) **Energy & Supply-Chain "
            "Trajectory** — same fields; (3) **Services & Wage Trajectory** — "
            "same fields; (4) **Market-Implied Expectations** — 5Y breakeven, "
            "10Y breakeven, and 5Y5Y forward, each with its recent trend and "
            "the risk-premium caveat; (5) **Survey Expectations** — NY Fed SCE "
            "1-year and 3-year medians (5-year if available); (6) "
            "**Divergence Flag** — explicit callout when components disagree; "
            "(7) **Fed Policy Assessment** — current stance and likely path, "
            "grounded in the FOMC calendar and recent speeches; (8) **Overall "
            "Summary** — written LAST, synthesizing the sections above rather "
            "than replacing them."
            " Do not average these signals into a single inflation call. "
            "Identify which components are diverging and explain the mechanism. "
            "If shelter and services point in different directions, say so "
            "explicitly rather than netting them out. Breakevens reflect "
            "market-implied expectations but also carry liquidity and "
            "inflation-risk premia — never present them as a pure expectations "
            "reading."
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
            "macro_policy_report": report,
        }

    return macro_policy_analyst_node
