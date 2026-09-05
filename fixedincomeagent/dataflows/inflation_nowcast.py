"""Cleveland Fed Inflation Nowcasting: daily CPI/PCE nowcasts.

Source verified 2026-09-05: the Cleveland Fed publishes nowcasts at
https://www.clevelandfed.org/indicators-and-data/inflation-nowcasting.
That page offers NO CSV/XLSX download and no REST API anymore — the only
machine-readable data is the JSON powering its charts
(``/-/media/files/webcharts/inflationnowcasting/nowcast_{month,year,quarter}.json``).
This module reads the month-over-month file; the year-over-year and
quarterly files at the sibling URLs share the same shape if ever needed.

File shape (FusionCharts export): a list of chart objects, one per nowcasted
month since 2013-07. Each chart's ``chart.subcaption`` is the nowcasted month
(``"YYYY-M"``), its categories are the business days the nowcasts were
published as ``"MM/DD"`` labels (year inferred from the nowcasted month:
labels with a month number below it belong to the following year), plus
release markers like ``"PCE Jul"`` interspersed in the category list. The
dataset holds one series per measure, aligned with the day labels ONLY (the
release markers have no data points). Cells are blank once the corresponding
actual has been released.

Point-in-time: ``curr_date`` filters to nowcast rows dated on or before it.
The downloaded file is cumulative, so historical nowcasts are values
as-published-today — the Cleveland Fed may revise past nowcasts (e.g. the
October 2025 CPI gap handling), so for strict backtesting a local archive of
past downloads would be needed. Downloads are cached under
``data_cache_dir/cleveland_fed/`` with a 24h TTL for live runs.
"""
import json
import logging
import os
import re
import time
from datetime import date, datetime, timedelta

import requests

from .config import get_config

logger = logging.getLogger(__name__)

# Network timeout (seconds), mirroring treasury.py.
REQUEST_TIMEOUT = 30

# The nowcast file updates each business day ~10:00 ET; 24h TTL for live runs.
CACHE_TTL = timedelta(hours=24)

# Rows cap for the recent daily-nowcast table.
MAX_ROWS = 15

# Verified 2026-09-05: linked from the page's chart widgets via
# data-data-config; no CSV/XLSX asset exists on the page anymore.
DOWNLOAD_URL = (
    "https://www.clevelandfed.org/-/media/files/webcharts/"
    "inflationnowcasting/nowcast_month.json"
)

# The four nowcast measures, in report column order. "Actual ..." series in
# the same file are realized prints, not nowcasts, and are never read.
NOWCAST_SERIES = [
    "CPI Inflation",
    "Core CPI Inflation",
    "PCE Inflation",
    "Core PCE Inflation",
]
COLUMN_NAMES = ["CPI", "Core CPI", "PCE", "Core PCE"]

_MONTH_RE = re.compile(r"^(\d{4})-(\d{1,2})$")
_DAY_RE = re.compile(r"^(\d{1,2})/(\d{1,2})$")


class ClevelandFedFormatError(ValueError):
    """The Cleveland Fed nowcast file came back with an unexpected shape."""


def _request(url: str) -> str:
    """GET the nowcast file; the single HTTP boundary of this module."""
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def _cache_path() -> str:
    return os.path.join(
        get_config()["data_cache_dir"], "cleveland_fed", "nowcast_month.json"
    )


