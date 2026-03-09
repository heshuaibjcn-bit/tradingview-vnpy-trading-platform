"""
Data models for system monitoring.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List


class ServiceType(Enum):
    """Types of services being monitored."""
    WEBSOCKET = "websocket"
    MARKET_DATA = "market_data"
    STRATEGY_ENGINE = "strategy_engine"
    THS_CLIENT = "ths_client"
    DATABASE = "database"
    ALERT_ENGINE = "alert_engine"


class HealthLevel(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ServiceStatus:
    """Status of a single service."""
    name: str
    service_type: ServiceType
    healthy: bool
    level: HealthLevel
    message: str = ""
    last_check: datetime = field(default_factory=datetime.now)
    uptime_seconds: float = 0
    error_count: int = 0
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "service_type": self.service_type.value,
            "healthy": self.healthy,
            "level": self.level.value,
            "message": self.message,
            "last_check": self.last_check.isoformat(),
            "uptime_seconds": self.uptime_seconds,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "metadata": self.metadata,
        }


@dataclass
class HealthStatus:
    """Overall system health status."""
    status: HealthLevel
    services: Dict[str, ServiceStatus] = field(default_factory=dict)
    system_info: Dict[str, Any] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def service_count(self) -> int:
        return len(self.services)

    @property
    def healthy_count(self) -> int:
        return sum(1 for s in self.services.values() if s.healthy)

    @property
    def unhealthy_count(self) -> int:
        return sum(1 for s in self.services.values() if not s.healthy)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "service_count": self.service_count,
            "healthy_count": self.healthy_count,
            "unhealthy_count": self.unhealthy_count,
            "services": {k: v.to_dict() for k, v in self.services.items()},
            "system_info": self.system_info,
            "alerts": self.alerts,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class LogEntry:
    """A single log entry."""
    timestamp: datetime
    level: LogLevel
    service: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "service": self.service,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class AlertRule:
    """Rule for triggering monitoring alerts."""
    name: str
    condition: str  # e.g., "error_count > 10", "uptime < 60"
    service: Optional[str] = None  # None = applies to all services
    cooldown_seconds: int = 300  # Minimum time between alerts
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

    def should_trigger(self, current_time: datetime) -> bool:
        """Check if enough time has passed since last trigger."""
        if not self.enabled:
            return False
        if self.last_triggered is None:
            return True
        elapsed = (current_time - self.last_triggered).total_seconds()
        return elapsed >= self.cooldown_seconds
