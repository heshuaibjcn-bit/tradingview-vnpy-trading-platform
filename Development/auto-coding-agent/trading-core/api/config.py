"""
Configuration Management API

Provides endpoints for managing configuration hot reload.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

from config.hot_reload import get_config_reload_manager, ConfigChangeResult


router = APIRouter(
    prefix="/api/config",
    tags=["config"],
)


class ConfigUpdateRequest(BaseModel):
    """Configuration update request"""
    updates: Dict[str, Any]


@router.get("/current")
async def get_current_config(
    config_type: str = Query("general", description="Type of configuration"),
):
    """
    Get current configuration

    Args:
        config_type: Type of configuration

    Returns:
        Current configuration data
    """
    manager = get_config_reload_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Config reload manager not available")

    config = manager.get_current_config(config_type)

    if not config:
        raise HTTPException(status_code=404, detail=f"Config not found: {config_type}")

    return {
        "config_type": config_type,
        "config": config,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/update")
async def update_config(
    request: ConfigUpdateRequest,
    config_type: str = Query("general", description="Type of configuration"),
):
    """
    Update configuration programmatically

    Args:
        request: Update request with key-value pairs
        config_type: Type of configuration

    Returns:
        Update result
    """
    manager = get_config_reload_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Config reload manager not available")

    result = await manager.update_config(config_type, request.updates)

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return result.to_dict()


@router.post("/reload")
async def reload_config(
    config_type: str = Query("general", description="Type of configuration"),
    file_path: Optional[str] = Query(None, description="Config file path"),
):
    """
    Reload configuration from file

    Args:
        config_type: Type of configuration
        file_path: Optional config file path

    Returns:
        Reload result
    """
    manager = get_config_reload_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Config reload manager not available")

    result = await manager.reload_config(config_type, file_path)

    return result.to_dict()


@router.get("/versions")
async def get_config_versions(
    config_type: str = Query("general", description="Type of configuration"),
):
    """
    Get all versions of a configuration

    Args:
        config_type: Type of configuration

    Returns:
        List of config versions
    """
    manager = get_config_reload_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Config reload manager not available")

    versions = manager.get_config_versions(config_type)

    return {
        "config_type": config_type,
        "versions": [v.to_dict() for v in versions],
        "active_version": manager._active_versions.get(config_type),
        "total_versions": len(versions),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/history")
async def get_config_history(
    config_type: Optional[str] = Query(None, description="Filter by config type"),
    limit: int = Query(50, description="Maximum results"),
):
    """
    Get configuration change history

    Args:
        config_type: Filter by config type
        limit: Maximum results

    Returns:
        Change history
    """
    manager = get_config_reload_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Config reload manager not available")

    history = manager.get_config_history(config_type=config_type, limit=limit)

    return {
        "history": [h.to_dict() for h in history],
        "count": len(history),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/status")
async def get_config_status():
    """
    Get config reload manager status

    Returns:
        Manager status
    """
    manager = get_config_reload_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Config reload manager not available")

    status = manager.get_status()

    return status


@router.post("/reload/toggle")
async def toggle_auto_reload():
    """
    Toggle automatic config file watching

    Returns:
        Updated status
    """
    manager = get_config_reload_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Config reload manager not available")

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


@router.post("/rollback")
async def rollback_config(
    config_type: str = Query(..., description="Type of configuration"),
    version_id: str = Query(..., description="Version ID to rollback to"),
):
    """
    Rollback configuration to previous version

    Args:
        config_type: Type of configuration
        version_id: Version ID to rollback to

    Returns:
        Rollback result
    """
    manager = get_config_reload_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Config reload manager not available")

    success = await manager._rollback_config(config_type, version_id)

    if not success:
        raise HTTPException(status_code=500, detail="Rollback failed")

    return {
        "success": True,
        "config_type": config_type,
        "version_id": version_id,
        "message": f"Rolled back to {version_id}",
        "timestamp": datetime.now().isoformat(),
    }
