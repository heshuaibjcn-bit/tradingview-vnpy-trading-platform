"""
Trade analysis module for statistics and metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import statistics
from loguru import logger

from .models import TradeLog, SignalLog


@dataclass
class TradingStatistics:
    """Trading statistics summary."""
    # Basic stats
    total_trades: int = 0
    buy_trades: int = 0
    sell_trades: int = 0

    # Financial stats
    total_buy_amount: float = 0.0
    total_sell_amount: float = 0.0
    total_commission: float = 0.0
    net_amount: float = 0.0

    # Per-symbol stats
    symbol_stats: Dict[str, "SymbolStats"] = field(default_factory=dict)

    # Time stats
    first_trade_time: Optional[datetime] = None
    last_trade_time: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "total_trades": self.total_trades,
            "buy_trades": self.buy_trades,
            "sell_trades": self.sell_trades,
            "total_buy_amount": self.total_buy_amount,
            "total_sell_amount": self.total_sell_amount,
            "total_commission": self.total_commission,
            "net_amount": self.net_amount,
            "symbol_stats": {
                k: v.to_dict() for k, v in self.symbol_stats.items()
            },
            "first_trade_time": self.first_trade_time.isoformat() if self.first_trade_time else None,
            "last_trade_time": self.last_trade_time.isoformat() if self.last_trade_time else None,
        }


@dataclass
class SymbolStats:
    """Statistics for a single symbol."""
    symbol: str
    trade_count: int = 0
    total_quantity: int = 0
    total_buy: float = 0.0
    total_sell: float = 0.0
    net_position: int = 0
    avg_buy_price: float = 0.0
    avg_sell_price: float = 0.0
    realized_pnl: float = 0.0

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "trade_count": self.trade_count,
            "total_quantity": self.total_quantity,
            "total_buy": self.total_buy,
            "total_sell": self.total_sell,
            "net_position": self.net_position,
            "avg_buy_price": self.avg_buy_price,
            "avg_sell_price": self.avg_sell_price,
            "realized_pnl": self.realized_pnl,
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for analysis."""
    # Return metrics
    total_return: float = 0.0
    total_return_pct: float = 0.0

    # Trade metrics
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0

    # Risk metrics
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0

    # Activity metrics
    avg_trades_per_day: float = 0.0
    avg_hold_time: float = 0.0  # in hours

    def to_dict(self) -> dict:
        return {
            "total_return": self.total_return,
            "total_return_pct": self.total_return_pct,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
            "largest_win": self.largest_win,
            "largest_loss": self.largest_loss,
            "max_drawdown": self.max_drawdown,
            "max_drawdown_pct": self.max_drawdown_pct,
            "sharpe_ratio": self.sharpe_ratio,
            "avg_trades_per_day": self.avg_trades_per_day,
            "avg_hold_time": self.avg_hold_time,
        }


