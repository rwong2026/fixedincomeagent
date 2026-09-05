"""Shelter & rents data: Zillow ZORI and Apartment List rent estimates.

Two national-level market-rent series, both monthly bulk CSVs (no API):

* Zillow Observed Rent Index (ZORI), "Smoothed: All Homes Plus Multifamily
  Time Series" — verified 2026-09-05 on https://www.zillow.com/research/data/
  (RENTALS section, geography "Metro & U.S."). ``ZILLOW_CSV_URL`` is the
  national sibling of the Metro file the page's Download button serves: one
  header row, one data row (RegionName "United States"), one column per
  month-end date from 2015-01-31. Zillow warns it makes "occasional changes
  to CSV download paths"; monthly data updates on the 16th. Downloads are
  cached under ``data_cache_dir/zillow/`` with a 7-day TTL.
* Apartment List Rent Estimates — verified 2026-09-05 via
  https://www.apartmentlist.com/research/category/data-rent-estimates. The
  page is behind Cloudflare bot protection (403 to non-browser clients) and
  every monthly release is a NEW Contentful asset URL (content-hash path plus
  a ``_YYYY_MM`` filename suffix; ``APARTMENT_LIST_CSV_URL`` below was the
  2026-06 release), so there is NO stable programmatic download URL. This
  leg is therefore a LOCAL-FILE INGEST: download the "Rent Estimates" CSV in
  a browser and drop it into ``data_cache_dir/apartment_list/`` (any name;
  the newest ``*.csv`` wins). Shape: quoted header
  ``location_name,location_type,location_fips_code,population,state,county,
  metro,bed_size,YYYY_MM,...``; the national series is the row with
  location_name "United States" and bed_size "overall". When no file is
  present the report says so and renders the Zillow leg alone.

Point-in-time: ``curr_date`` filters to months ending on or before it. Both
files are cumulative as-published-today — Zillow restates the full ZORI
history each release and Apartment List re-extrapolates its estimates — so
historical values read from today's files are NOT point-in-time; strict
backtesting requires archiving each download. Month-end filtering also hides
publication lag (the July ZORI, dated 07-31, only appears on the site in
mid-August); treat the most recent backtest months with care.
"""
import calendar
import csv
import io
import logging
import os
import time
from datetime import date, datetime, timedelta

import requests

from .config import get_config

logger = logging.getLogger(__name__)

# Network timeout (seconds), mirroring treasury.py.
REQUEST_TIMEOUT = 30

# Zillow updates monthly (on the 16th); refresh the cache weekly.
CACHE_TTL = timedelta(days=7)

# Months shown in the combined recent-months table.
RECENT_MONTHS = 12

# Verified 2026-09-05: national ZORI (smoothed, all homes + multifamily).
# Sibling of the page's Metro download; Zillow warns CSV paths change
# occasionally — a 404 or HTML body fails loudly in _parse_zillow.
ZILLOW_CSV_URL = (
    "https://files.zillowstatic.com/research/public_csvs/zori/"
    "National_zori_uc_sfrcondomfr_sm_month.csv"
)

# Verified 2026-09-05 (the 2026-06 release, found on the data page via a
# Wayback snapshot). The URL rotates with every monthly release and the page
# blocks non-browser clients, so this constant only documents where the local
# file comes from — this module never fetches it.
APARTMENT_LIST_CSV_URL = (
    "https://assets.ctfassets.net/jeox55pd4d8n/1KG2u9qAn6YlTDnQA1q6Jd/"
    "dcdd8e50defdf26e6b84e0dab33284c3/Apartment_List_Rent_Estimates_2026_06.csv"
)

_ZILLOW_ID_COLUMNS = ["RegionID", "SizeRank", "RegionName", "RegionType"]


class ZillowFormatError(ValueError):
    """The Zillow ZORI CSV came back with an unexpected shape."""


class ApartmentListFormatError(ValueError):
    """The local Apartment List CSV has an unexpected shape."""


def _request(url: str) -> str:
    """GET a CSV; the single HTTP boundary of this module (Zillow only)."""
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def _zillow_cache_path() -> str:
    return os.path.join(
        get_config()["data_cache_dir"], "zillow", "zori_national.csv"
    )


def _apartment_list_path() -> str | None:
    """Newest *.csv under data_cache_dir/apartment_list/, or None."""
    d = os.path.join(get_config()["data_cache_dir"], "apartment_list")
    if not os.path.isdir(d):
        return None
    csvs = [os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith(".csv")]
    if not csvs:
        return None
    return max(csvs, key=os.path.getmtime)


