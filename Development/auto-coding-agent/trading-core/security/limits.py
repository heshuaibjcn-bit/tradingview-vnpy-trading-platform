"""
Trading limits and emergency stop.
"""

from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger


class LimitType(Enum):
    """Types of trading limits."""
    DAILY_LOSS = "daily_loss"
    DAILY_TRADES = "daily_trades"
    DAILY_TURNOVER = "daily_turnover"
    MAX_POSITION = "max_position"
    MAX_EXPOSURE = "max_exposure"
    WEEKLY_LOSS = "weekly_loss"
    MONTHLY_LOSS = "monthly_loss"


class LimitStatus:
    """Status of a trading limit."""

    def __init__(
        self,
        limit_type: LimitType,
        current_value: float,
        limit_value: float,
        exceeded: bool = False,
    ):
        self.limit_type = limit_type
        self.current_value = current_value
        self.limit_value = limit_value
        self.exceeded = exceeded
        self.timestamp = datetime.now()

    @property
    def utilization_pct(self) -> float:
        """Get utilization as percentage."""
        if self.limit_value == 0:
            return 0
        return (self.current_value / self.limit_value) * 100


class LimitChecker:
    """
    Checks and enforces trading limits.

    Prevents over-trading and excessive losses.
    """

    def __init__(self):
        self._limits: Dict[str, Dict[LimitType, float]] = {}
        self._daily_tracking: Dict[str, Dict] = {}
        self._emergency_stop_active = False
        self._emergency_stop_reason: Optional[str] = None
        self._emergency_stop_callbacks: List[Callable] = []

    def set_limit(
        self,
        user_id: str,
        limit_type: LimitType,
        value: float,
    ) -> None:
        """Set a trading limit for a user."""
        if user_id not in self._limits:
            self._limits[user_id] = {}

        self._limits[user_id][limit_type] = value
        logger.info(f"Limit set for user {user_id}: {limit_type.value} = {value}")

    def get_limit(
        self,
        user_id: str,
        limit_type: LimitType,
    ) -> Optional[float]:
        """Get a trading limit for a user."""
        return self._limits.get(user_id, {}).get(limit_type)

    def check_limit(
        self,
        user_id: str,
        limit_type: LimitType,
        current_value: float,
    ) -> LimitStatus:
        """
        Check if a limit is exceeded.

        Args:
            user_id: User ID
            limit_type: Type of limit to check
            current_value: Current value to check

        Returns:
            LimitStatus with exceeded flag
        """
        limit_value = self.get_limit(user_id, limit_type)

        if limit_value is None:
            # No limit set
            return LimitStatus(limit_type, current_value, float('inf'), False)

        exceeded = current_value >= limit_value

        if exceeded:
            logger.warning(
                f"Limit exceeded for user {user_id}: {limit_type.value} "
                f"({current_value} >= {limit_value})"
            )

        return LimitStatus(limit_type, current_value, limit_value, exceeded)

    def check_all_limits(self, user_id: str) -> List[LimitStatus]:
        """Check all limits for a user."""
        statuses = []

        # Get current tracking values
        tracking = self._daily_tracking.get(user_id, {})

        for limit_type, limit_value in self._limits.get(user_id, {}).items():
            if limit_type == LimitType.DAILY_LOSS:
                current = tracking.get("daily_loss", 0)
            elif limit_type == LimitType.DAILY_TRADES:
                current = tracking.get("trade_count", 0)
            elif limit_type == LimitType.DAILY_TURNOVER:
                current = tracking.get("turnover", 0)
            else:
                current = 0

            status = LimitStatus(limit_type, current, limit_value, current >= limit_value)
            statuses.append(status)

        return statuses

    def track_trade(
        self,
        user_id: str,
        quantity: int,
        price: float,
        is_buy: bool,
        pnl: float = 0,
    ) -> None:
        """
        Track a trade for limit checking.

        Args:
            user_id: User ID
            quantity: Trade quantity
            price: Trade price
            is_buy: Whether this is a buy order
            pnl: Profit/loss for closed positions
        """
        today = datetime.now().date().isoformat()

        if user_id not in self._daily_tracking:
            self._daily_tracking[user_id] = {}

        tracking = self._daily_tracking[user_id]

        # Initialize daily tracking
        if tracking.get("date") != today:
            tracking["date"] = today
            tracking["trade_count"] = 0
            tracking["turnover"] = 0
            tracking["daily_loss"] = 0

        # Update tracking
        tracking["trade_count"] = tracking.get("trade_count", 0) + 1
        tracking["turnover"] = tracking.get("turnover", 0) + quantity * price

        if pnl < 0:
            tracking["daily_loss"] = tracking.get("daily_loss", 0) + abs(pnl)

        # Check for emergency stop
        self._check_emergency_stop(user_id, tracking)

    def _check_emergency_stop(self, user_id: str, tracking: Dict) -> None:
        """Check if emergency stop should be triggered."""
        daily_loss_limit = self.get_limit(user_id, LimitType.DAILY_LOSS)

        if daily_loss_limit and tracking.get("daily_loss", 0) >= daily_loss_limit:
            self.trigger_emergency_stop(
                user_id,
                f"Daily loss limit exceeded: {tracking['daily_loss']:.2f} >= {daily_loss_limit:.2f}"
            )

    def trigger_emergency_stop(self, user_id: str, reason: str) -> None:
        """
        Trigger emergency stop for all trading.

        Args:
            user_id: User ID
            reason: Reason for emergency stop
        """
        self._emergency_stop_active = True
        self._emergency_stop_reason = reason

        logger.critical(f"EMERGENCY STOP triggered for user {user_id}: {reason}")

        # Notify callbacks
        for callback in self._emergency_stop_callbacks:
            try:
                callback(user_id, reason)
            except Exception as e:
                logger.error(f"Error in emergency stop callback: {e}")

    def reset_emergency_stop(self, user_id: str) -> None:
        """Reset emergency stop for a user."""
        self._emergency_stop_active = False
        self._emergency_stop_reason = None
        logger.info(f"Emergency stop reset for user {user_id}")

    def is_emergency_stop_active(self, user_id: Optional[str] = None) -> bool:
        """Check if emergency stop is active."""
        return self._emergency_stop_active

    def add_emergency_stop_callback(self, callback: Callable) -> None:
        """Add callback for emergency stop events."""
        self._emergency_stop_callbacks.append(callback)

    def get_emergency_stop_reason(self) -> Optional[str]:
        """Get reason for emergency stop."""
        return self._emergency_stop_reason

    def reset_daily_tracking(self, user_id: str) -> None:
        """Reset daily tracking for a user (called at start of new day)."""
        if user_id in self._daily_tracking:
            self._daily_tracking[user_id] = {
                "date": datetime.now().date().isoformat(),
                "trade_count": 0,
                "turnover": 0,
                "daily_loss": 0,
            }


class TradingLimits:
    """
    High-level trading limits manager.

    Provides convenient methods for setting up common limits.
    """

    def __init__(self, checker: Optional[LimitChecker] = None):
        self.checker = checker or LimitChecker()

    def setup_default_limits(
        self,
        user_id: str,
        daily_loss_limit: float = 5000.0,
        daily_trade_limit: int = 50,
        daily_turnover_limit: float = 50000.0,
        max_position_ratio: float = 0.3,
        max_exposure_ratio: float = 0.95,
    ) -> None:
        """
        Set up default trading limits for a user.

        Args:
            user_id: User ID
            daily_loss_limit: Maximum daily loss
            daily_trade_limit: Maximum trades per day
            daily_turnover_limit: Maximum daily turnover
            max_position_ratio: Maximum position as ratio of capital
            max_exposure_ratio: Maximum total exposure
        """
        self.checker.set_limit(user_id, LimitType.DAILY_LOSS, daily_loss_limit)
        self.checker.set_limit(user_id, LimitType.DAILY_TRADES, daily_trade_limit)
        self.checker.set_limit(user_id, LimitType.DAILY_TURNOVER, daily_turnover_limit)
        self.checker.set_limit(user_id, LimitType.MAX_POSITION, max_position_ratio)
        self.checker.set_limit(user_id, LimitType.MAX_EXPOSURE, max_exposure_ratio)

        logger.info(f"Default limits set up for user {user_id}")

    def can_place_order(
        self,
        user_id: str,
        order_value: float,
        current_exposure: float,
    ) -> tuple[bool, str]:
        """
        Check if an order can be placed.

        Args:
            user_id: User ID
            order_value: Value of the order
            current_exposure: Current total exposure

        Returns:
            (allowed, reason) tuple
        """
        if self.checker.is_emergency_stop_active():
            reason = f"Emergency stop active: {self.checker.get_emergency_stop_reason()}"
            return False, reason

        # Check all limits
        statuses = self.checker.check_all_limits(user_id)

        for status in statuses:
            if status.exceeded:
                return False, f"Limit exceeded: {status.limit_type.value}"

        # Check exposure
        max_exposure = self.checker.get_limit(user_id, LimitType.MAX_EXPOSURE)
        if max_exposure and current_exposure + order_value > max_exposure:
            return False, f"Would exceed max exposure: {(current_exposure + order_value):.2f} > {max_exposure:.2f}"

        return True, "OK"
