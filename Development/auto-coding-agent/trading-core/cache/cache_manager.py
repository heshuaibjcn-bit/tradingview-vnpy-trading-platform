"""
Intelligent Cache System for Trading System

This module implements a multi-level caching system with:
- LRU (Least Recently Used) eviction
- TTL (Time To Live) expiration
- Cache statistics and monitoring
- Preheating and invalidation
"""

import asyncio
import time
import json
import hashlib
from typing import Dict, List, Optional, Any, Callable, Tuple
from collections import OrderedDict
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import threading


class CacheStrategy(Enum):
    """Cache eviction strategies"""
    LRU = "lru"  # Least Recently Used
    TTL = "ttl"  # Time To Live
    LFU = "lfu"  # Least Frequently Used


@dataclass
class CacheEntry:
    """A single cache entry"""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    ttl: Optional[float] = None
    size: int = 0

    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def touch(self):
        """Update access time and count"""
        self.accessed_at = time.time()
        self.access_count += 1


@dataclass
class CacheConfig:
    """Cache configuration"""
    max_size: int = 1000
    default_ttl: Optional[float] = None  # None = no expiration
    strategy: CacheStrategy = CacheStrategy.LRU
    enable_stats: bool = True
    enable_persistence: bool = False
    persistence_path: str = "data/cache/"


