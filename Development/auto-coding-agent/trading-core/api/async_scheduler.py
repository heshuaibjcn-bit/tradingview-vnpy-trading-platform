"""
Async Scheduler Management API

Provides endpoints for monitoring and controlling the async task scheduler.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

from agents import get_agency
from agents.async_scheduler import (
    get_global_scheduler,
    TaskPriority,
)


router = APIRouter(
    prefix="/api/async-scheduler",
    tags=["async-scheduler"],
)


class ConcurrencyConfigUpdate(BaseModel):
    """Concurrency configuration update"""
    max_concurrent_tasks: Optional[int] = None
    max_queue_size: Optional[int] = None
    task_timeout: Optional[float] = None
    queue_timeout: Optional[float] = None
    enable_priorities: Optional[bool] = None
    enable_monitoring: Optional[bool] = None


class TaskSubmitRequest(BaseModel):
    """Task submission request"""
    task_id: Optional[str] = None
    priority: str = "NORMAL"  # CRITICAL, HIGH, NORMAL, LOW, IDLE
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = {}


@router.get("/stats")
async def get_scheduler_stats():
    """
    Get async scheduler statistics

    Returns:
        Scheduler statistics
    """
    scheduler = get_global_scheduler()
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")

    stats = scheduler.get_stats()

    return {
        "stats": stats,
        "is_running": scheduler.is_running,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/config")
async def get_scheduler_config():
    """
    Get scheduler configuration

    Returns:
        Current scheduler configuration
    """
    scheduler = get_global_scheduler()
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")

    config = scheduler.config

    return {
        "config": {
            "max_concurrent_tasks": config.max_concurrent_tasks,
            "max_queue_size": config.max_queue_size,
            "task_timeout": config.task_timeout,
            "queue_timeout": config.queue_timeout,
            "enable_priorities": config.enable_priorities,
            "enable_monitoring": config.enable_monitoring,
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/config")
async def update_scheduler_config(config_update: ConcurrencyConfigUpdate):
    """
    Update scheduler configuration

    Args:
        config_update: Configuration updates

    Returns:
        Updated configuration
    """
    scheduler = get_global_scheduler()
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")

    config = scheduler.config

    # Update configuration
    if config_update.max_concurrent_tasks is not None:
        if config_update.max_concurrent_tasks <= 0:
            raise HTTPException(status_code=400, detail="max_concurrent_tasks must be positive")
        config.max_concurrent_tasks = config_update.max_concurrent_tasks
    if config_update.max_queue_size is not None:
        if config_update.max_queue_size <= 0:
            raise HTTPException(status_code=400, detail="max_queue_size must be positive")
        config.max_queue_size = config_update.max_queue_size
    if config_update.task_timeout is not None:
        if config_update.task_timeout <= 0:
            raise HTTPException(status_code=400, detail="task_timeout must be positive")
        config.task_timeout = config_update.task_timeout
    if config_update.queue_timeout is not None:
        if config_update.queue_timeout <= 0:
            raise HTTPException(status_code=400, detail="queue_timeout must be positive")
        config.queue_timeout = config_update.queue_timeout
    if config_update.enable_priorities is not None:
        config.enable_priorities = config_update.enable_priorities
    if config_update.enable_monitoring is not None:
        config.enable_monitoring = config_update.enable_monitoring

    logger.info(f"Scheduler config updated: {config_update}")

    return {
        "config": {
            "max_concurrent_tasks": config.max_concurrent_tasks,
            "max_queue_size": config.max_queue_size,
            "task_timeout": config.task_timeout,
            "queue_timeout": config.queue_timeout,
            "enable_priorities": config.enable_priorities,
            "enable_monitoring": config.enable_monitoring,
        },
        "message": "Configuration updated",
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/reset-stats")
async def reset_scheduler_stats():
    """
    Reset scheduler statistics

    Returns:
        Reset confirmation
    """
    scheduler = get_global_scheduler()
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")

    scheduler.reset_stats()

    return {
        "message": "Statistics reset",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/tasks/{task_id}")
async def get_task_info(task_id: str):
    """
    Get information about a specific task

    Args:
        task_id: Task ID

    Returns:
        Task information
    """
    scheduler = get_global_scheduler()
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")

    task_info = scheduler.get_task_info(task_id)

    if not task_info:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    return {
        "task_info": task_info,
        "timestamp": datetime.now().isoformat(),
    }


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """
    Cancel a task

    Args:
        task_id: Task ID to cancel

    Returns:
        Cancellation result
    """
    scheduler = get_global_scheduler()
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")

    cancelled = await scheduler.cancel(task_id)

    if not cancelled:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    return {
        "task_id": task_id,
        "message": "Task cancelled",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/health")
async def get_scheduler_health():
    """
    Get scheduler health status

    Returns:
        Health status and diagnostics
    """
    scheduler = get_global_scheduler()
    if not scheduler:
        return {
            "enabled": False,
            "status": "disabled",
            "timestamp": datetime.now().isoformat(),
        }

    stats = scheduler.get_stats()
    config = scheduler.config

    health_issues = []

    # Check queue utilization
    queue_utilization = stats['current_queue_size'] / config.max_queue_size
    if queue_utilization > 0.8:
        health_issues.append(f"Queue utilization high: {queue_utilization:.1%}")

    # Check task failure rate
    failure_rate = stats['tasks_failed'] / max(stats['tasks_submitted'], 1)
    if failure_rate > 0.1:
        health_issues.append(f"High failure rate: {failure_rate:.1%}")

    # Check timeout rate
    timeout_rate = stats['tasks_timeout'] / max(stats['tasks_submitted'], 1)
    if timeout_rate > 0.05:
        health_issues.append(f"High timeout rate: {timeout_rate:.1%}")

    # Check average wait time
    if stats['avg_wait_time'] > 1.0:
        health_issues.append(f"High average wait time: {stats['avg_wait_time']:.2f}s")

    # Determine overall status
    if health_issues:
        status = "degraded" if len(health_issues) < 3 else "unhealthy"
    else:
        status = "healthy"

    return {
        "enabled": True,
        "status": status,
        "is_running": scheduler.is_running,
        "health_issues": health_issues,
        "metrics": {
            "queue_utilization": queue_utilization,
            "failure_rate": failure_rate,
            "timeout_rate": timeout_rate,
            "avg_wait_time": stats['avg_wait_time'],
            "avg_run_time": stats['avg_run_time'],
            "success_rate": stats['success_rate'],
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/priorities")
async def get_priority_levels():
    """
    Get available priority levels

    Returns:
        List of priority levels
    """
    return {
        "priorities": [
            {"name": "CRITICAL", "value": TaskPriority.CRITICAL, "description": "Emergency stop, critical errors"},
            {"name": "HIGH", "value": TaskPriority.HIGH, "description": "Time-sensitive market data"},
            {"name": "NORMAL", "value": TaskPriority.NORMAL, "description": "Regular operations"},
            {"name": "LOW", "value": TaskPriority.LOW, "description": "Background tasks"},
            {"name": "IDLE", "value": TaskPriority.IDLE, "description": "Maintenance tasks"},
        ],
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/concurrency")
async def get_concurrency_info():
    """
    Get concurrency manager information

    Returns:
        Concurrency manager statistics
    """
    agency = get_agency()
    if not agency:
        raise HTTPException(status_code=503, detail="Agency not available")

    concurrency_manager = getattr(agency, '_concurrency_manager', None)
    if not concurrency_manager:
        raise HTTPException(status_code=404, detail="Concurrency manager not available")

    stats = concurrency_manager.get_stats()

    return {
        "stats": stats,
        "config": {
            "max_concurrent_per_agent": concurrency_manager.max_concurrent_per_agent,
            "max_messages_per_second": concurrency_manager.max_messages_per_second,
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/concurrency/config")
async def update_concurrency_config(
    max_concurrent_per_agent: Optional[int] = Query(None, description="Max concurrent per agent"),
    max_messages_per_second: Optional[float] = Query(None, description="Max messages per second"),
):
    """
    Update concurrency manager configuration

    Args:
        max_concurrent_per_agent: Max concurrent messages per agent
        max_messages_per_second: Max message rate

    Returns:
        Updated configuration
    """
    agency = get_agency()
    if not agency:
        raise HTTPException(status_code=503, detail="Agency not available")

    concurrency_manager = getattr(agency, '_concurrency_manager', None)
    if not concurrency_manager:
        raise HTTPException(status_code=404, detail="Concurrency manager not available")

    if max_concurrent_per_agent is not None:
        if max_concurrent_per_agent <= 0:
            raise HTTPException(status_code=400, detail="max_concurrent_per_agent must be positive")
        concurrency_manager.max_concurrent_per_agent = max_concurrent_per_agent

    if max_messages_per_second is not None:
        if max_messages_per_second <= 0:
            raise HTTPException(status_code=400, detail="max_messages_per_second must be positive")
        concurrency_manager.max_messages_per_second = max_messages_per_second

    logger.info(f"Concurrency config updated: max_concurrent={max_concurrent_per_agent}, max_rate={max_messages_per_second}")

    return {
        "config": {
            "max_concurrent_per_agent": concurrency_manager.max_concurrent_per_agent,
            "max_messages_per_second": concurrency_manager.max_messages_per_second,
        },
        "message": "Concurrency configuration updated",
        "timestamp": datetime.now().isoformat(),
    }
