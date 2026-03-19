"""
Unit tests for cache system
"""

import time
import pytest
import asyncio

from cache.cache_manager import (
    CacheStrategy,
    CacheEntry,
    CacheConfig,
    CacheStats,
    IntelligentCache,
    CacheManager,
    cache_key,
)


class TestCacheEntry:
    """Test CacheEntry"""

    def test_entry_creation(self):
        """Test creating a cache entry"""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            ttl=10.0,
        )

        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.ttl == 10.0
        assert entry.access_count == 0

    def test_entry_expiration(self):
        """Test entry expiration check"""
        entry = CacheEntry(
            key="test",
            value="value",
            ttl=0.1,  # 100ms TTL
        )

        # Should not be expired immediately
        assert not entry.is_expired()

        # Wait for expiration
        time.sleep(0.15)
        assert entry.is_expired()

    def test_entry_touch(self):
        """Test updating entry access info"""
        entry = CacheEntry(
            key="test",
            value="value",
        )

        initial_time = entry.accessed_at
        entry.touch()

        assert entry.accessed_at > initial_time
        assert entry.access_count == 1


class TestCacheConfig:
    """Test CacheConfig"""

    def test_default_config(self):
        """Test default configuration"""
        config = CacheConfig()

        assert config.max_size == 1000
        assert config.default_ttl is None
        assert config.strategy == CacheStrategy.LRU
        assert config.enable_stats is True

    def test_custom_config(self):
        """Test custom configuration"""
        config = CacheConfig(
            max_size=500,
            default_ttl=60.0,
            strategy=CacheStrategy.TTL,
        )

        assert config.max_size == 500
        assert config.default_ttl == 60.0
        assert config.strategy == CacheStrategy.TTL


