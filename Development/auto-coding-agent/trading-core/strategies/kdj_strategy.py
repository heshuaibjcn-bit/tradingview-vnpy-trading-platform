"""
KDJ 策略
KDJ (Stochastic) Strategy

Generates buy/sell signals based on KDJ indicator overbought/oversold levels
"""

from typing import List, Optional
from datetime import datetime

from .base import BaseStrategy, Signal, SignalType, StrategyConfig
from market.fetcher import RealtimeQuote, OHLCV, get_kline
from market.processor import IndicatorCalculator
from utils.logger import logger


class KDJStrategy(BaseStrategy):
    """
    KDJ stochastic strategy

    Generates signals based on:
    - K line crossing above D line (bullish)
    - K line crossing below D line (bearish)
    - Overbought (>80) and oversold (<20) levels
    """

    def __init__(self, config: StrategyConfig):
        """
        Initialize KDJ strategy

        Expected parameters:
            - k_period: K line period (default: 9)
            - d_period: D line period (default: 3)
            - j_period: J line period (default: 3)
            - overbought: Overbought level (default: 80)
            - oversold: Oversold level (default: 20)
        """
        super().__init__(config)

        self.k_period = self.get_parameter("k_period", 9)
        self.d_period = self.get_parameter("d_period", 3)
        self.j_period = self.get_parameter("j_period", 3)
        self.overbought = self.get_parameter("overbought", 80)
        self.oversold = self.get_parameter("oversold", 20)

        logger.info(
            f"KDJ strategy initialized: k={self.k_period}, d={self.d_period}, "
            f"j={self.j_period}, overbought={self.overbought}, oversold={self.oversold}"
        )

    async def generate_signal(self, quote: RealtimeQuote) -> Optional[Signal]:
        """Not used for KDJ strategy"""
        return None

    async def analyze(self, symbol: str) -> List[Signal]:
        """
        Analyze symbol and generate signals based on KDJ

        Args:
            symbol: Stock symbol

        Returns:
            List of signals
        """
        try:
            # Fetch K-line data
            required_count = self.k_period + self.d_period + self.j_period + 10
            ohlcv_list = await get_kline(symbol, period="101", count=required_count)

            if len(ohlcv_list) < required_count:
                logger.warning(
                    f"Not enough data for KDJ strategy {self.name} on {symbol}: "
                    f"{len(ohlcv_list)} < {required_count}"
                )
                return []

            # Prepare data for KDJ calculation
            highs = [ohlcv.high for ohlcv in ohlcv_list]
            lows = [ohlcv.low for ohlcv in ohlcv_list]
            closes = [ohlcv.close for ohlcv in ohlcv_list]

            calc = IndicatorCalculator()
            kdj_result = calc.kdj(
                highs,
                lows,
                closes,
                self.k_period,
                self.d_period,
                self.j_period
            )

            if not kdj_result or "k" not in kdj_result:
                return []

            k_list = kdj_result["k"]
            d_list = kdj_result.get("d", [])
            j_list = kdj_result.get("j", [])

            if len(k_list) < 2 or len(d_list) < 2:
                return []

            # Get current and previous values
            current_k = k_list[-1]
            current_d = d_list[-1]
            current_j = j_list[-1] if j_list else 0

            prev_k = k_list[-2]
            prev_d = d_list[-2]

            # Get current price
            current_quote = await get_realtime_quote(symbol)
            if not current_quote:
                return []
            current_price = current_quote.price

            signals = []

            # Bullish signals
            # 1. K crosses above D from oversold
            if (prev_k <= prev_d and
                current_k > current_d and
                prev_k < self.oversold):

                signals.append(Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=current_price,
                    quantity=self._calculate_quantity(current_price),
                    confidence=self._calculate_oversold_confidence(current_k),
                    reason=f"KDJ bullish from oversold: K({current_k:.2f}) > D({current_d:.2f}), "
                          f"was at {prev_k:.2f} (oversold: {self.oversold})"
                ))
                logger.info(
                    f"BUY signal: {symbol} K({current_k:.2f}) > D({current_d:.2f}) from oversold"
                )

            # 2. K and D both in oversold zone, starting to rise
            elif (current_k < self.oversold and
                  current_d < self.oversold and
                  current_k > prev_k and
                  current_d > prev_d):

                signals.append(Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=current_price,
                    quantity=self._calculate_quantity(current_price),
                    confidence=0.7,
                    reason=f"KDJ oversold rebound: K({current_k:.2f}), D({current_d:.2f}) "
                          f"both below {self.oversold} and rising"
                ))
                logger.info(
                    f"BUY signal: {symbol} KDJ oversold rebound K({current_k:.2f}), D({current_d:.2f})"
                )

            # Bearish signals
            # 1. K crosses below D from overbought
            elif (prev_k >= prev_d and
                  current_k < current_d and
                  prev_k > self.overbought):

                signals.append(Signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=current_price,
                    quantity=self._calculate_quantity(current_price),
                    confidence=self._calculate_overbought_confidence(current_k),
                    reason=f"KDJ bearish from overbought: K({current_k:.2f}) < D({current_d:.2f}), "
                          f"was at {prev_k:.2f} (overbought: {self.overbought})"
                ))
                logger.info(
                    f"SELL signal: {symbol} K({current_k:.2f}) < D({current_d:.2f}) from overbought"
                )

            # 2. K and D both in overbought zone, starting to fall
            elif (current_k > self.overbought and
                  current_d > self.overbought and
                  current_k < prev_k and
                  current_d < prev_d):

                signals.append(Signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=current_price,
                    quantity=self._calculate_quantity(current_price),
                    confidence=0.7,
                    reason=f"KDJ overbought decline: K({current_k:.2f}), D({current_d:.2f}) "
                          f"both above {self.overbought} and falling"
                ))
                logger.info(
                    f"SELL signal: {symbol} KDJ overbought decline K({current_k:.2f}), D({current_d:.2f})"
                )

            return signals

        except Exception as e:
            logger.error(f"Error in KDJ strategy {self.name} for {symbol}: {e}")
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

    def _calculate_oversold_confidence(self, k_value: float) -> float:
        """Calculate confidence for oversold signal"""
        # Deeper in oversold = higher confidence
        depth = self.oversold - k_value
        return min(max(depth / 40.0, 0.3), 1.0)

    def _calculate_overbought_confidence(self, k_value: float) -> float:
        """Calculate confidence for overbought signal"""
        # Higher above overbought = higher confidence
        height = k_value - self.overbought
        return min(max(height / 40.0, 0.3), 1.0)


def create_kdj_strategy(
    name: str,
    symbols: List[str],
    k_period: int = 9,
    d_period: int = 3,
    j_period: int = 3,
    overbought: int = 80,
    oversold: int = 20,
    enabled: bool = False
) -> KDJStrategy:
    """
    Create KDJ strategy with default config

    Args:
        name: Strategy name
        symbols: Symbols to trade
        k_period: K line period
        d_period: D line period
        j_period: J line period
        overbought: Overbought threshold
        oversold: Oversold threshold
        enabled: Enable strategy

    Returns:
        KDJStrategy instance
    """
    config = StrategyConfig(
        name=name,
        type="kdj",
        enabled=enabled,
        symbols=symbols,
        parameters={
            "k_period": k_period,
            "d_period": d_period,
            "j_period": j_period,
            "overbought": overbought,
            "oversold": oversold
        },
        risk_params={
            "max_position_ratio": 0.3,
            "stop_loss_ratio": 0.05,
            "take_profit_ratio": 0.10
        }
    )

    return KDJStrategy(config)
