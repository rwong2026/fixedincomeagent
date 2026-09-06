"""Report parity: the shared writer produces the report tree for the CLI and the
programmatic API alike (#1037)."""

from types import SimpleNamespace

import pytest

from fixedincomeagent.graph.trading_graph import TradingAgentsGraph
from fixedincomeagent.reporting import write_report_tree


def _state():
    return {
        "market_report": "MKT",
        "news_report": "NEWS",
        "investment_debate_state": {"judge_decision": "RM PLAN"},
        "trader_investment_plan": "TRADE",
        "risk_debate_state": {"judge_decision": "PM DECISION"},
    }


@pytest.mark.unit
def test_write_report_tree_creates_files(tmp_path):
    out = write_report_tree(_state(), "AAPL", tmp_path)
    assert out.name == "complete_report.md"
    assert (tmp_path / "1_analysts" / "market.md").read_text() == "MKT"
    assert (tmp_path / "1_analysts" / "news.md").read_text() == "NEWS"
    assert (tmp_path / "2_research" / "manager.md").read_text() == "RM PLAN"
    assert (tmp_path / "3_trading" / "trader.md").read_text() == "TRADE"
    assert (tmp_path / "5_portfolio" / "decision.md").read_text() == "PM DECISION"
    complete = out.read_text()
    assert "Trading Analysis Report: AAPL" in complete
    assert "MKT" in complete and "PM DECISION" in complete


@pytest.mark.unit
def test_save_reports_explicit_path(tmp_path):
    # Unbound: with an explicit save_path, the method doesn't touch self/config.
    out = TradingAgentsGraph.save_reports(None, _state(), "AAPL", save_path=tmp_path)
    assert (tmp_path / "complete_report.md").exists()
    assert out == tmp_path / "complete_report.md"


@pytest.mark.unit
def test_save_reports_defaults_under_results_dir(tmp_path):
    mock_self = SimpleNamespace(config={"results_dir": str(tmp_path)})
    out = TradingAgentsGraph.save_reports(mock_self, _state(), "AAPL")
    assert out.exists()
    assert out.parent.parent.name == "reports"  # results_dir/reports/AAPL_<stamp>/...
    assert out.parent.name.startswith("AAPL_")


@pytest.mark.unit
def test_cli_save_report_to_disk(tmp_path):
    from cli.main import save_report_to_disk

    out = save_report_to_disk(_state(), "10Y", tmp_path / "10Y_auto")
    assert out.exists()
    assert out.name == "complete_report.md"


@pytest.mark.unit
def test_run_analysis_autosaves_without_prompt(monkeypatch, tmp_path):
    from unittest.mock import MagicMock
    import cli.main as m

    monkeypatch.setattr(
        m,
        "get_user_selections",
        lambda: {
            "ticker": "10Y",
            "asset_type": "treasury",
            "analysis_date": "2026-09-06",
            "analysts": [MagicMock(value="macro_policy")],
            "research_depth": 1,
            "llm_provider": "openai",
            "backend_url": None,
            "shallow_thinker": "dummy",
            "deep_thinker": "dummy",
        },
    )

    class MockAnalysis:
        def __init__(self, *a, **k):
            pass

        def run_streaming(self, *a, **k):
            return [{"market_report": "MKT"}]

    monkeypatch.setattr(m, "FixedIncomeAnalysis", MockAnalysis)

    saved = []

    def mock_save(final_state, ticker, save_path):
        saved.append((ticker, save_path))
        return tmp_path / "complete_report.md"

    monkeypatch.setattr(m, "save_report_to_disk", mock_save)

    prompts = []

    def mock_prompt(text, default=""):
        prompts.append(text)
        return "N"

    monkeypatch.setattr(m.typer, "prompt", mock_prompt)
    monkeypatch.setattr(m, "Live", MagicMock())

    m.run_analysis(checkpoint=False)

    # Save happened automatically
    assert len(saved) == 1
    assert saved[0][0] == "10Y"
    assert "10Y_" in str(saved[0][1])

    # "Save report?" prompt was NOT called; only "Display full report on screen?" was prompted
    assert not any("Save report" in p for p in prompts)
    assert any("Display full report" in p for p in prompts)

