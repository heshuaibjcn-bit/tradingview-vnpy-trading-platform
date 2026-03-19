"""
Batch Processing Management API

Provides endpoints for monitoring and controlling message batch processing.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

from agents import get_agency


router = APIRouter(
    prefix="/api/batch-processing",
    tags=["batch-processing"],
)


class BatchConfigUpdate(BaseModel):
    """Batch processing configuration update"""
    enabled: Optional[bool] = None
    max_batch_size: Optional[int] = None
    max_wait_time: Optional[float] = None
    max_queue_size: Optional[int] = None


class BatchStatsResponse(BaseModel):
    """Batch processing statistics response"""
    messages_queued: int
    messages_batched: int
    messages_immediate: int
    batches_processed: int
    batches_flushed_by_size: int
    batches_flushed_by_time: int
    total_batch_time: float
    avg_batch_size: float
    avg_batch_latency: float
    queue_overruns: int
    min_batch_latency: float
    max_batch_latency: float
    throughput_per_second: float


@router.get("/stats")
async def get_batch_stats():
    """
    Get batch processing statistics

    Returns:
        Batch processing statistics
    """
    agency = get_agency()
    if not agency:
        raise HTTPException(status_code=503, detail="Agency not available")

    # Get batch message bus from agency
    batch_bus = getattr(agency, '_batch_message_bus', None)
    if not batch_bus:
        raise HTTPException(status_code=404, detail="Batch processing not enabled")

    stats = batch_bus.get_stats()
    batch_stats = stats.get('batch_processing', {})

    # Calculate throughput
    if batch_stats.get('total_batch_time', 0) > 0:
        throughput = batch_stats.get('messages_batched', 0) / batch_stats['total_batch_time']
    else:
        throughput = 0.0

    return {
        "batch_processing": batch_stats,
        "queue_size": stats.get('queue_size', 0),
        "throughput_per_second": throughput,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/config")
async def get_batch_config():
    """
    Get batch processing configuration

    Returns:
        Current batch processing configuration
    """
    agency = get_agency()
    if not agency:
        raise HTTPException(status_code=503, detail="Agency not available")

    batch_bus = getattr(agency, '_batch_message_bus', None)
    if not batch_bus:
        raise HTTPException(status_code=404, detail="Batch processing not enabled")

    config = batch_bus.get_config()

    return {
        "config": config,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/config")
async def update_batch_config(config_update: BatchConfigUpdate):
    """
    Update batch processing configuration

    Args:
        config_update: Configuration updates

    Returns:
        Updated configuration
    """
    agency = get_agency()
    if not agency:
        raise HTTPException(status_code=503, detail="Agency not available")

    batch_bus = getattr(agency, '_batch_message_bus', None)
    if not batch_bus:
        raise HTTPException(status_code=404, detail="Batch processing not enabled")

    # Get current config
    batcher = batch_bus._batcher
    if not batcher:
        raise HTTPException(status_code=500, detail="Batcher not available")

    config = batcher.config

    # Update configuration
    if config_update.enabled is not None:
        config.enabled = config_update.enabled
    if config_update.max_batch_size is not None:
        if config_update.max_batch_size <= 0:
            raise HTTPException(status_code=400, detail="max_batch_size must be positive")
        config.max_batch_size = config_update.max_batch_size
    if config_update.max_wait_time is not None:
        if config_update.max_wait_time <= 0:
            raise HTTPException(status_code=400, detail="max_wait_time must be positive")
        config.max_wait_time = config_update.max_wait_time
    if config_update.max_queue_size is not None:
        if config_update.max_queue_size <= 0:
            raise HTTPException(status_code=400, detail="max_queue_size must be positive")
        config.max_queue_size = config_update.max_queue_size

    logger.info(f"Batch config updated: {config_update}")

    return {
        "config": batch_bus.get_config(),
        "message": "Configuration updated",
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/reset-stats")
async def reset_batch_stats():
    """
    Reset batch processing statistics

    Returns:
        Reset confirmation
    """
    agency = get_agency()
    if not agency:
        raise HTTPException(status_code=503, detail="Agency not available")

    batch_bus = getattr(agency, '_batch_message_bus', None)
    if not batch_bus:
        raise HTTPException(status_code=404, detail="Batch processing not enabled")

    batcher = batch_bus._batcher
    if not batcher:
        raise HTTPException(status_code=500, detail="Batcher not available")

    batcher.reset_stats()

    return {
        "message": "Statistics reset",
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/flush")
async def flush_batch_queue():
    """
    Immediately flush the batch queue

    Returns:
        Flush confirmation
    """
    agency = get_agency()
    if not agency:
        raise HTTPException(status_code=503, detail="Agency not available")

    batch_bus = getattr(agency, '_batch_message_bus', None)
    if not batch_bus:
        raise HTTPException(status_code=404, detail="Batch processing not enabled")

    batcher = batch_bus._batcher
    if not batcher:
        raise HTTPException(status_code=500, detail="Batcher not available")

    await batcher._flush()

    return {
        "message": "Queue flushed",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/health")
async def get_batch_health():
    """
    Get batch processing health status

    Returns:
        Health status and diagnostics
    """
    agency = get_agency()
    if not agency:
        raise HTTPException(status_code=503, detail="Agency not available")

    batch_bus = getattr(agency, '_batch_message_bus', None)
    if not batch_bus:
        return {
            "enabled": False,
            "status": "disabled",
            "timestamp": datetime.now().isoformat(),
        }

    stats = batch_bus.get_stats()
    batch_stats = stats.get('batch_processing', {})
    queue_size = stats.get('queue_size', 0)

    # Determine health status
    config = batch_bus.get_config()
    health_issues = []

    # Check queue size
    if queue_size > config.get('max_queue_size', 10000) * 0.8:
        health_issues.append(f"Queue size ({queue_size}) above 80% threshold")

    # Check queue overruns
    overruns = batch_stats.get('queue_overruns', 0)
    if overruns > 100:
        health_issues.append(f"High queue overruns: {overruns}")

    # Check batch latency
    avg_latency = batch_stats.get('avg_batch_latency', 0)
    if avg_latency > 1.0:
        health_issues.append(f"High batch latency: {avg_latency:.3f}s")

    # Determine overall status
    if health_issues:
        status = "degraded" if len(health_issues) < 3 else "unhealthy"
    else:
        status = "healthy"

    return {
        "enabled": True,
        "status": status,
        "health_issues": health_issues,
        "queue_size": queue_size,
        "queue_utilization": queue_size / config.get('max_queue_size', 10000),
        "batch_stats": {
            "avg_latency": avg_latency,
            "throughput": batch_stats.get('messages_batched', 0) / max(batch_stats.get('total_batch_time', 0.001), 0.001),
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/immediate-types")
async def get_immediate_types():
    """
    Get message types that are processed immediately (not batched)

    Returns:
        List of immediate message types
    """
    agency = get_agency()
    if not agency:
        raise HTTPException(status_code=503, detail="Agency not available")

    batch_bus = getattr(agency, '_batch_message_bus', None)
    if not batch_bus:
        raise HTTPException(status_code=404, detail="Batch processing not enabled")

    batcher = batch_bus._batcher
    if not batcher:
        raise HTTPException(status_code=500, detail="Batcher not available")

    return {
        "immediate_types": list(batcher.config.immediate_types),
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/immediate-types")
async def add_immediate_type(msg_type: str):
    """
    Add a message type to the immediate processing list

    Args:
        msg_type: Message type to process immediately

    Returns:
        Updated list of immediate types
    """
    agency = get_agency()
    if not agency:
        raise HTTPException(status_code=503, detail="Agency not available")

    batch_bus = getattr(agency, '_batch_message_bus', None)
    if not batch_bus:
        raise HTTPException(status_code=404, detail="Batch processing not enabled")

    batcher = batch_bus._batcher
    if not batcher:
        raise HTTPException(status_code=500, detail="Batcher not available")

    batcher.config.immediate_types.add(msg_type)

    logger.info(f"Added immediate message type: {msg_type}")

    return {
        "immediate_types": list(batcher.config.immediate_types),
        "message": f"Added '{msg_type}' to immediate types",
        "timestamp": datetime.now().isoformat(),
    }


@router.delete("/immediate-types/{msg_type}")
async def remove_immediate_type(msg_type: str):
    """
    Remove a message type from the immediate processing list

    Args:
        msg_type: Message type to remove

    Returns:
        Updated list of immediate types
    """
    agency = get_agency()
    if not agency:
        raise HTTPException(status_code=503, detail="Agency not available")

    batch_bus = getattr(agency, '_batch_message_bus', None)
    if not batch_bus:
        raise HTTPException(status_code=404, detail="Batch processing not enabled")

    batcher = batch_bus._batcher
    if not batcher:
        raise HTTPException(status_code=500, detail="Batcher not available")

    if msg_type in batcher.config.immediate_types:
        batcher.config.immediate_types.remove(msg_type)
        message = f"Removed '{msg_type}' from immediate types"
    else:
        message = f"'{msg_type}' not in immediate types"

    logger.info(message)

    return {
        "immediate_types": list(batcher.config.immediate_types),
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }
