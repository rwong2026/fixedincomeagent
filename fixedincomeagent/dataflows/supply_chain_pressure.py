"""NY Fed Global Supply Chain Pressure Index (GSCPI): monthly index.

Source verified 2026-09-06: the GSCPI page
https://www.newyorkfed.org/research/policy/gscpi hosts an interactive chart
whose Angular app references three assets (extracted from its main-es2015.js):

- ``/medialibrary/research/interactives/gscpi/downloads/gscpi_data.xlsx``
  (the page's "Download data" button): CORRUPT server-side — an OLE2 wrapper
  around a zip containing only theme parts (no workbook) with a zero-padded
  tail; pandas/openpyxl cannot read it.
- ``/medialibrary/research/interactives/data/gscpi/gscpi_interactive_data.csv``
  (the chart's actual data): USED HERE.
- ``/medialibrary/research/interactives/data/gscpi/gscpi.json`` (page text).

Note the site returns HTTP 200 with an HTML error page for bad paths, so
format validation must be strict. The CSV is a vintage matrix: first column
``Date`` = observation month-end (``DD-Mon-YYYY``), then one column per
publication vintage labeled ``Mon-YY`` (Jan-22 .. current); GSCPI updates at
10:00 ET on the fourth business day of each month. The LAST vintage column is
the current series; earlier vintages have blank tails (months not yet
published at that vintage), and the file ends in a fully blank trailer row.

Point-in-time: ``curr_date`` filters to observations on or before it. Each
vintage is the full history as-published that month, so the downloaded file
contains revised values as-published-today — for strict backtesting the
latest vintage on or before ``curr_date``'s publication would have to be
selected instead (the columns make that possible if ever needed). Downloads
are cached under ``data_cache_dir/gscpi/`` with a 30-day TTL.
"""
import logging
import os
import re
import time
from datetime import date, datetime, timedelta
from io import StringIO

import pandas as pd
import requests

from .config import get_config

logger = logging.getLogger(__name__)

# Network timeout (seconds), mirroring inflation_nowcast.py.
REQUEST_TIMEOUT = 30
# The series updates monthly; a 30-day TTL keeps live runs fresh.
CACHE_TTL = timedelta(days=30)
# Rows cap for the recent monthly table.
MAX_ROWS = 12

# Verified 2026-09-06: linked from the chart app's main-es2015.js; the page's
# XLSX download is corrupt server-side (see the module docstring).
DOWNLOAD_URL = (
    "https://www.newyorkfed.org/medialibrary/research/interactives/"
    "data/gscpi/gscpi_interactive_data.csv"
)

_VINTAGE_RE = re.compile(r"^[A-Z][a-z]{2}-\d{2}$")
_OBS_DATE_FMT = "%d-%b-%Y"  # e.g. 31-Aug-2026 (English month abbrev)


class GscpiFormatError(ValueError):
    """The NY Fed GSCPI file came back with an unexpected shape."""


def _request(url: str) -> str:
    """GET the data file; the single HTTP boundary of this module."""
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def _cache_path() -> str:
    return os.path.join(
        get_config()["data_cache_dir"], "gscpi", "gscpi_interactive_data.csv"
    )


