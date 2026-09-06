"""Unit tests for TradingAgentsGraph FI reflection and benchmark integration."""

from unittest.mock import MagicMock, patch

import pytest

from fixedincomeagent.agents.utils.memory import TradingMemoryLog
from fixedincomeagent.graph.trading_graph import TradingAgentsGraph


@pytest.fixture(autouse=True)
def mock_trading_graph_llm():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "FI Reflection: curve steepening played out."
    client = MagicMock()
    client.get_llm.return_value = mock_llm
    with patch("fixedincomeagent.graph.trading_graph.create_llm_client", return_value=client):
        yield mock_llm


@pytest.fixture
def memory_log(tmp_path):
    log_file = tmp_path / "trading_memory.md"
    return TradingMemoryLog({"memory_log_path": str(log_file)})


def test_fi_mode_property():
    fi_graph = TradingAgentsGraph(
        selected_analysts=["macro_policy", "curve_technicals"],
    )
    assert fi_graph.fi_mode is True

    equity_graph = TradingAgentsGraph(
        selected_analysts=["market", "news"],
    )
    assert equity_graph.fi_mode is False


def test_resolve_pending_entries_fi_mode(memory_log):
    # Seed a pending entry for UST
    decision_text = (
        "## Direction Calls\n\n"
        "**2Y**: up (<10bp)\n"
        "**5Y**: down (10-25bp)\n"
        "**10Y**: neutral (<10bp)\n"
        "**30Y**: up (25bp+)\n"
    )
    memory_log.store_decision("UST", "2026-09-01", decision_text)

    graph = TradingAgentsGraph(
        selected_analysts=["macro_policy", "curve_technicals"],
        config={"memory_log_path": str(memory_log._log_path), "fi_horizon_days": 5},
    )

    mock_benchmark_res = {
        "trade_date": "2026-09-01",
        "resolution_date": "2026-09-09",
        "holding_days": 5,
        "tenor_changes": {
            "2Y": {"delta_bp": 15.0},
            "5Y": {"delta_bp": -8.0},
            "10Y": {"delta_bp": 3.0},
            "30Y": {"delta_bp": -2.0},
        },
        "benchmark_bp": 2.0,
        "strategy_bp": 5.25,
        "alpha_bp": 3.25,
        "hit_rate": "hit:3/4",
        "hits": {"2Y": True, "5Y": True, "10Y": True, "30Y": False},
    }

    with patch(
        "fixedincomeagent.graph.trading_graph.calculate_treasury_curve_benchmark",
        return_value=mock_benchmark_res,
    ) as mock_calc:
        graph._resolve_pending_entries("UST")
        mock_calc.assert_called_once()

    entries = memory_log.load_entries()
    assert len(entries) == 1
    entry = entries[0]
    assert entry["pending"] is False
    assert entry["raw"] == "hit:3/4"
    assert entry["alpha"] == "+3.2bp"
    assert entry["resolved"] == "2026-09-09"
    assert "FI Reflection: curve steepening played out." in entry["reflection"]


def test_resolve_pending_entries_equity_mode_preserved(memory_log):
    memory_log.store_decision("AAPL", "2026-09-01", "Rating: Buy\nApple growth.")

    graph = TradingAgentsGraph(
        selected_analysts=["market", "news"],
        config={"memory_log_path": str(memory_log._log_path)},
    )

    with patch.object(
        graph,
        "_fetch_returns",
        return_value=(0.04, 0.015, 5, "2026-09-08"),
    ) as mock_fetch, patch.object(
        graph.reflector,
        "reflect_on_final_decision",
        return_value="Equity Reflection: AAPL outperformed.",
    ) as mock_reflect:
        graph._resolve_pending_entries("AAPL")
        mock_fetch.assert_called_once()
        mock_reflect.assert_called_once()

    entries = memory_log.load_entries()
    assert len(entries) == 1
    entry = entries[0]
    assert entry["pending"] is False
    assert entry["raw"] == "+4.0%"
    assert entry["alpha"] == "+1.5%"
    assert entry["resolved"] == "2026-09-08"
