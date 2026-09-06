import json
from pathlib import Path

import pytest

from fixedincomeagent.graph.trading_graph import TradingAgentsGraph


@pytest.mark.unit
def test_fi_state_logging(tmp_path: Path):
    """Verify fixed-income state keys are persisted in run logs without KeyError."""
    g = object.__new__(TradingAgentsGraph)
    g.config = {"results_dir": str(tmp_path)}
    g.ticker = "UST"
    g.log_states_dict = {}

    mock_state = {
        "company_of_interest": "UST",
        "trade_date": "2026-09-04",
        "macro_policy_report": "Mock macro report",
        "curve_technicals_report": "Mock curve report",
        "fed_speak_report": "Mock fed report",
        "macro_calendar_report": "Mock calendar report",
        "direction_debate_state": {
            "higher_yields_history": "High yields arg",
            "lower_yields_history": "Low yields arg",
            "history": "Direction history",
            "judge_decision": "Direction judge",
        },
        "shape_debate_state": {
            "steepener_history": "Steepener arg",
            "flattener_history": "Flattener arg",
            "history": "Shape history",
            "judge_decision": "Shape judge",
        },
        "trader_investment_plan": "Mock FI trader plan",
        "investment_plan": "Mock FI PM plan",
        "final_trade_decision": "Mock final decision",
    }

    g._log_state("2026-09-04", mock_state)

    log_file = tmp_path / "UST" / "FixedIncomeAgentStrategy_logs" / "full_states_log_2026-09-04.json"
    assert log_file.exists()

    with open(log_file, encoding="utf-8") as f:
        saved_data = json.load(f)

    assert saved_data["company_of_interest"] == "UST"
    assert saved_data["trade_date"] == "2026-09-04"
    assert saved_data["macro_policy_report"] == "Mock macro report"
    assert saved_data["curve_technicals_report"] == "Mock curve report"
    assert saved_data["fed_speak_report"] == "Mock fed report"
    assert saved_data["macro_calendar_report"] == "Mock calendar report"
    assert saved_data["direction_debate_state"]["judge_decision"] == "Direction judge"
    assert saved_data["shape_debate_state"]["judge_decision"] == "Shape judge"
    assert saved_data["trader_investment_decision"] == "Mock FI trader plan"
    assert saved_data["final_trade_decision"] == "Mock final decision"
    assert saved_data["investment_plan"] == "Mock FI PM plan"


@pytest.mark.unit
def test_equity_state_logging(tmp_path: Path):
    """Verify equity mode states continue to log correctly."""
    g = object.__new__(TradingAgentsGraph)
    g.config = {"results_dir": str(tmp_path)}
    g.ticker = "AAPL"
    g.log_states_dict = {}

    mock_state = {
        "company_of_interest": "AAPL",
        "trade_date": "2026-09-04",
        "market_report": "Mock market report",
        "sentiment_report": "Mock sentiment report",
        "news_report": "Mock news report",
        "fundamentals_report": "Mock fundamentals report",
        "investment_debate_state": {
            "bull_history": "Bull speech",
            "bear_history": "Bear speech",
            "history": "Debate history",
            "current_response": "Response",
            "judge_decision": "Bullish",
        },
        "risk_debate_state": {
            "aggressive_history": "Aggressive speech",
            "conservative_history": "Conservative speech",
            "neutral_history": "Neutral speech",
            "history": "Risk history",
            "judge_decision": "Low risk",
        },
        "trader_investment_plan": "Mock equity trader plan",
        "investment_plan": "Mock equity PM plan",
        "final_trade_decision": "Mock final trade decision",
    }

    g._log_state("2026-09-04", mock_state)

    log_file = tmp_path / "AAPL" / "FixedIncomeAgentStrategy_logs" / "full_states_log_2026-09-04.json"
    assert log_file.exists()

    with open(log_file, encoding="utf-8") as f:
        saved_data = json.load(f)

    assert saved_data["company_of_interest"] == "AAPL"
    assert saved_data["market_report"] == "Mock market report"
    assert saved_data["sentiment_report"] == "Mock sentiment report"
    assert saved_data["investment_debate_state"]["judge_decision"] == "Bullish"
    assert saved_data["risk_debate_state"]["judge_decision"] == "Low risk"
    assert saved_data["trader_investment_decision"] == "Mock equity trader plan"
    assert saved_data["final_trade_decision"] == "Mock final trade decision"
