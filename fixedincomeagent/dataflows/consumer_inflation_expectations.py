"""NY Fed Survey of Consumer Expectations: median inflation expectations.

Source verified 2026-09-05: the SCE page
https://www.newyorkfed.org/microeconomics/sce links a "Chart Data" workbook
(``/medialibrary/interactives/sce/sce/downloads/data/frbny-sce-data.xlsx``,
~1.2 MB) holding the aggregate series behind the interactive charts — the
public microdata workbooks on the same page are per-respondent and far
larger, and are NOT used here. Note the site returns HTTP 200 with an HTML
error page for bad paths, so format validation must be strict.

Workbook shape (two sheets read here; both share the same layout):

- ``Inflation expectations``: row 1 source/license line, row 2 title, row 3
  blank, row 4 headers (first cell empty), then one row per survey month
  keyed by an integer ``YYYYMM`` (201306 .. current). Columns include
  ``Median one-year ahead expected inflation rate`` and ``Median three-year
  ahead expected inflation rate`` among percentile and point-prediction
  columns that are not read.
- ``Five-year ahead Infl Exp``: same layout, ``Median five-year ahead
  expected inflation rate``; the five-year series starts 2022-01.

Point-in-time: ``curr_date`` filters to survey months ending on or before it.
Two caveats for backtesting: (1) a survey month is released around the
second week of the FOLLOWING month (e.g. the July survey in early August),
so as-of dates inside that lag see the latest survey slightly early; (2) the
workbook is today's snapshot as-published — the SCE aggregate medians are
computed once from each month's microdata and are not revised, but no
historical vintages of this file are kept. Downloads are cached under
``data_cache_dir/ny_fed_sce/`` with a 30-day TTL.
"""
import calendar
import logging
import os
import time
from datetime import date, datetime, timedelta
from io import BytesIO

import pandas as pd
import requests

from .config import get_config

logger = logging.getLogger(__name__)

# Network timeout (seconds), mirroring supply_chain_pressure.py.
REQUEST_TIMEOUT = 30
# The survey updates monthly; a 30-day TTL keeps live runs fresh.
CACHE_TTL = timedelta(days=30)
# Rows cap for the recent monthly table.
MAX_ROWS = 12

# Verified 2026-09-05: the "Chart Data" link on the SCE page; aggregate
# series only (the microdata workbooks are separate, much larger files).
DOWNLOAD_URL = (
    "https://www.newyorkfed.org/medialibrary/interactives/sce/sce/"
    "downloads/data/frbny-sce-data.xlsx"
)

# (sheet name, exact median column header) per horizon, in report order.
HORIZONS = [
    ("1-year", "Inflation expectations",
     "Median one-year ahead expected inflation rate"),
    ("3-year", "Inflation expectations",
     "Median three-year ahead expected inflation rate"),
    ("5-year", "Five-year ahead Infl Exp",
     "Median five-year ahead expected inflation rate"),
]
SHEET_NAMES = ["Inflation expectations", "Five-year ahead Infl Exp"]


class SceFormatError(ValueError):
    """The NY Fed SCE workbook came back with an unexpected shape."""


def _request(url: str) -> bytes:
    """GET the data workbook; the single HTTP boundary of this module."""
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.content


def _cache_path() -> str:
    return os.path.join(
        get_config()["data_cache_dir"], "ny_fed_sce", "frbny-sce-data.xlsx"
    )


def _month_end(yyyymm: object, sheet: str) -> date:
    """Validate an integer YYYYMM survey-month key and return its month-end."""
    text = str(yyyymm).split(".")[0]  # openpyxl ints read back as '201306'
    if len(text) != 6 or not text.isdigit():
        raise SceFormatError(
            f"New York Fed SCE workbook ({DOWNLOAD_URL}): survey month key "
            f"{yyyymm!r} in sheet {sheet!r} is not an integer YYYYMM. The "
            "file format may have changed."
        )
    year, month = int(text[:4]), int(text[4:])
    if not 1 <= month <= 12:
        raise SceFormatError(
            f"New York Fed SCE workbook ({DOWNLOAD_URL}): survey month key "
            f"{yyyymm!r} in sheet {sheet!r} has month {month}. The file "
            "format may have changed."
        )
    return date(year, month, calendar.monthrange(year, month)[1])


