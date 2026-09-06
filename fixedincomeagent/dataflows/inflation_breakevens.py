"""Inflation breakevens (FRED): TIPS-implied inflation compensation.

Fetches the configured breakeven series (``fi_breakeven_series`` in
default_config: 5Y spot T5YIE, 10Y spot T10YIE, 5Y5Y forward T5YIFR) and
renders them as one consolidated markdown report.

Breakevens are NOT pure inflation-expectation readings: they embed liquidity
and inflation-risk premia (TIPS trade at a liquidity discount, and investors
demand compensation for inflation uncertainty). The report states this
explicitly so downstream analysts do not over-read a level shift as a change
in expected inflation.

Point-in-time: the data vintage is pinned to ``curr_date`` (clamped to FRED's
own today) exactly like fred.py, so a historical run sees only the values
published by that date — no future revisions leak into a backtest (#1275).
"""
import logging
from datetime import datetime, timedelta

import requests

from . import fred
from .config import get_config

logger = logging.getLogger(__name__)


def _fetch_points(series_id: str, start_date: str, curr_date: str, realtime: dict) -> list:
    """Fetch one series' in-window observations, skipping FRED's '.' missings."""
    try:
        observations = fred._request(
            "series/observations",
            {
                "series_id": series_id,
                "observation_start": start_date,
                "observation_end": curr_date,
                "sort_order": "asc",
                **realtime,
            },
        ).get("observations", [])
    except requests.RequestException as e:
        logger.warning("Inflation breakevens request failed for %s: %s", series_id, e)
        return []
    return [
        (o["date"], o["value"])
        for o in observations
        if o.get("value") not in (".", None, "")
    ]


def get_inflation_breakevens(curr_date: str, look_back_days: int = 365) -> str:
    """Fetch the configured inflation breakeven series as one markdown report.

    Args:
        curr_date: The as-of date (yyyy-mm-dd). Bounds the observation window
            and pins the data vintage (see module docstring).
        look_back_days: Trailing window length.

    Returns:
        A markdown report: a summary table (latest value and change over the
        window per series) with the premia caveat. A series with no in-window
        observations is flagged "no data" rather than aborting the report.
    """
    end_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    start_date = (end_dt - timedelta(days=look_back_days)).strftime("%Y-%m-%d")

    # Same vintage pin as fred.py: clamp to FRED's US-Central today so a live
    # run whose local date is a day ahead of Chicago doesn't 400 (#1275).
    pit = min(curr_date, fred._fred_today())
    realtime = {"realtime_start": pit, "realtime_end": pit}

    series = get_config().get("fi_breakeven_series", {})

    header = (
        f"## Inflation Breakevens (FRED)\n"
        f"- Window: {start_date} to {curr_date} (data vintage pinned to {pit})\n"
        f"- **Caveat:** breakeven rates embed liquidity and inflation-risk "
        f"premia — they are not pure readings of expected inflation.\n"
    )

    if not series:
        return header + "\nNo breakeven series configured (`fi_breakeven_series`).\n"

    rows = []
    for label, series_id in series.items():
        points = _fetch_points(series_id, start_date, curr_date, realtime)
        if not points:
            rows.append(f"| {label} | {series_id} | no data | — | — |")
            continue
        first_date, first_val = points[0]
        last_date, last_val = points[-1]
        try:
            change = f"{float(last_val) - float(first_val):+.2f}"
        except ValueError:
            change = "—"
        rows.append(f"| {label} | {series_id} | {last_val} | {last_date} | {change} |")

    table = (
        "\n| Series | FRED ID | Latest (%) | As of | Change over window |\n"
        "| --- | --- | --- | --- | --- |\n"
        + "\n".join(rows)
        + "\n"
    )
    return header + table
