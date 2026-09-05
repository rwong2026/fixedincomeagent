from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from fixedincomeagent.agents.utils.agent_utils import (
    get_auction_results,
    get_fomc_calendar,
    get_fred_series,
    get_language_instruction,
)


def create_macro_calendar_analyst(llm):
    def macro_calendar_analyst_node(state):
        current_date = state["trade_date"]

        tools = [
            get_fomc_calendar,
            get_fred_series,
            get_auction_results,
        ]

        system_message = (
            "You are a macro-calendar analyst for US rates. Your job is to "
            "map the event risk ahead: data releases, Fed events, and "
            "Treasury supply. Use the available tools to gather evidence: "
            "get_fomc_calendar(curr_date) for recent and upcoming FOMC "
            "meetings, get_fred_series(indicator, curr_date, look_back_days) "
            "for recent macro releases (e.g. 'cpi', 'core_pce', "
            "'unemployment', 'real_gdp', 'nonfarm_payrolls'), and "
            "get_auction_results(curr_date, look_back_days) for recent "
            "Treasury auction outcomes."
            " Structure your final report as markdown with these sections, in "
            "order: (1) **Forward Calendar** — the key releases and events "
            "over the next two to four weeks (CPI, PPI, NFP / employment "
            "report, GDP, PCE, retail sales, FOMC meetings), each with its "
            "expected date where determinable; (2) **Consensus vs Prior** — "
            "for each key release, the market consensus expectation versus "
            "the prior print, flagging where a large gap implies event risk; "
            "(3) **Recent Surprises** — releases over the past month that "
            "surprised versus consensus, and the direction and rough size of "
            "the market impact (yields up/down, curve steeper/flatter); "
            "(4) **Treasury Supply** — recent auction results (bid-to-cover, "
            "tail) and what they signal about demand for upcoming supply; "
            "(5) **Event-Risk Summary** — written LAST, the two or three "
            "dates that matter most for the rates outlook and why."
            " Be explicit about uncertainty: where consensus is not directly "
            "observable from the tools, say so rather than inventing a "
            "number. Rank events by their likely rates impact — a CPI print "
            "into a live FOMC meeting outranks a routine auction."
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
            "macro_calendar_report": report,
        }

    return macro_calendar_analyst_node
