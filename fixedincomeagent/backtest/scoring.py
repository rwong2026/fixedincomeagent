"""Backtest scoring (Task 7.3): score predicted calls against realized outcomes.

Pure scoring over ``BacktestRun`` objects produced by the Task 7.1 runner —
no network, no config.

Semantics
---------
Hit rule (direction and shape, symmetric): a call is a hit iff the predicted
label exactly equals the actual label. A predicted up/down landing on a
neutral actual is a miss; a predicted neutral landing on an up/down actual
is also a miss; neutral-vs-neutral is a hit. Same rule for shape with
steepen/flatten/unchanged.

Scorable calls: a direction call is scored only when its tenor appears in
``actual_direction``; a shape call only when its spread appears in
``actual_shape``. Magnitude is scored only when the tenor also appears in
``actual_yield_changes_bp``. Unscorable calls are skipped (not counted as
misses).

Magnitude buckets use the absolute realized change with the same boundaries
as ``DirectionCall.magnitude_bucket``: |Δ| < 10bp -> ``<10bp``;
10bp <= |Δ| < 25bp -> ``10-25bp``; |Δ| >= 25bp -> ``25bp+``.

Calibration pools direction and shape calls (both carry a confidence) into
ten decile bins, structured for a reliability diagram: each bin reports its
count, mean predicted confidence, and empirical hit rate.

Empty input (or any zero-denominator rate) is defined as 0.0 — no exceptions.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from fixedincomeagent.backtest.runner import BacktestRun

_N_CAL_BINS = 10


@dataclass
class CalibrationBin:
    """One confidence decile for a reliability diagram."""

    lower: float  # inclusive
    upper: float  # exclusive, except the top bin which also includes 1.0
    count: int = 0
    mean_confidence: float = 0.0  # 0.0 when empty
    empirical_hit_rate: float = 0.0  # 0.0 when empty


@dataclass
class BacktestScorecard:
    """Flat, printable aggregate over a list of BacktestRun."""

    n_runs: int = 0
    n_direction_calls: int = 0
    n_direction_hits: int = 0
    n_shape_calls: int = 0
    n_shape_hits: int = 0
    per_tenor_hit_rate: dict[str, float] = field(default_factory=dict)
    per_tenor_calls: dict[str, int] = field(default_factory=dict)
    per_spread_hit_rate: dict[str, float] = field(default_factory=dict)
    per_spread_calls: dict[str, int] = field(default_factory=dict)
    calibration_bins: list[CalibrationBin] = field(default_factory=list)
    n_magnitude_calls: int = 0
    n_magnitude_hits: int = 0
    magnitude_accuracy: float = 0.0


def _bucketize_change(change_bp: float) -> str:
    """Magnitude bucket of a realized bp change (absolute value)."""
    a = abs(change_bp)
    if a < 10:
        return "<10bp"
    if a < 25:
        return "10-25bp"
    return "25bp+"


def _cal_bin_index(confidence: float) -> int:
    """Decile index; confidence 1.0 lands in the top bin."""
    return min(int(confidence * _N_CAL_BINS), _N_CAL_BINS - 1)


def _rate(hits: int, total: int) -> float:
    return hits / total if total else 0.0


def score_backtest(results: list[BacktestRun]) -> BacktestScorecard:
    """Score replayed runs into an aggregate BacktestScorecard."""
    tenor_hits: Counter[str] = Counter()
    tenor_n: Counter[str] = Counter()
    spread_hits: Counter[str] = Counter()
    spread_n: Counter[str] = Counter()
    bin_confs: list[list[float]] = [[] for _ in range(_N_CAL_BINS)]
    bin_hits = [0] * _N_CAL_BINS
    mag_hits = mag_n = 0

    def _cal_record(confidence: float, hit: bool) -> None:
        i = _cal_bin_index(confidence)
        bin_confs[i].append(confidence)
        bin_hits[i] += hit

    for run in results:
        for call in run.direction_calls:
            actual = run.actual_direction.get(call.tenor)
            if actual is None:
                continue
            hit = call.direction == actual
            tenor_n[call.tenor] += 1
            tenor_hits[call.tenor] += hit
            _cal_record(call.confidence, hit)
            change = run.actual_yield_changes_bp.get(call.tenor)
            if change is not None:
                mag_n += 1
                mag_hits += _bucketize_change(change) == call.magnitude_bucket
        for call in run.shape_calls:
            actual = run.actual_shape.get(call.spread)
            if actual is None:
                continue
            hit = call.shape == actual
            spread_n[call.spread] += 1
            spread_hits[call.spread] += hit
            _cal_record(call.confidence, hit)

    bins = [
        CalibrationBin(
            lower=i / _N_CAL_BINS,
            upper=(i + 1) / _N_CAL_BINS,
            count=len(bin_confs[i]),
            mean_confidence=(
                sum(bin_confs[i]) / len(bin_confs[i]) if bin_confs[i] else 0.0
            ),
            empirical_hit_rate=_rate(bin_hits[i], len(bin_confs[i])),
        )
        for i in range(_N_CAL_BINS)
    ]
    return BacktestScorecard(
        n_runs=len(results),
        n_direction_calls=sum(tenor_n.values()),
        n_direction_hits=sum(tenor_hits.values()),
        n_shape_calls=sum(spread_n.values()),
        n_shape_hits=sum(spread_hits.values()),
        per_tenor_hit_rate={t: _rate(tenor_hits[t], n) for t, n in tenor_n.items()},
        per_tenor_calls=dict(tenor_n),
        per_spread_hit_rate={s: _rate(spread_hits[s], n) for s, n in spread_n.items()},
        per_spread_calls=dict(spread_n),
        calibration_bins=bins,
        n_magnitude_calls=mag_n,
        n_magnitude_hits=mag_hits,
        magnitude_accuracy=_rate(mag_hits, mag_n),
    )


def render(sc: BacktestScorecard) -> str:
    """Markdown summary of a scorecard."""
    lines = [
        "# Backtest Scorecard",
        "",
        f"Runs: {sc.n_runs} | "
        f"Direction: {sc.n_direction_hits}/{sc.n_direction_calls} hits | "
        f"Shape: {sc.n_shape_hits}/{sc.n_shape_calls} hits | "
        f"Magnitude: {sc.n_magnitude_hits}/{sc.n_magnitude_calls} "
        f"({sc.magnitude_accuracy:.1%})",
        "",
        "## Direction hit rate (per tenor)",
        "",
        "| Tenor | Calls | Hit rate |",
        "|---|---|---|",
        *(
            f"| {t} | {sc.per_tenor_calls[t]} | {r:.1%} |"
            for t, r in sc.per_tenor_hit_rate.items()
        ),
        "",
        "## Shape hit rate (per spread)",
        "",
        "| Spread | Calls | Hit rate |",
        "|---|---|---|",
        *(
            f"| {s} | {sc.per_spread_calls[s]} | {r:.1%} |"
            for s, r in sc.per_spread_hit_rate.items()
        ),
        "",
        "## Confidence Calibration (deciles)",
        "",
        "| Bin | Calls | Mean confidence | Empirical hit rate |",
        "|---|---|---|---|",
        *(
            f"| [{b.lower:.1f}, {b.upper:.1f}) | {b.count} | "
            f"{b.mean_confidence:.1%} | {b.empirical_hit_rate:.1%} |"
            for b in sc.calibration_bins
        ),
    ]
    return "\n".join(lines)
