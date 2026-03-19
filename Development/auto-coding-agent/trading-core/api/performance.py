"""
Performance Monitoring API

Provides endpoints for system performance monitoring and metrics.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional, List
from datetime import datetime
from loguru import logger

from monitoring.metrics import get_metrics_collector, init_metrics_collector
from monitoring.alerts import AlertEngine, AlertSeverity
from monitoring.reports import ReportGenerator


router = APIRouter(
    prefix="/api/performance",
    tags=["performance"],
)


def get_alert_engine():
    """Get alert engine instance"""
    # This should be initialized in main.py
    # For now, return None if not available
    return None


@router.get("/metrics/current")
async def get_current_metrics():
    """
    Get current system performance metrics

    Returns:
        Current PerformanceMetrics
    """
    collector = get_metrics_collector()
    if not collector:
        raise HTTPException(status_code=503, detail="Metrics collector not available")

    metrics = collector.get_current_metrics()

    if not metrics:
        raise HTTPException(status_code=404, detail="No metrics available")

    return metrics.to_dict()


@router.get("/metrics/history")
async def get_metrics_history(
    limit: int = Query(100, description="Number of data points"),
):
    """
    Get metrics history

    Args:
        limit: Maximum number of data points

    Returns:
        List of historical metrics
    """
    collector = get_metrics_collector()
    if not collector:
        raise HTTPException(status_code=503, detail="Metrics collector not available")

    history = collector.get_metrics_history(limit=limit)

    return {
        "data": [m.to_dict() for m in history],
        "count": len(history),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/metrics/summary")
async def get_metrics_summary():
    """
    Get metrics summary statistics

    Returns:
        Summary with averages, min, max for key metrics
    """
    collector = get_metrics_collector()
    if not collector:
        raise HTTPException(status_code=503, detail="Metrics collector not available")

    summary = collector.get_metrics_summary()

    return summary


@router.get("/alerts")
async def get_alerts(
    active_only: bool = Query(False, description="Only return active alerts"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(100, description="Maximum alerts to return"),
):
    """
    Get alerts

    Args:
        active_only: Only return active alerts
        severity: Filter by severity level
        limit: Maximum alerts to return

    Returns:
        List of alerts
    """
    engine = get_alert_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Alert engine not available")

    if active_only:
        alerts = engine.get_active_alerts()
    else:
        alerts = engine.get_alert_history(limit=limit)
        if severity:
            try:
                sev = AlertSeverity(severity)
                alerts = [a for a in alerts if a.severity == sev]
            except ValueError:
                pass

    return {
        "alerts": [a.to_dict() for a in alerts],
        "count": len(alerts),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/alerts/summary")
async def get_alerts_summary():
    """
    Get alert summary statistics

    Returns:
        Alert summary with counts by severity
    """
    engine = get_alert_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Alert engine not available")

    summary = engine.get_alert_summary()

    return summary


@router.get("/alerts/rules")
async def get_alert_rules():
    """
    Get all alert rules

    Returns:
        List of alert rules
    """
    engine = get_alert_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Alert engine not available")

    rules = engine.get_rules()

    return {
        "rules": [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "metric": r.metric,
                "condition": r.condition.value,
                "threshold": r.threshold,
                "severity": r.severity.value,
                "duration_seconds": r.duration_seconds,
                "enabled": r.enabled,
            }
            for r in rules
        ],
        "count": len(rules),
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/alerts/rules/{rule_id}/toggle")
async def toggle_alert_rule(rule_id: str):
    """
    Enable or disable an alert rule

    Args:
        rule_id: Rule ID to toggle

    Returns:
        Updated rule
    """
    engine = get_alert_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Alert engine not available")

    rule = engine.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")

    rule.enabled = not rule.enabled
    engine.update_rule(rule)

    return {
        "rule_id": rule.id,
        "enabled": rule.enabled,
        "message": f"Rule {'enabled' if rule.enabled else 'disabled'}",
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/reports/generate")
async def generate_report(
    background_tasks: BackgroundTasks,
    hours: int = Query(24, description="Hours to report on"),
):
    """
    Generate performance report

    Args:
        hours: Number of hours to report on

    Returns:
        Generated report
    """
    collector = get_metrics_collector()
    if not collector:
        raise HTTPException(status_code=503, detail="Metrics collector not available")

    engine = get_alert_engine()
    generator = ReportGenerator(collector, engine)

    report = generator.generate_report(hours=hours)

    # Save report in background
    def save_report():
        generator.save_report(report, format="json")
        generator.save_report(report, format="markdown")

    background_tasks.add_task(save_report)

    return report.to_dict()


@router.get("/reports/latest")
async def get_latest_report():
    """
    Get the most recent performance report

    Returns:
        Latest PerformanceReport
    """
    collector = get_metrics_collector()
    if not collector:
        raise HTTPException(status_code=503, detail="Metrics collector not available")

    engine = get_alert_engine()
    generator = ReportGenerator(collector, engine)

    report = generator.get_latest_report()

    if not report:
        raise HTTPException(status_code=404, detail="No reports available")

    return report.to_dict()


@router.get("/status")
async def get_performance_status():
    """
    Get overall performance status

    Returns:
        System performance status summary
    """
    collector = get_metrics_collector()
    if not collector:
        raise HTTPException(status_code=503, detail="Metrics collector not available")

    # Get current metrics
    current = collector.get_current_metrics()

    # Get metrics summary
    summary = collector.get_metrics_summary()

    # Get alert summary
    alert_summary = {}
    engine = get_alert_engine()
    if engine:
        alert_summary = engine.get_alert_summary()

    # Determine overall status
    status = "healthy"
    if alert_summary.get("active_alerts", 0) > 0:
        status = "warning"
    if alert_summary.get("by_severity", {}).get("critical", 0) > 0:
        status = "critical"

    return {
        "status": status,
        "current_metrics": current.to_dict() if current else None,
        "metrics_summary": summary,
        "alert_summary": alert_summary,
        "timestamp": datetime.now().isoformat(),
    }