def _parse_rows(content: bytes) -> list[tuple[date, dict[str, float]]]:
    """Parse the workbook into (survey month-end, {horizon: median}) rows.

    Raises SceFormatError on any deviation from the documented shape: the
    file is unversioned, so a format change must fail loudly rather than be
    cached or rendered as if it were data.
    """
    try:
        sheets = pd.read_excel(
            BytesIO(content), sheet_name=SHEET_NAMES, skiprows=3
        )
    except Exception as e:
        raise SceFormatError(
            f"New York Fed SCE download ({DOWNLOAD_URL}) is not the expected "
            f"two-sheet XLSX: {e}. The file format may have changed."
        ) from e

    by_month: dict[date, dict[str, float]] = {}
    for horizon, sheet_name, column in HORIZONS:
        frame = sheets[sheet_name]
        if column not in frame.columns:
            raise SceFormatError(
                f"New York Fed SCE workbook ({DOWNLOAD_URL}): sheet "
                f"{sheet_name!r} has no {column!r} column among "
                f"{list(frame.columns)[:4]!r}. The file format may have "
                "changed."
            )
        month_col = frame.columns[0]
        prev = None
        for key, value in zip(frame[month_col], frame[column]):
            if pd.isna(key) and pd.isna(value):
                continue  # fully blank row
            month_date = _month_end(key, sheet_name)
            if prev is not None and month_date <= prev:
                raise SceFormatError(
                    f"New York Fed SCE workbook ({DOWNLOAD_URL}): survey "
                    f"months in sheet {sheet_name!r} are not increasing at "
                    f"{key!r}. The file format may have changed."
                )
            prev = month_date
            if pd.isna(value):
                raise SceFormatError(
                    f"New York Fed SCE workbook ({DOWNLOAD_URL}): blank "
                    f"{column!r} for survey month {key!r}. The file format "
                    "may have changed."
                )
            try:
                numeric = float(value)
            except (TypeError, ValueError) as e:
                raise SceFormatError(
                    f"New York Fed SCE workbook ({DOWNLOAD_URL}): "
                    f"non-numeric value {value!r} in {column!r} for survey "
                    f"month {key!r}. The file format may have changed."
                ) from e
            by_month.setdefault(month_date, {})[horizon] = numeric
    return sorted(by_month.items())


def _load_rows() -> list[tuple[date, dict[str, float]]]:
    """Return parsed rows, from the cache when fresh.

    A download is parsed (and thereby validated) BEFORE it is cached: the
    feed is unversioned, so a format change must never be cached as data.
    """
    path = _cache_path()
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < CACHE_TTL.total_seconds():
        with open(path, "rb") as f:
            return _parse_rows(f.read())
    content = _request(DOWNLOAD_URL)
    rows = _parse_rows(content)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)
    return rows


def get_consumer_inflation_expectations(curr_date: str) -> str:
    """Fetch NY Fed SCE median inflation expectations as a markdown report.

    Args:
        curr_date: The as-of date (yyyy-mm-dd). Only survey months ending on
            or before this date are used, so a historical run never sees
            future surveys. (Values are as-published in today's workbook —
            see the module docstring for the release-lag/backtesting caveat.)

    Returns:
        A markdown report: the latest median one-, three- and five-year
        ahead inflation expectations with a recent trend line, plus a table
        of recent monthly medians.
    """
    end_dt = datetime.strptime(curr_date, "%Y-%m-%d").date()

    try:
        rows = _load_rows()
    except SceFormatError as e:
        return f"ERROR: {e}"
    visible = [r for r in rows if r[0] <= end_dt]

    header = (
        "## Consumer Inflation Expectations (NY Fed SCE)\n"
        "- Source: Federal Reserve Bank of New York, Survey of Consumer "
        "Expectations (median expected inflation rate, %; monthly)\n"
        f"- As-of date: {end_dt} (survey months ending after this date are excluded)\n"
    )
    if not visible:
        return header + (
            f"\nNo SCE observations on or before {end_dt}. The one- and "
            "three-year series start in June 2013, the five-year series in "
            "January 2022.\n"
        )

    latest_month, latest = visible[-1]

    def _cell(values: dict, horizon: str) -> str:
        return f"{values[horizon]:.2f}" if horizon in values else ""

    summary = (
        f"\nLatest survey month ({latest_month:%Y-%m}): "
        f"one-year ahead **{_cell(latest, '1-year')}%**, "
        f"three-year ahead **{_cell(latest, '3-year')}%**, "
        f"five-year ahead **{_cell(latest, '5-year')}%**.\n"
    )

    trend = ""
    one_year = [(m, v["1-year"]) for m, v in visible if "1-year" in v]
    if len(one_year) >= 4:
        delta = one_year[-1][1] - one_year[-4][1]
        if abs(delta) < 0.005:
            trend = "One-year-ahead expectations are unchanged over the last three months.\n"
        else:
            direction = "rose" if delta > 0 else "fell"
            trend = (
                f"One-year-ahead expectations {direction} {abs(delta):.2f} "
                "percentage points over the last three months.\n"
            )

    shown = visible
    note = ""
    if len(visible) > MAX_ROWS:
        shown = visible[-MAX_ROWS:]
        note = f"\n_(showing the most recent {MAX_ROWS} of {len(visible)} monthly readings)_\n"

    monthly = (
        "\n**Recent monthly medians (%):**\n"
        + note
        + "\n| Month | 1-year ahead | 3-year ahead | 5-year ahead |\n"
        "| --- | --- | --- | --- |\n"
        + "\n".join(
            f"| {month:%Y-%m} | {_cell(values, '1-year')} | "
            f"{_cell(values, '3-year')} | {_cell(values, '5-year')} |"
            for month, values in shown
        )
        + "\n"
    )

    return header + summary + trend + monthly
