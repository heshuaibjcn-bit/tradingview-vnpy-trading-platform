"""
Stop Loss and Take Profit Manager

Manages automatic stop-loss and take-profit orders.
"""

from dataclasses import dataclass
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from loguru import logger


@dataclass
class StopLossOrder:
    """Stop loss or take profit order configuration."""
    id: str
    position_id: str
    user_id: str
    symbol: str
    quantity: int
    entry_price: float
    stop_type: str  # "stop_loss", "take_profit", "trailing_stop"
    trigger_price: float
    # For trailing stops
    trailing_percent: float = 0  # Distance from high as percentage
    highest_price: float = 0
    # For time-based stops
    expiry_time: Optional[datetime] = None
    # State
    active: bool = True
    triggered: bool = False
    triggered_at: Optional[datetime] = None


@dataclass
class StopLossConfig:
    """Default stop loss configuration."""
    enabled: bool = True
    default_stop_loss_pct: float = 0.05  # 5% stop loss
    default_take_profit_pct: float = 0.15  # 15% take profit
    trailing_stop_enabled: bool = False
    trailing_stop_pct: float = 0.03  # 3% trailing stop


class StopLossManager:
    """
    Manages stop loss and take profit orders.

    Monitors positions and automatically triggers exit orders when
    stop loss or take profit levels are hit.
    """

    def __init__(self, config: Optional[StopLossConfig] = None):
        self.config = config or StopLossConfig()
        self.orders: Dict[str, StopLossOrder] = {}
        self._callbacks: List[callable] = []

    def add_callback(self, callback: callable) -> None:
        """Add a callback to be triggered when stop loss is hit."""
        self._callbacks.append(callback)

    def create_stop_loss(
        self,
        position_id: str,
        user_id: str,
        symbol: str,
        quantity: int,
        entry_price: float,
        stop_loss_pct: Optional[float] = None,
        take_profit_pct: Optional[float] = None
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Create stop loss and/or take profit orders for a position.

        Returns (stop_loss_id, take_profit_id)
        """
        stop_loss_id = None
        take_profit_id = None

        # Create stop loss order
        if stop_loss_pct or self.config.default_stop_loss_pct:
            sl_pct = stop_loss_pct or self.config.default_stop_loss_pct
            sl_price = entry_price * (1 - sl_pct)
            sl_order = StopLossOrder(
                id=f"sl_{datetime.now().timestamp()}",
                position_id=position_id,
                user_id=user_id,
                symbol=symbol,
                quantity=quantity,
                entry_price=entry_price,
                stop_type="stop_loss",
                trigger_price=sl_price,
            )
            self.orders[sl_order.id] = sl_order
            stop_loss_id = sl_order.id

        # Create take profit order
        if take_profit_pct or self.config.default_take_profit_pct:
            tp_pct = take_profit_pct or self.config.default_take_profit_pct
            tp_price = entry_price * (1 + tp_pct)
            tp_order = StopLossOrder(
                id=f"tp_{datetime.now().timestamp()}",
                position_id=position_id,
                user_id=user_id,
                symbol=symbol,
                quantity=quantity,
                entry_price=entry_price,
                stop_type="take_profit",
                trigger_price=tp_price,
            )
            self.orders[tp_order.id] = tp_order
            take_profit_id = tp_order.id

        logger.info(f"Created stop loss orders for {symbol}: SL={stop_loss_id}, TP={take_profit_id}")
        return stop_loss_id, take_profit_id

    def create_trailing_stop(
        self,
        position_id: str,
        user_id: str,
        symbol: str,
        quantity: int,
        entry_price: float,
        trailing_pct: Optional[float] = None
    ) -> Optional[str]:
        """Create a trailing stop order."""
        if not self.config.trailing_stop_enabled:
            logger.warning("Trailing stop is not enabled")
            return None

        pct = trailing_pct or self.config.trailing_stop_pct
        stop_price = entry_price * (1 - pct)

        order = StopLossOrder(
            id=f"ts_{datetime.now().timestamp()}",
            position_id=position_id,
            user_id=user_id,
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            stop_type="trailing_stop",
            trigger_price=stop_price,
            trailing_percent=pct,
            highest_price=entry_price,
        )
        self.orders[order.id] = order

        logger.info(f"Created trailing stop for {symbol}: {order.id}")
        return order.id

    def check_orders(self, symbol: str, current_price: float) -> List[StopLossOrder]:
        """
        Check all active orders for a symbol against current price.

        Returns list of triggered orders.
        """
        triggered = []

        for order in self.orders.values():
            if not order.active or order.triggered or order.symbol != symbol:
                continue

            order_triggered = False

            if order.stop_type == "stop_loss":
                order_triggered = current_price <= order.trigger_price

            elif order.stop_type == "take_profit":
                order_triggered = current_price >= order.trigger_price

            elif order.stop_type == "trailing_stop":
                # Update highest price
                if current_price > order.highest_price:
                    order.highest_price = current_price
                    # Adjust stop price
                    order.trigger_price = order.highest_price * (1 - order.trailing_percent)

                order_triggered = current_price <= order.trigger_price

            if order_triggered:
                order.triggered = True
                order.triggered_at = datetime.now()
                order.active = False
                triggered.append(order)

                logger.info(f"Stop loss triggered: {order.symbol} @ {current_price:.2f} "
                           f"(type: {order.stop_type}, trigger: {order.trigger_price:.2f})")

                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback(order)
                    except Exception as e:
                        logger.error(f"Error in stop loss callback: {e}")

        return triggered

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an active stop loss order."""
        if order_id in self.orders:
            self.orders[order_id].active = False
            logger.info(f"Cancelled stop loss order: {order_id}")
            return True
        return False

    def cancel_position_orders(self, position_id: str) -> int:
        """Cancel all orders for a position."""
        cancelled = 0
        for order in self.orders.values():
            if order.position_id == position_id and order.active:
                order.active = False
                cancelled += 1
        logger.info(f"Cancelled {cancelled} orders for position {position_id}")
        return cancelled

    def get_active_orders(self, user_id: str) -> List[StopLossOrder]:
        """Get all active orders for a user."""
        return [o for o in self.orders.values()
                if o.user_id == user_id and o.active and not o.triggered]

    def cleanup_old_orders(self, days: int = 30) -> int:
        """Remove old triggered/cancelled orders."""
        cutoff = datetime.now() - timedelta(days=days)
        original_count = len(self.orders)

        to_remove = [
            order_id for order_id, order in self.orders.items()
            if (not order.active or order.triggered) and
            (order.triggered_at and order.triggered_at < cutoff or
             order_id in self.orders and order.triggered_at is None)
        ]

        for order_id in to_remove:
            del self.orders[order_id]

        logger.info(f"Cleaned up {len(to_remove)} old stop loss orders")
        return len(to_remove)
