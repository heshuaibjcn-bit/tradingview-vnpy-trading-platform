"""
Trade and signal recording module.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Callable
import json
import uuid
from loguru import logger

from .models import TradeLog, SignalLog, OperationLog, OperationType


class TradeRecorder:
    """Records all trading operations to log and database."""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self._trades: List[TradeLog] = []
        self._operations: List[OperationLog] = []
        self._callbacks: List[Callable] = []

        # Create daily log file
        today = datetime.now().strftime("%Y-%m-%d")
        self.trade_log_file = self.log_dir / f"trades_{today}.log"

    def add_callback(self, callback: Callable[[TradeLog], None]) -> None:
        """Add a callback to be called when a trade is recorded."""
        self._callbacks.append(callback)

    def log_trade(
        self,
        user_id: str,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        order_id: Optional[str] = None,
        strategy_id: Optional[str] = None,
        signal_id: Optional[str] = None,
        commission: float = 0.0,
        metadata: dict | None = None,
    ) -> TradeLog:
        """Record a trade execution."""
        trade = TradeLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            amount=quantity * price,
            commission=commission,
            order_id=order_id,
            strategy_id=strategy_id,
            signal_id=signal_id,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )

        self._trades.append(trade)
        self._write_trade_log(trade)

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(trade)
            except Exception as e:
                logger.error(f"Error in trade callback: {e}")

        logger.info(
            f"Trade logged: {side.upper()} {quantity} {symbol} @ ¥{price:.2f}"
        )
        return trade

    def log_operation(
        self,
        operation_type: OperationType,
        message: str,
        user_id: Optional[str] = None,
        symbol: Optional[str] = None,
        success: bool = True,
        details: dict | None = None,
        error: Optional[str] = None,
    ) -> OperationLog:
        """Record a trading operation."""
        operation = OperationLog(
            id=str(uuid.uuid4()),
            operation_type=operation_type,
            timestamp=datetime.now(),
            user_id=user_id,
            symbol=symbol,
            success=success,
            message=message,
            details=details or {},
            error=error,
        )

        self._operations.append(operation)
        self._write_operation_log(operation)

        log_level = "info" if success else "error"
        getattr(logger, log_level)(
            f"Operation: {operation_type.value} - {message}"
        )
        return operation

    def _write_trade_log(self, trade: TradeLog) -> None:
        """Write trade to log file."""
        try:
            with open(self.trade_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(trade.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write trade log: {e}")

    def _write_operation_log(self, operation: OperationLog) -> None:
        """Write operation to log file."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            op_log_file = self.log_dir / f"operations_{today}.log"
            with open(op_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(operation.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write operation log: {e}")

    def get_trades(
        self,
        user_id: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[TradeLog]:
        """Get filtered trades."""
        trades = self._trades

        if user_id:
            trades = [t for t in trades if t.user_id == user_id]
        if symbol:
            trades = [t for t in trades if t.symbol == symbol]
        if start_date:
            trades = [t for t in trades if t.timestamp >= start_date]
        if end_date:
            trades = [t for t in trades if t.timestamp <= end_date]

        return sorted(trades, key=lambda t: t.timestamp, reverse=True)[:limit]

    def get_operations(
        self,
        operation_type: Optional[OperationType] = None,
        user_id: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 100,
    ) -> List[OperationLog]:
        """Get filtered operations."""
        ops = self._operations

        if operation_type:
            ops = [o for o in ops if o.operation_type == operation_type]
        if user_id:
            ops = [o for o in ops if o.user_id == user_id]
        if symbol:
            ops = [o for o in ops if o.symbol == symbol]

        return sorted(ops, key=lambda o: o.timestamp, reverse=True)[:limit]


class SignalRecorder:
    """Records strategy signals for analysis."""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self._signals: List[SignalLog] = []

        # Create daily log file
        today = datetime.now().strftime("%Y-%m-%d")
        self.signal_log_file = self.log_dir / f"signals_{today}.log"

    def log_signal(
        self,
        strategy_id: str,
        strategy_name: str,
        symbol: str,
        signal_type: str,
        price: float,
        confidence: float = 1.0,
        indicators: dict | None = None,
        metadata: dict | None = None,
    ) -> SignalLog:
        """Record a strategy signal."""
        signal = SignalLog(
            id=str(uuid.uuid4()),
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            symbol=symbol,
            signal_type=signal_type,
            price=price,
            confidence=confidence,
            indicators=indicators or {},
            executed=False,
            metadata=metadata or {},
        )

        self._signals.append(signal)
        self._write_signal_log(signal)

        logger.info(
            f"Signal logged: {strategy_name} {signal_type.upper()} {symbol} @ ¥{price:.2f} (confidence: {confidence:.2f})"
        )
        return signal

    def mark_executed(self, signal_id: str) -> None:
        """Mark a signal as executed."""
        for signal in self._signals:
            if signal.id == signal_id:
                signal.executed = True
                signal.execution_time = datetime.now()
                logger.info(f"Signal marked as executed: {signal_id}")
                return

    def _write_signal_log(self, signal: SignalLog) -> None:
        """Write signal to log file."""
        try:
            with open(self.signal_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(signal.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write signal log: {e}")

    def get_signals(
        self,
        strategy_id: Optional[str] = None,
        symbol: Optional[str] = None,
        executed_only: bool = False,
        limit: int = 100,
    ) -> List[SignalLog]:
        """Get filtered signals."""
        signals = self._signals

        if strategy_id:
            signals = [s for s in signals if s.strategy_id == strategy_id]
        if symbol:
            signals = [s for s in signals if s.symbol == symbol]
        if executed_only:
            signals = [s for s in signals if s.executed]

        return sorted(signals, key=lambda s: s.created_at, reverse=True)[:limit]