def _parse_zillow(text: str) -> list[tuple[date, float]]:
    """Parse the national ZORI CSV into (month-end date, rent) rows.

    Raises ZillowFormatError on any deviation from the documented shape: the
    file is unversioned, so a format change must fail loudly rather than be
    cached or rendered as if it were data.
    """
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or [c.strip() for c in rows[0][:4]] != _ZILLOW_ID_COLUMNS:
        raise ZillowFormatError(
            f"Zillow ZORI download ({ZILLOW_CSV_URL}) has an unexpected "
            f"header: expected 'RegionID,SizeRank,RegionName,RegionType,"
            "<YYYY-MM-DD>...', got {str(rows[0][:5])[:120]!r}. The file "
            "format may have changed."
        )
    header = rows[0]
    try:
        col_dates = [
            datetime.strptime(c.strip(), "%Y-%m-%d").date() for c in header[4:]
        ]
    except ValueError as e:
        raise ZillowFormatError(
            f"Zillow ZORI download ({ZILLOW_CSV_URL}): month columns are not "
            f"'YYYY-MM-DD' dates ({e}). The file format may have changed."
        ) from e
    if not col_dates:
        raise ZillowFormatError(
            f"Zillow ZORI download ({ZILLOW_CSV_URL}) has no month columns. "
            "The file format may have changed."
        )
    us = next(
        (r for r in rows[1:] if len(r) >= 4 and r[2].strip() == "United States"),
        None,
    )
    if us is None:
        raise ZillowFormatError(
            f"Zillow ZORI download ({ZILLOW_CSV_URL}) has no 'United States' "
            "row. The file format may have changed."
        )
    if len(us) != len(header):
        raise ZillowFormatError(
            f"Zillow ZORI download ({ZILLOW_CSV_URL}): the United States row "
            f"has {len(us)} cells for {len(header)} columns. The file format "
            "may have changed."
        )
    out = []
    for d, raw in zip(col_dates, us[4:]):
        raw = raw.strip()
        if not raw:
            continue
        try:
            out.append((d, float(raw)))
        except ValueError as e:
            raise ZillowFormatError(
                f"Zillow ZORI download ({ZILLOW_CSV_URL}): non-numeric rent "
                f"{raw!r} for {d}. The file format may have changed."
            ) from e
    return sorted(out)


def _parse_apartment_list(text: str, path: str) -> list[tuple[date, float]]:
    """Parse a local Apartment List rent estimates CSV.

    Raises ApartmentListFormatError on any deviation from the documented
    shape: a wrong file in the ingest directory must fail loudly rather than
    render as if it were the national series.
    """
    rows = list(csv.reader(io.StringIO(text)))
    if (
        not rows
        or not rows[0]
        or rows[0][0].strip() != "location_name"
        or "bed_size" not in rows[0][:8]
    ):
        raise ApartmentListFormatError(
            f"Apartment List CSV ({path}) has an unexpected header: expected "
            "'location_name,...,bed_size,<YYYY_MM>...', got "
            f"{str(rows[0][:9])[:120] if rows else 'an empty file'!r}. The "
            "file format may have changed, or this is not the Rent Estimates "
            "download."
        )
    header = rows[0]
    bed = header.index("bed_size")
    col_dates = []
    for c in header[bed + 1:]:
        try:
            y, m = (int(p) for p in c.strip().split("_"))
            col_dates.append(date(y, m, calendar.monthrange(y, m)[1]))
        except (ValueError, IndexError) as e:
            raise ApartmentListFormatError(
                f"Apartment List CSV ({path}): month column {c!r} is not "
                "'YYYY_MM'. The file format may have changed."
            ) from e
    if not col_dates:
        raise ApartmentListFormatError(
            f"Apartment List CSV ({path}) has no YYYY_MM month columns. The "
            "file format may have changed."
        )
    national = next(
        (
            r
            for r in rows[1:]
            if len(r) > bed
            and r[0].strip() == "United States"
            and r[bed].strip() == "overall"
        ),
        None,
    )
    if national is None:
        raise ApartmentListFormatError(
            f"Apartment List CSV ({path}) has no United States 'overall' row. "
            "The file format may have changed."
        )
    if len(national) != len(header):
        raise ApartmentListFormatError(
            f"Apartment List CSV ({path}): the United States row has "
            f"{len(national)} cells for {len(header)} columns. The file "
            "format may have changed."
        )
    out = []
    for d, raw in zip(col_dates, national[bed + 1:]):
        raw = raw.strip()
        if not raw:
            continue
        try:
            out.append((d, float(raw)))
        except ValueError as e:
            raise ApartmentListFormatError(
                f"Apartment List CSV ({path}): non-numeric rent {raw!r} for "
                f"{d}. The file format may have changed."
            ) from e
    return sorted(out)


def _load_zillow() -> list[tuple[date, float]]:
    """Return parsed national ZORI rows, from the cache when fresh.

    A download is parsed (and thereby validated) BEFORE it is cached: the
    feed is unversioned, so a format change must never be cached as data.
    """
    path = _zillow_cache_path()
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < CACHE_TTL.total_seconds():
        with open(path, encoding="utf-8") as f:
            return _parse_zillow(f.read())
    text = _request(ZILLOW_CSV_URL)
    rows = _parse_zillow(text)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return rows


