"""
网格交易策略
Grid Trading Strategy

Places buy/sell orders at predetermined price levels in a grid
"""

from typing import List, Optional, Dict
from datetime import datetime
from collections import defaultdict

from .base import BaseStrategy, Signal, SignalType, StrategyConfig
from market.fetcher import RealtimeQuote, get_realtime_quote
from utils.logger import logger


class GridTradingStrategy(BaseStrategy):
    """
    Grid trading strategy

    Creates a grid of buy orders below current price and sell orders above
    Profits from price oscillations in a ranging market

    Parameters:
        - grid_count: Number of grid levels (default: 10)
        - grid_spacing: Percentage spacing between levels (default: 0.01 = 1%)
        - base_price: Reference price for grid center (default: current price)
        - min_price: Minimum grid price
        - max_price: Maximum grid price
    """

    def __init__(self, config: StrategyConfig):
        """
        Initialize grid trading strategy

        Expected parameters:
            - grid_count: Number of grid levels on each side (default: 5)
            - grid_spacing: Percentage between levels (default: 0.01 = 1%)
            - position_size: Quantity per grid level (default: 100)
        """
        super().__init__(config)

        self.grid_count = self.get_parameter("grid_count", 5)
        self.grid_spacing = self.get_parameter("grid_spacing", 0.01)
        self.position_size = self.get_parameter("position_size", 100)

        # Grid state per symbol
        self._grids: Dict[str, "GridState"] = {}
        self._positions: Dict[str, Dict[float, int]] = defaultdict(dict)

        logger.info(
            f"Grid trading strategy initialized: grid_count={self.grid_count}, "
            f"grid_spacing={self.grid_spacing * 100}%"
        )

    def initialize_grid(self, symbol: str, base_price: float) -> None:
        """Initialize grid levels for a symbol"""
        if symbol in self._grids:
            return

        buy_levels = []
        sell_levels = []

        # Create buy levels below current price
        for i in range(1, self.grid_count + 1):
            price = base_price * (1 - self.grid_spacing * i)
            buy_levels.append(price)

        # Create sell levels above current price
        for i in range(1, self.grid_count + 1):
            price = base_price * (1 + self.grid_spacing * i)
            sell_levels.append(price)

        self._grids[symbol] = GridState(
            symbol=symbol,
            base_price=base_price,
            buy_levels=sorted(buy_levels, reverse=True),  # Highest first
            sell_levels=sorted(sell_levels),
        )

        logger.info(
            f"Grid initialized for {symbol}: base={base_price:.2f}, "
            f"buy_range={buy_levels[-1]:.2f}-{buy_levels[0]:.2f}, "
            f"sell_range={sell_levels[0]:.2f}-{sell_levels[-1]:.2f}"
        )

    async def generate_signal(self, quote: RealtimeQuote) -> Optional[Signal]:
        """
        Generate signal based on grid levels

        For grid trading, signals are generated when:
        1. Price hits a buy level -> place buy order
        2. Price hits a sell level -> sell existing position
        """
        symbol = quote.symbol
        current_price = quote.price

        # Initialize grid if not exists
        if symbol not in self._grids:
            self.initialize_grid(symbol, current_price)

        grid = self._grids[symbol]
        signals = []

        # Check buy levels
        for buy_price in grid.buy_levels:
            # If price at or below buy level and no position at this level
            if current_price <= buy_price and buy_price not in self._positions[symbol]:
                # Generate buy signal
                return Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=buy_price,
                    quantity=self.position_size,
                    confidence=0.8,
                    reason=f"Grid buy: price({current_price:.2f}) at/below buy level({buy_price:.2f})",
                    metadata={"grid_level": buy_price, "grid_type": "buy"}
                )

        # Check sell levels
        for sell_price in grid.sell_levels:
            # If price at or above sell level and have position from lower level
            if current_price >= sell_price:
                # Find positions to sell
                for buy_price_level in list(self._positions[symbol].keys()):
                    if sell_price >= buy_price_level * (1 + self.grid_spacing):
                        qty = self._positions[symbol][buy_price_level]
                        if qty > 0:
                            return Signal(
                                symbol=symbol,
                                signal_type=SignalType.SELL,
                                price=sell_price,
                                quantity=qty,
                                confidence=0.9,
                                reason=f"Grid sell: price({current_price:.2f}) at/above sell level({sell_price:.2f}), "
                                      f"closing position from {buy_price_level:.2f}",
                                metadata={"grid_level": sell_price, "grid_type": "sell", "buy_level": buy_price_level}
                            )

        return None

    async def analyze(self, symbol: str) -> List[Signal]:
        """Analyze symbol for grid trading signals"""
        try:
            quote = await get_realtime_quote(symbol)
            if not quote:
                return []

            signal = await self.generate_signal(quote)
            return [signal] if signal else []

        except Exception as e:
            logger.error(f"Error in grid strategy {self.name} for {symbol}: {e}")
            return []

    def record_fill(self, symbol: str, price: float, quantity: int, side: str) -> None:
        """
        Record a filled order and update grid state

        This should be called when an order generated by the strategy is filled
        """
        if side == "buy":
            # Record long position
            self._positions[symbol][price] = quantity
            logger.info(f"Grid position opened: {symbol} {quantity}@{price:.2f}")
        elif side == "sell":
            # Close corresponding position
            # Find the buy level this sell corresponds to
            for buy_price in list(self._positions[symbol].keys()):
                if price >= buy_price * (1 + self.grid_spacing / 2):
                    qty = self._positions[symbol].get(buy_price, 0)
                    if qty > 0:
                        actual_qty = min(qty, quantity)
                        self._positions[symbol][buy_price] = qty - actual_qty
                        if self._positions[symbol][buy_price] <= 0:
                            del self._positions[symbol][buy_price]
                        logger.info(
                            f"Grid position closed: {symbol} {actual_qty}@{price:.2f}, "
                            f"profit: {(price - buy_price) * actual_qty:.2f}"
                        )
                        break

    def get_grid_state(self, symbol: str) -> Optional[Dict]:
        """Get current grid state for a symbol"""
        if symbol not in self._grids:
            return None

        grid = self._grids[symbol]
        return {
            "base_price": grid.base_price,
            "buy_levels": grid.buy_levels,
            "sell_levels": grid.sell_levels,
            "positions": dict(self._positions[symbol]),
        }


class GridState:
    """Grid state for a symbol"""

    def __init__(
        self,
        symbol: str,
        base_price: float,
        buy_levels: List[float],
        sell_levels: List[float],
    ):
        self.symbol = symbol
        self.base_price = base_price
        self.buy_levels = buy_levels
        self.sell_levels = sell_levels
        self.created_at = datetime.now()


def create_grid_strategy(
    name: str,
    symbols: List[str],
    grid_count: int = 5,
    grid_spacing: float = 0.01,
    position_size: int = 100,
    enabled: bool = False
) -> GridTradingStrategy:
    """
    Create grid trading strategy with default config

    Args:
        name: Strategy name
        symbols: Symbols to trade
        grid_count: Number of grid levels per side
        grid_spacing: Percentage between levels
        position_size: Quantity per level
        enabled: Enable strategy

    Returns:
        GridTradingStrategy instance
    """
    config = StrategyConfig(
        name=name,
        type="grid",
        enabled=enabled,
        symbols=symbols,
        parameters={
            "grid_count": grid_count,
            "grid_spacing": grid_spacing,
            "position_size": position_size
        },
        risk_params={
            "max_position_ratio": 0.5,
            "max_total_position": 50000
        }
    )

    return GridTradingStrategy(config)
