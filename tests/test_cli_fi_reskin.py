"""Tests for FI CLI re-skinning and dual-track support in CLI."""

from unittest.mock import patch

import pytest

from cli.main import MessageBuffer, update_analyst_statuses
from cli.models import AnalystType
from cli.utils import ANALYST_ORDER, get_ticker
from fixedincomeagent.reporting import write_report_tree


@pytest.mark.unit
def test_analyst_type_enum_has_fi_analysts():
    assert AnalystType.MACRO_POLICY.value == "macro_policy"
    assert AnalystType.CURVE_TECHNICALS.value == "curve_technicals"
    assert AnalystType.FED_SPEAK.value == "fed_speak"
    assert AnalystType.MACRO_CALENDAR.value == "macro_calendar"

    # Equity analysts still preserved
    assert AnalystType.MARKET.value == "market"
    assert AnalystType.SOCIAL.value == "social"
    assert AnalystType.NEWS.value == "news"
    assert AnalystType.FUNDAMENTALS.value == "fundamentals"


@pytest.mark.unit
def test_analyst_order_defaults_to_fi_first():
    fi_types = [
        AnalystType.MACRO_POLICY,
        AnalystType.CURVE_TECHNICALS,
        AnalystType.FED_SPEAK,
        AnalystType.MACRO_CALENDAR,
    ]
    order_types = [atype for _, atype in ANALYST_ORDER[:4]]
    assert order_types == fi_types


@pytest.mark.unit
def test_get_ticker_defaults_to_ust():
    with patch("questionary.text") as mock_text:
        mock_text.return_value.ask.return_value = ""
        assert get_ticker() == "UST"

    with patch("questionary.text") as mock_text:
        mock_text.return_value.ask.return_value = "   "
        assert get_ticker() == "UST"

    with patch("questionary.text") as mock_text:
        mock_text.return_value.ask.return_value = "10Y"
        assert get_ticker() == "10Y"


@pytest.mark.unit
def test_message_buffer_fi_mode():
    mb = MessageBuffer()
    mb.init_for_analysis(["macro_policy", "curve_technicals", "fed_speak", "macro_calendar"])

    # FI debaters and traders present
    assert "Higher Yields Researcher" in mb.agent_status
    assert "Direction Research Manager" in mb.agent_status
    assert "Steepener Researcher" in mb.agent_status
    assert "Shape Research Manager" in mb.agent_status
    assert "FI Trader" in mb.agent_status
    assert "FI Portfolio Manager" in mb.agent_status

    # Equity agents NOT in agent_status
    assert "Bull Researcher" not in mb.agent_status
    assert "Bear Researcher" not in mb.agent_status
    assert "Trader" not in mb.agent_status

    # FI report sections present
    assert "macro_policy_report" in mb.report_sections
    assert "direction_debate_state" in mb.report_sections
    assert "shape_debate_state" in mb.report_sections
    assert "final_trade_decision" in mb.report_sections


@pytest.mark.unit
def test_message_buffer_equity_mode():
    mb = MessageBuffer()
    mb.init_for_analysis(["market", "news"])

    # Equity debaters and traders present
    assert "Bull Researcher" in mb.agent_status
    assert "Bear Researcher" in mb.agent_status
    assert "Trader" in mb.agent_status
    assert "Portfolio Manager" in mb.agent_status

    # FI debaters NOT in agent_status
    assert "Higher Yields Researcher" not in mb.agent_status
    assert "FI Trader" not in mb.agent_status
    assert "FI Portfolio Manager" not in mb.agent_status

    # Equity report sections present
    assert "market_report" in mb.report_sections
    assert "news_report" in mb.report_sections
    assert "macro_policy_report" not in mb.report_sections


@pytest.mark.unit
def test_update_analyst_statuses_fi_transition():
    mb = MessageBuffer()
    mb.init_for_analysis(["macro_policy"])
    assert mb.agent_status["Macro Policy Analyst"] == "pending"
    assert mb.agent_status["Higher Yields Researcher"] == "pending"

    update_analyst_statuses(mb, {"macro_policy_report": "Inflation is trending down."})
    assert mb.agent_status["Macro Policy Analyst"] == "completed"
    assert mb.agent_status["Higher Yields Researcher"] == "in_progress"


@pytest.mark.unit
def test_write_report_tree_fi(tmp_path):
    state = {
        "macro_policy_report": "FED POLICY OUTLOOK",
        "curve_technicals_report": "CURVE STEEPENING OBSERVED",
        "direction_debate_state": {
            "higher_yields_history": "HY ARG",
            "lower_yields_history": "LY ARG",
            "judge_decision": "DIR DECISION",
        },
        "shape_debate_state": {
            "steepener_history": "STEEP ARG",
            "flattener_history": "FLAT ARG",
            "judge_decision": "SHAPE DECISION",
        },
        "trader_investment_plan": "FI TRADE PLAN",
        "final_trade_decision": "FI PM ALLOCATION",
    }
    out = write_report_tree(state, "UST", tmp_path)
    assert out.name == "complete_report.md"
    assert (tmp_path / "1_analysts" / "macro_policy.md").read_text() == "FED POLICY OUTLOOK"
    assert (tmp_path / "1_analysts" / "curve_technicals.md").read_text() == "CURVE STEEPENING OBSERVED"
    assert (tmp_path / "2_research" / "direction_manager.md").read_text() == "DIR DECISION"
    assert (tmp_path / "2_research" / "shape_manager.md").read_text() == "SHAPE DECISION"
    assert (tmp_path / "3_trading" / "trader.md").read_text() == "FI TRADE PLAN"
    assert (tmp_path / "5_portfolio" / "decision.md").read_text() == "FI PM ALLOCATION"

    complete = out.read_text()
    assert "Trading Analysis Report: UST" in complete
    assert "FED POLICY OUTLOOK" in complete
    assert "FI PM ALLOCATION" in complete
