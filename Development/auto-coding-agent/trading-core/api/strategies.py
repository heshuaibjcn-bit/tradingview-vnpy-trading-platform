"""
Strategy Hot Reload API

Provides endpoints for managing strategy hot reload functionality.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional, List
from datetime import datetime
from loguru import logger

from strategies.hot_reload import get_hot_reload_manager, ReloadResult
from strategies import StrategyEngine


router = APIRouter(
    prefix="/api/strategies",
    tags=["strategies-hot-reload"],
)


def get_strategy_engine() -> Optional[StrategyEngine]:
    """Get strategy engine instance"""
    # This should be initialized in main.py
    return None


@router.post("/{strategy_id}/reload")
async def reload_strategy(
    strategy_id: str,
    force: bool = Query(False, description="Force reload even if unchanged"),
):
    """
    Reload a strategy

    Args:
        strategy_id: Strategy ID to reload
        force: Force reload even if file hasn't changed

    Returns:
        Reload result
    """
    manager = get_hot_reload_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Hot reload manager not available")

    result = await manager.reload_strategy(strategy_id, force=force)

    return result.to_dict()


@router.post("/{strategy_id}/rollback")
async def rollback_strategy(
    strategy_id: str,
    version_id: str = Query(..., description="Version ID to rollback to"),
):
    """
    Rollback strategy to previous version

    Args:
        strategy_id: Strategy ID
        version_id: Version ID to rollback to

    Returns:
        Rollback result
    """
    manager = get_hot_reload_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Hot reload manager not available")

    result = await manager.rollback_to_version(strategy_id, version_id)

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return result.to_dict()


@router.get("/{strategy_id}/versions")
async def get_strategy_versions(
    strategy_id: str,
):
    """
    Get all versions of a strategy

    Args:
        strategy_id: Strategy ID

    Returns:
        List of strategy versions
    """
    manager = get_hot_reload_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Hot reload manager not available")

    versions = manager.get_strategy_versions(strategy_id)

    return {
        "strategy_id": strategy_id,
        "versions": [v.to_dict() for v in versions],
        "active_version": manager.get_active_version(strategy_id),
        "total_versions": len(versions),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/reload/history")
async def get_reload_history(
    strategy_id: Optional[str] = Query(None, description="Filter by strategy ID"),
    limit: int = Query(50, description="Maximum results"),
):
    """
    Get reload history

    Args:
        strategy_id: Filter by strategy ID
        limit: Maximum results

    Returns:
        Reload history
    """
    manager = get_hot_reload_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Hot reload manager not available")

    history = manager.get_reload_history(strategy_id=strategy_id, limit=limit)

    return {
        "history": [h.to_dict() for h in history],
        "count": len(history),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/reload/status")
async def get_reload_status():
    """
    Get hot reload manager status

    Returns:
        Manager status information
    """
    manager = get_hot_reload_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Hot reload manager not available")

    status = manager.get_status()

    return status


@router.post("/reload/toggle")
async def toggle_auto_reload():
    """
    Toggle automatic file watching

    Returns:
        Updated status
    """
    manager = get_hot_reload_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Hot reload manager not available")

    if manager.auto_reload:
        manager.stop_watching()
        message = "Auto-reload disabled"
        auto_reload = False
    else:
        manager.start_watching()
        message = "Auto-reload enabled"
        auto_reload = True

    return {
        "auto_reload": auto_reload,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }
