"""
Backtesting Engine

Executes trading strategies on historical data and calculates performance.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional, Any
from datetime import datetime
from loguru import logger

from .data import HistoricalDataFetcher
from .metrics import calculate_metrics, BacktestMetrics


@dataclass
class Trade:
    """Represents a single trade in the backtest."""
    entry_time: datetime
    exit_time: Optional[datetime]
    symbol: str
    side: str  # "long" or "short"
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    pnl: float
    commission: float = 0.0


@dataclass
class BacktestResult:
    """Results of a backtest run."""

    # Strategy info
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str

    # Performance
    initial_capital: float
    final_capital: float
    equity_curve: pd.Series
    metrics: BacktestMetrics

    # Trades
    trades: List[Trade] = field(default_factory=list)

    # Parameters
    parameters: Dict[str, Any] = field(default_factory=dict)


class BacktestEngine:
    """
    Backtesting engine for trading strategies.

    Usage:
        engine = BacktestEngine(initial_capital=100000)

        def strategy(data, position):
            # Returns 'buy', 'sell', or None
            if len(data) > 0:
                return 'buy' if position == 0 else None
            return None

        result = engine.run(
            strategy=strategy,
            symbol="600519",
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
    """

    def __init__(
        self,
        initial_capital: float = 100000,
        commission_rate: float = 0.0003,  # 0.03% commission
        slippage_rate: float = 0.0001,    # 0.01% slippage
    ):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.data_fetcher = HistoricalDataFetcher()

        # State variables
        self.cash = initial_capital
        self.position = 0  # Positive for long, negative for short
        self.position_price = 0  # Average entry price
        self.equity_curve = []
        self.trades = []

    def run(
        self,
        strategy: Callable,
        symbol: str,
        start_date: str,
        end_date: str,
        parameters: Optional[Dict[str, Any]] = None,
        interval: str = "1d",
    ) -> BacktestResult:
        """
        Run a backtest on a strategy.

        Args:
            strategy: Function that takes (data_slice, position) and returns 'buy', 'sell', or None
            symbol: Stock symbol to backtest
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            parameters: Strategy parameters
            interval: Data interval

        Returns:
            BacktestResult with performance metrics
        """
        logger.info(f"Starting backtest for {symbol} from {start_date} to {end_date}")

        # Reset state
        self.cash = self.initial_capital
        self.position = 0
        self.position_price = 0
        self.equity_curve = []
        self.trades = []

        # Fetch historical data
        data = self.data_fetcher.fetch(symbol, start_date, end_date, interval)

        if data.empty:
            logger.warning(f"No data found for {symbol}")
            return self._create_result(
                strategy.__name__ if hasattr(strategy, "__name__") else "Unknown",
                symbol,
                start_date,
                end_date,
                parameters or {}
            )

        # Track current trade
        current_trade = None

        # Run strategy on each data point
        for i in range(1, len(data)):
            current_data = data.iloc[:i+1]
            current_price = current_data.iloc[-1]["close"]
            current_time = current_data.index[-1]

            # Update equity
            equity = self.cash + self.position * current_price
            self.equity_curve.append((current_time, equity))

            # Get strategy signal
            signal = strategy(current_data, self.position, parameters or {})

            # Execute signals
            if signal == "buy" and self.position == 0:
                # Buy signal
                self._execute_buy(current_price, current_time, symbol)

            elif signal == "sell" and self.position > 0:
                # Sell signal
                self._execute_sell(current_price, current_time, symbol)

        # Close any remaining position
        if self.position > 0:
            final_price = data.iloc[-1]["close"]
            final_time = data.index[-1]
            self._execute_sell(final_price, final_time, symbol)

        # Create equity curve series
        equity_df = pd.DataFrame(
            self.equity_curve,
            columns=["datetime", "equity"]
        ).set_index("datetime")
        equity_series = equity_df["equity"]

        # Calculate metrics
        trades_dict = [
            {
                "entry_time": t.entry_time,
                "exit_time": t.exit_time,
                "symbol": t.symbol,
                "pnl": t.pnl,
            }
            for t in self.trades
        ]

        metrics = calculate_metrics(equity_series, trades_dict, self.initial_capital)

        logger.info(f"Backtest complete. Total return: {metrics.total_return:.2%}")

        return self._create_result(
            strategy.__name__ if hasattr(strategy, "__name__") else "Unknown",
            symbol,
            start_date,
            end_date,
            parameters or {},
            equity_series,
            metrics
        )

    def _execute_buy(self, price: float, time: datetime, symbol: str) -> None:
        """Execute a buy order."""
        # Calculate quantity (buy with available cash)
        available_cash = self.cash * (1 - self.commission_rate - self.slippage_rate)
        quantity = int(available_cash / price / 100) * 100  # Round to lot size (100)

        if quantity < 100:
            return

        # Apply slippage
        actual_price = price * (1 + self.slippage_rate)
        commission = actual_price * quantity * self.commission_rate
        total_cost = actual_price * quantity + commission

        if total_cost > self.cash:
            return

        self.cash -= total_cost
        self.position = quantity
        self.position_price = actual_price

    def _execute_sell(self, price: float, time: datetime, symbol: str) -> None:
        """Execute a sell order."""
        if self.position <= 0:
            return

        # Apply slippage
        actual_price = price * (1 - self.slippage_rate)
        commission = actual_price * self.position * self.commission_rate
        total_proceeds = actual_price * self.position - commission

        # Calculate PnL
        pnl = total_proceeds - (self.position_price * self.position + commission * 2)

        self.cash += total_proceeds

        # Record trade
        trade = Trade(
            entry_time=datetime.now(),  # Would be actual entry time in real implementation
            exit_time=time,
            symbol=symbol,
            side="long",
            entry_price=self.position_price,
            exit_price=actual_price,
            quantity=self.position,
            pnl=pnl,
            commission=commission * 2,
        )
        self.trades.append(trade)

        self.position = 0
        self.position_price = 0

    def _create_result(
        self,
        strategy_name: str,
        symbol: str,
        start_date: str,
        end_date: str,
        parameters: Dict[str, Any],
        equity_curve: Optional[pd.Series] = None,
        metrics: Optional[BacktestMetrics] = None,
    ) -> BacktestResult:
        """Create a BacktestResult object."""
        if equity_curve is None:
            equity_curve = pd.Series([self.initial_capital])

        if metrics is None:
            metrics = calculate_metrics(equity_curve, [], self.initial_capital)

        return BacktestResult(
            strategy_name=strategy_name,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=equity_curve.iloc[-1] if len(equity_curve) > 0 else self.initial_capital,
            equity_curve=equity_curve,
            metrics=metrics,
            trades=self.trades,
            parameters=parameters,
        )


# Built-in strategies for backtesting

def moving_average_cross_strategy(
    data: pd.DataFrame,
    position: float,
    parameters: Dict[str, Any]
) -> Optional[str]:
    """
    Simple moving average crossover strategy.

    Parameters:
        short_period: Short MA period (default: 5)
        long_period: Long MA period (default: 20)
    """
    short_period = parameters.get("short_period", 5)
    long_period = parameters.get("long_period", 20)

    if len(data) < long_period:
        return None

    close = data["close"]
    short_ma = close.iloc[-short_period:].mean()
    long_ma = close.iloc[-long_period:].mean()

    # Previous MA values
    short_ma_prev = close.iloc[-short_period-1:-1].mean()
    long_ma_prev = close.iloc[-long_period-1:-1].mean()

    # Crossover detection
    if short_ma_prev <= long_ma_prev and short_ma > long_ma:
        return "buy"  # Golden cross
    elif short_ma_prev >= long_ma_prev and short_ma < long_ma:
        return "sell"  # Death cross

    return None


def rsi_strategy(
    data: pd.DataFrame,
    position: float,
    parameters: Dict[str, Any]
) -> Optional[str]:
    """
    RSI-based strategy.

    Parameters:
        period: RSI period (default: 14)
        oversold: Oversold threshold (default: 30)
        overbought: Overbought threshold (default: 70)
    """
    period = parameters.get("period", 14)
    oversold = parameters.get("oversold", 30)
    overbought = parameters.get("overbought", 70)

    if len(data) < period + 1:
        return None

    close = data["close"]
    delta = close.diff()

    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)

    avg_gain = gains.iloc[-period:].mean()
    avg_loss = losses.iloc[-period:].mean()

    if avg_loss == 0:
        return None

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    if rsi < oversold and position == 0:
        return "buy"
    elif rsi > overbought and position > 0:
        return "sell"

    return None
