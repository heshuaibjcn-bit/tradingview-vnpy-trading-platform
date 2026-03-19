"""
Cache Module - Intelligent Caching System

Provides multi-level caching with LRU/TTL strategies.
"""

from .cache_manager import (
    CacheStrategy,
    CacheEntry,
    CacheConfig,
    CacheStats,
    IntelligentCache,
    CacheManager,
    get_global_cache_manager,
    init_global_cache_manager,
    cache_key,
)

__all__ = [
    "CacheStrategy",
    "CacheEntry",
    "CacheConfig",
    "CacheStats",
    "IntelligentCache",
    "CacheManager",
    "get_global_cache_manager",
    "init_global_cache_manager",
    "cache_key",
]

__version__ = "1.0.0"