class TradeAnalyzer:
    """Analyzes trading logs to generate statistics."""

    def __init__(self):
        self._trades: List[TradeLog] = []
        self._signals: List[SignalLog] = []

    def add_trades(self, trades: List[TradeLog]) -> None:
        """Add trades for analysis."""
        self._trades.extend(trades)

    def add_signals(self, signals: List[SignalLog]) -> None:
        """Add signals for analysis."""
        self._signals.extend(signals)

    def calculate_statistics(self, symbol: Optional[str] = None) -> TradingStatistics:
        """Calculate basic trading statistics."""
        trades = self._filter_trades(symbol)

        if not trades:
            return TradingStatistics()

        stats = TradingStatistics()
        stats.total_trades = len(trades)
        stats.first_trade_time = min(t.timestamp for t in trades)
        stats.last_trade_time = max(t.timestamp for t in trades)

        symbol_agg: Dict[str, List[TradeLog]] = {}

        for trade in trades:
            if trade.side == "buy":
                stats.buy_trades += 1
                stats.total_buy_amount += trade.amount
            else:
                stats.sell_trades += 1
                stats.total_sell_amount += trade.amount

            stats.total_commission += trade.commission

            # Group by symbol
            if trade.symbol not in symbol_agg:
                symbol_agg[trade.symbol] = []
            symbol_agg[trade.symbol].append(trade)

        stats.net_amount = stats.total_sell_amount - stats.total_buy_amount - stats.total_commission

        # Calculate per-symbol stats
        for sym, sym_trades in symbol_agg.items():
            stats.symbol_stats[sym] = self._calculate_symbol_stats(sym, sym_trades)

        return stats

    def calculate_performance(
        self,
        initial_capital: float = 100000.0,
        symbol: Optional[str] = None,
    ) -> PerformanceMetrics:
        """Calculate performance metrics."""
        trades = self._filter_trades(symbol)
        trades = sorted(trades, key=lambda t: t.timestamp)

        if not trades:
            return PerformanceMetrics()

        metrics = PerformanceMetrics()

        # Calculate equity curve
        equity_curve = self._calculate_equity_curve(trades, initial_capital)
        if not equity_curve:
            return metrics

        final_equity = equity_curve[-1]["equity"]
        metrics.total_return = final_equity - initial_capital
        metrics.total_return_pct = (metrics.total_return / initial_capital) * 100

        # Calculate win/loss stats
        winning_trades = []
        losing_trades = []

        # Group trades by position (buy + sell pairs)
        positions = self._group_positions(trades)
        for pos in positions:
            if pos["pnl"] > 0:
                winning_trades.append(pos["pnl"])
            else:
                losing_trades.append(pos["pnl"])

        if winning_trades:
            metrics.avg_win = statistics.mean(winning_trades)
            metrics.largest_win = max(winning_trades)

        if losing_trades:
            metrics.avg_loss = statistics.mean(losing_trades)
            metrics.largest_loss = min(losing_trades)

        total_wins = sum(winning_trades) if winning_trades else 0
        total_losses = abs(sum(losing_trades)) if losing_trades else 0
        total_closed_trades = len(winning_trades) + len(losing_trades)

        if total_closed_trades > 0:
            metrics.win_rate = (len(winning_trades) / total_closed_trades) * 100

        if total_losses > 0:
            metrics.profit_factor = total_wins / total_losses
        elif total_wins > 0:
            metrics.profit_factor = float('inf')

        # Calculate max drawdown
        metrics.max_drawdown, metrics.max_drawdown_pct = self._calculate_max_drawdown(equity_curve)

        # Calculate Sharpe ratio (simplified, assumes 252 trading days)
        if len(equity_curve) > 1:
            returns = [
                (equity_curve[i]["equity"] - equity_curve[i-1]["equity"]) / equity_curve[i-1]["equity"]
                for i in range(1, len(equity_curve))
            ]
            if returns:
                avg_return = statistics.mean(returns)
                std_return = statistics.stdev(returns) if len(returns) > 1 else 0
                if std_return > 0:
                    # Annualized Sharpe ratio (simplified)
                    metrics.sharpe_ratio = (avg_return / std_return) * (252 ** 0.5)

        # Calculate avg trades per day
        if trades:
            time_span = (trades[-1].timestamp - trades[0].timestamp).total_seconds() / 86400
            if time_span > 0:
                metrics.avg_trades_per_day = len(trades) / time_span

        return metrics

    def calculate_signal_analysis(self) -> Dict:
        """Analyze signal execution rates."""
        if not self._signals:
            return {}

        total = len(self._signals)
        executed = sum(1 for s in self._signals if s.executed)
        ignored = total - executed

        by_strategy: Dict[str, Dict] = {}
        for signal in self._signals:
            if signal.strategy_name not in by_strategy:
                by_strategy[signal.strategy_name] = {
                    "total": 0,
                    "executed": 0,
                    "buy": 0,
                    "sell": 0,
                }
            by_strategy[signal.strategy_name]["total"] += 1
            if signal.executed:
                by_strategy[signal.strategy_name]["executed"] += 1
            if signal.signal_type == "buy":
                by_strategy[signal.strategy_name]["buy"] += 1
            elif signal.signal_type == "sell":
                by_strategy[signal.strategy_name]["sell"] += 1

        return {
            "total_signals": total,
            "executed_signals": executed,
            "ignored_signals": ignored,
            "execution_rate": (executed / total * 100) if total > 0 else 0,
            "by_strategy": by_strategy,
        }

    def get_equity_curve(
        self,
        initial_capital: float = 100000.0,
        symbol: Optional[str] = None,
    ) -> List[Dict]:
        """Get equity curve data for charting."""
        trades = self._filter_trades(symbol)
        return self._calculate_equity_curve(trades, initial_capital)

    def _filter_trades(self, symbol: Optional[str]) -> List[TradeLog]:
        """Filter trades by symbol."""
        if symbol:
            return [t for t in self._trades if t.symbol == symbol]
        return self._trades

    def _calculate_symbol_stats(self, symbol: str, trades: List[TradeLog]) -> SymbolStats:
        """Calculate statistics for a specific symbol."""
        stats = SymbolStats(symbol=symbol)
        stats.trade_count = len(trades)

        buy_trades = [t for t in trades if t.side == "buy"]
        sell_trades = [t for t in trades if t.side == "sell"]

        for t in buy_trades:
            stats.total_buy += t.amount
            stats.total_quantity += t.quantity

        for t in sell_trades:
            stats.total_sell += t.amount
            stats.total_quantity -= t.quantity

        stats.net_position = stats.total_quantity

        if buy_trades:
            stats.avg_buy_price = statistics.mean([t.price for t in buy_trades])
        if sell_trades:
            stats.avg_sell_price = statistics.mean([t.price for t in sell_trades])

        # Simplified realized P&L calculation
        # (In production, this would use FIFO or specific cost basis)
        stats.realized_pnl = stats.total_sell - stats.total_buy

        return stats

    def _group_positions(self, trades: List[TradeLog]) -> List[Dict]:
        """Group trades into positions for P&L calculation."""
        positions = []
        symbol_positions: Dict[str, List[TradeLog]] = {}

        for trade in trades:
            if trade.symbol not in symbol_positions:
                symbol_positions[trade.symbol] = []

            symbol_positions[trade.symbol].append(trade)

        for symbol, sym_trades in symbol_positions.items():
            # FIFO position matching
            buy_queue: List[TradeLog] = []
            for trade in sorted(sym_trades, key=lambda t: t.timestamp):
                if trade.side == "buy":
                    buy_queue.append(trade)
                elif trade.side == "sell" and buy_queue:
                    remaining_qty = trade.quantity
                    while remaining_qty > 0 and buy_queue:
                        buy_trade = buy_queue[0]
                        buy_qty = buy_trade.quantity

                        if buy_qty <= remaining_qty:
                            # Close entire position
                            pnl = (trade.price - buy_trade.price) * buy_qty - trade.commission
                            positions.append({
                                "symbol": symbol,
                                "entry_price": buy_trade.price,
                                "exit_price": trade.price,
                                "quantity": buy_qty,
                                "pnl": pnl,
                                "hold_time": (trade.timestamp - buy_trade.timestamp).total_seconds() / 3600,
                            })
                            remaining_qty -= buy_qty
                            buy_queue.pop(0)
                        else:
                            # Partial close
                            pnl = (trade.price - buy_trade.price) * remaining_qty - trade.commission
                            positions.append({
                                "symbol": symbol,
                                "entry_price": buy_trade.price,
                                "exit_price": trade.price,
                                "quantity": remaining_qty,
                                "pnl": pnl,
                                "hold_time": (trade.timestamp - buy_trade.timestamp).total_seconds() / 3600,
                            })
                            buy_trade.quantity -= remaining_qty
                            remaining_qty = 0

        return positions

    def _calculate_equity_curve(
        self,
        trades: List[TradeLog],
        initial_capital: float,
    ) -> List[Dict]:
        """Calculate equity curve from trades."""
        if not trades:
            return []

        equity = initial_capital
        curve = []

        for trade in sorted(trades, key=lambda t: t.timestamp):
            if trade.side == "sell":
                equity += trade.amount - trade.commission
            else:
                equity -= trade.amount + trade.commission

            curve.append({
                "timestamp": trade.timestamp.isoformat(),
                "equity": equity,
                "symbol": trade.symbol,
                "side": trade.side,
                "price": trade.price,
            })

        return curve

    def _calculate_max_drawdown(self, equity_curve: List[Dict]) -> Tuple[float, float]:
        """Calculate maximum drawdown from equity curve."""
        if not equity_curve:
            return 0.0, 0.0

        peak = equity_curve[0]["equity"]
        max_dd = 0.0
        max_dd_pct = 0.0

        for point in equity_curve:
            equity = point["equity"]
            if equity > peak:
                peak = equity

            dd = peak - equity
            dd_pct = (dd / peak * 100) if peak > 0 else 0

            if dd > max_dd:
                max_dd = dd
                max_dd_pct = dd_pct

        return max_dd, max_dd_pct
