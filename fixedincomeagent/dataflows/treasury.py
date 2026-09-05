"""Treasury.gov data vendor: par yield curve (CMT) rates and auction results.

Two official, keyless sources, verified 2026-09:

* Par yields — the Daily Treasury Par Yield Curve Rates (constant maturity
  Treasury, CMT) CSV feed on home.treasury.gov. This dataset is NOT in the
  Treasury Fiscal Data API: ``daily_treasury_par_yield_curve`` and
  ``daily_treasury_rates`` under ``api.fiscaldata.treasury.gov`` both 404,
  and the Fiscal Data ``avg_interest_rates`` dataset is the average rate on
  outstanding marketable securities, not the par curve. The CSV feed is per
  calendar year, most recent day first, tenors 1 Mo .. 30 Yr.
* Auction results — Fiscal Data API ``v1/accounting/od/auctions_query``
  (Treasury securities auction announcements + competitive results: high
  yield/price/investment rate, bid-to-cover ratio, offering amount).

Past-year yield CSVs are final, so they are cached under ``data_cache_dir``;
the current-year file still updates intraday and is always refetched.
Auction windows are ad-hoc date ranges and are always fetched fresh.
"""
import csv
import io
import json
import logging
import os
from datetime import date, datetime, timedelta

import requests

from .config import get_config

logger = logging.getLogger(__name__)

# Network timeout (seconds), mirroring the FRED client.
REQUEST_TIMEOUT = 30

DEFAULT_LOOKBACK_DAYS = 90

# Rows cap for the rendered daily-yield table (same rationale as fred.py).
MAX_ROWS = 40

# A 90-day window holds ~80 auctions (weekly bills + coupon cycles).
PAGE_SIZE = 500

PAR_YIELD_CSV_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/"
    "interest-rates/daily-treasury-rates.csv/{year}/all"
)
FISCALDATA_API_BASE = (
    "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
)
AUCTIONS_ENDPOINT = "v1/accounting/od/auctions_query"

AUCTION_FIELDS = [
    "auction_date",
    "cusip",
    "security_type",
    "security_term",
    "high_yield",
    "high_investment_rate",
    "high_price",
    "bid_to_cover_ratio",
    "offering_amt",
]

# Tenors shown in the daily table and the change-over-window summary.
KEY_TENORS = ["3 Mo", "2 Yr", "5 Yr", "10 Yr", "30 Yr"]
SUMMARY_TENORS = ["2 Yr", "10 Yr"]

# The Fiscal Data API encodes missing values as the literal string "null".
_NULL = (None, "", "null")


def _request(url: str, params: dict | None = None) -> str:
    """GET a Treasury endpoint and return the raw response body."""
    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def _yield_csv_cache_path(year: int) -> str:
    cache_dir = get_config()["data_cache_dir"]
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"treasury_par_yield_curve_{year}.csv")


class TreasuryFormatError(ValueError):
    """A Treasury source returned 200 with an unexpected body shape."""


def _load_yield_csv(year: int) -> str:
    """Return the par yield curve CSV for a calendar year.

    Past years are immutable and cached on disk; the current year still
    updates every business day, so it is always fetched fresh. The body is
    validated before it is cached or parsed: the feed is unversioned, so a
    format change must fail loudly rather than be cached as final data.
    """
    path = _yield_csv_cache_path(year)
    if year < date.today().year and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    text = _request(
        PAR_YIELD_CSV_URL.format(year=year),
        {
            "type": "daily_treasury_yield_curve",
            "field_tdr_date_value": str(year),
            "_format": "csv",
        },
    )
    header = text.split("\n", 1)[0].split(",")
    if header[0].strip() != "Date" or len(header) < 2:
        raise TreasuryFormatError(
            f"Treasury par yield CSV for {year} has an unexpected format: "
            f"expected a header of 'Date,<tenor>...', got {header[0].strip()!r}. "
            "The home.treasury.gov feed format may have changed."
        )
    if year < date.today().year:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    return text


def _parse_yield_csv(text: str) -> tuple[list[str], list[tuple[date, dict]]]:
    """Parse a yield CSV into (tenor order, [(date, {tenor: yield})]).

    Assumes a header already validated by ``_load_yield_csv``.
    """
    reader = csv.reader(io.StringIO(text))
    header = next(reader)
    tenors = header[1:]
    rows = []
    for line in reader:
        if len(line) != len(header):
            continue
        try:
            day = datetime.strptime(line[0].strip(), "%m/%d/%Y").date()
        except ValueError:
            continue
        values = {
            tenor: val.strip()
            for tenor, val in zip(tenors, line[1:], strict=True)
            if val.strip()
        }
        if values:
            rows.append((day, values))
    return tenors, rows


