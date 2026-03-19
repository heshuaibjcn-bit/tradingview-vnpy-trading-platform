"""
Data Models for Agent System

This module defines data models used throughout the agent system.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class AgentHealth(str, Enum):
    """Agent health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class AgentMetrics:
    """Performance metrics for an agent"""
    messages_sent: int = 0
    messages_received: int = 0
    errors: int = 0
    last_activity: Optional[datetime] = None
    uptime_seconds: float = 0.0
    memory_mb: float = 0.0
    cpu_percent: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "errors": self.errors,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "uptime_seconds": self.uptime_seconds,
            "memory_mb": self.memory_mb,
            "cpu_percent": self.cpu_percent,
        }


@dataclass
class AgentInfo:
    """Information about an agent"""
    name: str
    version: str
    status: str
    health: AgentHealth = AgentHealth.UNKNOWN
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    metrics: AgentMetrics = field(default_factory=AgentMetrics)
    started_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "health": self.health.value,
            "description": self.description,
            "dependencies": self.dependencies,
            "metrics": self.metrics.to_dict(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "metadata": self.metadata,
        }

    @property
    def uptime(self) -> float:
        """Get agent uptime in seconds"""
        if self.started_at:
            return (datetime.now() - self.started_at).total_seconds()
        return 0.0

    @property
    def is_healthy(self) -> bool:
        """Check if agent is healthy"""
        return self.health == AgentHealth.HEALTHY

    @property
    def is_running(self) -> bool:
        """Check if agent is running"""
        return self.status in ("RUNNING", "STARTING")


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    agent_name: str
    healthy: bool
    status: str
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "agent_name": self.agent_name,
            "healthy": self.healthy,
            "status": self.status,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }


@dataclass
class SystemStatus:
    """Overall system status"""
    total_agents: int = 0
    running_agents: int = 0
    stopped_agents: int = 0
    error_agents: int = 0
    healthy_agents: int = 0
    unhealthy_agents: int = 0
    uptime_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_agents": self.total_agents,
            "running_agents": self.running_agents,
            "stopped_agents": self.stopped_agents,
            "error_agents": self.error_agents,
            "healthy_agents": self.healthy_agents,
            "unhealthy_agents": self.unhealthy_agents,
            "uptime_seconds": self.uptime_seconds,
            "timestamp": self.timestamp.isoformat(),
        }

    @property
    def health_percentage(self) -> float:
        """Calculate percentage of healthy agents"""
        if self.total_agents == 0:
            return 100.0
        return (self.healthy_agents / self.total_agents) * 100
