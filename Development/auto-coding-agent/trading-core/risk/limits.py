"""
Position and Trading Limits

Defines limits for trading activity.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum


class LimitType(str, Enum):
    """Types of risk limits."""
    MAX_POSITION_SIZE = "max_position_size"      # Maximum shares per position
    MAX_POSITION_VALUE = "max_position_value"    # Maximum value per position
    MAX_TOTAL_POSITIONS = "max_total_positions"  # Maximum number of positions
    MAX_POSITION_PCT = "max_position_pct"        # Max % of capital per position
    MAX_TOTAL_EXPOSURE = "max_total_exposure"    # Max total exposure % of capital
    MAX_DAILY_TRADES = "max_daily_trades"        # Maximum trades per day
    MAX_DAILY_LOSS = "max_daily_loss"            # Maximum loss per day
    MAX_DAILY_TURNOVER = "max_daily_turnover"    # Maximum turnover per day


@dataclass
class RiskLimit:
    """A single risk limit configuration."""
    id: str
    user_id: str
    limit_type: LimitType
    value: float
    symbol: Optional[str] = None  # None = applies to all symbols
    enabled: bool = True

    def check(self, current_value: float) -> bool:
        """Check if current value is within the limit."""
        if not self.enabled:
            return True

        if self.limit_type in [LimitType.MAX_POSITION_SIZE,
                                LimitType.MAX_POSITION_VALUE,
                                LimitType.MAX_DAILY_TRADES,
                                LimitType.MAX_DAILY_LOSS,
                                LimitType.MAX_DAILY_TURNOVER]:
            return current_value <= self.value
        elif self.limit_type in [LimitType.MAX_TOTAL_POSITIONS]:
            return int(current_value) <= int(self.value)
        else:
            return current_value <= self.value


@dataclass
class PositionLimits:
    """
    Position size and exposure limits.
    """

    # Per-position limits
    max_shares_per_position: int = 10000       # Max shares per single position
    max_value_per_position: float = 100000      # Max value per single position
    max_position_pct: float = 0.30              # Max 30% of capital per position

    # Portfolio limits
    max_total_positions: int = 10               # Max number of positions
    max_total_exposure: float = 0.95            # Max 95% of capital invested

    # Symbol-specific limits (can override defaults)
    symbol_limits: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def get_max_shares(self, symbol: str, current_price: float, capital: float) -> int:
        """Get maximum allowed shares for a symbol."""
        # Apply symbol-specific limit if exists
        if symbol in self.symbol_limits:
            sym_limits = self.symbol_limits[symbol]
            max_shares = int(sym_limits.get("max_shares", self.max_shares_per_position))
            max_value = sym_limits.get("max_value", self.max_value_per_position)
            max_pct = sym_limits.get("max_pct", self.max_position_pct)
        else:
            max_shares = self.max_shares_per_position
            max_value = self.max_value_per_position
            max_pct = self.max_position_pct

        # Calculate limits by different constraints
        by_shares = max_shares
        by_value = int(max_value / current_price) if current_price > 0 else max_shares
        by_pct = int((capital * max_pct) / current_price) if current_price > 0 else max_shares

        # Round down to nearest 100 (lot size)
        return min(by_shares, by_value, by_pct) // 100 * 100

    def can_add_position(self, symbol: str, quantity: int, price: float,
                         current_positions_value: float, capital: float) -> tuple[bool, str]:
        """Check if adding a position is within risk limits."""
        position_value = quantity * price

        # Check max position value
        if position_value > self.max_value_per_position:
            symbol_limit = self.symbol_limits.get(symbol, {}).get("max_value", self.max_value_per_position)
            if position_value > symbol_limit:
                return False, f"Position value ¥{position_value:.0f} exceeds limit ¥{symbol_limit:.0f}"

        # Check max positions count
        if len(self.get_all_symbols(symbol)) >= self.max_total_positions:
            return False, f"Maximum number of positions ({self.max_total_positions}) reached"

        # Check total exposure
        total_exposure = (current_positions_value + position_value) / capital
        if total_exposure > self.max_total_exposure:
            return False, f"Total exposure would be {total_exposure:.1%}, exceeding limit {self.max_total_exposure:.1%}"

        return True, "OK"

    def get_all_symbols(self, new_symbol: str) -> list:
        """Get list of symbols including the new one."""
        # This is a placeholder - in real implementation, would track existing positions
        return [new_symbol]

    def check_position_size(self, symbol: str, quantity: int, price: float, capital: float) -> tuple[bool, str]:
        """Check if position size is within limits."""
        max_shares = self.get_max_shares(symbol, price, capital)
        if quantity > max_shares:
            return False, f"Quantity {quantity} exceeds maximum {max_shares} shares"
        return True, "OK"


@dataclass
class TradingLimits:
    """
    Trading activity limits.
    """

    max_daily_trades: int = 50               # Max trades per day
    max_daily_loss: float = 0.05              # Max 5% loss per day
    max_daily_turnover: float = 500000        # Max daily turnover amount
    max_trades_per_symbol: int = 5           # Max trades per symbol per day
    min_time_between_trades: int = 0         # Min seconds between trades

    # Daily tracking
    trades_today: int = 0
    loss_today: float = 0
    turnover_today: float = 0
    symbol_trades_today: Dict[str, int] = field(default_factory=dict)
    last_trade_time: Optional[float] = None

    def can_trade(self, symbol: str, quantity: int, price: float,
                  current_time: float) -> tuple[bool, str]:
        """Check if trading is allowed based on limits."""
        # Check max daily trades
        if self.trades_today >= self.max_daily_trades:
            return False, f"Daily trade limit ({self.max_daily_trades}) reached"

        # Check max trades per symbol
        symbol_trades = self.symbol_trades_today.get(symbol, 0)
        if symbol_trades >= self.max_trades_per_symbol:
            return False, f"Symbol trade limit ({self.max_trades_per_symbol}) reached for {symbol}"

        # Check min time between trades
        if self.min_time_between_trades > 0 and self.last_trade_time is not None:
            elapsed = current_time - self.last_trade_time
            if elapsed < self.min_time_between_trades:
                return False, f"Must wait {self.min_time_between_trades - elapsed:.0f}s between trades"

        # Check daily loss limit
        if self.loss_today >= self.max_daily_loss:
            return False, f"Daily loss limit ({self.max_daily_loss:.1%}) reached"

        # Check daily turnover
        if self.turnover_today >= self.max_daily_turnover:
            return False, f"Daily turnover limit (¥{self.max_daily_turnover:.0f}) reached"

        return True, "OK"

    def record_trade(self, symbol: str, quantity: int, price: float,
                     realized_pnl: float = 0, current_time: Optional[float] = None) -> None:
        """Record a trade for limit tracking."""
        self.trades_today += 1
        self.symbol_trades_today[symbol] = self.symbol_trades_today.get(symbol, 0) + 1
        self.turnover_today += quantity * price
        self.last_trade_time = current_time or 0

        if realized_pnl < 0:
            self.loss_today += abs(realized_pnl)

    def reset_daily(self) -> None:
        """Reset daily limits (call at start of each day)."""
        self.trades_today = 0
        self.loss_today = 0
        self.turnover_today = 0
        self.symbol_trades_today.clear()
        self.last_trade_time = None
