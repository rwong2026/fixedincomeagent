"""Manheim Used Vehicle Value Index: wholesale used-vehicle prices.

LIMITATION — MANUAL LOW-FREQUENCY INGEST: Manheim/Cox Automotive provides
NO free structured feed or public API for this series. The monthly index
value is published in press releases on coxautoinc.com/insights/. This
module therefore reads a LOCAL CSV that a human updates by hand once a
month: ``data_cache_dir/manheim/used_vehicle_index.csv``. When the file is
absent the report says so and renders no data (not an error); a malformed
file fails loudly.

Expected CSV schema (one header row, one data row per month)::

    date,index_value
    2026-06-30,210.4
    2026-07-31,211.0

``date`` is the month-END date (YYYY-MM-DD) of the index month;
``index_value`` is the published Manheim Used Vehicle Value Index level.

Point-in-time: ``curr_date`` filters to months ending on or before it.
Because the file is maintained by hand from press releases, its rows are
only as point-in-time as the maintainer's discipline — archive the CSV each
month if strict backtesting matters.
"""
import csv
import io
import os
from datetime import date, datetime

from .config import get_config

# Months shown in the recent-months table.
RECENT_MONTHS = 12


class ManheimFormatError(ValueError):
    """The local Manheim index CSV has an unexpected shape."""


def _csv_path() -> str:
    return os.path.join(
        get_config()["data_cache_dir"], "manheim", "used_vehicle_index.csv"
    )


def _parse(text: str, path: str) -> list[tuple[date, float]]:
    """Parse the local Manheim CSV into (month-end date, index) rows.

    Raises ManheimFormatError on any deviation from the documented schema:
    a wrong or corrupted file in the ingest directory must fail loudly
    rather than render as if it were the index.
    """
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or [c.strip() for c in rows[0][:2]] != ["date", "index_value"]:
        raise ManheimFormatError(
            f"Manheim index CSV ({path}) has an unexpected header: expected "
            "'date,index_value', got "
            f"{str(rows[0][:3])[:120] if rows else 'an empty file'!r}. See "
            "the module docstring for the expected schema."
        )
    out = []
    for lineno, row in enumerate(rows[1:], start=2):
        if not row or all(not c.strip() for c in row):
            continue  # tolerate blank lines
        if len(row) != 2:
            raise ManheimFormatError(
                f"Manheim index CSV ({path}) line {lineno}: expected 2 "
                f"columns (date,index_value), got {len(row)}. See the module "
                "docstring for the expected schema."
            )
        try:
            d = datetime.strptime(row[0].strip(), "%Y-%m-%d").date()
        except ValueError as e:
            raise ManheimFormatError(
                f"Manheim index CSV ({path}) line {lineno}: date "
                f"{row[0].strip()!r} is not 'YYYY-MM-DD'. See the module "
                "docstring for the expected schema."
            ) from e
        try:
            v = float(row[1].strip())
        except ValueError as e:
            raise ManheimFormatError(
                f"Manheim index CSV ({path}) line {lineno}: index value "
                f"{row[1].strip()!r} is not numeric. See the module "
                "docstring for the expected schema."
            ) from e
        out.append((d, v))
    if not out:
        raise ManheimFormatError(
            f"Manheim index CSV ({path}) has a header but no data rows. "
            "See the module docstring for the expected schema."
        )
    return sorted(out)


def _by_month(rows: list[tuple[date, float]]) -> dict[tuple[int, int], float]:
    return {(d.year, d.month): v for d, v in rows}


def _pct(growth: float | None) -> str:
    return "" if growth is None else f"{growth * 100:+.1f}%"


def get_used_vehicle_index(curr_date: str) -> str:
    """Render the Manheim Used Vehicle Value Index as a markdown report.

    Args:
        curr_date: The as-of date (yyyy-mm-dd). Only months ending on or
            before this date are used, so a historical run never sees future
            months.

    Returns:
        A markdown report: the latest index level and year-over-year change,
        plus a table of recent months. When the local CSV does not exist,
        the report says the manually maintained source is currently
        unavailable and renders no data (not an error); a malformed CSV
        returns an ERROR report naming the problem.
    """
    end_dt = datetime.strptime(curr_date, "%Y-%m-%d").date()
    path = _csv_path()

    header = (
        "## Manheim Used Vehicle Index\n"
        "- Source: Manheim Used Vehicle Value Index (wholesale used-vehicle "
        "prices, monthly) — manually maintained local CSV; no free API "
        "(see module docstring)\n"
        f"- As-of date: {end_dt} (months ending after this date are excluded)\n"
    )

    if not os.path.exists(path):
        return header + (
            "\nManheim used vehicle index data not available locally. This "
            "source is manually maintained: transcribe the monthly index "
            "value from the latest Cox Automotive press release "
            f"(coxautoinc.com/insights/) into {path} (schema in the module "
            "docstring) to enable this report.\n"
        )

    with open(path, encoding="utf-8-sig") as f:
        try:
            rows = [r for r in _parse(f.read(), path) if r[0] <= end_dt]
        except ManheimFormatError as e:
            return f"ERROR: {e}"

    if not rows:
        return header + f"\nNo Manheim index observations on or before {end_dt}.\n"

    by_month = _by_month(rows)
    yoy = {
        (y, m): v / by_month[(y - 1, m)] - 1
        for (y, m), v in by_month.items()
        if (y - 1, m) in by_month
    }

    d, v = rows[-1]
    latest = (
        "\n**Latest reading:**\n\n"
        "| Month | Index | YoY |\n"
        "| --- | --- | --- |\n"
        f"| {d.year}-{d.month:02d} | {v:.1f} | "
        f"{_pct(yoy.get((d.year, d.month)))} |\n"
    )

    months = sorted(by_month)
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
        + "\n| Month | Index | YoY |\n"
        "| --- | --- | --- |\n"
        + "\n".join(
            f"| {y}-{m:02d} | {by_month[(y, m)]:.1f} | {_pct(yoy.get((y, m)))} |"
            for y, m in shown
        )
        + "\n"
    )

    return header + latest + table
