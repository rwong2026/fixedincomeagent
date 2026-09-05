from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from fixedincomeagent.agents.utils.agent_utils import (
    get_cot_data,
    get_fed_speeches,
    get_fomc_calendar,
    get_language_instruction,
)


def create_fed_speak_analyst(llm):
    def fed_speak_analyst_node(state):
        current_date = state["trade_date"]

        tools = [
            get_fed_speeches,
            get_fomc_calendar,
            get_cot_data,
        ]

        system_message = (
            "You are a Fed-communication analyst. Your job is to read Federal "
            "Reserve communication and rates-market positioning, and turn it "
            "into a call on the likely policy path. Use the available tools "
            "to gather evidence: get_fed_speeches(curr_date, look_back_days) "
            "for recent speeches and testimony by FOMC members, "
            "get_fomc_calendar(curr_date) for recent and upcoming meetings "
            "and decisions, and get_cot_data(curr_date, contract) for CFTC "
            "Commitments of Traders positioning in Treasury futures."
            " Structure your final report as markdown with these sections, in "
            "order: (1) **Communication Sentiment** — classify each recent "
            "speaker as hawkish, dovish, or neutral, weighted by their role "
            "(Chair, Vice Chair, and Board members carry more weight than "
            "regional presidents), and give the net tone; (2) **Tone "
            "Shift** — is the aggregate tone turning more hawkish or more "
            "dovish versus the prior weeks, and which speakers drove the "
            "shift; (3) **Positioning** — what COT data shows about speculator "
            "and asset-manager positioning in Treasury futures: crowded "
            "longs or shorts, and whether positioning is stretched versus "
            "its recent range; (4) **Policy-Path Expectations** — the "
            "consensus expectation for the next FOMC decisions (hold / cut / "
            "hike, and timing), anchored to the meeting calendar, and "
            "whether recent communication supports or pushes back against "
            "that consensus; (5) **Overall Summary** — written LAST, "
            "synthesizing the sections above."
            " Distinguish between a single outlier speaker and a genuine "
            "committee-wide shift; never let one speech dominate the call. "
            "Positioning is a contrarian signal at extremes — say so "
            "explicitly when it is stretched."
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
            "fed_speak_report": report,
        }

    return fed_speak_analyst_node
