"""Unit tests for Fixed Income reflection and memory log updates."""

from unittest.mock import MagicMock

import pytest

from fixedincomeagent.agents.utils.memory import TradingMemoryLog
from fixedincomeagent.graph.reflection import Reflector

_SEP = TradingMemoryLog._SEPARATOR


@pytest.fixture
def memory_log(tmp_path):
    log_file = tmp_path / "trading_memory.md"
    return TradingMemoryLog({"memory_log_path": str(log_file)})


# ---------------------------------------------------------------------------
# Reflection tests
# ---------------------------------------------------------------------------

def test_reflect_on_fi_decision():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = (
        "Directional calls on the front and belly were accurate as front-end yields rose. "
        "The short 30Y thesis underperformed due to duration bid. Next time hedge long-end "
        "supply concessions with flight-to-safety signals."
    )

    reflector = Reflector(mock_llm)
    final_decision = (
        "## Direction Calls\n\n"
        "**2Y**: up (<10bp)\n"
        "**5Y**: down (10-25bp)\n"
        "**10Y**: neutral (<10bp)\n"
        "**30Y**: up (25bp+)\n"
    )
    tenor_changes = {
        "2Y": {"delta_bp": 15.0},
        "5Y": {"delta_bp": -8.0},
        "10Y": {"delta_bp": 3.0},
        "30Y": {"delta_bp": -2.0},
    }

    reflection = reflector.reflect_on_fi_decision(
        final_decision=final_decision,
        benchmark_bp=2.0,
        hit_rate="hit:3/4",
        tenor_changes=tenor_changes,
        alpha_bp=3.25,
    )

    assert "Directional calls on the front and belly" in reflection
    mock_llm.invoke.assert_called_once()
    messages = mock_llm.invoke.call_args[0][0]
    system_msg = messages[0][1]
    human_msg = messages[1][1]

    # Verify prompt contents
    assert "Treasury yield-curve decision" in system_msg
    assert "Hit rate: hit:3/4" in human_msg
    assert "Equal-weight curve benchmark yield change: +2.0bp" in human_msg
    assert "Alpha vs benchmark: +3.2bp" in human_msg
    assert "2Y: +15.0bp" in human_msg
    assert "5Y: -8.0bp" in human_msg
    assert "Final Decision:" in human_msg


def test_equity_reflection_remains_intact():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "Thesis held as SPY underperformed."

    reflector = Reflector(mock_llm)
    res = reflector.reflect_on_final_decision(
        final_decision="Rating: Buy\nEntry at $180",
        raw_return=0.05,
        alpha_return=0.02,
        benchmark_name="SPY",
    )
    assert res == "Thesis held as SPY underperformed."
    messages = mock_llm.invoke.call_args[0][0]
    human_msg = messages[1][1]
    assert "Raw return: +5.0%" in human_msg
    assert "Alpha vs SPY: +2.0%" in human_msg


# ---------------------------------------------------------------------------
# Memory Log tests
# ---------------------------------------------------------------------------

def test_memory_log_update_with_fi_outcome(memory_log):
    memory_log.store_decision(
        ticker="UST",
        trade_date="2026-09-01",
        final_trade_decision="## Direction Calls\n**2Y**: up\n",
    )

    pending = memory_log.get_pending_entries()
    assert len(pending) == 1
    assert pending[0]["ticker"] == "UST"

    memory_log.update_with_outcome(
        ticker="UST",
        trade_date="2026-09-01",
        raw_return="hit:3/4",
        alpha_return="+3.2bp",
        holding_days=5,
        reflection="Good front-end call.",
        resolution_date="2026-09-09",
    )

    resolved = memory_log.load_entries()
    assert len(resolved) == 1
    entry = resolved[0]
    assert entry["ticker"] == "UST"
    assert entry["pending"] is False
    assert entry["raw"] == "hit:3/4"
    assert entry["alpha"] == "+3.2bp"
    assert entry["holding"] == "5d"
    assert entry["resolved"] == "2026-09-09"
    assert "Good front-end call." in entry["reflection"]


def test_memory_log_batch_update_with_fi_outcomes(memory_log):
    memory_log.store_decision(
        ticker="UST",
        trade_date="2026-09-01",
        final_trade_decision="## Direction Calls\n**10Y**: up\n",
    )
    memory_log.store_decision(
        ticker="AAPL",
        trade_date="2026-09-01",
        final_trade_decision="Rating: Buy\nApple growth.",
    )

    updates = [
        {
            "ticker": "UST",
            "trade_date": "2026-09-01",
            "raw_return": "hit:4/4",
            "alpha_return": "+5.0bp",
            "holding_days": 5,
            "reflection": "Flawless curve positioning.",
            "resolution_date": "2026-09-09",
        },
        {
            "ticker": "AAPL",
            "trade_date": "2026-09-01",
            "raw_return": 0.04,
            "alpha_return": 0.015,
            "holding_days": 5,
            "reflection": "iPhone sales exceeded forecast.",
            "resolution_date": "2026-09-08",
        },
    ]

    memory_log.batch_update_with_outcomes(updates)
    entries = memory_log.load_entries()
    assert len(entries) == 2

    ust_entry = next(e for e in entries if e["ticker"] == "UST")
    aapl_entry = next(e for e in entries if e["ticker"] == "AAPL")

    assert ust_entry["raw"] == "hit:4/4"
    assert ust_entry["alpha"] == "+5.0bp"
    assert ust_entry["holding"] == "5d"

    assert aapl_entry["raw"] == "+4.0%"
    assert aapl_entry["alpha"] == "+1.5%"
    assert aapl_entry["holding"] == "5d"
