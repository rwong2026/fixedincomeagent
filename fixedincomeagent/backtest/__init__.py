"""Backtesting harness: point-in-time replay of the FI pipeline."""

from .regime_dates import REGIME_TEST_DATES, all_dates
from .runner import BacktestResults, BacktestRun, BacktestRunner
from .scoring import BacktestScorecard, CalibrationBin, render, score_backtest

__all__ = [
    "BacktestResults",
    "BacktestRun",
    "BacktestRunner",
    "BacktestScorecard",
    "CalibrationBin",
    "REGIME_TEST_DATES",
    "all_dates",
    "render",
    "score_backtest",
]
