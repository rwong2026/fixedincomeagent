"""Regime test dates (Task 7.2): curated test-date set spanning regimes."""
from __future__ import annotations

from datetime import datetime

import pytest

from fixedincomeagent.backtest.regime_dates import REGIME_TEST_DATES, all_dates

_EXPECTED_REGIMES = {
    "2022_hiking",
    "2019_inversion",
    "2020_cut_cycle",
    "2024_2025_cutting",
}


@pytest.mark.unit
def test_four_named_regimes():
    assert set(REGIME_TEST_DATES) == _EXPECTED_REGIMES


@pytest.mark.unit
def test_each_regime_has_plausible_count():
    for regime, dates in REGIME_TEST_DATES.items():
        assert 4 <= len(dates) <= 8, f"{regime}: {len(dates)} dates"


@pytest.mark.unit
def test_dates_are_strict_iso_sorted_and_unique():
    for regime, dates in REGIME_TEST_DATES.items():
        parsed = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
        assert [p.strftime("%Y-%m-%d") for p in parsed] == dates  # strict ISO
        assert dates == sorted(dates), f"{regime} not sorted ascending"
        assert len(dates) == len(set(dates)), f"{regime} has duplicates"


@pytest.mark.unit
def test_dates_fall_inside_named_regime_window():
    for regime, dates in REGIME_TEST_DATES.items():
        year = int(regime[:4])
        for d in dates:
            assert year - 1 <= int(d[:4]) <= year + 1, f"{regime}: {d}"


@pytest.mark.unit
def test_spot_check_known_dates():
    assert "2022-03-01" in REGIME_TEST_DATES["2022_hiking"]
    assert "2019-08-01" in REGIME_TEST_DATES["2019_inversion"]
    assert "2020-04-01" in REGIME_TEST_DATES["2020_cut_cycle"]
    assert "2024-09-01" in REGIME_TEST_DATES["2024_2025_cutting"]


@pytest.mark.unit
def test_all_dates_flattened_sorted_unique():
    flat = all_dates()
    assert len(flat) == sum(len(v) for v in REGIME_TEST_DATES.values())
    assert flat == sorted(flat)
    assert len(flat) == len(set(flat))
    assert all(d in flat for dates in REGIME_TEST_DATES.values() for d in dates)
