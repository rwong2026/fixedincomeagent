"""ALFRED (Archival FRED) point-in-time vintage fetcher.

Returns economic data as it was known on a specific historical date, using
FRED's realtime_start/realtime_end parameters. Critical for backtesting:
revision-prone series (CPI, NFP, GDP, PCE) must use the vintage that was
published by the test date, not today's revised figures.

Uses the same FRED API and API key as fred.py. The distinction is purely
in the realtime parameters: fred.py pins to curr_date (current analysis);
this module pins to an arbitrary historical vintage_date for replay.
"""
import logging
from datetime import datetime, timedelta

import requests

from .fred import (
    MAX_ROWS,
    _fred_today,
    _request,
)

logger = logging.getLogger(__name__)

DEFAULT_LOOKBACK_DAYS = 365


def get_vintage_dates(series_id: str, limit: int | None = None) -> list[str]:
    """Return available vintage dates for a FRED series (ALFRED).

    Args:
        series_id: FRED series ID (e.g. "CPIAUCSL").
        limit: If provided, return the most recent ``limit`` dates.

    Returns:
        List of ISO date strings (yyyy-mm-dd) in ascending order.
    """
    try:
        data = _request(
            "series/vintagedates",
            {"series_id": series_id, "sort_order": "asc"},
        )
    except requests.RequestException as e:
        logger.warning("ALFRED vintage dates request failed for %s: %s", series_id, e)
        return []
    dates = data.get("vintage_dates", [])
    if limit:
        dates = dates[-limit:]
    return dates


def get_alfred_vintage(
    series_id: str,
    vintage_date: str,
    look_back_days: int | None = None,
) -> str:
    """Fetch a FRED series as it was known on vintage_date (ALFRED).

    Args:
        series_id: FRED series ID (e.g. "CPIAUCSL", "PAYEMS", "GDP").
        vintage_date: The point-in-time date (yyyy-mm-dd). Data returned
            is exactly what was published by this date — no later revisions.
        look_back_days: Trailing observation window. None uses 365.

    Returns:
        Markdown report with vintage metadata, latest value, and table.
    """
    if look_back_days is None:
        look_back_days = DEFAULT_LOOKBACK_DAYS

    # Clamp vintage to FRED's own today (same logic as fred.py)
    pit = min(vintage_date, _fred_today())
    realtime = {"realtime_start": pit, "realtime_end": pit}

    end_dt = datetime.strptime(vintage_date, "%Y-%m-%d")
    start_date = (end_dt - timedelta(days=look_back_days)).strftime("%Y-%m-%d")

    try:
        meta = _request("series", {"series_id": series_id, **realtime}).get("seriess") or []
    except requests.RequestException as e:
        logger.warning("ALFRED metadata request failed for %s: %s", series_id, e)
        return f"ALFRED: series '{series_id}' unavailable due to network error: {e}"

    if not meta:
        return f"ALFRED: series '{series_id}' not found at vintage {pit}."
    info = meta[0]
    title = info.get("title", series_id)
    units = info.get("units_short") or info.get("units", "")
    frequency = info.get("frequency", "")

    try:
        observations = _request(
            "series/observations",
            {
                "series_id": series_id,
                "observation_start": start_date,
                "observation_end": vintage_date,
                "sort_order": "asc",
                **realtime,
            },
        ).get("observations", [])
    except requests.RequestException as e:
        logger.warning("ALFRED observations request failed for %s: %s", series_id, e)
        return f"ALFRED: observations for '{series_id}' unavailable due to network error: {e}"

    points = [
        (o["date"], o["value"])
        for o in observations
        if o.get("value") not in (".", None, "")
    ]

    header = (
        f"## ALFRED Vintage: {title} ({series_id})\n"
        f"- Vintage date (data as-known): {pit}\n"
        f"- Units: {units}\n"
        f"- Frequency: {frequency}\n"
        f"- Window: {start_date} to {vintage_date}\n"
    )

    if not points:
        return header + (
            f"\nNo observations for {series_id} at the {pit} vintage "
            f"in this window."
        )

    first_date, first_val = points[0]
    last_date, last_val = points[-1]
    try:
        delta = float(last_val) - float(first_val)
        summary = f"\n**Latest:** {last_val} ({last_date}) | **Change:** {delta:+.2f} from {first_val} ({first_date})\n"
    except ValueError:
        summary = f"\n**Latest:** {last_val} ({last_date})\n"

    shown = points[-MAX_ROWS:] if len(points) > MAX_ROWS else points
    note = f"\n_(showing {len(shown)} of {len(points)} observations)_\n" if len(points) > MAX_ROWS else ""

    table = (
        "\n| Date | Value |\n| --- | --- |\n"
        + "\n".join(f"| {d} | {v} |" for d, v in shown)
        + "\n"
    )

    return header + summary + note + table
