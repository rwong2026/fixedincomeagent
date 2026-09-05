"""Baseline comparisons (Task 7.4): the two bars every scorecard must beat.

1. ``no_change_baseline`` — predict "neutral" for every configured tenor and
   "unchanged" for every configured spread. This is the TRIVIAL bar: over a
   20-trading-day horizon yields are close to a random walk, so a flat
   no-change forecast is always competitive.
2. ``forwards_implied_baseline`` — predict the move implied by the forward
   curve. This is the REAL bar: the forward curve embeds the market's
   unbiased estimate of future rates. **Beating only the no-change baseline
   proves very little; if the agent system doesn't beat the forwards-implied
   baseline, the added complexity isn't justified.**

Forwards math
-------------
For tenor with maturity P years and horizon h = ``fi_horizon_days``/252 years,
the implied forward yield is the front-of-curve arbitrage-free forward rate
for the P-year rate h years out. The code uses the linear par-yield form
(standard money-market approximation):

    f(h->P) = (P*y_P - h*y_h) / (P-h),
    implied change = f - y_P

where y_h is the curve yield at maturity h. With h = 20/252 below the
shortest published par point (1 Mo), y_h is taken as the 1 Mo yield — an
approximation (the exact form uses the continuous zero rate at h), error
sub-bp at these slopes. The exact continuously-compounded form is

    f(h->P) = (P*z(P) - h*z(h)) / (P-h),

with z the zero curve; using linear par yields for z is the second, standard
money-market approximation — and the right choice here: only the linear form
implies exactly zero change on a flat curve (the ln(1+·) form does not).

Economic reading: for a linear curve y(x) = y0 + s*x (so y_P - y_h =
s*(P-m), m = 1/12y) the implied change collapses to h*(y_P - y_h)/(P-h) =
s*h*(P-m)/(P-h) — ~s*h and essentially tenor-independent, so
a mild +/-10bp/year slope implies only ~+/-0.8bp over 20 trading days
("neutral" under the default 5bp threshold). That is the sane bar for a
random-walk-dominated horizon. (The earlier terminal-stub forward over
[P-h, P] is a valid rate — the market's implied ~1-month rate P-h years out —
but its implied change scales with maturity, not horizon, so it is not the
horizon baseline this scorecard compares against.)

Data source: the Treasury.gov daily par yield curve CSV (``dataflows.treasury``
— keyless, point-in-time safe: past years are final and cached). The FRED
``fi_tenor_series`` set (DGS2/5/10/30) cannot supply y_h (nothing below 2Y);
the par curve CSV carries 1 Mo..30 Yr. DGS series republish these same CMT
yields, so the baseline's curve matches the runner's actuals series.

Classification reuses the runner's threshold semantics
(``fi_neutral_threshold_bp``: moves below the threshold are neutral,
exactly-at-threshold is directional) and the scorer's magnitude buckets, so
baseline and agent calls are classified identically.

Confidence: both baselines emit a flat 0.5 — a baseline carries no conviction
information, and 0.5 parks every call in the same calibration decile so the
scorecard's calibration view stays honest.

``BaselineRun.implied_changes_bp`` records the numeric per-tenor implied
changes (all zeros for no-change) for audit and Phase 7 reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from fixedincomeagent.agents.schemas import DirectionCall, ShapeCall
from fixedincomeagent.backtest.runner import (
    BacktestRun,
    _classify_direction,
    _classify_shape,
)
from fixedincomeagent.backtest.scoring import _bucketize_change
from fixedincomeagent.dataflows.config import get_config
from fixedincomeagent.dataflows.treasury import _load_yield_csv, _parse_yield_csv

_BASELINE_CONFIDENCE = 0.5

_TRADING_DAYS_PER_YEAR = 252

# Snap-back window so a baseline curve exists even when test_date falls on a
# weekend/holiday (mirrors runner._BASELINE_LOOKBACK_DAYS).
_ASOF_LOOKBACK_DAYS = 14

# Treasury CSV tenor labels -> maturity in years.
_CSV_TENOR_YEARS = {
    "1 Mo": 1 / 12, "2 Mo": 2 / 12, "3 Mo": 0.25, "4 Mo": 4 / 12,
    "6 Mo": 0.5, "1 Yr": 1.0, "2 Yr": 2.0, "3 Yr": 3.0, "5 Yr": 5.0,
    "7 Yr": 7.0, "10 Yr": 10.0, "20 Yr": 20.0, "30 Yr": 30.0,
}


@dataclass
class BaselineRun:
    """One baseline's predictions for a test date (scorer-ready call lists)."""

    test_date: str
    direction_calls: list[DirectionCall]
    shape_calls: list[ShapeCall]
    implied_changes_bp: dict[str, float] = field(default_factory=dict)


def _tenor_years(tenor: str) -> float:
    """Maturity in years of a configured tenor label like ``"10Y"``."""
    return float(tenor.removesuffix("Y"))


def _implied_change_bp(y_p: float, p: float, y_h: float, h: float) -> float:
    """Front-of-curve forward minus spot, in bp (see module docs)."""
    forward = (p * y_p - h * y_h) / (p - h)
    return (forward - y_p) * 10000


