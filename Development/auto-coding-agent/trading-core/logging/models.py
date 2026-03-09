"""
Data models for trading logs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any
import json


class OperationType(Enum):
    """Types of trading operations."""
    # Order operations
    ORDER_SUBMIT = "order_submit"
    ORDER_CANCEL = "order_cancel"
    ORDER_FILLED = "order_filled"
    ORDER_PARTIAL_FILLED = "order_partial_filled"
    ORDER_FAILED = "order_failed"

    # Position operations
    POSITION_OPEN = "position_open"
    POSITION_CLOSE = "position_close"
    POSITION_UPDATE = "position_update"

    # Strategy operations
    SIGNAL_GENERATED = "signal_generated"
    SIGNAL_EXECUTED = "signal_executed"
    SIGNAL_IGNORED = "signal_ignored"

    # System operations
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    ERROR = "error"


@dataclass
class TradeLog:
    """Log entry for a trade execution."""
    id: str
    user_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: int
    price: float
    amount: float
    commission: float = 0.0
    order_id: Optional[str] = None
    strategy_id: Optional[str] = None
    signal_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "price": self.price,
            "amount": self.amount,
            "commission": self.commission,
            "order_id": self.order_id,
            "strategy_id": self.strategy_id,
            "signal_id": self.signal_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class SignalLog:
    """Log entry for a strategy signal."""
    id: str
    strategy_id: str
    strategy_name: str
    symbol: str
    signal_type: str  # 'buy', 'sell', 'hold'
    price: float
    confidence: float = 1.0
    indicators: dict[str, Any] = field(default_factory=dict)
    executed: bool = False
    execution_time: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "signal_type": self.signal_type,
            "price": self.price,
            "confidence": self.confidence,
            "indicators": self.indicators,
            "executed": self.executed,
            "execution_time": self.execution_time.isoformat() if self.execution_time else None,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class OperationLog:
    """Log entry for a trading operation."""
    id: str
    operation_type: OperationType
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    symbol: Optional[str] = None
    success: bool = True
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "operation_type": self.operation_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "symbol": self.symbol,
            "success": self.success,
            "message": self.message,
            "details": self.details,
            "error": self.error,
        }
