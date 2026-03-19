"""
System monitoring module for health checks and diagnostics.
"""

from .health import HealthChecker, HealthStatus, ServiceStatus
from .logger import SystemLogger, LogLevel
from .monitor import SystemMonitor, AlertRule

# Performance monitoring
from .metrics import (
    MetricsCollector,
    PerformanceMetrics,
    MetricPoint,
    get_metrics_collector,
    init_metrics_collector,
)
from .alerts import AlertEngine, AlertRule as AlertRuleNew, Alert, AlertSeverity, AlertCondition
from .reports import ReportGenerator, PerformanceReport

__all__ = [
    # Health monitoring
    "HealthChecker",
    "HealthStatus",
    "ServiceStatus",
    "SystemLogger",
    "LogLevel",
    "SystemMonitor",
    "AlertRule",
    # Performance metrics
    "MetricsCollector",
    "PerformanceMetrics",
    "MetricPoint",
    "get_metrics_collector",
    "init_metrics_collector",
    # Alerts
    "AlertEngine",
    "AlertRuleNew",
    "Alert",
    "AlertSeverity",
    "AlertCondition",
    # Reports
    "ReportGenerator",
    "PerformanceReport",
]

__version__ = "2.0.0"
