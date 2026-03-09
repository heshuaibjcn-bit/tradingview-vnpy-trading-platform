"""
行情数据缓存模块
Market Data Cache Module
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

from .fetcher import OHLCV, RealtimeQuote, MarketDataSource
from utils.logger import logger


class CacheEntry:
    """Cache entry with TTL"""

    def __init__(self, data: Any, ttl: timedelta):
        self.data = data
        self.expires_at = datetime.now() + ttl

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return datetime.now() > self.expires_at


class MarketDataCache:
    """
    Market data cache
    """

    def __init__(self, default_ttl: timedelta = timedelta(seconds=5)):
        """
        Initialize cache

        Args:
            default_ttl: Default time-to-live for cache entries
        """
        self._cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

        logger.info(f"MarketDataCache initialized (TTL: {default_ttl.total_seconds()}s)")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        entry = self._cache.get(key)

        if entry is None:
            self._misses += 1
            return None

        if entry.is_expired():
            del self._cache[key]
            self._misses += 1
            return None

        self._hits += 1
        return entry.data

    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> None:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live (uses default if None)
        """
        ttl = ttl or self.default_ttl
        self._cache[key] = CacheEntry(value, ttl)

    def delete(self, key: str) -> bool:
        """
        Delete value from cache

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
        logger.info("Cache cleared")

    def cleanup(self) -> int:
        """
        Remove expired entries

        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with stats
        """
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0

        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
        }

    async def get_or_fetch(
        self,
        key: str,
        fetcher: callable,
        ttl: Optional[timedelta] = None
    ) -> Optional[Any]:
        """
        Get from cache or fetch using provided function

        Args:
            key: Cache key
            fetcher: Async function to fetch data
            ttl: Cache TTL

        Returns:
            Cached or fetched data
        """
        # Try cache first
        cached = self.get(key)
        if cached is not None:
            logger.debug(f"Cache hit: {key}")
            return cached

        # Cache miss - fetch data
        logger.debug(f"Cache miss: {key}")
        data = await fetcher()

        if data is not None:
            self.set(key, data, ttl)

        return data


class QuoteCache(MarketDataCache):
    """
    Specialized cache for realtime quotes
    """

    def __init__(self, ttl: timedelta = timedelta(seconds=3)):
        super().__init__(default_ttl=ttl)

    def get_quote(self, symbol: str) -> Optional[RealtimeQuote]:
        """Get cached quote"""
        return self.get(f"quote:{symbol}")

    def set_quote(self, symbol: str, quote: RealtimeQuote) -> None:
        """Set cached quote"""
        self.set(f"quote:{symbol}", quote)

    def get_batch_quotes(self, symbols: List[str]) -> Dict[str, Optional[RealtimeQuote]]:
        """Get multiple cached quotes"""
        result = {}
        for symbol in symbols:
            result[symbol] = self.get_quote(symbol)
        return result

    def set_batch_quotes(self, quotes: List[RealtimeQuote]) -> None:
        """Set multiple cached quotes"""
        for quote in quotes:
            self.set_quote(quote.symbol, quote)


class KLineCache(MarketDataCache):
    """
    Specialized cache for K-line data
    """

    def __init__(self, ttl: timedelta = timedelta(minutes=5)):
        super().__init__(default_ttl=ttl)

    def get_kline(self, symbol: str, period: str = "101") -> Optional[List[OHLCV]]:
        """Get cached K-line data"""
        return self.get(f"kline:{symbol}:{period}")

    def set_kline(
        self,
        symbol: str,
        ohlcv_list: List[OHLCV],
        period: str = "101"
    ) -> None:
        """Set cached K-line data"""
        self.set(f"kline:{symbol}:{period}", ohlcv_list)


class PersistentCache:
    """
    Persistent cache backed by file storage
    """

    def __init__(self, cache_dir: str = "cache/market_data"):
        """
        Initialize persistent cache

        Args:
            cache_dir: Directory for cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._memory_cache: Dict[str, Any] = {}

        logger.info(f"PersistentCache initialized: {self.cache_dir}")

    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key"""
        # Replace invalid filename characters
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str, max_age: Optional[timedelta] = None) -> Optional[Any]:
        """
        Get value from persistent cache

        Args:
            key: Cache key
            max_age: Maximum age of cached data

        Returns:
            Cached value or None
        """
        # Check memory cache first
        if key in self._memory_cache:
            return self._memory_cache[key]

        file_path = self._get_file_path(key)

        if not file_path.exists():
            return None

        # Check file age
        if max_age:
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if datetime.now() - file_mtime > max_age:
                return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Store in memory cache
            self._memory_cache[key] = data

            return data

        except Exception as e:
            logger.error(f"Error reading cache file {file_path}: {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """
        Set value in persistent cache

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
        """
        # Store in memory cache
        self._memory_cache[key] = value

        # Write to file
        file_path = self._get_file_path(key)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(value, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error writing cache file {file_path}: {e}")

    def delete(self, key: str) -> bool:
        """
        Delete value from persistent cache

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        # Remove from memory cache
        if key in self._memory_cache:
            del self._memory_cache[key]

        # Remove file
        file_path = self._get_file_path(key)

        if file_path.exists():
            file_path.unlink()
            return True

        return False

    def clear(self) -> None:
        """Clear all cached data"""
        self._memory_cache.clear()

        # Remove all cache files
        for file_path in self.cache_dir.glob("*.json"):
            file_path.unlink()

        logger.info("Persistent cache cleared")


# Global cache instances
quote_cache = QuoteCache()
kline_cache = KLineCache()
persistent_cache = PersistentCache()


async def get_cached_quote(
    symbol: str,
    fetcher_func: callable
) -> Optional[RealtimeQuote]:
    """
    Get quote from cache or fetch

    Args:
        symbol: Stock code
        fetcher_func: Async function to fetch quote

    Returns:
        RealtimeQuote or None
    """
    return await quote_cache.get_or_fetch(
        f"quote:{symbol}",
        fetcher_func
    )
