"""Pre-computed curve spreads tool.

Eliminates LLM arithmetic hallucinations by computing spreads in Python
from the Treasury par yield curve, then returning a markdown report the
LLM can cite verbatim.
"""
import re
from typing import Annotated

from langchain_core.tools import tool

from fixedincomeagent.dataflows.config import get_config
from fixedincomeagent.dataflows.interface import route_to_vendor


def _parse_latest_yields(report: str) -> dict[str, float]:
    """Extract the latest-curve yields from a par-yield markdown report.

    Looks for the ``**Latest curve (...):**`` block and parses the
    ``| Tenor | Yield % |`` table that follows it.
    """
    yields: dict[str, float] = {}
    in_table = False
    for line in report.splitlines():
        if "Latest curve" in line:
            in_table = True
            continue
        if in_table and line.startswith("|"):
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) == 2 and parts[0] != "Tenor":
                try:
                    yields[parts[0]] = float(parts[1])
                except ValueError:
                    continue
        elif in_table and not line.startswith("|") and line.strip():
            break  # end of table
    return yields


# Map config tenor labels ("2Y") to the par-yield CSV header names ("2 Yr").
_TENOR_TO_CSV = {
    "1M": "1 Mo", "2M": "2 Mo", "3M": "3 Mo", "4M": "4 Mo", "6M": "6 Mo",
    "1Y": "1 Yr", "2Y": "2 Yr", "3Y": "3 Yr", "5Y": "5 Yr", "7Y": "7 Yr",
    "10Y": "10 Yr", "20Y": "20 Yr", "30Y": "30 Yr",
}


@tool
def get_curve_spreads(
    curr_date: Annotated[str, "As-of date in yyyy-mm-dd format"],
    look_back_days: Annotated[
        int, "Trailing window length in days; omit for a 90-day window"
    ] = 90,
) -> str:
    """
    Compute Treasury yield-curve spreads and butterflies from the par yield
    curve. Returns exact, pre-computed values in basis points — use these
    numbers verbatim in your report instead of doing arithmetic yourself.

    Args:
        curr_date (str): As-of date in yyyy-mm-dd format
        look_back_days (int): Trailing window length; omit for a 90-day window

    Returns:
        str: A markdown table of pre-computed spreads with the formula shown.
    """
    report = route_to_vendor("get_treasury_par_yields", curr_date, look_back_days)
    if report.startswith("ERROR"):
        return f"Spread computation unavailable: par yield data error. {report}"

    yields = _parse_latest_yields(report)
    if not yields:
        return "Spread computation unavailable: could not parse par yield curve."

    cfg = get_config()
    definitions = cfg.get("fi_spread_definitions", {})

    # Extract the as-of date from the report header.
    date_match = re.search(r"Latest curve \((\d{4}-\d{2}-\d{2})\)", report)
    as_of = date_match.group(1) if date_match else curr_date

    lines = [
        "## Pre-Computed Curve Spreads",
        f"- Source: Treasury par yield curve (as-of {as_of})",
        "- Computed by: Python (deterministic arithmetic)",
        "",
        "| Spread | Value (bp) | Formula | Inputs |",
        "| --- | --- | --- | --- |",
    ]

    for name, legs in definitions.items():
        csv_legs = [_TENOR_TO_CSV.get(t, t) for t in legs]
        vals = [yields.get(cl) for cl in csv_legs]

        if any(v is None for v in vals):
            missing = [cl for cl, v in zip(csv_legs, vals) if v is None]
            lines.append(f"| {name} | N/A | — | Missing: {', '.join(missing)} |")
            continue

        if len(legs) == 2:
            # Simple spread: long - short
            spread_pct = vals[1] - vals[0]
            spread_bp = round(spread_pct * 100)
            formula = f"{csv_legs[1]} - {csv_legs[0]}"
            inputs = f"{vals[1]:.2f}% - {vals[0]:.2f}%"
            lines.append(f"| {name} | {spread_bp:+d} | {formula} | {inputs} |")
        elif len(legs) == 3:
            # Butterfly: 2 × belly - (wing1 + wing2)
            belly_val = vals[1]
            wing_sum = vals[0] + vals[2]
            spread_pct = (belly_val * 2) - wing_sum
            spread_bp = round(spread_pct * 100)
            formula = f"2×{csv_legs[1]} - ({csv_legs[0]} + {csv_legs[2]})"
            inputs = f"2×{belly_val:.2f}% - ({vals[0]:.2f}% + {vals[2]:.2f}%)"
            lines.append(f"| {name} | {spread_bp:+d} | {formula} | {inputs} |")

    lines.append("")
    lines.append(
        "**Use these pre-computed values verbatim in your report.** "
        "Do not recalculate them."
    )

    return "\n".join(lines)
