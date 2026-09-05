"""CFTC Commitments of Traders: Treasury futures positioning (TFF report).

Source verified 2026-09-05: the CFTC publishes Traders in Financial Futures
(TFF, futures-only) data through the Socrata open-data API, dataset
``gpe5-46if`` at https://publicreporting.cftc.gov/resource/gpe5-46if.json
(see https://publicreporting.cftc.gov/stories/s/TFF-Futures-Only/r4w3-av2r).
Rows are weekly (as of Tuesday, released Friday), newest first when ordered
by ``report_date_as_yyyy_mm_dd DESC``, with numeric fields returned as JSON
strings. The report's market display names are NOT stable over time (e.g.
"10-YEAR U.S. TREASURY NOTES" was renamed "UST 10Y NOTE", "U.S. TREASURY
BONDS" became "ULTRA UST BOND"), so contracts are keyed by the stable
``cftc_contract_market_code``.

Fields read per weekly row: ``open_interest_all``,
``dealer_positions_long_all`` / ``dealer_positions_short_all``,
``asset_mgr_positions_long`` / ``asset_mgr_positions_short``,
``lev_money_positions_long`` / ``lev_money_positions_short``.

Point-in-time: the query filters server-side to report dates on or before
``curr_date``, so a historical run never sees future reports. Responses are
cached under ``data_cache_dir/cftc_cot/`` keyed by contract and as-of date
with a 7-day TTL (the report is weekly; COT figures are not revised).
"""
import json
import logging
import os
import time
from datetime import date, datetime, timedelta

import requests

from .config import get_config

logger = logging.getLogger(__name__)

# Network timeout (seconds), mirroring supply_chain_pressure.py.
REQUEST_TIMEOUT = 30
# The report updates weekly; a 7-day TTL keeps live runs fresh.
CACHE_TTL = timedelta(days=7)
# Number of recent weekly reports to show in the table.
MAX_ROWS = 8
# Reports fetched per query (table rows plus one for the week-over-week delta).
FETCH_ROWS = MAX_ROWS + 1

# Verified 2026-09-05: CFTC Socrata TFF futures-only dataset.
API_URL = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"

# Friendly contract name -> (stable CFTC contract market code, display name).
# Codes verified 2026-09-05 against the API's distinct-name query; display
# names use the long form since the feed's short names change over time.
CONTRACTS = {
    "UST_2Y": ("042601", "2-Year U.S. Treasury Note futures"),
    "UST_5Y": ("044601", "5-Year U.S. Treasury Note futures"),
    "UST_10Y": ("043602", "10-Year U.S. Treasury Note futures"),
    "UST_30Y": ("020604", "Ultra U.S. Treasury Bond futures"),
}

# (report column, long field, short field).
CATEGORIES = [
    ("Dealer", "dealer_positions_long_all", "dealer_positions_short_all"),
    ("Asset Manager", "asset_mgr_positions_long", "asset_mgr_positions_short"),
    ("Leveraged Money", "lev_money_positions_long", "lev_money_positions_short"),
]

REQUIRED_FIELDS = [
    "report_date_as_yyyy_mm_dd",
    "market_and_exchange_names",
    "open_interest_all",
] + [field for _, long_f, short_f in CATEGORIES for field in (long_f, short_f)]


class CotFormatError(ValueError):
    """The CFTC Socrata response came back with an unexpected shape."""


def _request(url: str, params: dict) -> list:
    """GET the Socrata API; the single HTTP boundary of this module."""
    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def _cache_path(code: str, end: date) -> str:
    return os.path.join(
        get_config()["data_cache_dir"], "cftc_cot", f"{code}_{end}.json"
    )


def _parse_rows(payload: object) -> list[tuple[date, dict[str, int]]]:
    """Parse the Socrata JSON payload into (report date, positions) rows.

    Raises CotFormatError on any deviation from the documented shape: the
    feed is unversioned, so a format change must fail loudly rather than be
    cached or rendered as if it were data.
    """
    if not isinstance(payload, list):
        raise CotFormatError(
            f"CFTC COT Socrata API ({API_URL}) returned a non-list payload "
            f"({str(payload)[:120]!r}). The API format may have changed."
        )
    rows = []
    prev = None
    for row in payload:
        missing = [f for f in REQUIRED_FIELDS if f not in row]
        if missing:
            raise CotFormatError(
                f"CFTC COT Socrata API ({API_URL}) row is missing fields "
                f"{missing!r}; got {sorted(row)[:6]!r}. The API format may "
                "have changed."
            )
        try:
            report_date = datetime.strptime(
                row["report_date_as_yyyy_mm_dd"][:10], "%Y-%m-%d"
            ).date()
        except (TypeError, ValueError) as e:
            raise CotFormatError(
                f"CFTC COT Socrata API ({API_URL}): report date "
                f"{row['report_date_as_yyyy_mm_dd']!r} is not YYYY-MM-DD. "
                "The API format may have changed."
            ) from e
        if prev is not None and report_date >= prev:
            raise CotFormatError(
                f"CFTC COT Socrata API ({API_URL}): report dates are not "
                f"strictly descending at {report_date}. The API format may "
                "have changed."
            )
        prev = report_date
        positions: dict[str, int] = {}
        for field in REQUIRED_FIELDS[2:]:
            try:
                positions[field] = int(row[field])
            except (TypeError, ValueError) as e:
                raise CotFormatError(
                    f"CFTC COT Socrata API ({API_URL}): non-numeric value "
                    f"{row[field]!r} in {field!r} for report date "
                    f"{report_date}. The API format may have changed."
                ) from e
        rows.append((report_date, positions))
    return rows


def _load_rows(code: str, end: date) -> list[tuple[date, dict[str, int]]]:
    """Return parsed rows, from the cache when fresh.

    A response is parsed (and thereby validated) BEFORE it is cached: the
    feed is unversioned, so a format change must never be cached as data.
    """
    path = _cache_path(code, end)
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < CACHE_TTL.total_seconds():
        with open(path, "rb") as f:
            return _parse_rows(json.load(f))
    params = {
        "$select": ",".join(REQUIRED_FIELDS),
        "$where": (
            f"cftc_contract_market_code='{code}' AND "
            f"report_date_as_yyyy_mm_dd <= '{end}'"
        ),
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": str(FETCH_ROWS),
    }
    payload = _request(API_URL, params)
    rows = _parse_rows(payload)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f)
    return rows


def _fmt(n: int) -> str:
    return f"{n:+,}"


def get_cot_data(curr_date: str, contract: str = "UST_10Y") -> str:
    """Fetch CFTC COT Treasury futures positioning as a markdown report.

    Args:
        curr_date: The as-of date (yyyy-mm-dd). Only weekly reports dated on
            or before this date are used, so a historical run never sees
            future positioning.
        contract: One of ``UST_2Y``, ``UST_5Y``, ``UST_10Y`` (default),
            ``UST_30Y`` (Ultra Bond).

    Returns:
        A markdown report: latest net positioning (long minus short) of
        Dealer, Asset Manager and Leveraged Money traders, the week-over-week
        change, and a table of recent weekly reports.

    Raises:
        ValueError: If ``contract`` is not a known Treasury futures contract.
    """
    if contract not in CONTRACTS:
        raise ValueError(
            f"Unknown COT contract {contract!r}. Use one of "
            f"{sorted(CONTRACTS)} (e.g. 'UST_10Y')."
        )
    code, display_name = CONTRACTS[contract]
    end_dt = datetime.strptime(curr_date, "%Y-%m-%d").date()

    try:
        rows = _load_rows(code, end_dt)
    except CotFormatError as e:
        return f"ERROR: {e}"
    # The query filters to report dates <= curr_date server-side; the cache
    # is keyed by that same date, so every row here is point-in-time safe.
    visible = [r for r in rows if r[0] <= end_dt]

    header = (
        f"## CFTC COT Positioning — {display_name}\n"
        "- Source: CFTC Commitments of Traders, Traders in Financial Futures "
        "report (futures-only; weekly, as of Tuesday)\n"
        f"- As-of date: {end_dt} (reports after this date are excluded)\n"
    )
    if not visible:
        return header + (
            f"\nNo COT reports on or before {end_dt}. The TFF report series "
            "starts in June 2006.\n"
        )

    latest_date, latest = visible[0]
    summary = f"\nLatest report ({latest_date}), open interest {latest['open_interest_all']:,} contracts:\n"
    for name, long_f, short_f in CATEGORIES:
        net = latest[long_f] - latest[short_f]
        summary += (
            f"- {name} net: **{_fmt(net)}** "
            f"(long {latest[long_f]:,} / short {latest[short_f]:,})\n"
        )

    change = ""
    if len(visible) >= 2:
        prior = visible[1][1]
        deltas = []
        for name, long_f, short_f in CATEGORIES:
            delta = (latest[long_f] - latest[short_f]) - (
                prior[long_f] - prior[short_f]
            )
            deltas.append(
                f"{name} {'unchanged' if delta == 0 else _fmt(delta)}"
            )
        change = "\nWeek-over-week change in net positioning: " + "; ".join(deltas) + ".\n"

    shown = visible[:MAX_ROWS]
    note = ""
    if len(visible) > MAX_ROWS:
        note = f"\n_(showing the most recent {MAX_ROWS} of {len(visible)} weekly reports)_\n"

    table = (
        "\n**Recent weekly net positioning (contracts):**\n"
        + note
        + "\n| Report date | Open interest | Dealer net | Asset Manager net | Leveraged Money net |\n"
        "| --- | --- | --- | --- | --- |\n"
        + "\n".join(
            f"| {d} | {p['open_interest_all']:,} | "
            + " | ".join(_fmt(p[lf] - p[sf]) for _, lf, sf in CATEGORIES)
            + " |"
            for d, p in shown
        )
        + "\n"
    )

    return header + summary + change + table