def get_treasury_par_yields(
    curr_date: str, look_back_days: int = DEFAULT_LOOKBACK_DAYS
) -> str:
    """Fetch the daily Treasury par yield curve as a markdown report.

    Args:
        curr_date: The as-of date (yyyy-mm-dd). Rows after it are excluded,
            so a historical run never sees future yields.
        look_back_days: Trailing window length (default 90).

    Returns:
        A markdown report with the latest in-window curve, the change in key
        tenors over the window, and a daily table of key tenors.
    """
    end_dt = datetime.strptime(curr_date, "%Y-%m-%d").date()
    start_dt = end_dt - timedelta(days=look_back_days)

    tenors: list[str] = []
    rows: list[tuple[date, dict]] = []
    try:
        for year in range(start_dt.year, end_dt.year + 1):
            year_tenors, year_rows = _parse_yield_csv(_load_yield_csv(year))
            tenors.extend(t for t in year_tenors if t not in tenors)
            rows.extend(year_rows)
    except TreasuryFormatError as e:
        return f"ERROR: {e}"
    window = sorted(dv for dv in rows if start_dt <= dv[0] <= end_dt)

    header = (
        "## Treasury Par Yield Curve (Daily CMT Rates)\n"
        "- Source: home.treasury.gov Daily Treasury Par Yield Curve Rates\n"
        f"- Window: {start_dt} to {end_dt}\n"
    )
    if not window:
        return header + (
            "\nNo Treasury par yield observations in this window. The curve "
            "is published on business days only; try a longer look_back_days.\n"
        )

    latest_date, latest_vals = window[-1]
    snapshot = (
        f"\n**Latest curve ({latest_date}):**\n\n"
        "| Tenor | Yield % |\n| --- | --- |\n"
        + "\n".join(
            f"| {t} | {latest_vals[t]} |" for t in tenors if t in latest_vals
        )
        + "\n"
    )

    changes = []
    first_vals = window[0][1]
    for tenor in SUMMARY_TENORS:
        if tenor in first_vals and tenor in latest_vals:
            delta = float(latest_vals[tenor]) - float(first_vals[tenor])
            changes.append(
                f"{tenor}: {first_vals[tenor]} -> {latest_vals[tenor]} "
                f"({delta:+.2f})"
            )
    summary = "\n**Change over window:** " + " | ".join(changes) + "\n" if changes else ""

    shown = window
    note = ""
    if len(window) > MAX_ROWS:
        shown = window[-MAX_ROWS:]
        note = f"\n_(showing the most recent {MAX_ROWS} of {len(window)} days)_\n"

    key = [t for t in KEY_TENORS if t in tenors]
    table = (
        "\n| Date | " + " | ".join(key) + " |\n"
        "| --- |" + " --- |" * len(key) + "\n"
        + "\n".join(
            f"| {d} | " + " | ".join(vals.get(t, "") for t in key) + " |"
            for d, vals in shown
        )
        + "\n"
    )

    return header + snapshot + summary + note + table


def _is_priced(auction: dict) -> bool:
    """True when competitive results exist (not just an announcement)."""
    return any(
        auction.get(f) not in _NULL
        for f in ("high_yield", "high_investment_rate", "high_price", "bid_to_cover_ratio")
    )


def get_auction_results(
    curr_date: str, look_back_days: int = DEFAULT_LOOKBACK_DAYS
) -> str:
    """Fetch recent Treasury auction results as a markdown report.

    Args:
        curr_date: The as-of date (yyyy-mm-dd); bounds the auction window.
        look_back_days: Trailing window length (default 90).

    Returns:
        A markdown report of auctions priced in the window, most recent
        first: term, CUSIP, high yield (or investment rate for bills),
        bid-to-cover ratio, and offering size.
    """
    end_dt = datetime.strptime(curr_date, "%Y-%m-%d").date()
    start_dt = end_dt - timedelta(days=look_back_days)

    payload = json.loads(
        _request(
            f"{FISCALDATA_API_BASE}/{AUCTIONS_ENDPOINT}",
            {
                "fields": ",".join(AUCTION_FIELDS),
                "filter": (
                    f"auction_date:gte:{start_dt},auction_date:lte:{end_dt}"
                ),
                "sort": "-auction_date",
                "page[size]": PAGE_SIZE,
            },
        )
    )
    # The API is unversioned in practice: a shape change must fail loudly
    # rather than degrade into a false "no results" report.
    if not isinstance(payload, dict) or "data" not in payload:
        return (
            f"ERROR: Treasury Fiscal Data API ({AUCTIONS_ENDPOINT}) returned "
            f"an unexpected response: expected a JSON object with a 'data' "
            f"key, got {str(payload)[:200]!r}. The API shape may have changed."
        )
    rows = [r for r in payload["data"] if _is_priced(r)]

    header = (
        "## Treasury Auction Results\n"
        "- Source: Treasury Fiscal Data API (v1/accounting/od/auctions_query)\n"
        f"- Window: {start_dt} to {end_dt}\n"
    )
    if not rows:
        return header + "\nNo auction results in this window.\n"

    lines = []
    for r in rows:
        # Bills quote an investment rate; notes/bonds a yield. high_price is
        # deliberately not a fallback — a price in a rate column misleads
        # (FRNs would show ~100). FRNs report a discount margin instead;
        # their rate cell stays empty.
        rate = next(
            (r[f] for f in ("high_yield", "high_investment_rate")
             if r.get(f) not in _NULL),
            "",
        )
        if rate:
            rate = f"{float(rate):.3f}"
        btc = r.get("bid_to_cover_ratio")
        btc = f"{float(btc):.2f}" if btc not in _NULL else ""
        offering = r.get("offering_amt")
        offering = f"{float(offering) / 1e9:.1f}" if offering not in _NULL else ""
        security = f"{r.get('security_term', '')} {r.get('security_type', '')}".strip()
        lines.append(
            f"| {r.get('auction_date', '')} | {security} | {r.get('cusip', '')} "
            f"| {rate} | {btc} | {offering} |"
        )

    table = (
        "\n| Auction Date | Security | CUSIP | Rate % | Bid-to-Cover | Offering ($B) |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        + "\n".join(lines)
        + "\n"
    )

    return header + table
