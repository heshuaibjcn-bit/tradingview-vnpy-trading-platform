"""
Backtesting Metrics Calculator

Calculates performance metrics for backtesting results.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class BacktestMetrics:
    """Performance metrics for a backtest."""

    # Return metrics
    total_return: float          # Total return over the period
    annual_return: float         # Annualized return
    daily_return_mean: float     # Mean daily return
    daily_return_std: float      # Standard deviation of daily returns

    # Risk metrics
    max_drawdown: float          # Maximum drawdown
    max_drawdown_duration: int   # Duration of max drawdown (days)
    sharpe_ratio: float          # Sharpe ratio (annualized)
    sortino_ratio: float         # Sortino ratio (annualized)

    # Trade metrics
    total_trades: int            # Total number of trades
    winning_trades: int          # Number of winning trades
    losing_trades: int           # Number of losing trades
    win_rate: float              # Win rate (0-1)

    # Profit metrics
    avg_profit: float            # Average profit per trade
    avg_loss: float              # Average loss per trade
    profit_factor: float         # Ratio of total profit to total loss
    expectancy: float            # Expected value per trade

    # Additional metrics
    calmar_ratio: float          # Calmar ratio (annual return / max drawdown)
    omega_ratio: float           # Omega ratio
    var_95: float               # Value at risk at 95% confidence

    # Trading metrics
    avg_holding_period: float    # Average holding period (days)
    best_trade: float           # Best single trade return
    worst_trade: float          # Worst single trade return


def calculate_metrics(
    equity_curve: pd.Series,
    trades: List[dict],
    initial_capital: float = 100000,
    risk_free_rate: float = 0.03
) -> BacktestMetrics:
    """
    Calculate performance metrics for a backtest.

    Args:
        equity_curve: Series of equity values over time
        trades: List of trade dictionaries with 'entry_time', 'exit_time', 'pnl'
        initial_capital: Initial capital amount
        risk_free_rate: Annual risk-free rate for Sharpe ratio calculation

    Returns:
        BacktestMetrics object with all calculated metrics
    """
    if len(equity_curve) == 0:
        return BacktestMetrics(
            total_return=0, annual_return=0, daily_return_mean=0, daily_return_std=0,
            max_drawdown=0, max_drawdown_duration=0, sharpe_ratio=0, sortino_ratio=0,
            total_trades=0, winning_trades=0, losing_trades=0, win_rate=0,
            avg_profit=0, avg_loss=0, profit_factor=0, expectancy=0,
            calmar_ratio=0, omega_ratio=0, var_95=0,
            avg_holding_period=0, best_trade=0, worst_trade=0
        )

    # Calculate returns
    returns = equity_curve.pct_change().fillna(0)

    # Total return
    total_return = (equity_curve.iloc[-1] / initial_capital) - 1

    # Annualized return (assuming 252 trading days)
    days = len(equity_curve)
    years = days / 252
    annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

    # Daily return statistics
    daily_return_mean = returns.mean()
    daily_return_std = returns.std()

    # Maximum drawdown
    cummax = equity_curve.cummax()
    drawdown = (equity_curve - cummax) / cummax
    max_drawdown = drawdown.min()

    # Max drawdown duration
    drawdown_periods = drawdown[drawdown < 0]
    if len(drawdown_periods) > 0:
        # Find consecutive drawdown periods
        is_drawdown = drawdown < 0
        drawdown_starts = is_drawdown & ~is_drawdown.shift(1).fillna(False)
        drawdown_ends = ~is_drawdown & is_drawdown.shift(1).fillna(False)

        durations = []
        for start, end in zip(drawdown_starts[drawdown_starts].index,
                             drawdown_ends[drawdown_ends].index):
            duration = (end - start).days
            durations.append(duration)

        max_drawdown_duration = int(max(durations)) if durations else 0
    else:
        max_drawdown_duration = 0

    # Sharpe ratio (annualized)
    excess_returns = returns - (risk_free_rate / 252)
    sharpe_ratio = (excess_returns.mean() / excess_returns.std() * np.sqrt(252)
                    if excess_returns.std() > 0 else 0)

    # Sortino ratio (downside deviation only)
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std()
    sortino_ratio = (excess_returns.mean() / downside_std * np.sqrt(252)
                     if downside_std > 0 else 0)

    # Trade statistics
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t.get("pnl", 0) > 0)
    losing_trades = sum(1 for t in trades if t.get("pnl", 0) < 0)
    win_rate = winning_trades / total_trades if total_trades > 0 else 0

    # Profit/loss metrics
    profits = [t["pnl"] for t in trades if t.get("pnl", 0) > 0]
    losses = [abs(t["pnl"]) for t in trades if t.get("pnl", 0) < 0]

    avg_profit = np.mean(profits) if profits else 0
    avg_loss = np.mean(losses) if losses else 0

    total_profit = sum(profits)
    total_loss = sum(losses)
    profit_factor = total_profit / total_loss if total_loss > 0 else float("inf") if total_profit > 0 else 0

    expectancy = (total_profit - total_loss) / total_trades if total_trades > 0 else 0

    # Additional ratios
    calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

    # Omega ratio (threshold = 0)
    gains = excess_returns[excess_returns > 0].sum()
    losses_abs = abs(excess_returns[excess_returns < 0].sum())
    omega_ratio = gains / losses_abs if losses_abs > 0 else float("inf")

    # Value at Risk at 95%
    var_95 = np.percentile(returns, 5)

    # Holding period
    holding_periods = []
    for trade in trades:
        entry = pd.to_datetime(trade.get("entry_time"))
        exit_time = pd.to_datetime(trade.get("exit_time"))
        if pd.notna(entry) and pd.notna(exit_time):
            holding_periods.append((exit_time - entry).days)

    avg_holding_period = np.mean(holding_periods) if holding_periods else 0

    # Best and worst trades
    trade_pnls = [t.get("pnl", 0) for t in trades]
    best_trade = max(trade_pnls) if trade_pnls else 0
    worst_trade = min(trade_pnls) if trade_pnls else 0

    return BacktestMetrics(
        total_return=total_return,
        annual_return=annual_return,
        daily_return_mean=daily_return_mean,
        daily_return_std=daily_return_std,
        max_drawdown=max_drawdown,
        max_drawdown_duration=max_drawdown_duration,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=win_rate,
        avg_profit=avg_profit,
        avg_loss=avg_loss,
        profit_factor=profit_factor,
        expectancy=expectancy,
        calmar_ratio=calmar_ratio,
        omega_ratio=omega_ratio,
        var_95=var_95,
        avg_holding_period=avg_holding_period,
        best_trade=best_trade,
        worst_trade=worst_trade,
    )


def format_metrics(metrics: BacktestMetrics) -> dict:
    """Convert metrics to a dictionary for JSON serialization."""
    return {
        "returns": {
            "total": f"{metrics.total_return:.2%}",
            "annualized": f"{metrics.annual_return:.2%}",
            "daily_mean": f"{metrics.daily_return_mean:.4%}",
            "daily_std": f"{metrics.daily_return_std:.4%}",
        },
        "risk": {
            "max_drawdown": f"{metrics.max_drawdown:.2%}",
            "drawdown_duration": f"{metrics.max_drawdown_duration} days",
            "sharpe_ratio": f"{metrics.sharpe_ratio:.2f}",
            "sortino_ratio": f"{metrics.sortino_ratio:.2f}",
        },
        "trades": {
            "total": metrics.total_trades,
            "winning": metrics.winning_trades,
            "losing": metrics.losing_trades,
            "win_rate": f"{metrics.win_rate:.1%}",
        },
        "profits": {
            "avg_profit": f"¥{metrics.avg_profit:.2f}",
            "avg_loss": f"¥{metrics.avg_loss:.2f}",
            "profit_factor": f"{metrics.profit_factor:.2f}",
            "expectancy": f"¥{metrics.expectancy:.2f}",
        },
        "additional": {
            "calmar_ratio": f"{metrics.calmar_ratio:.2f}",
            "omega_ratio": f"{metrics.omega_ratio:.2f}",
            "var_95": f"{metrics.var_95:.4%}",
        },
        "holding": {
            "avg_period": f"{metrics.avg_holding_period:.1f} days",
            "best_trade": f"¥{metrics.best_trade:.2f}",
            "worst_trade": f"¥{metrics.worst_trade:.2f}",
        },
    }
