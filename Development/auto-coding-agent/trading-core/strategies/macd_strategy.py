"""
MACD 策略
Moving Average Convergence Divergence (MACD) Strategy

Generates buy/sell signals based on MACD indicator crossovers
"""

from typing import List, Optional
from datetime import datetime

from .base import BaseStrategy, Signal, SignalType, StrategyConfig
from market.fetcher import RealtimeQuote, OHLCV, get_kline
from market.processor import IndicatorCalculator
from utils.logger import logger


class MACDStrategy(BaseStrategy):
    """
    MACD crossover strategy

    Generates signals when MACD line crosses signal line
    Also considers histogram for confirmation

    MACD = EMA(12) - EMA(26)
    Signal = EMA(MACD, 9)
    Histogram = MACD - Signal
    """

    def __init__(self, config: StrategyConfig):
        """
        Initialize MACD strategy

        Expected parameters:
            - fast_period: Fast EMA period (default: 12)
            - slow_period: Slow EMA period (default: 26)
            - signal_period: Signal EMA period (default: 9)
            - histogram_confirm: Use histogram for confirmation (default: true)
        """
        super().__init__(config)

        self.fast_period = self.get_parameter("fast_period", 12)
        self.slow_period = self.get_parameter("slow_period", 26)
        self.signal_period = self.get_parameter("signal_period", 9)
        self.histogram_confirm = self.get_parameter("histogram_confirm", True)

        # Store previous values for crossover detection
        self._last_macd: Optional[float] = None
        self._last_signal: Optional[float] = None
        self._last_histogram: Optional[float] = None

        logger.info(
            f"MACD strategy initialized: fast={self.fast_period}, "
            f"slow={self.slow_period}, signal={self.signal_period}"
        )

    async def generate_signal(self, quote: RealtimeQuote) -> Optional[Signal]:
        """Not used for MACD strategy"""
        return None

    async def analyze(self, symbol: str) -> List[Signal]:
        """
        Analyze symbol and generate signals based on MACD

        Args:
            symbol: Stock symbol

        Returns:
            List of signals
        """
        try:
            # Fetch K-line data (need enough for slow + signal periods)
            required_count = self.slow_period + self.signal_period + 10
            ohlcv_list = await get_kline(symbol, period="101", count=required_count)

            if len(ohlcv_list) < required_count:
                logger.warning(
                    f"Not enough data for MACD strategy {self.name} on {symbol}: "
                    f"{len(ohlcv_list)} < {required_count}"
                )
                return []

            # Calculate MACD
            closes = [ohlcv.close for ohlcv in ohlcv_list]
            calc = IndicatorCalculator()

            macd_result = calc.macd(
                closes,
                self.fast_period,
                self.slow_period,
                self.signal_period
            )

            if not macd_result or "macd" not in macd_result:
                return []

            macd_list = macd_result["macd"]
            signal_list = macd_result["signal"]
            histogram_list = macd_result.get("histogram", [])

            if len(macd_list) < 2 or len(signal_list) < 2:
                return []

            # Get current and previous values
            current_macd = macd_list[-1]
            current_signal = signal_list[-1]
            current_histogram = histogram_list[-1] if histogram_list else 0

            prev_macd = macd_list[-2]
            prev_signal = signal_list[-2]
            prev_histogram = histogram_list[-2] if histogram_list and len(histogram_list) >= 2 else 0

            # Get current price
            current_quote = await get_realtime_quote(symbol)
            if not current_quote:
                return []
            current_price = current_quote.price

            signals = []

            # Bullish crossover: MACD crosses above signal line
            # Additional confirmation: histogram turns positive
            if (prev_macd <= prev_signal and
                current_macd > current_signal):

                # Optional histogram confirmation
                if not self.histogram_confirm or current_histogram > 0:
                    signals.append(Signal(
                        symbol=symbol,
                        signal_type=SignalType.BUY,
                        price=current_price,
                        quantity=self._calculate_quantity(current_price),
                        confidence=self._calculate_confidence(current_histogram),
                        reason=f"MACD bullish crossover: MACD({current_macd:.2f}) > "
                              f"Signal({current_signal:.2f}), Histogram({current_histogram:.2f})"
                    ))
                    logger.info(
                        f"BUY signal: {symbol} MACD({current_macd:.2f}) > "
                        f"Signal({current_signal:.2f}), Hist({current_histogram:.2f})"
                    )

            # Bearish crossover: MACD crosses below signal line
            # Additional confirmation: histogram turns negative
            elif (prev_macd >= prev_signal and
                  current_macd < current_signal):

                # Optional histogram confirmation
                if not self.histogram_confirm or current_histogram < 0:
                    signals.append(Signal(
                        symbol=symbol,
                        signal_type=SignalType.SELL,
                        price=current_price,
                        quantity=self._calculate_quantity(current_price),
                        confidence=self._calculate_confidence(abs(current_histogram)),
                        reason=f"MACD bearish crossover: MACD({current_macd:.2f}) < "
                              f"Signal({current_signal:.2f}), Histogram({current_histogram:.2f})"
                    ))
                    logger.info(
                        f"SELL signal: {symbol} MACD({current_macd:.2f}) < "
                        f"Signal({current_signal:.2f}), Hist({current_histogram:.2f})"
                    )

            # Store current values
            self._last_macd = current_macd
            self._last_signal = current_signal
            self._last_histogram = current_histogram

            return signals

        except Exception as e:
            logger.error(f"Error in MACD strategy {self.name} for {symbol}: {e}")
            return []

    def _calculate_quantity(self, price: float) -> int:
        """Calculate order quantity based on price"""
        if price < 50:
            return 100
        elif price < 100:
            return 50
        elif price < 200:
            return 20
        else:
            return 10

    def _calculate_confidence(self, histogram: float) -> float:
        """
        Calculate confidence based on histogram strength

        Stronger histogram = stronger trend = higher confidence
        """
        # Scale histogram to confidence (0.1 to 1.0)
        abs_histogram = abs(histogram)
        return min(max(abs_histogram / 2.0, 0.1), 1.0)


def create_macd_strategy(
    name: str,
    symbols: List[str],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    histogram_confirm: bool = True,
    enabled: bool = False
) -> MACDStrategy:
    """
    Create MACD strategy with default config

    Args:
        name: Strategy name
        symbols: Symbols to trade
        fast_period: Fast EMA period
        slow_period: Slow EMA period
        signal_period: Signal EMA period
        histogram_confirm: Use histogram confirmation
        enabled: Enable strategy

    Returns:
        MACDStrategy instance
    """
    config = StrategyConfig(
        name=name,
        type="macd",
        enabled=enabled,
        symbols=symbols,
        parameters={
            "fast_period": fast_period,
            "slow_period": slow_period,
            "signal_period": signal_period,
            "histogram_confirm": histogram_confirm
        },
        risk_params={
            "max_position_ratio": 0.3,
            "stop_loss_ratio": 0.05,
            "take_profit_ratio": 0.10
        }
    )

    return MACDStrategy(config)
