"""Treasury curve equal-weight benchmark calculation for Fixed Income reflection.

Provides performance measurement for fixed-income decisions:
- Fetches 2Y, 5Y, 10Y, 30Y Treasury yields from FRED (DGS2, DGS5, DGS10, DGS30)
- Computes per-tenor yield changes over the holding window
- Computes equal-weight benchmark yield change across the curve
- Evaluates directional hit rate and alpha vs the equal-weight curve benchmark
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Any

from fixedincomeagent.dataflows.fred import _request

logger = logging.getLogger(__name__)

DEFAULT_FI_TENOR_SERIES: dict[str, str] = {
    "2Y": "DGS2",
    "5Y": "DGS5",
    "10Y": "DGS10",
    "30Y": "DGS30",
}

DIRECTION_SYNONYMS: dict[str, str] = {
    "up": "up",
    "higher": "up",
    "bull": "up",  # yield up / bearish bond price
    "down": "down",
    "lower": "down",
    "bear": "down",  # yield down / bullish bond price
    "neutral": "neutral",
    "flat": "neutral",
    "unchanged": "neutral",
}

_DIRECTION_CALL_RE = re.compile(
    r"\*\*(2Y|5Y|10Y|30Y)\*\*:\s*([a-zA-Z]+)",
    re.IGNORECASE,
)


def parse_direction_calls(decisions: str | dict[str, str] | None) -> dict[str, str]:
    """Extract normalized per-tenor direction calls from markdown or a dictionary."""
    if not decisions:
        return {}

    calls: dict[str, str] = {}
    if isinstance(decisions, dict):
        for k, v in decisions.items():
            norm_key = k.strip().upper()
            norm_val = DIRECTION_SYNONYMS.get(str(v).strip().lower())
            if norm_key in DEFAULT_FI_TENOR_SERIES and norm_val:
                calls[norm_key] = norm_val
        return calls

    if isinstance(decisions, str):
        for match in _DIRECTION_CALL_RE.finditer(decisions):
            tenor = match.group(1).upper()
            raw_dir = match.group(2).lower()
            norm_dir = DIRECTION_SYNONYMS.get(raw_dir)
            if tenor in DEFAULT_FI_TENOR_SERIES and norm_dir:
                calls[tenor] = norm_dir

    return calls


def evaluate_directional_hit(
    predicted_direction: str,
    actual_delta_bp: float,
    neutral_threshold_bp: float = 5.0,
) -> bool:
    """Evaluate whether an individual tenor direction prediction was correct."""
    pred = DIRECTION_SYNONYMS.get(predicted_direction.strip().lower(), "")
    if pred == "up":
        return actual_delta_bp > neutral_threshold_bp
    if pred == "down":
        return actual_delta_bp < -neutral_threshold_bp
    if pred == "neutral":
        return abs(actual_delta_bp) <= neutral_threshold_bp
    return False


def _fetch_tenor_observations(
    series_id: str,
    start_date: str,
    end_date: str,
) -> list[tuple[str, float]]:
    """Fetch and filter valid numeric observations from FRED."""
    params = {
        "series_id": series_id,
        "observation_start": start_date,
        "observation_end": end_date,
        "sort_order": "asc",
    }
    data = _request("series/observations", params)
    observations = data.get("observations", [])

    valid: list[tuple[str, float]] = []
    for obs in observations:
        val = obs.get("value")
        if val not in (None, "", "."):
            try:
                valid.append((obs["date"], float(val)))
            except (ValueError, TypeError):
                continue
    return valid


def calculate_treasury_curve_benchmark(
    trade_date: str,
    holding_days: int = 5,
    resolution_date: str | None = None,
    decisions: str | dict[str, str] | None = None,
    neutral_threshold_bp: float = 5.0,
    tenor_series: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """Calculate Treasury curve benchmark yield changes and decision hit-rate.

    Args:
        trade_date: Beginning trade date (YYYY-MM-DD).
        holding_days: Required trading days for holding period (default 5).
        resolution_date: Optional explicit resolution date.
        decisions: Markdown decision string or dict of tenor direction calls.
        neutral_threshold_bp: Threshold for neutral band in bp (default 5.0).
        tenor_series: Optional custom tenor to series map.

    Returns:
        Structured result dict or None if observations are insufficient or unavailable.
    """
    series_map = tenor_series or DEFAULT_FI_TENOR_SERIES

    try:
        start_dt = datetime.strptime(trade_date, "%Y-%m-%d")
        if resolution_date:
            end_str = resolution_date
        else:
            # Buffer for weekends and holidays
            end_dt = start_dt + timedelta(days=holding_days + 14)
            end_str = end_dt.strftime("%Y-%m-%d")

        tenor_obs: dict[str, list[tuple[str, float]]] = {}
        for tenor, series_id in series_map.items():
            obs = _fetch_tenor_observations(series_id, trade_date, end_str)
            # Must have at least trade date and holding window observations
            if len(obs) <= holding_days:
                logger.info(
                    "Insufficient observations for %s (%d <= %d holding days)",
                    series_id, len(obs), holding_days,
                )
                return None
            tenor_obs[tenor] = obs

        # Resolve start, end, and resolution_date across tenors
        tenor_changes: dict[str, dict[str, float]] = {}
        res_dates: set[str] = set()

        for tenor in series_map:
            obs = tenor_obs[tenor]
            start_val = obs[0][1]
            end_val = obs[holding_days][1]
            res_date = obs[holding_days][0]
            res_dates.add(res_date)
            delta_bp = round((end_val - start_val) * 100.0, 2)
            tenor_changes[tenor] = {
                "start_yield": start_val,
                "end_yield": end_val,
                "delta_bp": delta_bp,
            }

        resolved_date = max(res_dates) if res_dates else end_str
        benchmark_bp = round(
            sum(t["delta_bp"] for t in tenor_changes.values()) / len(tenor_changes),
            2,
        )

        parsed_calls = parse_direction_calls(decisions)
        if parsed_calls:
            hits: dict[str, bool] = {}
            strategy_deltas: list[float] = []
            for tenor, call in parsed_calls.items():
                if tenor in tenor_changes:
                    delta = tenor_changes[tenor]["delta_bp"]
                    is_hit = evaluate_directional_hit(call, delta, neutral_threshold_bp)
                    hits[tenor] = is_hit

                    sign = 1.0 if call == "up" else (-1.0 if call == "down" else 0.0)
                    strategy_deltas.append(sign * delta)

            total_calls = len(hits)
            hit_count = sum(1 for h in hits.values() if h)
            hit_rate = f"hit:{hit_count}/{total_calls}" if total_calls > 0 else "n/a"

            strategy_bp = (
                round(sum(strategy_deltas) / len(strategy_deltas), 2)
                if strategy_deltas
                else 0.0
            )
            alpha_bp = round(strategy_bp - benchmark_bp, 2)
        else:
            hits = {}
            hit_rate = "n/a"
            strategy_bp = 0.0
            alpha_bp = 0.0

        return {
            "trade_date": trade_date,
            "resolution_date": resolved_date,
            "holding_days": holding_days,
            "tenor_changes": tenor_changes,
            "benchmark_bp": benchmark_bp,
            "strategy_bp": strategy_bp,
            "alpha_bp": alpha_bp,
            "hit_rate": hit_rate,
            "hits": hits,
        }

    except Exception as e:
        logger.warning(
            "Could not calculate Treasury curve benchmark for %s (will retry): %s",
            trade_date, e,
        )
        return None
