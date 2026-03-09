"""
均线策略
Moving Average (MA) Strategy

Generates buy/sell signals based on moving average crossovers
"""

from typing import List, Optional
from datetime import datetime, timedelta

from .base import BaseStrategy, Signal, SignalType, StrategyConfig
from market.fetcher import RealtimeQuote, OHLCV, get_kline
from market.processor import IndicatorCalculator
from utils.logger import logger


class MAStrategy(BaseStrategy):
    """
    Moving Average crossover strategy

    Generates signals when short MA crosses long MA
    """

    def __init__(self, config: StrategyConfig):
        """
        Initialize MA strategy

        Expected parameters:
            - short_period: Short MA period (default: 5)
            - long_period: Long MA period (default: 20)
            - use_ema: Use EMA instead of SMA (default: false)
        """
        super().__init__(config)

        self.short_period = self.get_parameter("short_period", 5)
        self.long_period = self.get_parameter("long_period", 20)
        self.use_ema = self.get_parameter("use_ema", False)

        self._last_short_ma: Optional[float] = None
        self._last_long_ma: Optional[float] = None
        self._last_signal: Optional[Signal] = None

        # Validate parameters
        if self.short_period >= self.long_period:
            logger.warning(
                f"Short period ({self.short_period}) >= long period ({self.long_period}), "
                "swapping values"
            )
            self.short_period, self.long_period = self.long_period, self.short_period

        logger.info(
            f"MA strategy initialized: short={self.short_period}, "
            f"long={self.long_period}, ema={self.use_ema}"
        )

    async def generate_signal(self, quote: RealtimeQuote) -> Optional[Signal]:
        """
        Generate signal from quote (not used in MA strategy)

        MA strategy requires historical data, so this is a placeholder
        """
        return None

    async def analyze(self, symbol: str) -> List[Signal]:
        """
        Analyze symbol and generate signals based on MA crossover

        Args:
            symbol: Stock symbol

        Returns:
            List of signals (usually 0 or 1)
        """
        try:
            # Fetch K-line data
            ohlcv_list = await get_kline(symbol, period="101", count=self.long_period + 10)

            if len(ohlcv_list) < self.long_period:
                logger.warning(
                    f"Not enough data for MA strategy {self.name} on {symbol}: "
                    f"{len(ohlcv_list)} < {self.long_period}"
                )
                return []

            # Calculate MAs
            closes = [ohlcv.close for ohlcv in ohlcv_list]
            calc = IndicatorCalculator()

            if self.use_ema:
                short_ma_list = calc.ema(closes, self.short_period)
                long_ma_list = calc.ema(closes, self.long_period)
            else:
                short_ma_list = calc.sma(closes, self.short_period)
                long_ma_list = calc.sma(closes, self.long_period)

            if not short_ma_list or not long_ma_list:
                return []

            current_short_ma = short_ma_list[-1]
            current_long_ma = long_ma_list[-1]

            # Get previous values
            if len(short_ma_list) < 2 or len(long_ma_list) < 2:
                return []

            prev_short_ma = short_ma_list[-2]
            prev_long_ma = long_ma_list[-2]

            # Get current price
            current_quote = await get_realtime_quote(symbol)
            if not current_quote:
                return []

            current_price = current_quote.price

            # Check for crossover
            signals = []

            # Golden cross (bullish): short MA crosses above long MA
            if (prev_short_ma <= prev_long_ma and
                current_short_ma > current_long_ma):

                # Additional confirmation: price is above both MAs
                if current_price > current_short_ma:
                    signals.append(Signal(
                        symbol=symbol,
                        signal_type=SignalType.BUY,
                        price=current_price,
                        quantity=self._calculate_quantity(current_price),
                        confidence=self._calculate_confidence(
                            current_short_ma,
                            current_long_ma
                        ),
                        reason=f"MA{self.short_period} crossed above MA{self.long_period} "
                              f"({current_short_ma:.2f} > {current_long_ma:.2f})"
                    ))
                    logger.info(
                        f"BUY signal: {symbol} MA{self.short_period}({current_short_ma:.2f}) > "
                        f"MA{self.long_period}({current_long_ma:.2f})"
                    )

            # Death cross (bearish): short MA crosses below long MA
            elif (prev_short_ma >= prev_long_ma and
                  current_short_ma < current_long_ma):

                # Additional confirmation: price is below both MAs
                if current_price < current_short_ma:
                    signals.append(Signal(
                        symbol=symbol,
                        signal_type=SignalType.SELL,
                        price=current_price,
                        quantity=self._calculate_quantity(current_price),
                        confidence=self._calculate_confidence(
                            current_short_ma,
                            current_long_ma
                        ),
                        reason=f"MA{self.short_period} crossed below MA{self.long_period} "
                              f"({current_short_ma:.2f} < {current_long_ma:.2f})"
                    ))
                    logger.info(
                        f"SELL signal: {symbol} MA{self.short_period}({current_short_ma:.2f}) < "
                        f"MA{self.long_period}({current_long_ma:.2f})"
                    )

            return signals

        except Exception as e:
            logger.error(f"Error in MA strategy {self.name} for {symbol}: {e}")
            return []

    def _calculate_quantity(self, price: float) -> int:
        """Calculate order quantity based on price"""
        # Default to 100 shares for stocks under 50 yuan
        if price < 50:
            return 100
        # For more expensive stocks, adjust quantity to keep order around 5000 yuan
        elif price < 100:
            return 50
        elif price < 200:
            return 20
        else:
            return 10

    def _calculate_confidence(self, short_ma: float, long_ma: float) -> float:
        """
        Calculate signal confidence based on MA separation

        Args:
            short_ma: Short MA value
            long_ma: Long MA value

        Returns:
            Confidence score (0-1)
        """
        # Calculate percentage difference
        diff_pct = abs(short_ma - long_ma) / long_ma

        # Cap at 20% difference = 1.0 confidence
        return min(diff_pct / 0.20, 1.0)


def create_ma_strategy(
    name: str,
    symbols: List[str],
    short_period: int = 5,
    long_period: int = 20,
    use_ema: bool = False,
    enabled: bool = False
) -> MAStrategy:
    """
    Create MA strategy with default config

    Args:
        name: Strategy name
        symbols: Symbols to trade
        short_period: Short MA period
        long_period: Long MA period
        use_ema: Use EMA instead of SMA
        enabled: Enable strategy

    Returns:
        MAStrategy instance
    """
    config = StrategyConfig(
        name=name,
        type="ma",
        enabled=enabled,
        symbols=symbols,
        parameters={
            "short_period": short_period,
            "long_period": long_period,
            "use_ema": use_ema
        },
        risk_params={
            "max_position_ratio": 0.3,
            "stop_loss_ratio": 0.05,
            "take_profit_ratio": 0.10
        }
    )

    return MAStrategy(config)