class TestCacheStats:
    """Test CacheStats"""

    def test_default_stats(self):
        """Test default statistics"""
        stats = CacheStats()

        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.expirations == 0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation"""
        stats = CacheStats()
        stats.hits = 80
        stats.misses = 20

        assert stats.get_hit_rate() == 0.8

    def test_hit_rate_empty(self):
        """Test hit rate with no requests"""
        stats = CacheStats()
        assert stats.get_hit_rate() == 0.0

    def test_stats_to_dict(self):
        """Test converting stats to dictionary"""
        stats = CacheStats()
        stats.hits = 100
        stats.misses = 50

        data = stats.to_dict()

        assert data["hits"] == 100
        assert data["misses"] == 50
        assert data["hit_rate"] == 100 / 150


class TestIntelligentCache:
    """Test IntelligentCache"""

    @pytest.fixture
    def cache(self):
        """Create a test cache"""
        config = CacheConfig(
            max_size=10,
            default_ttl=1.0,
        )
        return IntelligentCache("test_cache", config)

    def test_set_and_get(self, cache):
        """Test setting and getting values"""
        cache.set("key1", "value1")
        result = cache.get("key1")

        assert result == "value1"

    def test_get_default(self, cache):
        """Test getting non-existent key with default"""
        result = cache.get("nonexistent", "default")

        assert result == "default"

    def test_cache_hit_miss(self, cache):
        """Test cache hit and miss statistics"""
        cache.set("key1", "value1")

        # Hit
        cache.get("key1")
        assert cache._stats.hits == 1
        assert cache._stats.misses == 0

        # Miss
        cache.get("key2")
        assert cache._stats.hits == 1
        assert cache._stats.misses == 1

    def test_lru_eviction(self, cache):
        """Test LRU eviction policy"""
        # Fill cache to max size
        for i in range(10):
            cache.set(f"key{i}", f"value{i}")

        # Access first entry (make it recently used)
        cache.get("key0")

        # Add one more (should evict key1, least recently used)
        cache.set("key10", "value10")

        # key0 should still be there (recently accessed)
        assert cache.get("key0") == "value0"

        # key1 should be evicted (least recently used)
        assert cache.get("key1") is None

        assert cache._stats.evictions == 1

    def test_ttl_expiration(self, cache):
        """Test TTL-based expiration"""
        cache.set("key1", "value1", ttl=0.1)

        # Should exist immediately
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(0.15)

        # Should be expired
        assert cache.get("key1") is None
        assert cache._stats.expirations == 1

    def test_delete(self, cache):
        """Test deleting entries"""
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        result = cache.delete("key1")

        assert result is True
        assert cache.get("key1") is None

    def test_delete_nonexistent(self, cache):
        """Test deleting non-existent entry"""
        result = cache.delete("nonexistent")
        assert result is False

    def test_clear(self, cache):
        """Test clearing cache"""
        for i in range(5):
            cache.set(f"key{i}", f"value{i}")

        cache.clear()

        assert cache.get("key1") is None
        assert cache._stats.size == 0

    def test_invalidate_pattern(self, cache):
        """Test pattern-based invalidation"""
        cache.set("user:1:data", "value1")
        cache.set("user:2:data", "value2")
        cache.set("other:key", "value3")

        # Invalidate all user:* keys
        count = cache.invalidate("user:")

        assert count == 2
        assert cache.get("user:1:data") is None
        assert cache.get("user:2:data") is None
        assert cache.get("other:key") == "value3"

    def test_get_stats(self, cache):
        """Test getting cache statistics"""
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("key2")  # Miss

        stats = cache.get_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert "hit_rate" in stats

    def test_get_info(self, cache):
        """Test getting cache information"""
        cache.set("key1", "value1")

        info = cache.get_info()

        assert info["name"] == "test_cache"
        assert info["size"] == 1
        assert info["max_size"] == 10
        assert info["strategy"] == "lru"
        assert "stats" in info


class TestCacheManager:
    """Test CacheManager"""

    @pytest.fixture
    def manager(self):
        """Create a test cache manager"""
        return CacheManager()

    def test_default_caches(self, manager):
        """Test that default caches are created"""
        caches = manager.get_all_caches()

        assert "market_data" in caches
        assert "strategy_results" in caches
        assert "configuration" in caches
        assert "agent_state" in caches

    def test_create_cache(self, manager):
        """Test creating a new cache"""
        cache = manager.create_cache(
            "custom_cache",
            CacheConfig(max_size=100),
        )

        assert cache is not None
        assert cache.name == "custom_cache"
        assert cache.config.max_size == 100

    def test_get_cache(self, manager):
        """Test getting a cache by name"""
        cache = manager.get_cache("market_data")

        assert cache is not None
        assert cache.name == "market_data"

    def test_get_nonexistent_cache(self, manager):
        """Test getting non-existent cache"""
        cache = manager.get_cache("nonexistent")
        assert cache is None

    def test_global_stats(self, manager):
        """Test getting global statistics"""
        # Add some data
        market_cache = manager.get_cache("market_data")
        market_cache.set("600000", {"price": 10.0})
        market_cache.get("600000")  # Hit
        market_cache.get("000001")  # Miss

        stats = manager.get_global_stats()

        assert "caches" in stats
        assert "summary" in stats
        assert stats["summary"]["total_hits"] > 0
        assert stats["summary"]["total_misses"] > 0

    def test_invalidate_all(self, manager):
        """Test invalidating across all caches"""
        # Add same pattern to multiple caches
        market_cache = manager.get_cache("market_data")
        strategy_cache = manager.get_cache("strategy_results")

        market_cache.set("symbol:600000", "market_data")
        strategy_cache.set("symbol:600000", "strategy_result")

        # Invalidate across all caches
        total = manager.invalidate_all("symbol:")

        assert total == 2


class TestCacheKey:
    """Test cache_key function"""

    def test_simple_key(self):
        """Test simple key generation"""
        key = cache_key("user", 123)
        assert key == "user:123"

    def test_kwargs_key(self):
        """Test key generation with kwargs"""
        key = cache_key("user", id=123, name="test")
        # Should be sorted: id first, then name
        assert "id:123" in key
        assert "name:test" in key

    def test_complex_object(self):
        """Test key generation with complex object"""
        obj = {"data": [1, 2, 3]}
        key = cache_key(obj)

        # Complex objects should be hashed
        assert len(key) > 0
        assert key == cache_key(obj)  # Should be deterministic


class TestCachePreheating:
    """Test cache preheating"""

    @pytest.mark.asyncio
    async def test_preheat_cache(self):
        """Test preheating cache with data"""
        cache = IntelligentCache(
            "test",
            CacheConfig(max_size=100),
        )

        data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3",
        }

        await cache.preheat(data)

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache._stats.size == 3


class TestCachePerformance:
    """Performance tests for cache"""

    def test_cache_throughput(self):
        """Test cache read/write throughput"""
        cache = IntelligentCache(
            "perf_test",
            CacheConfig(max_size=10000, enable_stats=False),
        )

        # Benchmark writes
        start_time = time.time()
        for i in range(10000):
            cache.set(f"key{i}", f"value{i}")
        write_time = time.time() - start_time

        # Benchmark reads
        start_time = time.time()
        for i in range(10000):
            cache.get(f"key{i}")
        read_time = time.time() - start_time

        write_tps = 10000 / write_time
        read_tps = 10000 / read_time

        print(f"Cache write throughput: {write_tps:.0f} ops/sec")
        print(f"Cache read throughput: {read_tps:.0f} ops/sec")

        # Should be very fast
        assert write_tps > 10000
        assert read_tps > 50000

    def test_hit_rate_under_load(self):
        """Test cache hit rate with realistic load"""
        cache = IntelligentCache(
            "hit_rate_test",
            CacheConfig(max_size=1000, default_ttl=60.0),
        )

        # Simulate realistic access pattern
        # 80% of requests to 20% of data (Zipf distribution)
        popular_keys = [f"key{i}" for i in range(20)]
        unpopular_keys = [f"key{i}" for i in range(20, 1000)]

        # Load cache with popular data
        for key in popular_keys:
            cache.set(key, f"value_{key}")

        # Access pattern
        hits = 0
        misses = 0

        for _ in range(1000):
            if time.time() % 10 < 8:  # 80% of time
                # Access popular key
                key = popular_keys[int(time.time()) % len(popular_keys)]
            else:
                # Access unpopular key (not cached)
                key = unpopular_keys[int(time.time()) % len(unpopular_keys)]

            result = cache.get(key)
            if result is not None:
                hits += 1
            else:
                misses += 1

        hit_rate = hits / (hits + misses)

        print(f"Hit rate under load: {hit_rate:.1%}")

        # Should have good hit rate
        assert hit_rate > 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
