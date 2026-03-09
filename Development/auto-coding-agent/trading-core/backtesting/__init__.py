"""
Backtesting Module

Provides framework for backtesting trading strategies with historical data.
"""

from .engine import BacktestEngine, BacktestResult, Trade
from .data import HistoricalDataFetcher
from .metrics import calculate_metrics, BacktestMetrics
from .report import generate_report, generate_html_report

__all__ = [
    "BacktestEngine",
    "BacktestResult",
    "Trade",
    "HistoricalDataFetcher",
    "calculate_metrics",
    "BacktestMetrics",
    "generate_report",
    "generate_html_report",
]