def _parse_nowcasts(text: str) -> list[tuple[date, str, dict]]:
    """Parse the nowcast JSON into (nowcast date, month, {measure: value}).

    Raises ClevelandFedFormatError on any deviation from the documented
    shape: the file is unversioned, so a format change must fail loudly
    rather than be cached or rendered as if it were data.
    """
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        raise ClevelandFedFormatError(
            f"Cleveland Fed inflation nowcast download ({DOWNLOAD_URL}) is not "
            f"JSON: {e}. The file format may have changed."
        ) from e
    if not isinstance(payload, list) or not payload:
        raise ClevelandFedFormatError(
            f"Cleveland Fed inflation nowcast file ({DOWNLOAD_URL}) should be "
            f"a non-empty JSON list of per-month charts, got "
            f"{type(payload).__name__}. The file format may have changed."
        )

    rows = []
    for chart in payload:
        try:
            subcaption = chart["chart"]["subcaption"]
            categories = chart["categories"][0]["category"]
            datasets = {d["seriesname"]: d["data"] for d in chart["dataset"]}
        except (KeyError, IndexError, TypeError) as e:
            raise ClevelandFedFormatError(
                f"Cleveland Fed inflation nowcast file ({DOWNLOAD_URL}): a "
                f"chart object is missing chart/categories/dataset members "
                f"({e}). The file format may have changed."
            ) from e
        m = _MONTH_RE.match(str(subcaption))
        if not m:
            raise ClevelandFedFormatError(
                f"Cleveland Fed inflation nowcast file ({DOWNLOAD_URL}): "
                f"unexpected chart subcaption {subcaption!r}, expected "
                "'YYYY-M'. The file format may have changed."
            )
        year, month = int(m.group(1)), int(m.group(2))
        missing = [s for s in NOWCAST_SERIES if s not in datasets]
        if missing:
            raise ClevelandFedFormatError(
                f"Cleveland Fed inflation nowcast file ({DOWNLOAD_URL}): "
                f"series {missing} not found for {subcaption!r}. The file "
                "format may have changed."
            )
        # Day labels only: release markers like "PCE Jul" have no data
        # points, so dataset arrays align with the filtered day list.
        day_dates = []
        for cat in categories:
            dm = _DAY_RE.match(str(cat.get("label", "")))
            if not dm:
                continue
            mm, dd = int(dm.group(1)), int(dm.group(2))
            day_dates.append(date(year if mm >= month else year + 1, mm, dd))
        for series in NOWCAST_SERIES:
            if len(datasets[series]) != len(day_dates):
                raise ClevelandFedFormatError(
                    f"Cleveland Fed inflation nowcast file ({DOWNLOAD_URL}): "
                    f"series {series!r} for {subcaption!r} has "
                    f"{len(datasets[series])} points for {len(day_dates)} "
                    "nowcast days. The file format may have changed."
                )

        month_label = f"{year}-{month:02d}"
        for i, day in enumerate(day_dates):
            values = {}
            for series in NOWCAST_SERIES:
                raw = datasets[series][i].get("value", "")
                if raw in ("", None):
                    continue  # not yet nowcasted, or actual already released
                try:
                    values[series] = float(raw)
                except (TypeError, ValueError) as e:
                    raise ClevelandFedFormatError(
                        f"Cleveland Fed inflation nowcast file "
                        f"({DOWNLOAD_URL}): non-numeric value {raw!r} in "
                        f"{series!r} for {subcaption!r}. The file format may "
                        "have changed."
                    ) from e
            if values:
                rows.append((day, month_label, values))
    return rows


def _load_rows() -> list[tuple[date, str, dict]]:
    """Return parsed nowcast rows, from the cache when fresh.

    A download is parsed (and thereby validated) BEFORE it is cached: the
    feed is unversioned, so a format change must never be cached as data.
    """
    path = _cache_path()
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < CACHE_TTL.total_seconds():
        with open(path, encoding="utf-8") as f:
            return _parse_nowcasts(f.read())
    text = _request(DOWNLOAD_URL)
    rows = _parse_nowcasts(text)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return rows


def get_inflation_nowcast(curr_date: str) -> str:
    """Fetch Cleveland Fed inflation nowcasts as a markdown report.

    Args:
        curr_date: The as-of date (yyyy-mm-dd). Only nowcasts published on or
            before this date are used, so a historical run never sees future
            nowcasts. (Values are as-published in today's cumulative file —
            see the module docstring for the backtesting caveat.)

    Returns:
        A markdown report: the latest month-over-month nowcast per measure
        for the most recent nowcasted months, plus a table of recent daily
        nowcasts.
    """
    end_dt = datetime.strptime(curr_date, "%Y-%m-%d").date()

    try:
        rows = _load_rows()
    except ClevelandFedFormatError as e:
        return f"ERROR: {e}"
    visible = sorted(r for r in rows if r[0] <= end_dt)

    header = (
        "## Cleveland Fed Inflation Nowcasting\n"
        "- Source: Federal Reserve Bank of Cleveland, Inflation Nowcasting "
        "(month-over-month % change, updated each business day)\n"
        f"- As-of date: {end_dt} (nowcasts published after this date are excluded)\n"
    )
    if not visible:
        return header + (
            f"\nNo Cleveland Fed nowcast observations on or before {end_dt}. "
            "The series starts in July 2013.\n"
        )

    latest_by_month: dict[str, dict] = {}
    for _, month_label, values in visible:
        latest_by_month.setdefault(month_label, {}).update(values)
    months = sorted(latest_by_month)[-2:]

    def _cell(values: dict, series: str) -> str:
        return f"{values[series]:.2f}" if series in values else ""

    summary = (
        "\n**Latest nowcasts by month:**\n\n"
        "| Month | " + " | ".join(COLUMN_NAMES) + " |\n"
        "| --- |" + " --- |" * len(COLUMN_NAMES) + "\n"
        + "\n".join(
            f"| {m} | "
            + " | ".join(_cell(latest_by_month[m], s) for s in NOWCAST_SERIES)
            + " |"
            for m in months
        )
        + "\n"
    )

    shown = visible
    note = ""
    if len(visible) > MAX_ROWS:
        shown = visible[-MAX_ROWS:]
        note = f"\n_(showing the most recent {MAX_ROWS} of {len(visible)} daily nowcasts)_\n"

    daily = (
        "\n**Recent daily nowcasts:**\n"
        + note
        + "\n| Nowcast date | Month | " + " | ".join(COLUMN_NAMES) + " |\n"
        "| --- | --- |" + " --- |" * len(COLUMN_NAMES) + "\n"
        + "\n".join(
            f"| {day} | {month_label} | "
            + " | ".join(_cell(values, s) for s in NOWCAST_SERIES)
            + " |"
            for day, month_label, values in shown
        )
        + "\n"
    )

    return header + summary + daily
