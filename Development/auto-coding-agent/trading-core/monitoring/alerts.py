"""
Performance Alert Engine

Monitors performance metrics and triggers alerts based on configured rules.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger
import asyncio

from .metrics import PerformanceMetrics, MetricsCollector


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertCondition(str, Enum):
    """Alert condition types"""
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUAL_TO = "equal_to"
    NOT_EQUAL_TO = "not_equal_to"


@dataclass
class AlertRule:
    """Alert rule definition"""
    id: str
    name: str
    description: str
    metric: str  # e.g., "cpu_percent", "memory_percent"
    condition: AlertCondition
    threshold: float
    severity: AlertSeverity
    duration_seconds: int = 60  # How long condition must persist
    enabled: bool = True

    def evaluate(self, value: float) -> bool:
        """Evaluate if value triggers this rule"""
        if self.condition == AlertCondition.GREATER_THAN:
            return value > self.threshold
        elif self.condition == AlertCondition.LESS_THAN:
            return value < self.threshold
        elif self.condition == AlertCondition.EQUAL_TO:
            return value == self.threshold
        elif self.condition == AlertCondition.NOT_EQUAL_TO:
            return value != self.threshold
        return False


@dataclass
class Alert:
    """Triggered alert"""
    id: str
    rule_id: str
    rule_name: str
    severity: AlertSeverity
    message: str
    metric_value: float
    threshold: float
    triggered_at: str
    resolved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "message": self.message,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "triggered_at": self.triggered_at,
            "resolved_at": self.resolved_at,
        }


class AlertEngine:
    """
    Performance alert engine

    Evaluates metrics against rules and triggers alerts
    """

    def __init__(self, metrics_collector: MetricsCollector):
        """
        Initialize alert engine

        Args:
            metrics_collector: MetricsCollector to monitor
        """
        self.metrics_collector = metrics_collector
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self._callbacks: List[Callable[[Alert], None]] = []

        # Register default rules
        self._register_default_rules()

        logger.info("AlertEngine initialized")

    def _register_default_rules(self) -> None:
        """Register default alert rules"""
        default_rules = [
            AlertRule(
                id="cpu_high",
                name="High CPU Usage",
                description="CPU usage exceeds 80%",
                metric="cpu_percent",
                condition=AlertCondition.GREATER_THAN,
                threshold=80.0,
                severity=AlertSeverity.WARNING,
                duration_seconds=120,
            ),
            AlertRule(
                id="cpu_critical",
                name="Critical CPU Usage",
                description="CPU usage exceeds 95%",
                metric="cpu_percent",
                condition=AlertCondition.GREATER_THAN,
                threshold=95.0,
                severity=AlertSeverity.CRITICAL,
                duration_seconds=60,
            ),
            AlertRule(
                id="memory_high",
                name="High Memory Usage",
                description="Memory usage exceeds 85%",
                metric="memory_percent",
                condition=AlertCondition.GREATER_THAN,
                threshold=85.0,
                severity=AlertSeverity.WARNING,
                duration_seconds=120,
            ),
            AlertRule(
                id="memory_critical",
                name="Critical Memory Usage",
                description="Memory usage exceeds 95%",
                metric="memory_percent",
                condition=AlertCondition.GREATER_THAN,
                threshold=95.0,
                severity=AlertSeverity.CRITICAL,
                duration_seconds=60,
            ),
            AlertRule(
                id="disk_high",
                name="High Disk Usage",
                description="Disk usage exceeds 90%",
                metric="disk_usage_percent",
                condition=AlertCondition.GREATER_THAN,
                threshold=90.0,
                severity=AlertSeverity.ERROR,
                duration_seconds=300,
            ),
            AlertRule(
                id="agent_unhealthy",
                name="Unhealthy Agent Detected",
                description="One or more agents are unhealthy",
                metric="unhealthy_agents",
                condition=AlertCondition.GREATER_THAN,
                threshold=0,
                severity=AlertSeverity.WARNING,
                duration_seconds=60,
            ),
            AlertRule(
                id="throughput_low",
                name="Low Message Throughput",
                description="Message throughput is very low",
                metric="message_throughput",
                condition=AlertCondition.LESS_THAN,
                threshold=0.1,
                severity=AlertSeverity.INFO,
                duration_seconds=300,
            ),
        ]

        for rule in default_rules:
            self.add_rule(rule)

        logger.info(f"Registered {len(default_rules)} default alert rules")

    def add_rule(self, rule: AlertRule) -> None:
        """
        Add an alert rule

        Args:
            rule: AlertRule to add
        """
        self.rules[rule.id] = rule
        logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove an alert rule

        Args:
            rule_id: Rule ID to remove

        Returns:
            True if removed
        """
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")
            return True
        return False

    def get_rules(self) -> List[AlertRule]:
        """Get all alert rules"""
        return list(self.rules.values())

    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get specific alert rule"""
        return self.rules.get(rule_id)

    def update_rule(self, rule: AlertRule) -> bool:
        """
        Update an alert rule

        Args:
            rule: Updated rule

        Returns:
            True if updated
        """
        if rule.id in self.rules:
            self.rules[rule.id] = rule
            logger.info(f"Updated alert rule: {rule.name}")
            return True
        return False

    def register_callback(self, callback: Callable[[Alert], None]) -> None:
        """
        Register a callback to be invoked when alert is triggered

        Args:
            callback: Function to call with alert
        """
        self._callbacks.append(callback)

    def _trigger_alert(self, rule: AlertRule, metrics: PerformanceMetrics) -> Alert:
        """
        Trigger an alert

        Args:
            rule: Rule that was triggered
            metrics: Current metrics

        Returns:
            Alert object
        """
        # Get metric value
        metric_value = getattr(metrics, rule.metric, 0)

        # Create alert
        alert = Alert(
            id=f"{rule.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            message=f"{rule.description}: {metric_value:.2f} (threshold: {rule.threshold})",
            metric_value=metric_value,
            threshold=rule.threshold,
            triggered_at=datetime.now().isoformat(),
        )

        # Store in active alerts
        self.active_alerts[rule.id] = alert

        # Add to history
        self.alert_history.append(alert)

        # Trim history (keep last 1000)
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]

        # Log alert
        log_func = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.ERROR: logger.error,
            AlertSeverity.CRITICAL: logger.critical,
        }.get(rule.severity, logger.info)

        log_func(f"ALERT: {alert.message}")

        # Trigger callbacks
        for callback in self._callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

        return alert

    def _resolve_alert(self, rule_id: str) -> None:
        """
        Resolve an active alert

        Args:
            rule_id: Rule ID to resolve
        """
        if rule_id in self.active_alerts:
            alert = self.active_alerts[rule_id]
            alert.resolved_at = datetime.now().isoformat()
            del self.active_alerts[rule_id]
            logger.info(f"Resolved alert: {alert.rule_name}")

    def evaluate_metrics(self, metrics: PerformanceMetrics) -> List[Alert]:
        """
        Evaluate metrics against all rules

        Args:
            metrics: Current performance metrics

        Returns:
            List of newly triggered alerts
        """
        triggered_alerts = []

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            # Get metric value
            metric_value = getattr(metrics, rule.metric, None)

            if metric_value is None:
                continue

            # Evaluate rule
            if rule.evaluate(metric_value):
                # Check if alert is already active
                if rule.id not in self.active_alerts:
                    # Check duration (simplified - just trigger immediately)
                    alert = self._trigger_alert(rule, metrics)
                    triggered_alerts.append(alert)
            else:
                # Condition no longer met, resolve alert if active
                if rule.id in self.active_alerts:
                    self._resolve_alert(rule.id)

        return triggered_alerts

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())

    def get_alert_history(
        self,
        limit: int = 100,
        severity: Optional[AlertSeverity] = None,
    ) -> List[Alert]:
        """
        Get alert history

        Args:
            limit: Maximum number of alerts
            severity: Filter by severity

        Returns:
            List of alerts
        """
        history = self.alert_history[-limit:]

        if severity:
            history = [a for a in history if a.severity == severity]

        return history

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics"""
        total = len(self.alert_history)
        active = len(self.active_alerts)

        # Count by severity
        by_severity = {
            AlertSeverity.INFO.value: 0,
            AlertSeverity.WARNING.value: 0,
            AlertSeverity.ERROR.value: 0,
            AlertSeverity.CRITICAL.value: 0,
        }

        for alert in self.alert_history[-100:]:  # Last 100
            by_severity[alert.severity.value] += 1

        return {
            "total_alerts": total,
            "active_alerts": active,
            "by_severity": by_severity,
            "timestamp": datetime.now().isoformat(),
        }
