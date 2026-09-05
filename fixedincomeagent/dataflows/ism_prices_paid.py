"""ISM Manufacturing Prices Index ("prices paid"): input-cost pressure.

LIMITATION — FORWARD-ONLY TRACKING, HISTORY PAYWALLED: ISM does not provide
free historical API access to the Prices Index (history is paywalled via
ismworld.org). This module implements FORWARD-ONLY monthly tracking: a
human appends the Prices Index reading from the public Manufacturing ISM
Report On Business press release to a LOCAL CSV each month:
``data_cache_dir/ism/prices_paid.csv``. BACKTEST COVERAGE STARTS ONLY WHEN
TRACKING BEGINS — no history exists before the first appended row. When the
file is absent the report says so and renders no data (not an error); a
malformed file fails loudly.

Expected CSV schema (one header row, one data row per month)::

    date,prices_index
    2026-07-31,64.8
    2026-08-31,68.0

``date`` is the month-END date (YYYY-MM-DD) of the report month;
``prices_index`` is the published ISM Manufacturing Prices Index reading
(a diffusion index: above 50 means prices generally expanding).

Point-in-time: ``curr_date`` filters to months ending on or before it.
"""
import csv
import io
import os
from datetime import date, datetime

from .config import get_config

# Months shown in the recent-months table.
RECENT_MONTHS = 12


class ISMFormatError(ValueError):
    """The local ISM prices paid CSV has an unexpected shape."""


def _csv_path() -> str:
    return os.path.join(
        get_config()["data_cache_dir"], "ism", "prices_paid.csv"
    )


def _parse(text: str, path: str) -> list[tuple[date, float]]:
    """Parse the local ISM CSV into (month-end date, Prices Index) rows.

    Raises ISMFormatError on any deviation from the documented schema: a
    wrong or corrupted file in the ingest directory must fail loudly rather
    than render as if it were the Prices Index.
    """
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or [c.strip() for c in rows[0][:2]] != ["date", "prices_index"]:
        raise ISMFormatError(
            f"ISM prices paid CSV ({path}) has an unexpected header: expected "
            "'date,prices_index', got "
            f"{str(rows[0][:3])[:120] if rows else 'an empty file'!r}. See "
            "the module docstring for the expected schema."
        )
    out = []
    for lineno, row in enumerate(rows[1:], start=2):
        if not row or all(not c.strip() for c in row):
            continue  # tolerate blank lines
        if len(row) != 2:
            raise ISMFormatError(
                f"ISM prices paid CSV ({path}) line {lineno}: expected 2 "
                f"columns (date,prices_index), got {len(row)}. See the "
                "module docstring for the expected schema."
            )
        try:
            d = datetime.strptime(row[0].strip(), "%Y-%m-%d").date()
        except ValueError as e:
            raise ISMFormatError(
                f"ISM prices paid CSV ({path}) line {lineno}: date "
                f"{row[0].strip()!r} is not 'YYYY-MM-DD'. See the module "
                "docstring for the expected schema."
            ) from e
        try:
            v = float(row[1].strip())
        except ValueError as e:
            raise ISMFormatError(
                f"ISM prices paid CSV ({path}) line {lineno}: index value "
                f"{row[1].strip()!r} is not numeric. See the module "
                "docstring for the expected schema."
            ) from e
        out.append((d, v))
    if not out:
        raise ISMFormatError(
            f"ISM prices paid CSV ({path}) has a header but no data rows. "
            "See the module docstring for the expected schema."
        )
    return sorted(out)


def _mom(change: float | None) -> str:
    return "" if change is None else f"{change:+.1f}"


def get_ism_prices_paid(curr_date: str) -> str:
    """Render the ISM Manufacturing Prices Index as a markdown report.

    Args:
        curr_date: The as-of date (yyyy-mm-dd). Only months ending on or
            before this date are used, so a historical run never sees future
            months.

    Returns:
        A markdown report: the latest Prices Index reading and
        month-over-month change, plus a table of recent months. When the
        local CSV does not exist, the report says the manually maintained
        (forward-only) source is currently unavailable and renders no data
        (not an error); a malformed CSV returns an ERROR report naming the
        problem.
    """
    end_dt = datetime.strptime(curr_date, "%Y-%m-%d").date()
    path = _csv_path()

    header = (
        "## ISM Prices Paid\n"
        "- Source: ISM Manufacturing Prices Index (monthly diffusion index) "
        "— manually maintained local CSV, forward-only tracking; historical "
        "data paywalled (see module docstring)\n"
        f"- As-of date: {end_dt} (months ending after this date are excluded)\n"
        "- Readings above 50 indicate prices generally expanding; below 50, "
        "contracting\n"
    )

    if not os.path.exists(path):
        return header + (
            "\nISM prices paid data not available locally. This source is "
            "manually maintained with forward-only monthly tracking: append "
            "the Prices Index reading from each Manufacturing ISM Report On "
            "Business press release (ismworld.org) to "
            f"{path} (schema in the module docstring). Backtest coverage "
            "starts only when tracking begins.\n"
        )

    with open(path, encoding="utf-8-sig") as f:
        try:
            rows = [r for r in _parse(f.read(), path) if r[0] <= end_dt]
        except ISMFormatError as e:
            return f"ERROR: {e}"

    if not rows:
        return header + f"\nNo ISM prices paid observations on or before {end_dt}.\n"

    by_month = {(d.year, d.month): v for d, v in rows}
    mom = {}
    months = sorted(by_month)
    for prev, cur in zip(months, months[1:], strict=False):
        if (cur[0] - prev[0]) * 12 + cur[1] - prev[1] == 1:
            mom[cur] = by_month[cur] - by_month[prev]

    d, v = rows[-1]
    latest = (
        "\n**Latest reading:**\n\n"
        "| Month | Prices Index | MoM |\n"
        "| --- | --- | --- |\n"
        f"| {d.year}-{d.month:02d} | {v:.1f} | "
        f"{_mom(mom.get((d.year, d.month)))} |\n"
    )

    shown = months[-RECENT_MONTHS:]
    note = ""
    if len(months) > RECENT_MONTHS:
        note = (
            f"\n_(showing the most recent {len(shown)} of {len(months)} "
            "months)_\n"
        )
    table = (
        "\n**Recent months:**\n"
        + note
        + "\n| Month | Prices Index | MoM |\n"
        "| --- | --- | --- |\n"
        + "\n".join(
            f"| {y}-{m:02d} | {by_month[(y, m)]:.1f} | {_mom(mom.get((y, m)))} |"
            for y, m in shown
        )
        + "\n"
    )

    return header + latest + table
