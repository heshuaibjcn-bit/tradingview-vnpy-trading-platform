"""
Cache Management API

Provides endpoints for monitoring and controlling the cache system.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

from cache import get_global_cache_manager


router = APIRouter(
    prefix="/api/cache",
    tags=["cache"],
)


class CacheConfigUpdate(BaseModel):
    """Cache configuration update"""
    max_size: Optional[int] = None
    default_ttl: Optional[float] = None


class CachePreheatRequest(BaseModel):
    """Cache preheat request"""
    data: Dict[str, Any]


@router.get("/stats")
async def get_cache_stats():
    """
    Get cache statistics for all caches

    Returns:
        Cache statistics
    """
    manager = get_global_cache_manager()
    stats = manager.get_global_stats()

    return {
        "stats": stats,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/caches")
async def list_caches():
    """
    List all caches

    Returns:
        List of cache names and info
    """
    manager = get_global_cache_manager()
    caches = manager.get_all_caches()

    cache_info = {}
    for name, cache in caches.items():
        cache_info[name] = cache.get_info()

    return {
        "caches": cache_info,
        "count": len(caches),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/caches/{cache_name}")
async def get_cache_info(cache_name: str):
    """
    Get detailed information about a specific cache

    Args:
        cache_name: Cache name

    Returns:
        Cache information
    """
    manager = get_global_cache_manager()
    cache = manager.get_cache(cache_name)

    if not cache:
        raise HTTPException(status_code=404, detail=f"Cache not found: {cache_name}")

    return {
        "cache": cache.get_info(),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/caches/{cache_name}/stats")
async def get_cache_stats_detailed(cache_name: str):
    """
    Get detailed statistics for a specific cache

    Args:
        cache_name: Cache name

    Returns:
        Cache statistics
    """
    manager = get_global_cache_manager()
    cache = manager.get_cache(cache_name)

    if not cache:
        raise HTTPException(status_code=404, detail=f"Cache not found: {cache_name}")

    return {
        "cache_name": cache_name,
        "stats": cache.get_stats(),
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/caches/{cache_name}/config")
async def update_cache_config(
    cache_name: str,
    config_update: CacheConfigUpdate,
):
    """
    Update cache configuration

    Args:
        cache_name: Cache name
        config_update: Configuration updates

    Returns:
        Updated configuration
    """
    manager = get_global_cache_manager()
    cache = manager.get_cache(cache_name)

    if not cache:
        raise HTTPException(status_code=404, detail=f"Cache not found: {cache_name}")

    config = cache.config

    # Update configuration
    if config_update.max_size is not None:
        if config_update.max_size <= 0:
            raise HTTPException(status_code=400, detail="max_size must be positive")
        config.max_size = config_update.max_size
    if config_update.default_ttl is not None:
        if config_update.default_ttl < 0:
            raise HTTPException(status_code=400, detail="default_ttl must be non-negative")
        config.default_ttl = config_update.default_ttl

    logger.info(f"Cache '{cache_name}' config updated: {config_update}")

    return {
        "cache_name": cache_name,
        "config": {
            "max_size": config.max_size,
            "default_ttl": config.default_ttl,
            "strategy": config.strategy.value,
        },
        "message": "Configuration updated",
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/caches/{cache_name}/clear")
async def clear_cache(cache_name: str):
    """
    Clear all entries from a cache

    Args:
        cache_name: Cache name

    Returns:
        Clear confirmation
    """
    manager = get_global_cache_manager()
    cache = manager.get_cache(cache_name)

    if not cache:
        raise HTTPException(status_code=404, detail=f"Cache not found: {cache_name}")

    cache.clear()

    return {
        "cache_name": cache_name,
        "message": "Cache cleared",
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/caches/{cache_name}/invalidate")
async def invalidate_cache_entries(
    cache_name: str,
    pattern: Optional[str] = Query(None, description="Key pattern to invalidate"),
):
    """
    Invalidate cache entries matching pattern

    Args:
        cache_name: Cache name
        pattern: Key pattern (if None, clears all)

    Returns:
        Invalidation result
    """
    manager = get_global_cache_manager()
    cache = manager.get_cache(cache_name)

    if not cache:
        raise HTTPException(status_code=404, detail=f"Cache not found: {cache_name}")

    count = cache.invalidate(pattern)

    return {
        "cache_name": cache_name,
        "invalidated": count,
        "pattern": pattern or "all",
        "message": f"Invalidated {count} entries",
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/invalidate")
async def invalidate_all_caches(
    pattern: str = Query(..., description="Key pattern to invalidate"),
):
    """
    Invalidate entries across all caches

    Args:
        pattern: Key pattern

    Returns:
        Total invalidation result
    """
    manager = get_global_cache_manager()
    total = manager.invalidate_all(pattern)

    return {
        "total_invalidated": total,
        "pattern": pattern,
        "message": f"Invalidated {total} entries across all caches",
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/caches/{cache_name}/preheat")
async def preheat_cache(
    cache_name: str,
    request: CachePreheatRequest,
):
    """
    Preheat cache with data

    Args:
        cache_name: Cache name
        request: Preheat data

    Returns:
        Preheat confirmation
    """
    manager = get_global_cache_manager()
    cache = manager.get_cache(cache_name)

    if not cache:
        raise HTTPException(status_code=404, detail=f"Cache not found: {cache_name}")

    await cache.preheat(request.data)

    return {
        "cache_name": cache_name,
        "entries_loaded": len(request.data),
        "message": "Cache preheated",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/caches/{cache_name}/keys")
async def get_cache_keys(
    cache_name: str,
    limit: int = Query(100, description="Maximum keys to return"),
):
    """
    Get keys from a cache

    Args:
        cache_name: Cache name
        limit: Maximum keys to return

    Returns:
        List of cache keys
    """
    manager = get_global_cache_manager()
    cache = manager.get_cache(cache_name)

    if not cache:
        raise HTTPException(status_code=404, detail=f"Cache not found: {cache_name}")

    info = cache.get_info()
    keys = info.get("keys", [])

    return {
        "cache_name": cache_name,
        "keys": keys[:limit],
        "total": len(keys),
        "returned": min(len(keys), limit),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/health")
async def get_cache_health():
    """
    Get cache system health status

    Returns:
        Health status and diagnostics
    """
    manager = get_global_cache_manager()
    stats = manager.get_global_stats()

    health_issues = []

    # Check global hit rate
    hit_rate = stats.get("summary", {}).get("global_hit_rate", 0.0)
    if hit_rate < 0.5:
        health_issues.append(f"Low global hit rate: {hit_rate:.1%}")

    # Check individual caches
    for cache_name, cache_stats in stats.get("caches", {}).items():
        # Check cache hit rate
        cache_hit_rate = cache_stats.get("hit_rate", 0.0)
        if cache_hit_rate < 0.3:
            health_issues.append(f"Low hit rate for '{cache_name}': {cache_hit_rate:.1%}")

        # Check cache size
        size = cache_stats.get("size", 0)
        cache = manager.get_cache(cache_name)
        if cache:
            max_size = cache.config.max_size
            utilization = size / max_size if max_size > 0 else 0
            if utilization > 0.9:
                health_issues.append(f"High utilization for '{cache_name}': {utilization:.1%}")

        # Check high expiration rate
        expirations = cache_stats.get("expirations", 0)
        misses = cache_stats.get("misses", 0)
        if misses > 0 and expirations / misses > 0.5:
            health_issues.append(f"High expiration rate for '{cache_name}': {expirations}/{misses}")

    # Determine overall status
    if health_issues:
        status = "degraded" if len(health_issues) < 3 else "unhealthy"
    else:
        status = "healthy"

    return {
        "status": status,
        "health_issues": health_issues,
        "summary": stats.get("summary", {}),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/config")
async def get_all_cache_configs():
    """
    Get configuration for all caches

    Returns:
        All cache configurations
    """
    manager = get_global_cache_manager()
    caches = manager.get_all_caches()

    configs = {}
    for name, cache in caches.items():
        configs[name] = {
            "max_size": cache.config.max_size,
            "default_ttl": cache.config.default_ttl,
            "strategy": cache.config.strategy.value,
            "enable_stats": cache.config.enable_stats,
        }

    return {
        "configs": configs,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/reset-stats")
async def reset_all_stats():
    """
    Reset statistics for all caches

    Returns:
        Reset confirmation
    """
    manager = get_global_cache_manager()
    caches = manager.get_all_caches()

    for cache in caches.values():
        cache._stats.reset()

    return {
        "message": "Statistics reset for all caches",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/summary")
async def get_cache_summary():
    """
    Get cache system summary

    Returns:
        Summary of cache system
    """
    manager = get_global_cache_manager()
    stats = manager.get_global_stats()
    caches = manager.get_all_caches()

    summary = {
        "total_caches": len(caches),
        "cache_names": list(caches.keys()),
        "global_hit_rate": stats.get("summary", {}).get("global_hit_rate", 0.0),
        "total_entries": stats.get("summary", {}).get("total_entries", 0),
        "timestamp": datetime.now().isoformat(),
    }

    return summary
