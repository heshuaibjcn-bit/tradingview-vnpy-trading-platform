"""
System Monitor Agent

Wraps the SystemMonitor in an Agent interface, providing health monitoring
and auto-recovery capabilities.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

from .base import BaseAgent
from .messages import MessageType, AgentMessage
from monitoring.monitor import SystemMonitor, HealthChecker, SystemLogger
from monitoring.models import HealthStatus, ServiceStatus, AlertRule


class SystemMonitorAgent(BaseAgent):
    """
    Agent wrapper for SystemMonitor

    Monitors system health and triggers auto-recovery.
    """

    def __init__(
        self,
        system_monitor: SystemMonitor,
        monitor_interval: float = 30.0,
    ):
        """
        Initialize system monitor agent

        Args:
            system_monitor: SystemMonitor instance to wrap
            monitor_interval: Seconds between health checks
        """
        super().__init__(
            name="system_monitor",
            version="1.0.0",
            description="Monitors system health and auto-recovery",
        )

        self._monitor = system_monitor
        self._monitor_interval = monitor_interval

        # Background monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None

        # Registered agents to monitor
        self._monitored_agents: Dict[str, str] = {}  # agent_name -> service_name

        # Register message handlers
        self.register_handler(MessageType.HEALTH_CHECK, self._on_health_check)
        self.register_handler(MessageType.AGENT_REGISTER, self._on_agent_register)
        self.register_handler(MessageType.AGENT_UNREGISTER, self._on_agent_unregister)
        self.register_handler(MessageType.AGENT_ERROR, self._on_agent_error)

    async def on_start(self) -> None:
        """Called when agent starts"""
        # Start background monitoring
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

        logger.info(f"{self.name}: Started (interval={self._monitor_interval}s)")

    async def on_stop(self) -> None:
        """Called when agent stops"""
        # Stop monitoring
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        # Stop the system monitor
        await self._monitor.stop_monitoring()

        logger.info(f"{self.name}: Stopped")

    async def on_message(self, message: AgentMessage) -> None:
        """Called for every message (already handled by specific handlers)"""
        pass

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        try:
            # Start the system monitor
            await self._monitor.start_monitoring(self._monitor_interval)

            # Monitor is running in background, now send periodic status updates
            while True:
                try:
                    # Get health status
                    health_status = await self._monitor.check_and_alert()

                    # Broadcast health status
                    await self.send_message(
                        MessageType.HEALTH_STATUS,
                        {
                            "timestamp": datetime.now().isoformat(),
                            "services": {
                                name: status.to_dict()
                                for name, status in health_status.services.items()
                            },
                        },
                    )

                    await asyncio.sleep(self._monitor_interval)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"{self.name}: Error in monitoring loop - {e}")
                    await asyncio.sleep(self._monitor_interval)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"{self.name}: Error starting monitor - {e}")

    async def _on_health_check(self, message: AgentMessage) -> None:
        """Handle health check request"""
        try:
            # Perform immediate health check
            health_status = await self._monitor.check_and_alert()

            # Send response
            await self.send_message(
                MessageType.HEALTH_STATUS,
                {
                    "timestamp": datetime.now().isoformat(),
                    "services": {
                        name: status.to_dict()
                        for name, status in health_status.services.items()
                    },
                },
                recipient=message.sender,
                correlation_id=message.correlation_id,
            )

        except Exception as e:
            logger.error(f"{self.name}: Error performing health check - {e}")

    async def _on_agent_register(self, message: AgentMessage) -> None:
        """Handle agent registration"""
        try:
            agent_name = message.content.get("agent_name")

            if agent_name:
                # Register as a service to monitor
                service_name = f"agent_{agent_name}"

                # Add to health checker
                self._monitored_agents[agent_name] = service_name

                logger.info(f"{self.name}: Now monitoring agent: {agent_name}")

        except Exception as e:
            logger.error(f"{self.name}: Error registering agent - {e}")

    async def _on_agent_unregister(self, message: AgentMessage) -> None:
        """Handle agent unregistration"""
        try:
            agent_name = message.content.get("agent_name")

            if agent_name and agent_name in self._monitored_agents:
                del self._monitored_agents[agent_name]

                logger.info(f"{self.name}: Stopped monitoring agent: {agent_name}")

        except Exception as e:
            logger.error(f"{self.name}: Error unregistering agent - {e}")

    async def _on_agent_error(self, message: AgentMessage) -> None:
        """Handle agent error notification"""
        try:
            agent_name = message.content.get("agent_name")
            error_message = message.content.get("error", "Unknown error")

            logger.error(
                f"{self.name}: Agent error detected - {agent_name}: {error_message}"
            )

            # Attempt auto-recovery if registered
            if agent_name in self._monitored_agents:
                logger.info(f"{self.name}: Attempting auto-recovery for {agent_name}")

                # Send restart request
                await self.send_message(
                    MessageType.AGENT_STOPPED,
                    {
                        "agent_name": agent_name,
                        "reason": "Auto-recovery initiated",
                    },
                )

        except Exception as e:
            logger.error(f"{self.name}: Error handling agent error - {e}")

    # Public API methods

    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add an alert rule"""
        self._monitor.add_alert_rule(rule)

    def remove_alert_rule(self, name: str) -> None:
        """Remove an alert rule"""
        self._monitor.remove_alert_rule(name)

    def register_recovery(self, service: str, action) -> None:
        """Register a recovery action"""
        self._monitor.register_recovery(service, action)

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary"""
        return self._monitor.get_health_summary()

    async def check_health(self) -> HealthStatus:
        """Perform immediate health check"""
        return await self._monitor.check_and_alert()
