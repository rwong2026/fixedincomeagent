"""Curated backtest test dates spanning distinct rate regimes (Task 7.2).

Each regime lists a handful of test dates (ISO ``YYYY-MM-DD``) for the
point-in-time replay harness. Dates are the first (or mid-month) of the
month; the runner snaps the baseline to the last observation on/before the
date, so weekends/holidays need no adjustment here.
"""

from __future__ import annotations

REGIME_TEST_DATES: dict[str, list[str]] = {
    "2022_hiking": [
        "2022-03-01", "2022-05-01", "2022-07-01",
        "2022-09-01", "2022-11-01",
    ],
    "2019_inversion": [
        "2019-03-01", "2019-05-01", "2019-07-01",
        "2019-08-01", "2019-10-01",
    ],
    "2020_cut_cycle": [
        "2020-01-15", "2020-03-01", "2020-04-01",
        "2020-06-01", "2020-09-01",
    ],
    "2024_2025_cutting": [
        "2024-09-01", "2024-11-01", "2025-01-15",
        "2025-03-01", "2025-05-01",
    ],
}


def all_dates() -> list[str]:
    """Every regime test date flattened into one sorted, de-duplicated list."""
    return sorted({d for dates in REGIME_TEST_DATES.values() for d in dates})