def _spot_curve(test_date: str) -> dict[float, float]:
    """Par curve as of test_date: maturity (years) -> yield (decimal).

    Point-in-time: only rows dated on/before test_date are used; past-year
    CSVs are final, so latest data is the point-in-time data.
    """
    day = datetime.strptime(test_date, "%Y-%m-%d").date()
    start_year = (day - timedelta(days=_ASOF_LOOKBACK_DAYS)).year
    rows = []
    for year in range(start_year, day.year + 1):
        _tenors, year_rows = _parse_yield_csv(_load_yield_csv(year))
        rows.extend(year_rows)
    dated = [(d, vals) for d, vals in rows if d <= day]
    if not dated:
        raise ValueError(f"no par curve observation on/before {test_date}")
    _, vals = max(dated, key=lambda dv: dv[0])
    curve = {}
    for label, raw in vals.items():
        if label in _CSV_TENOR_YEARS:
            try:
                curve[_CSV_TENOR_YEARS[label]] = float(raw) / 100
            except ValueError:
                continue
    return curve


def _direction_call(tenor: str, change_bp: float, threshold: float,
                    rationale: str) -> DirectionCall:
    return DirectionCall(
        tenor=tenor,
        direction=_classify_direction(change_bp, threshold),
        magnitude_bucket=_bucketize_change(change_bp),
        confidence=_BASELINE_CONFIDENCE,
        rationale=rationale,
    )


def _shape_calls(changes_bp: dict[str, float], spreads: dict,
                 threshold: float, rationale: str) -> list[ShapeCall]:
    """Shape calls from per-tenor implied changes; runner spread semantics."""
    calls = []
    for name, legs in spreads.items():
        if any(tenor not in changes_bp for tenor in legs):
            continue  # spread references a tenor outside the configured set
        if len(legs) == 2:
            short, long_ = legs
            delta = changes_bp[long_] - changes_bp[short]
        else:  # butterfly: belly vs wings average (runner semantics)
            wing1, belly, wing2 = legs
            delta = changes_bp[belly] - (changes_bp[wing1] + changes_bp[wing2]) / 2
        calls.append(ShapeCall(
            spread=name,
            shape=_classify_shape(delta, threshold),
            confidence=_BASELINE_CONFIDENCE,
            rationale=rationale,
        ))
    return calls


def no_change_baseline(
    test_dates: list[str], config: dict | None = None
) -> list[BaselineRun]:
    """Random-walk prior: "neutral"/"unchanged" everywhere, zero implied move.

    Uses no market data at all, so point-in-time discipline is trivial.
    """
    config = config if config is not None else get_config()
    rationale = "no-change baseline: random-walk prior"
    runs = []
    for test_date in test_dates:
        runs.append(BaselineRun(
            test_date=test_date,
            direction_calls=[
                DirectionCall(
                    tenor=tenor,
                    direction="neutral",
                    magnitude_bucket="<10bp",
                    confidence=_BASELINE_CONFIDENCE,
                    rationale=rationale,
                )
                for tenor in config["fi_tenor_series"]
            ],
            shape_calls=[
                ShapeCall(
                    spread=name,
                    shape="unchanged",
                    confidence=_BASELINE_CONFIDENCE,
                    rationale=rationale,
                )
                for name in config["fi_spread_definitions"]
            ],
            implied_changes_bp=dict.fromkeys(config["fi_tenor_series"], 0.0),
        ))
    return runs


def forwards_implied_baseline(
    test_dates: list[str], config: dict | None = None
) -> list[BaselineRun]:
    """Forward-curve-implied moves over the horizon (see module docstring)."""
    config = config if config is not None else get_config()
    h = int(config["fi_horizon_days"]) / _TRADING_DAYS_PER_YEAR
    threshold = float(config["fi_neutral_threshold_bp"])
    runs = []
    for test_date in test_dates:
        curve = _spot_curve(test_date)
        # h (20/252y) is below the shortest published par point (1 Mo), so
        # y_h is approximated by the 1 Mo yield (see module docstring).
        y_h = curve[min(curve)]
        changes = {}
        for tenor in config["fi_tenor_series"]:
            p = _tenor_years(tenor)
            changes[tenor] = _implied_change_bp(curve[p], p, y_h, h)
        rationale = (
            f"forward-curve-implied move over {config['fi_horizon_days']}d "
            "from the daily par curve"
        )
        runs.append(BaselineRun(
            test_date=test_date,
            direction_calls=[
                _direction_call(tenor, change, threshold, rationale)
                for tenor, change in changes.items()
            ],
            shape_calls=_shape_calls(changes, config["fi_spread_definitions"],
                                     threshold, rationale),
            implied_changes_bp=changes,
        ))
    return runs


def with_actuals(
    baselines: list[BaselineRun], actuals: list[BacktestRun]
) -> list[BacktestRun]:
    """Re-skin baseline predictions as BacktestRuns scored by score_backtest.

    Realized outcomes (direction/shape/changes, horizon end) are taken from
    runner-produced BacktestRuns matched by test_date (KeyError if a baseline
    date has no actuals). Agent reports do not apply to baselines.
    """
    by_date = {r.test_date: r for r in actuals}
    return [
        BacktestRun(
            test_date=b.test_date,
            direction_calls=b.direction_calls,
            shape_calls=b.shape_calls,
            actual_direction=(a := by_date[b.test_date]).actual_direction,
            actual_shape=a.actual_shape,
            actual_yield_changes_bp=a.actual_yield_changes_bp,
            horizon_end_date=a.horizon_end_date,
        )
        for b in baselines
    ]