@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    size: int = 0
    total_size_bytes: int = 0

    def get_hit_rate(self) -> float:
        """Get cache hit rate"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "expirations": self.expirations,
            "size": self.size,
            "total_size_bytes": self.total_size_bytes,
            "hit_rate": self.get_hit_rate(),
        }


class IntelligentCache:
    """
    Intelligent cache with LRU/TTL strategies

    Features:
    - LRU eviction
    - TTL expiration
    - Statistics tracking
    - Persistence support
    """

    def __init__(
        self,
        name: str,
        config: Optional[CacheConfig] = None,
    ):
        """
        Initialize cache

        Args:
            name: Cache name
            config: Cache configuration
        """
        self.name = name
        self.config = config or CacheConfig()

        # Storage
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

        # Statistics
        self._stats = CacheStats()

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info(
            f"Cache '{name}' initialized "
            f"(max_size={self.config.max_size}, "
            f"strategy={self.config.strategy.value})"
        )

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats.misses += 1
                return default

            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self._stats.expirations += 1
                self._stats.misses += 1
                self._update_size()
                return default

            # Update entry (LRU: move to end)
            entry.touch()
            self._cache.move_to_end(key)
            self._stats.hits += 1

            return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
    ) -> None:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (overrides default)
        """
        with self._lock:
            # Calculate size (rough estimate)
            size = len(str(value))

            # Check if updating existing entry
            if key in self._cache:
                old_entry = self._cache[key]
                self._stats.total_size_bytes -= old_entry.size

            # Evict if necessary
            while len(self._cache) >= self.config.max_size and key not in self._cache:
                self._evict_lru()

            # Use default TTL if not specified
            if ttl is None:
                ttl = self.config.default_ttl

            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl,
                size=size,
            )

            self._cache[key] = entry
            self._cache.move_to_end(key)
            self._update_size()

    def delete(self, key: str) -> bool:
        """
        Delete entry from cache

        Args:
            key: Cache key

        Returns:
            True if entry was deleted
        """
        with self._lock:
            if key in self._cache:
                entry = self._cache.pop(key)
                self._stats.total_size_bytes -= entry.size
                self._update_size()
                return True
            return False

    def clear(self) -> None:
        """Clear all entries from cache"""
        with self._lock:
            self._cache.clear()
            self._stats.size = 0
            self._stats.total_size_bytes = 0

    def invalidate(self, pattern: Optional[str] = None) -> int:
        """
        Invalidate cache entries

        Args:
            pattern: Optional key pattern (if None, clears all)

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            if pattern is None:
                count = len(self._cache)
                self.clear()
                return count

            # Pattern matching
            to_delete = [
                key for key in self._cache.keys()
                if pattern in key
            ]

            for key in to_delete:
                entry = self._cache.pop(key)
                self._stats.total_size_bytes -= entry.size

            self._update_size()
            return len(to_delete)

    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if self._cache:
            key, entry = self._cache.popitem(last=False)
            self._stats.evictions += 1
            self._stats.total_size_bytes -= entry.size
            self._update_size()
            logger.debug(f"Cache '{self.name}': Evicted LRU entry: {key}")

    def _update_size(self) -> None:
        """Update cache size statistics"""
        self._stats.size = len(self._cache)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return self._stats.to_dict()

    def get_info(self) -> Dict[str, Any]:
        """Get detailed cache information"""
        with self._lock:
            return {
                "name": self.name,
                "size": len(self._cache),
                "max_size": self.config.max_size,
                "strategy": self.config.strategy.value,
                "default_ttl": self.config.default_ttl,
                "stats": self._stats.to_dict(),
                "keys": list(self._cache.keys()),
            }

    async def start(self) -> None:
        """Start background cleanup task"""
        if self._running:
            return

        self._running = True

        if self.config.default_ttl is not None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info(f"Cache '{self.name}' started")

    async def stop(self) -> None:
        """Stop background tasks"""
        if not self._running:
            return

        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info(f"Cache '{self.name}' stopped")

    async def _cleanup_loop(self) -> None:
        """Background cleanup of expired entries"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute

                with self._lock:
                    expired_keys = [
                        key for key, entry in self._cache.items()
                        if entry.is_expired()
                    ]

                    for key in expired_keys:
                        entry = self._cache.pop(key)
                        self._stats.expirations += 1
                        self._stats.total_size_bytes -= entry.size

                    if expired_keys:
                        self._update_size()
                        logger.debug(
                            f"Cache '{self.name}': Cleaned up {len(expired_keys)} expired entries"
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")

    async def preheat(
        self,
        data: Dict[str, Any],
    ) -> None:
        """
        Preheat cache with data

        Args:
            data: Dictionary of key-value pairs to cache
        """
        logger.info(f"Cache '{self.name}': Preheating with {len(data)} entries")

        for key, value in data.items():
            self.set(key, value)

        logger.info(f"Cache '{self.name}': Preheating complete")


class CacheManager:
    """
    Manages multiple caches for different data types

    Provides:
    - Market data cache (short TTL)
    - Strategy result cache (medium TTL)
    - Configuration cache (long TTL)
    - Unified statistics
    """

    def __init__(self):
        """Initialize cache manager"""
        self._caches: Dict[str, IntelligentCache] = {}
        self._lock = threading.RLock()

        # Create default caches
        self._create_default_caches()

    def _create_default_caches(self) -> None:
        """Create default caches for different data types"""
        # Market data cache (short TTL, high turnover)
        self.create_cache(
            "market_data",
            CacheConfig(
                max_size=10000,
                default_ttl=5.0,  # 5 seconds
                strategy=CacheStrategy.LRU,
                enable_stats=True,
            ),
        )

        # Strategy calculation cache (medium TTL)
        self.create_cache(
            "strategy_results",
            CacheConfig(
                max_size=5000,
                default_ttl=60.0,  # 1 minute
                strategy=CacheStrategy.LRU,
                enable_stats=True,
            ),
        )

        # Configuration cache (long TTL)
        self.create_cache(
            "configuration",
            CacheConfig(
                max_size=1000,
                default_ttl=300.0,  # 5 minutes
                strategy=CacheStrategy.TTL,
                enable_stats=True,
            ),
        )

        # Agent state cache (short TTL)
        self.create_cache(
            "agent_state",
            CacheConfig(
                max_size=500,
                default_ttl=10.0,  # 10 seconds
                strategy=CacheStrategy.LRU,
                enable_stats=True,
            ),
        )

    def create_cache(
        self,
        name: str,
        config: Optional[CacheConfig] = None,
    ) -> IntelligentCache:
        """
        Create a new cache

        Args:
            name: Cache name
            config: Cache configuration

        Returns:
            Created cache instance
        """
        with self._lock:
            if name in self._caches:
                logger.warning(f"Cache '{name}' already exists")
                return self._caches[name]

            cache = IntelligentCache(name, config)
            self._caches[name] = cache

            logger.info(f"Created cache: {name}")

            return cache

    def get_cache(self, name: str) -> Optional[IntelligentCache]:
        """
        Get a cache by name

        Args:
            name: Cache name

        Returns:
            Cache instance or None
        """
        return self._caches.get(name)

    def get_all_caches(self) -> Dict[str, IntelligentCache]:
        """Get all caches"""
        return self._caches.copy()

    async def start_all(self) -> None:
        """Start all caches"""
        for cache in self._caches.values():
            await cache.start()

    async def stop_all(self) -> None:
        """Stop all caches"""
        for cache in self._caches.values():
            await cache.stop()

    def get_global_stats(self) -> Dict[str, Any]:
        """Get statistics for all caches"""
        stats = {}

        for name, cache in self._caches.items():
            stats[name] = cache.get_stats()

        # Calculate global stats
        total_hits = sum(s.get("hits", 0) for s in stats.values())
        total_misses = sum(s.get("misses", 0) for s in stats.values())
        global_hit_rate = total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0.0

        return {
            "caches": stats,
            "summary": {
                "total_hits": total_hits,
                "total_misses": total_misses,
                "global_hit_rate": global_hit_rate,
                "total_entries": sum(s.get("size", 0) for s in stats.values()),
            },
        }

    def invalidate_all(self, pattern: str) -> int:
        """
        Invalidate entries across all caches

        Args:
            pattern: Key pattern to match

        Returns:
            Total number of entries invalidated
        """
        total = 0
        for cache in self._caches.values():
            total += cache.invalidate(pattern)
        return total


# Global cache manager instance
_global_cache_manager: Optional[CacheManager] = None


def get_global_cache_manager() -> CacheManager:
    """Get the global cache manager instance"""
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager()
    return _global_cache_manager


def init_global_cache_manager() -> CacheManager:
    """Initialize the global cache manager"""
    global _global_cache_manager
    _global_cache_manager = CacheManager()
    return _global_cache_manager


def cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from arguments

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Cache key string
    """
    key_parts = []

    # Add positional args
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        else:
            # Hash complex objects
            key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])

    # Add keyword args (sorted for consistency)
    for k in sorted(kwargs.keys()):
        v = kwargs[k]
        if isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}:{v}")
        else:
            key_parts.append(f"{k}:{hashlib.md5(str(v).encode()).hexdigest()[:8]}")

    return ":".join(key_parts)
