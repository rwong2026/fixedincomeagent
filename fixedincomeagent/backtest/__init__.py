"""Backtesting harness: point-in-time replay of the FI pipeline."""

from .baselines import (
    BaselineRun,
    forwards_implied_baseline,
    no_change_baseline,
    with_actuals,
)
from .regime_dates import REGIME_TEST_DATES, all_dates
from .runner import BacktestResults, BacktestRun, BacktestRunner
from .scoring import BacktestScorecard, CalibrationBin, render, score_backtest

__all__ = [
    "BacktestResults",
    "BacktestRun",
    "BacktestRunner",
    "BacktestScorecard",
    "BaselineRun",
    "CalibrationBin",
    "REGIME_TEST_DATES",
    "all_dates",
    "forwards_implied_baseline",
    "no_change_baseline",
    "render",
    "score_backtest",
    "with_actuals",
]