def _load_apartment_list() -> list[tuple[date, float]] | None:
    """Parse the local Apartment List CSV, or None when none was dropped in."""
    path = _apartment_list_path()
    if path is None:
        return None
    with open(path, encoding="utf-8-sig") as f:
        return _parse_apartment_list(f.read(), path)


def _by_month(rows: list[tuple[date, float]]) -> dict[tuple[int, int], float]:
    return {(d.year, d.month): v for d, v in rows}


def _yoy(by_month: dict[tuple[int, int], float]) -> dict[tuple[int, int], float]:
    """Year-over-year growth per month; None-equivalent (absent) when the
    same month a year earlier is missing."""
    return {
        (y, m): v / by_month[(y - 1, m)] - 1
        for (y, m), v in by_month.items()
        if (y - 1, m) in by_month
    }


def _pct(growth: float | None) -> str:
    return "" if growth is None else f"{growth * 100:+.1f}%"


def _dollars(value: float | None) -> str:
    return "" if value is None else f"${value:,.0f}"


def get_shelter_rents(curr_date: str) -> str:
    """Fetch national shelter/rent data as a markdown report.

    Args:
        curr_date: The as-of date (yyyy-mm-dd). Only months ending on or
            before this date are used, so a historical run never sees future
            months. (Values are as-published in today's cumulative files —
            see the module docstring for the backtesting caveat.)

    Returns:
        A markdown report comparing the Zillow ZORI and Apartment List rent
        levels and year-over-year rent-growth trajectories. When no
        Apartment List CSV is available locally, the report says so and
        renders the Zillow leg alone.
    """
    end_dt = datetime.strptime(curr_date, "%Y-%m-%d").date()

    try:
        zillow = [r for r in _load_zillow() if r[0] <= end_dt]
        aptlist_rows = _load_apartment_list()
        aptlist = (
            None
            if aptlist_rows is None
            else [r for r in aptlist_rows if r[0] <= end_dt]
        )
    except (ZillowFormatError, ApartmentListFormatError) as e:
        return f"ERROR: {e}"

    header = (
        "## Shelter & Rents: Zillow ZORI vs Apartment List\n"
        "- Sources: Zillow Observed Rent Index (national, smoothed, all homes "
        "+ multifamily) and Apartment List Rent Estimates (national, overall "
        "bed size)\n"
        f"- As-of date: {end_dt} (months ending after this date are excluded)\n"
    )
    if aptlist is None:
        header += (
            "- Apartment List data not available locally (no stable download "
            "URL — see module docstring): drop an "
            "Apartment_List_Rent_Estimates_*.csv from "
            "apartmentlist.com/research/category/data-rent-estimates into "
            f"{os.path.join(get_config()['data_cache_dir'], 'apartment_list')}"
            "/ to enable this leg.\n"
        )
    if not zillow and not aptlist:
        return header + (
            f"\nNo rent observations on or before {end_dt}. ZORI starts "
            "2015-01, Apartment List rent estimates start 2017-01.\n"
        )

    zmap = _by_month(zillow)
    amap = _by_month(aptlist or [])
    zyoy = _yoy(zmap)
    ayoy = _yoy(amap)

    latest = (
        "\n**Latest readings:**\n\n"
        "| Source | Latest month | Median rent | YoY growth |\n"
        "| --- | --- | --- | --- |\n"
    )
    if zillow:
        d, v = zillow[-1]
        latest += (
            f"| Zillow ZORI | {d.year}-{d.month:02d} | {_dollars(v)} | "
            f"{_pct(zyoy.get((d.year, d.month)))} |\n"
        )
    if aptlist:
        d, v = aptlist[-1]
        latest += (
            f"| Apartment List | {d.year}-{d.month:02d} | {_dollars(v)} | "
            f"{_pct(ayoy.get((d.year, d.month)))} |\n"
        )

    months = sorted(set(zmap) | set(amap))
    shown = months[-RECENT_MONTHS:]
    note = ""
    if len(months) > RECENT_MONTHS:
        note = f"\n_(showing the most recent {len(shown)} of {len(months)} months)_\n"

    if aptlist is None:
        head = "| Month | ZORI $ | ZORI YoY |\n| --- | --- | --- |\n"
        lines = [
            f"| {y}-{m:02d} | {_dollars(zmap.get((y, m)))} | "
            f"{_pct(zyoy.get((y, m)))} |"
            for y, m in shown
        ]
    else:
        head = (
            "| Month | ZORI $ | ZORI YoY | AptList $ | AptList YoY |\n"
            "| --- | --- | --- | --- | --- |\n"
        )
        lines = [
            f"| {y}-{m:02d} | {_dollars(zmap.get((y, m)))} | "
            f"{_pct(zyoy.get((y, m)))} | {_dollars(amap.get((y, m)))} | "
            f"{_pct(ayoy.get((y, m)))} |"
            for y, m in shown
        ]
    table = "\n**Recent months (national):**\n" + note + "\n" + head + "\n".join(lines) + "\n"

    return header + latest + table
