"""
Historical Data Fetcher for Backtesting

Fetches historical market data for backtesting.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
from loguru import logger


class HistoricalDataFetcher:
    """
    Fetches historical market data for backtesting.

    For now, this generates mock data. In production, it would fetch
    from a real data source like Tushare, AKShare, or a database.
    """

    def __init__(self):
        self._cache = {}

    def fetch(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical data for a symbol.

        Args:
            symbol: Stock symbol (e.g., "600519")
            start_date: Start date in "YYYY-MM-DD" format
            end_date: End date in "YYYY-MM-DD" format
            interval: Data interval ("1d", "1h", "30m", etc.)

        Returns:
            DataFrame with columns: datetime, open, high, low, close, volume
        """
        cache_key = f"{symbol}_{start_date}_{end_date}_{interval}"

        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        # Generate mock data for now
        df = self._generate_mock_data(symbol, start_date, end_date, interval)

        self._cache[cache_key] = df.copy()
        return df

    def fetch_multiple(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch historical data for multiple symbols.

        Args:
            symbols: List of stock symbols
            start_date: Start date in "YYYY-MM-DD" format
            end_date: End date in "YYYY-MM-DD" format
            interval: Data interval

        Returns:
            Dictionary mapping symbols to DataFrames
        """
        result = {}
        for symbol in symbols:
            try:
                result[symbol] = self.fetch(symbol, start_date, end_date, interval)
            except Exception as e:
                logger.error(f"Failed to fetch data for {symbol}: {e}")
        return result

    def _generate_mock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str
    ) -> pd.DataFrame:
        """Generate mock historical data for testing."""

        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        # Generate date range
        if interval == "1d":
            dates = pd.date_range(start, end, freq="B")  # Business days
        elif interval == "1h":
            dates = pd.date_range(start, end, freq="1H")
        elif interval == "30m":
            dates = pd.date_range(start, end, freq="30min")
        else:
            dates = pd.date_range(start, end, freq="D")

        if len(dates) == 0:
            return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])

        # Generate price data using a random walk
        import numpy as np
        np.random.seed(hash(symbol) % 10000)

        base_price = 10 + (hash(symbol) % 100)
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = [base_price]

        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        # Create OHLC data
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            high = close * (1 + abs(np.random.normal(0, 0.01)))
            low = close * (1 - abs(np.random.normal(0, 0.01)))
            open_price = prices[i-1] if i > 0 else close

            # Add some intraday variation
            if interval != "1d":
                high = max(open_price, close, high)
                low = min(open_price, close, low)

            volume = int(np.random.lognormal(15, 1))

            data.append({
                "datetime": date,
                "open": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": volume,
            })

        df = pd.DataFrame(data)
        df.set_index("datetime", inplace=True)

        return df

    def clear_cache(self) -> None:
        """Clear the data cache."""
        self._cache.clear()
