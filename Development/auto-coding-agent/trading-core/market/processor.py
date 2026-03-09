"""
行情数据处理模块
Market Data Processor Module
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

from .fetcher import OHLCV, RealtimeQuote, Tick
from utils.logger import logger


class IndicatorCalculator:
    """
    Technical indicator calculator
    """

    @staticmethod
    def sma(data: List[float], period: int) -> List[float]:
        """
        Simple Moving Average

        Args:
            data: Price data
            period: SMA period

        Returns:
            List of SMA values
        """
        if len(data) < period:
            return []

        df = pd.DataFrame({'price': data})
        sma = df['price'].rolling(window=period).mean()
        return sma.dropna().tolist()

    @staticmethod
    def ema(data: List[float], period: int) -> List[float]:
        """
        Exponential Moving Average

        Args:
            data: Price data
            period: EMA period

        Returns:
            List of EMA values
        """
        if len(data) < period:
            return []

        df = pd.DataFrame({'price': data})
        ema = df['price'].ewm(span=period, adjust=False).mean()
        return ema.dropna().tolist()

    @staticmethod
    def macd(
        data: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[List[float], List[float], List[float]]:
        """
        MACD (Moving Average Convergence Divergence)

        Args:
            data: Price data
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period

        Returns:
            Tuple of (macd, signal, histogram)
        """
        if len(data) < slow_period:
            return [], [], []

        df = pd.DataFrame({'price': data})

        # Calculate EMAs
        ema_fast = df['price'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df['price'].ewm(span=slow_period, adjust=False).mean()

        # MACD line
        macd = ema_fast - ema_slow

        # Signal line
        signal = macd.ewm(span=signal_period, adjust=False).mean()

        # Histogram
        histogram = macd - signal

        # Return as lists, dropping NaN values
        return (
            macd.dropna().tolist(),
            signal.dropna().tolist(),
            histogram.dropna().tolist()
        )

    @staticmethod
    def kdj(
        high: List[float],
        low: List[float],
        close: List[float],
        period: int = 9,
        k_period: int = 3,
        d_period: int = 3
    ) -> Tuple[List[float], List[float], List[float]]:
        """
        KDJ indicator

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: RSV period
            k_period: K smoothing period
            d_period: D smoothing period

        Returns:
            Tuple of (k, d, j)
        """
        if len(close) < period:
            return [], [], []

        df = pd.DataFrame({
            'high': high,
            'low': low,
            'close': close
        })

        # Calculate RSV
        low_min = df['low'].rolling(window=period).min()
        high_max = df['high'].rolling(window=period).max()
        rsv = (df['close'] - low_min) / (high_max - low_min) * 100

        # Calculate K, D, J
        k = rsv.ewm(alpha=1/k_period, adjust=False).mean()
        d = k.ewm(alpha=1/d_period, adjust=False).mean()
        j = 3 * k - 2 * d

        # Return as lists, dropping NaN values
        return (
            k.dropna().tolist(),
            d.dropna().tolist(),
            j.dropna().tolist()
        )

    @staticmethod
    def rsi(data: List[float], period: int = 14) -> List[float]:
        """
        Relative Strength Index

        Args:
            data: Price data
            period: RSI period

        Returns:
            List of RSI values
        """
        if len(data) < period + 1:
            return []

        df = pd.DataFrame({'price': data})
        delta = df['price'].diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.dropna().tolist()

    @staticmethod
    def bollinger_bands(
        data: List[float],
        period: int = 20,
        num_std: float = 2.0
    ) -> Tuple[List[float], List[float], List[float]]:
        """
        Bollinger Bands

        Args:
            data: Price data
            period: MA period
            num_std: Number of standard deviations

        Returns:
            Tuple of (upper, middle, lower) bands
        """
        if len(data) < period:
            return [], [], []

        df = pd.DataFrame({'price': data})

        middle = df['price'].rolling(window=period).mean()
        std = df['price'].rolling(window=period).std()

        upper = middle + (std * num_std)
        lower = middle - (std * num_std)

        return (
            upper.dropna().tolist(),
            middle.dropna().tolist(),
            lower.dropna().tolist()
        )


class DataProcessor:
    """
    Market data processor
    """

    def __init__(self):
        self.indicator_calc = IndicatorCalculator()

    def ohlcv_to_dataframe(self, ohlcv_list: List[OHLCV]) -> pd.DataFrame:
        """
        Convert OHLCV list to pandas DataFrame

        Args:
            ohlcv_list: List of OHLCV data

        Returns:
            DataFrame with OHLCV data
        """
        data = {
            'timestamp': [ohlcv.timestamp for ohlcv in ohlcv_list],
            'open': [ohlcv.open for ohlcv in ohlcv_list],
            'high': [ohlcv.high for ohlcv in ohlcv_list],
            'low': [ohlcv.low for ohlcv in ohlcv_list],
            'close': [ohlcv.close for ohlcv in ohlcv_list],
            'volume': [ohlcv.volume for ohlcv in ohlcv_list],
            'amount': [ohlcv.amount for ohlcv in ohlcv_list],
        }

        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df

    def calculate_returns(
        self,
        ohlcv_list: List[OHLCV],
        period: int = 1
    ) -> List[float]:
        """
        Calculate returns

        Args:
            ohlcv_list: List of OHLCV data
            period: Return period

        Returns:
            List of return values
        """
        df = self.ohlcv_to_dataframe(ohlcv_list)
        returns = df['close'].pct_change(period).dropna()
        return returns.tolist()

    def calculate_volatility(
        self,
        ohlcv_list: List[OHLCV],
        period: int = 20
    ) -> float:
        """
        Calculate historical volatility (standard deviation of returns)

        Args:
            ohlcv_list: List of OHLCV data
            period: Period for volatility calculation

        Returns:
            Volatility value
        """
        returns = self.calculate_returns(ohlcv_list)

        if len(returns) < period:
            period = len(returns)

        if period == 0:
            return 0.0

        recent_returns = returns[-period:]
        return float(np.std(recent_returns))

    def find_support_resistance(
        self,
        ohlcv_list: List[OHLCV],
        window: int = 20
    ) -> Tuple[float, float]:
        """
        Find support and resistance levels

        Args:
            ohlcv_list: List of OHLCV data
            window: Lookback window

        Returns:
            Tuple of (support, resistance)
        """
        if len(ohlcv_list) < window:
            window = len(ohlcv_list)

        recent = ohlcv_list[-window:]
        lows = [ohlcv.low for ohlcv in recent]
        highs = [ohlcv.high for ohlcv in recent]

        support = float(min(lows))
        resistance = float(max(highs))

        return support, resistance

    def detect_breakout(
        self,
        ohlcv_list: List[OHLCV],
        threshold: float = 0.02
    ) -> Dict[str, Any]:
        """
        Detect price breakout

        Args:
            ohlcv_list: List of OHLCV data
            threshold: Breakout threshold (percentage)

        Returns:
            Detection result
        """
        if len(ohlcv_list) < 2:
            return {
                'detected': False,
                'direction': None,
                'strength': 0
            }

        current = ohlcv_list[-1]
        previous = ohlcv_list[-2]

        # Get recent high and low
        support, resistance = self.find_support_resistance(ohlcv_list)

        # Check for breakout
        if current.close > resistance * (1 + threshold):
            return {
                'detected': True,
                'direction': 'up',
                'strength': (current.close - resistance) / resistance,
                'resistance': resistance
            }
        elif current.close < support * (1 - threshold):
            return {
                'detected': True,
                'direction': 'down',
                'strength': (support - current.close) / support,
                'support': support
            }

        return {
            'detected': False,
            'direction': None,
            'strength': 0
        }

    def calculate_atr(
        self,
        ohlcv_list: List[OHLCV],
        period: int = 14
    ) -> float:
        """
        Calculate Average True Range

        Args:
            ohlcv_list: List of OHLCV data
            period: ATR period

        Returns:
            ATR value
        """
        if len(ohlcv_list) < period + 1:
            return 0.0

        df = self.ohlcv_to_dataframe(ohlcv_list)

        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return float(atr.iloc[-1])


class QuoteAnalyzer:
    """
    Realtime quote analyzer
    """

    @staticmethod
    def is_limit_up(quote: RealtimeQuote, threshold: float = 0.095) -> bool:
        """Check if price is at limit up"""
        return quote.change_percent >= threshold * 100

    @staticmethod
    def is_limit_down(quote: RealtimeQuote, threshold: float = 0.095) -> bool:
        """Check if price is at limit down"""
        return quote.change_percent <= -threshold * 100

    @staticmethod
    def get_price_position(quote: RealtimeQuote) -> str:
        """Get price position within daily range"""
        if quote.high == quote.low:
            return "middle"

        range_size = quote.high - quote.low
        position = (quote.price - quote.low) / range_size

        if position >= 0.8:
            return "high"
        elif position >= 0.6:
            return "upper_mid"
        elif position >= 0.4:
            return "middle"
        elif position >= 0.2:
            return "lower_mid"
        else:
            return "low"

    @staticmethod
    def calculate_bid_ask_spread(quote: RealtimeQuote) -> Tuple[float, float]:
        """
        Calculate bid-ask spread

        Returns:
            Tuple of (absolute spread, percentage spread)
        """
        if quote.ask_price == 0:
            return 0.0, 0.0

        abs_spread = quote.ask_price - quote.bid_price
        pct_spread = (abs_spread / quote.ask_price) * 100

        return abs_spread, pct_spread


# Global instances
indicator_calc = IndicatorCalculator()
data_processor = DataProcessor()
quote_analyzer = QuoteAnalyzer()