def _parse_rows(text: str) -> list[tuple[date, float]]:
    """Parse the current (last vintage) column into (observation date, value).

    Raises GscpiFormatError on any deviation from the documented shape: the
    file is unversioned, so a format change must fail loudly rather than be
    cached or rendered as if it were data. Fully blank rows (the trailer)
    are skipped; vintage labels must be non-decreasing over time.
    """
    try:
        # StringIO so the parser never sees an HTML error page as input.
        frame = pd.read_csv(StringIO(text))
    except Exception as e:
        raise GscpiFormatError(
            f"New York Fed GSCPI download ({DOWNLOAD_URL}) is not parseable "
            f"CSV: {e}. The file format may have changed."
        ) from e
    columns = list(frame.columns)
    if len(columns) < 2 or columns[0] != "Date":
        raise GscpiFormatError(
            f"New York Fed GSCPI file ({DOWNLOAD_URL}) should have a 'Date' "
            f"observation column followed by vintage columns, got "
            f"{columns[:3]!r}. The file format may have changed."
        )
    vintages = [(c, datetime.strptime(c, "%b-%y").date()) for c in columns[1:]
                if _VINTAGE_RE.match(c)]
    if not vintages:
        raise GscpiFormatError(
            f"New York Fed GSCPI file ({DOWNLOAD_URL}) has no 'Mon-YY' "
            f"vintage column among {columns[1:]!r}. The file format may have "
            "changed."
        )
    for (prev_name, prev), (curr_name, curr) in zip(vintages, vintages[1:], strict=False):
        if curr < prev:
            raise GscpiFormatError(
                f"New York Fed GSCPI file ({DOWNLOAD_URL}): vintage columns "
                f"go backwards ({prev_name} before {curr_name}). The file "
                "format may have changed."
            )
    current_col = vintages[-1][0]

    rows: list[tuple[date, float]] = []
    for obs, value in zip(frame["Date"], frame[current_col], strict=True):
        if pd.isna(obs) and pd.isna(value):
            continue  # blank trailer row
        if pd.isna(value):
            continue  # month not yet published under a vintage (blank tail)
        try:
            obs_date = datetime.strptime(str(obs), _OBS_DATE_FMT).date()
        except ValueError as e:
            raise GscpiFormatError(
                f"New York Fed GSCPI file ({DOWNLOAD_URL}): observation date "
                f"{obs!r} is not DD-Mon-YYYY. The file format may have changed."
            ) from e
        if pd.isna(obs):
            raise GscpiFormatError(
                f"New York Fed GSCPI file ({DOWNLOAD_URL}): a row has a value "
                "in the current vintage but no observation date. The file "
                "format may have changed."
            )
        try:
            numeric = float(value)
        except (TypeError, ValueError) as e:
            raise GscpiFormatError(
                f"New York Fed GSCPI file ({DOWNLOAD_URL}): non-numeric "
                f"value {value!r} in vintage {current_col!r} for {obs!r}. "
                "The file format may have changed."
            ) from e
        rows.append((obs_date, numeric))
    return rows


def _load_rows() -> list[tuple[date, float]]:
    """Return parsed rows, from the cache when fresh.

    A download is parsed (and thereby validated) BEFORE it is cached: the
    feed is unversioned, so a format change must never be cached as data.
    """
    path = _cache_path()
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < CACHE_TTL.total_seconds():
        with open(path, encoding="utf-8") as f:
            return _parse_rows(f.read())
    text = _request(DOWNLOAD_URL)
    rows = _parse_rows(text)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return rows


def get_supply_chain_pressure(curr_date: str) -> str:
    """Fetch the NY Fed GSCPI as a markdown report.

    Args:
        curr_date: The as-of date (yyyy-mm-dd). Only observations on or
            before this date are used, so a historical run never sees future
            readings. (Values are as-published in today's vintage — see the
            module docstring for the revision/backtesting caveat.)

    Returns:
        A markdown report: the latest GSCPI reading with a plain-English
        interpretation, plus a table of recent monthly readings.
    """
    end_dt = datetime.strptime(curr_date, "%Y-%m-%d").date()

    try:
        rows = _load_rows()
    except GscpiFormatError as e:
        return f"ERROR: {e}"
    visible = [r for r in rows if r[0] <= end_dt]

    header = (
        "## Global Supply Chain Pressure Index (GSCPI)\n"
        "- Source: Federal Reserve Bank of New York, Global Supply Chain "
        "Pressure Index (standard deviations from average; monthly)\n"
        f"- As-of date: {end_dt} (observations after this date are excluded)\n"
    )
    if not visible:
        return header + (
            f"\nNo GSCPI observations on or before {end_dt}. The series "
            "starts in September 1997.\n"
        )

    latest_date, latest_value = visible[-1]
    direction = "above" if latest_value > 0 else "below"
    interpretation = (
        f"Latest reading ({latest_date:%Y-%m}): **{latest_value:.2f}** "
        f"standard deviations {direction} the historical average "
        + (
            "-- supply chains are under above-average pressure.\n"
            if latest_value > 0
            else "-- supply chains are under below-average pressure.\n"
        )
    )

    shown = visible
    note = ""
    if len(visible) > MAX_ROWS:
        shown = visible[-MAX_ROWS:]
        note = f"\n_(showing the most recent {MAX_ROWS} of {len(visible)} monthly readings)_\n"

    monthly = (
        "\n**Recent monthly readings:**\n"
        + note
        + "\n| Month | GSCPI (std devs) |\n"
        "| --- | --- |\n"
        + "\n".join(
            f"| {obs:%Y-%m} | {value:.2f} |" for obs, value in shown
        )
        + "\n"
    )

    return header + "\n" + interpretation + monthly
