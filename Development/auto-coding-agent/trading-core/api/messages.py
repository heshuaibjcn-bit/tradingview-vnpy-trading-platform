"""
Message Management API

Provides endpoints for managing and querying agent messages.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional, List
from datetime import datetime
from pathlib import Path
from loguru import logger

from agents import get_agency


router = APIRouter(
    prefix="/api/messages",
    tags=["messages"],
)


def get_message_db():
    """Get message database instance"""
    agency = get_agency()
    return agency.message_db if agency else None


@router.get("/stats")
async def get_message_stats():
    """
    Get message database statistics

    Returns:
        Statistics about stored messages
    """
    db = get_message_db()
    if not db:
        raise HTTPException(status_code=503, detail="Message database not available")

    stats = db.get_message_stats()
    size = db.get_database_size()

    return {
        **stats,
        "database_size": size,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/stats/trend")
async def get_message_trend(
    interval_minutes: int = Query(60, description="Time interval in minutes"),
    limit: int = Query(24, description="Number of data points"),
):
    """
    Get message count trend over time

    Args:
        interval_minutes: Time interval in minutes
        limit: Number of data points

    Returns:
        List of {timestamp, count} data points
    """
    db = get_message_db()
    if not db:
        raise HTTPException(status_code=503, detail="Message database not available")

    trend = db.get_message_trend(interval_minutes=interval_minutes, limit=limit)

    return {
        "trend": trend,
        "interval_minutes": interval_minutes,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/export")
async def export_messages(
    background_tasks: BackgroundTasks,
    format: str = Query("json", description="Export format (csv or json)"),
    msg_type: Optional[str] = Query(None, description="Filter by message type"),
    sender: Optional[str] = Query(None, description="Filter by sender"),
    hours: Optional[int] = Query(None, description="Last N hours"),
    limit: int = Query(10000, description="Max messages to export"),
):
    """
    Export messages to file

    Args:
        format: Export format (csv or json)
        msg_type: Filter by message type
        sender: Filter by sender
        hours: Last N hours
        limit: Maximum messages to export

    Returns:
        Export file download
    """
    db = get_message_db()
    if not db:
        raise HTTPException(status_code=503, detail="Message database not available")

    # Generate output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("data/exports")
    output_dir.mkdir(parents=True, exist_ok=True)

    if format == "csv":
        output_path = output_dir / f"messages_{timestamp}.csv"
        success = db.export_to_csv(
            str(output_path),
            msg_type=msg_type,
            sender=sender,
            limit=limit,
        )
    else:
        output_path = output_dir / f"messages_{timestamp}.json"
        success = db.export_to_json(
            str(output_path),
            msg_type=msg_type,
            sender=sender,
            limit=limit,
        )

    if not success:
        raise HTTPException(status_code=500, detail="Export failed")

    # Schedule cleanup of old export files (keep last 10)
    def cleanup_old_exports():
        exports = sorted(output_dir.glob(f"messages_*.{format}"), reverse=True)
        for old_file in exports[10:]:
            old_file.unlink()
            logger.info(f"Deleted old export: {old_file}")

    background_tasks.add_task(cleanup_old_exports)

    return FileResponse(
        path=str(output_path),
        filename=output_path.name,
        media_type="text/csv" if format == "csv" else "application/json",
    )


@router.post("/clean")
async def clean_old_messages(
    days: int = Query(30, description="Messages older than N days"),
    archive: bool = Query(False, description="Archive instead of delete"),
):
    """
    Clean old messages

    Args:
        days: Messages older than this will be cleaned
        archive: If True, archive messages; if False, delete them

    Returns:
        Number of messages cleaned
    """
    db = get_message_db()
    if not db:
        raise HTTPException(status_code=503, detail="Message database not available")

    if archive:
        count = db.archive_old_messages(days=days)
        action = "archived"
    else:
        count = db.clear_old_messages(days=days)
        action = "deleted"

    logger.info(f"Cleaned {count} messages ({action}, older than {days} days)")

    return {
        "count": count,
        "action": action,
        "days": days,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/optimize")
async def optimize_database():
    """
    Optimize message database (VACUUM and ANALYZE)

    Returns:
        Optimization result
    """
    db = get_message_db()
    if not db:
        raise HTTPException(status_code=503, detail="Message database not available")

    success = db.optimize_database()

    if not success:
        raise HTTPException(status_code=500, detail="Optimization failed")

    size = db.get_database_size()

    return {
        "success": True,
        "database_size": size,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/types")
async def get_message_types():
    """
    Get all message types and their counts

    Returns:
        Dictionary of message type -> count
    """
    db = get_message_db()
    if not db:
        raise HTTPException(status_code=503, detail="Message database not available")

    counts = db.get_message_count_per_type()

    return {
        "types": counts,
        "total_types": len(counts),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/senders")
async def get_message_senders():
    """
    Get all message senders and their counts

    Returns:
        Dictionary of sender -> count
    """
    db = get_message_db()
    if not db:
        raise HTTPException(status_code=503, detail="Message database not available")

    counts = db.get_message_count_per_sender()

    return {
        "senders": counts,
        "total_senders": len(counts),
        "timestamp": datetime.now().isoformat(),
    }
