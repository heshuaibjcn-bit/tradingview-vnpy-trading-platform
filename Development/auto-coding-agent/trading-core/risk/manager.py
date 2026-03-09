"""
Risk Manager

Central risk management system that checks all trading decisions
against risk limits and controls.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from loguru import logger

from .limits import PositionLimits, TradingLimits, RiskLimit, LimitType
from .stoploss import StopLossManager, StopLossConfig


@dataclass
class RiskCheck:
    """Result of a risk check."""
    passed: bool
    reason: str
    warnings: List[str] = field(default_factory=list)


class RiskManager:
    """
    Central risk management system.

    Coordinates position limits, trading limits, and stop-loss management.
    """

    def __init__(
        self,
        position_limits: Optional[PositionLimits] = None,
        trading_limits: Optional[TradingLimits] = None,
        stop_loss_config: Optional[StopLossConfig] = None,
    ):
        self.position_limits = position_limits or PositionLimits()
        self.trading_limits = trading_limits or TradingLimits()
        self.stop_loss_manager = StopLossManager(stop_loss_config)

        # Custom risk limits
        self.custom_limits: List[RiskLimit] = []

    def add_limit(self, limit: RiskLimit) -> None:
        """Add a custom risk limit."""
        self.custom_limits.append(limit)
        logger.info(f"Added risk limit: {limit.limit_type.value} = {limit.value}")

    def remove_limit(self, limit_id: str) -> bool:
        """Remove a custom risk limit."""
        for i, limit in enumerate(self.custom_limits):
            if limit.id == limit_id:
                self.custom_limits.pop(i)
                logger.info(f"Removed risk limit: {limit_id}")
                return True
        return False

    def check_trade(
        self,
        user_id: str,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        current_positions_value: float,
        capital: float
    ) -> RiskCheck:
        """
        Check if a trade is allowed under risk controls.

        Returns RiskCheck with passed/failed status and reason.
        """
        warnings = []

        # 1. Check position size limits
        size_ok, size_reason = self.position_limits.check_position_size(
            symbol, quantity, price, capital
        )
        if not size_ok:
            return RiskCheck(passed=False, reason=size_reason, warnings=warnings)

        # 2. Check trading limits
        import time
        trade_ok, trade_reason = self.trading_limits.can_trade(
            symbol, quantity, price, time.time()
        )
        if not trade_ok:
            return RiskCheck(passed=False, reason=trade_reason, warnings=warnings)

        # 3. Check custom limits
        for limit in self.custom_limits:
            if limit.enabled and (limit.symbol is None or limit.symbol == symbol):
                if not limit.check(quantity * price):
                    return RiskCheck(
                        passed=False,
                        reason=f"Risk limit exceeded: {limit.limit_type.value} > {limit.value}",
                        warnings=warnings
                    )

        # 4. Generate warnings for approaching limits
        if self.trading_limits.trades_today >= self.trading_limits.max_daily_trades * 0.9:
            warnings.append("Approaching daily trade limit")

        exposure = (current_positions_value + quantity * price) / capital
        if exposure >= self.position_limits.max_total_exposure * 0.9:
            warnings.append(f"Approaching max exposure ({exposure:.1%} of {self.position_limits.max_total_exposure:.1%})")

        return RiskCheck(passed=True, reason="Trade approved", warnings=warnings)

    def record_trade(
        self,
        user_id: str,
        symbol: str,
        quantity: int,
        price: float,
        realized_pnl: float = 0
    ) -> None:
        """Record a trade for limit tracking."""
        import time
        self.trading_limits.record_trade(symbol, quantity, price, realized_pnl, time.time())

    def reset_daily_limits(self) -> None:
        """Reset daily trading limits (call at start of each trading day)."""
        self.trading_limits.reset_daily()
        logger.info("Daily trading limits reset")

    def get_risk_summary(self, user_id: str, capital: float) -> dict:
        """Get a summary of current risk status."""
        return {
            "position_limits": {
                "max_shares_per_position": self.position_limits.max_shares_per_position,
                "max_value_per_position": self.position_limits.max_value_per_position,
                "max_position_pct": f"{self.position_limits.max_position_pct:.1%}",
                "max_total_positions": self.position_limits.max_total_positions,
                "max_total_exposure": f"{self.position_limits.max_total_exposure:.1%}",
            },
            "trading_limits": {
                "max_daily_trades": self.trading_limits.max_daily_trades,
                "trades_today": self.trading_limits.trades_today,
                "max_daily_loss": f"{self.trading_limits.max_daily_loss:.1%}",
                "loss_today": f"{self.trading_limits.loss_today:.2f}",
                "max_daily_turnover": f"¥{self.trading_limits.max_daily_turnover:.0f}",
                "turnover_today": f"¥{self.trading_limits.turnover_today:.0f}",
            },
            "stop_loss": {
                "enabled": self.stop_loss_manager.config.enabled,
                "default_stop_loss": f"{self.stop_loss_manager.config.default_stop_loss_pct:.1%}",
                "default_take_profit": f"{self.stop_loss_manager.config.default_take_profit_pct:.1%}",
                "active_orders": len(self.stop_loss_manager.get_active_orders(user_id)),
            },
        }
