from fixedincomeagent.default_config import DEFAULT_CONFIG


def test_fi_tenors_present():
    assert "fi_tenors" in DEFAULT_CONFIG
    assert DEFAULT_CONFIG["fi_tenors"] == ["2Y", "5Y", "10Y", "30Y"]

def test_fi_spreads_present():
    assert "fi_spreads" in DEFAULT_CONFIG
    assert "2s10s" in DEFAULT_CONFIG["fi_spreads"]
    assert "5s30s" in DEFAULT_CONFIG["fi_spreads"]
    assert "2s5s10s_fly" in DEFAULT_CONFIG["fi_spreads"]

def test_fi_horizon_days():
    assert DEFAULT_CONFIG["fi_horizon_days"] == 20

def test_fi_neutral_threshold_bp():
    assert DEFAULT_CONFIG["fi_neutral_threshold_bp"] == 5
    # Document: moves < this threshold are classified "neutral"

def test_fi_prompt_and_backtest_config_pairs_stay_linked():
    # Prompts read fi_tenors/fi_spreads; the backtest reads
    # fi_tenor_series/fi_spread_definitions. Drift between the pairs silently
    # degrades scoring (spreads skipped, not missed) — keep them in lockstep.
    assert set(DEFAULT_CONFIG["fi_tenors"]) == set(DEFAULT_CONFIG["fi_tenor_series"])
    assert list(DEFAULT_CONFIG["fi_spreads"]) == list(DEFAULT_CONFIG["fi_spread_definitions"])
