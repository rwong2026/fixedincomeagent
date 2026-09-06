"""Tests for the programmatic API (FixedIncomeAnalysis)."""

from unittest.mock import MagicMock, patch

import pytest

from fixedincomeagent.api import FixedIncomeAnalysis
from fixedincomeagent.graph.analyst_execution import FI_ANALYST_KEYS


@pytest.mark.unit
def test_api_defaults_to_fi_analysts():
    with patch("fixedincomeagent.api.TradingAgentsGraph"):
        api = FixedIncomeAnalysis()
        assert set(api.selected_analysts) == FI_ANALYST_KEYS


@pytest.mark.unit
def test_api_accepts_custom_analysts():
    with patch("fixedincomeagent.api.TradingAgentsGraph"):
        api = FixedIncomeAnalysis(analysts=["market", "news"])
        assert api.selected_analysts == ("market", "news")


@pytest.mark.unit
def test_api_run():
    mock_state = {"macro_policy_report": "POLICY", "final_trade_decision": "DECISION"}
    mock_signal = "HOLD"

    with patch("fixedincomeagent.api.TradingAgentsGraph") as mock_graph_cls:
        instance = mock_graph_cls.return_value
        instance.propagate.return_value = (mock_state, mock_signal)

        api = FixedIncomeAnalysis()
        result = api.run("UST", "2026-09-04")

        instance.propagate.assert_called_once_with("UST", "2026-09-04", asset_type="stock")
        assert result["macro_policy_report"] == "POLICY"
        assert result["final_trade_decision"] == "DECISION"
        assert result["signal"] == "HOLD"


@pytest.mark.unit
def test_api_run_streaming():
    with patch("fixedincomeagent.api.TradingAgentsGraph") as mock_graph_cls:
        instance = mock_graph_cls.return_value
        instance.resolve_instrument_context.return_value = "UST_CTX"
        instance.propagator.create_initial_state.return_value = {"company_of_interest": "UST"}
        instance.propagator.get_graph_args.return_value = {}
        instance.begin_checkpoint.return_value = "tid_123"
        instance.checkpoint_input.return_value = {"company_of_interest": "UST"}

        chunk1 = {"messages": [MagicMock(content="hello", id="1")]}
        chunk2 = {"direction_debate_state": {"judge_decision": "HIGHER"}}
        instance.graph.stream.return_value = [chunk1, chunk2]

        api = FixedIncomeAnalysis()
        chunks = list(api.run_streaming("UST", "2026-09-04"))

        assert len(chunks) == 2
        assert chunks[0] == chunk1
        assert chunks[1] == chunk2
        instance.clear_checkpoint_on_success.assert_called_once_with("UST", "2026-09-04", "stock")
        instance.end_checkpoint.assert_called_once()


@pytest.mark.unit
def test_api_save_reports(tmp_path):
    with patch("fixedincomeagent.api.TradingAgentsGraph") as mock_graph_cls:
        instance = mock_graph_cls.return_value
        instance.save_reports.return_value = tmp_path / "complete_report.md"

        api = FixedIncomeAnalysis()
        path = api.save_reports({"final_trade_decision": "DECISION"}, "UST", save_path=tmp_path)
        instance.save_reports.assert_called_once_with({"final_trade_decision": "DECISION"}, "UST", save_path=tmp_path)
        assert path == tmp_path / "complete_report.md"
