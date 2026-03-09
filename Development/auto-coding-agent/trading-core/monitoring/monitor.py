"""
System monitor with auto-recovery capabilities.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Callable
from loguru import logger

from .models import HealthStatus, ServiceStatus, AlertRule, HealthLevel
from .health import HealthChecker
from .logger import SystemLogger, LogLevel


class SystemMonitor:
    """Main system monitoring class with auto-recovery."""

    def __init__(
        self,
        health_checker: Optional[HealthChecker] = None,
        system_logger: Optional[SystemLogger] = None,
    ):
        self.health_checker = health_checker or HealthChecker()
        self.logger = system_logger or SystemLogger()
        self._alert_rules: List[AlertRule] = []
        self._recovery_actions: Dict[str, Callable] = {}
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None

    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self._alert_rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")

    def remove_alert_rule(self, name: str) -> None:
        """Remove an alert rule by name."""
        self._alert_rules = [r for r in self._alert_rules if r.name != name]
        logger.info(f"Removed alert rule: {name}")

    def register_recovery(self, service: str, action: Callable) -> None:
        """Register a recovery action for a service."""
        self._recovery_actions[service] = action
        logger.info(f"Registered recovery action for: {service}")

    async def check_and_alert(self) -> HealthStatus:
        """Check all services and trigger alerts if needed."""
        status = await self.health_checker.check_all_services()
        current_time = datetime.now()

        for rule in self._alert_rules:
            if not rule.should_trigger(current_time):
                continue

            triggered = False

            # Check each service against the rule
            for service_name, service in status.services.items():
                if rule.service and rule.service != service_name:
                    continue

                # Evaluate rule condition (simplified)
                if self._evaluate_rule(rule, service):
                    triggered = True
                    await self._trigger_alert(rule, service)

            if triggered:
                rule.last_triggered = current_time
                rule.trigger_count += 1

        return status

    def _evaluate_rule(self, rule: AlertRule, service: ServiceStatus) -> bool:
        """Evaluate if a rule condition is met."""
        condition = rule.condition.lower()

        # Simple condition evaluation
        if "error_count" in condition:
            threshold = self._extract_number(condition)
            if threshold and service.error_count > threshold:
                return True

        if "unhealthy" in condition and not service.healthy:
            return True

        if "critical" in condition and service.level == HealthLevel.CRITICAL:
            return True

        if "uptime" in condition:
            threshold = self._extract_number(condition)
            if threshold and service.uptime_seconds < threshold:
                return True

        return False

    def _extract_number(self, text: str) -> Optional[float]:
        """Extract number from string."""
        import re
        match = re.search(r'(\d+\.?\d*)', text)
        return float(match.group(1)) if match else None

    async def _trigger_alert(self, rule: AlertRule, service: ServiceStatus) -> None:
        """Trigger an alert."""
        message = f"Alert: {rule.name} - Service {service.name} triggered condition: {rule.condition}"
        self.logger.warning(
            "monitor",
            message,
            service=service.name,
            rule=rule.name,
            condition=rule.condition,
        )
        logger.warning(message)

        # Attempt auto-recovery
        if service.name in self._recovery_actions:
            try:
                logger.info(f"Attempting auto-recovery for {service.name}")
                await self._recovery_actions[service.name]()
                self.logger.info(
                    "monitor",
                    f"Auto-recovery attempted for {service.name}",
                    service=service.name,
                )
            except Exception as e:
                logger.error(f"Auto-recovery failed for {service.name}: {e}")

    async def start_monitoring(self, interval: float = 30.0) -> None:
        """Start continuous monitoring with alerts."""
        if self._running:
            return

        self._running = True
        self.logger.info("monitor", "System monitoring started")

        async def monitor_loop():
            while self._running:
                try:
                    await self.check_and_alert()
                except Exception as e:
                    logger.error(f"Monitor loop error: {e}")
                    self.logger.error("monitor", f"Monitor error: {e}")
                await asyncio.sleep(interval)

        self._monitor_task = asyncio.create_task(monitor_loop())
        await self.health_checker.start_monitoring()

    async def stop_monitoring(self) -> None:
        """Stop monitoring."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        await self.health_checker.stop_monitoring()
        self.logger.info("monitor", "System monitoring stopped")

    def get_health_summary(self) -> dict:
        """Get a summary of system health."""
        statuses = self.health_checker.get_all_statuses()
        recent_logs = self.logger.get_recent_logs(20)

        return {
            "services": {name: s.to_dict() for name, s in statuses.items()},
            "recent_logs": [log.to_dict() for log in recent_logs],
            "timestamp": datetime.now().isoformat(),
        }


# Global singleton instance
_global_monitor: Optional[SystemMonitor] = None


def get_global_monitor() -> SystemMonitor:
    """Get the global system monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = SystemMonitor()
    return _global_monitor
