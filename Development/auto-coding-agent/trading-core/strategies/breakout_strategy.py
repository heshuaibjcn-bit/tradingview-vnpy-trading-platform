"""
突破策略
Breakout Strategy

Generates buy/sell signals based on price breakouts from consolidation
"""

from typing import List, Optional
from datetime import datetime

from .base import BaseStrategy, Signal, SignalType, StrategyConfig
from market.fetcher import RealtimeQuote, OHLCV, get_kline
from utils.logger import logger


class BreakoutStrategy(BaseStrategy):
    """
    Price breakout strategy

    Generates signals when price breaks through resistance or support levels
    Uses Donchian channels or pivot points for level detection
    """

    def __init__(self, config: StrategyConfig):
        """
        Initialize breakout strategy

        Expected parameters:
            - period: Lookback period for high/low (default: 20)
            - atr_period: ATR period for volatility measurement (default: 14)
            - atr_multiplier: ATR multiplier for confirmation (default: 1.5)
            - volume_confirm: Use volume for confirmation (default: true)
        """
        super().__init__(config)

        self.period = self.get_parameter("period", 20)
        self.atr_period = self.get_parameter("atr_period", 14)
        self.atr_multiplier = self.get_parameter("atr_multiplier", 1.5)
        self.volume_confirm = self.get_parameter("volume_confirm", True)

        logger.info(
            f"Breakout strategy initialized: period={self.period}, "
            f"atr_period={self.atr_period}, atr_multiplier={self.atr_multiplier}"
        )

    async def generate_signal(self, quote: RealtimeQuote) -> Optional[Signal]:
        """Not used for breakout strategy"""
        return None

    async def analyze(self, symbol: str) -> List[Signal]:
        """
        Analyze symbol and generate signals based on breakout

        Args:
            symbol: Stock symbol

        Returns:
            List of signals
        """
        try:
            # Fetch K-line data
            required_count = self.period + 10
            ohlcv_list = await get_kline(symbol, period="101", count=required_count)

            if len(ohlcv_list) < required_count:
                logger.warning(
                    f"Not enough data for breakout strategy {self.name} on {symbol}: "
                    f"{len(ohlcv_list)} < {required_count}"
                )
                return []

            # Calculate support and resistance
            lookback_data = ohlcv_list[:-1]  # Exclude current bar
            current_bar = ohlcv_list[-1]

            highs = [bar.high for bar in lookback_data]
            lows = [bar.low for bar in lookback_data]
            volumes = [bar.volume for bar in lookback_data]

            resistance = max(highs[-self.period:])
            support = min(lows[-self.period:])
            avg_volume = sum(volumes[-self.period:]) / self.period if self.period > 0 else 0

            current_price = current_bar.close
            current_high = current_bar.high
            current_low = current_bar.low
            current_volume = current_bar.volume

            signals = []

            # Bullish breakout: price breaks above resistance
            if current_high > resistance:
                # Volume confirmation
                volume_confirmed = not self.volume_confirm or current_volume > avg_volume

                if volume_confirmed:
                    # Calculate confidence based on breakout strength
                    breakout_strength = (current_high - resistance) / resistance
                    confidence = min(breakout_strength * 10 + 0.5, 1.0)

                    signals.append(Signal(
                        symbol=symbol,
                        signal_type=SignalType.BUY,
                        price=current_price,
                        quantity=self._calculate_quantity(current_price),
                        confidence=confidence,
                        reason=f"Bullish breakout: price({current_price:.2f}) broke above "
                              f"resistance({resistance:.2f}), strength: {breakout_strength:.2%}"
                    ))
                    logger.info(
                        f"BUY signal: {symbol} broke above resistance {resistance:.2f} "
                        f"at {current_price:.2f}"
                    )

            # Bearish breakout: price breaks below support
            elif current_low < support:
                # Volume confirmation (higher volume for breakdown)
                volume_confirmed = not self.volume_confirm or current_volume > avg_volume

                if volume_confirmed:
                    # Calculate confidence based on breakdown strength
                    breakdown_strength = (support - current_low) / support
                    confidence = min(breakdown_strength * 10 + 0.5, 1.0)

                    signals.append(Signal(
                        symbol=symbol,
                        signal_type=SignalType.SELL,
                        price=current_price,
                        quantity=self._calculate_quantity(current_price),
                        confidence=confidence,
                        reason=f"Bearish breakdown: price({current_price:.2f}) broke below "
                              f"support({support:.2f}), strength: {breakdown_strength:.2%}"
                    ))
                    logger.info(
                        f"SELL signal: {symbol} broke below support {support:.2f} "
                        f"at {current_price:.2f}"
                    )

            return signals

        except Exception as e:
            logger.error(f"Error in breakout strategy {self.name} for {symbol}: {e}")
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


def create_breakout_strategy(
    name: str,
    symbols: List[str],
    period: int = 20,
    atr_period: int = 14,
    atr_multiplier: float = 1.5,
    volume_confirm: bool = True,
    enabled: bool = False
) -> BreakoutStrategy:
    """
    Create breakout strategy with default config

    Args:
        name: Strategy name
        symbols: Symbols to trade
        period: Lookback period for levels
        atr_period: ATR period
        atr_multiplier: ATR multiplier
        volume_confirm: Use volume confirmation
        enabled: Enable strategy

    Returns:
        BreakoutStrategy instance
    """
    config = StrategyConfig(
        name=name,
        type="breakout",
        enabled=enabled,
        symbols=symbols,
        parameters={
            "period": period,
            "atr_period": atr_period,
            "atr_multiplier": atr_multiplier,
            "volume_confirm": volume_confirm
        },
        risk_params={
            "max_position_ratio": 0.2,
            "stop_loss_ratio": 0.03,
            "take_profit_ratio": 0.06
        }
    )

    return BreakoutStrategy(config)
