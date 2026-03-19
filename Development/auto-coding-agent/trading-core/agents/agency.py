"""
Trading Agency - Main Controller

This module implements the main controller for the agent-based trading system.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from loguru import logger

from .base import BaseAgent, AgentStatus
from .message_bus import AgentMessageBus
from .registry import AgentRegistry
from .models import SystemStatus
from .messages import MessageType, create_message


class TradingAgency:
    """
    Main controller for the agent-based trading system

    The Agency manages all agents and provides:
    - Central message bus for communication
    - Agent lifecycle management
    - Health monitoring
    - Unified API for system control
    """

    def __init__(
        self,
        enable_persistence: bool = True,
        db_path: str = "data/messages.db",
        health_check_interval: float = 30.0,
        message_history_size: int = 1000,
    ):
        """
        Initialize the trading agency

        Args:
            enable_persistence: Whether to persist messages to database
            db_path: Path to message database
            health_check_interval: Seconds between health checks
            message_history_size: Maximum messages in memory
        """
        # Message bus
        self._message_bus = AgentMessageBus(
            enable_persistence=enable_persistence,
            db_path=db_path,
            history_size=message_history_size,
        )

        # Agent registry
        self._registry = AgentRegistry(
            health_check_interval=health_check_interval,
        )

        # Agency state
        self._running = False
        self._started_at: Optional[datetime] = None

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"TradingAgency initialized "
            f"(persistence={enable_persistence}, "
            f"health_check_interval={health_check_interval}s)"
        )

    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent with the agency

        Args:
            agent: Agent to register
        """
        # Register with message bus
        self._message_bus.register_agent(agent)

        # Register with registry
        self._registry.register(agent)

        logger.info(f"Agent registered with agency: {agent.name}")

    def unregister_agent(self, agent_name: str) -> bool:
        """
        Unregister an agent from the agency

        Args:
            agent_name: Name of agent to unregister

        Returns:
            True if agent was unregistered
        """
        # Unregister from registry
        result = self._registry.unregister(agent_name)

        # Unregister from message bus
        self._message_bus.unregister_agent(agent_name)

        return result

    async def start(self) -> None:
        """
        Start the agency and all agents

        This method:
        1. Updates agency status
        2. Starts health monitoring
        3. Starts all agents in dependency order
        """
        if self._running:
            logger.warning("TradingAgency already running")
            return

        try:
            logger.info("Starting TradingAgency...")

            self._running = True
            self._started_at = datetime.now()

            # Start health checks
            await self._registry.start_health_checks()

            # Start all agents
            results = await self._registry.start_all_agents()

            successful = sum(1 for v in results.values() if v)
            total = len(results)

            if successful == total:
                logger.info(f"✅ TradingAgency started successfully ({successful}/{total} agents)")
            else:
                logger.warning(
                    f"⚠️ TradingAgency started with errors "
                    f"({successful}/{total} agents successful)"
                )

        except Exception as e:
            logger.error(f"Failed to start TradingAgency: {e}")
            self._running = False
            raise

    async def stop(self) -> None:
        """
        Stop the agency and all agents

        This method:
        1. Stops all agents
        2. Stops health monitoring
        3. Updates agency status
        """
        if not self._running:
            logger.warning("TradingAgency not running")
            return

        try:
            logger.info("Stopping TradingAgency...")

            # Stop all agents
            await self._registry.stop_all_agents()

            # Stop health checks
            await self._registry.stop_health_checks()

            # Shutdown message bus
            await self._message_bus.shutdown()

            self._running = False

            logger.info("✅ TradingAgency stopped")

        except Exception as e:
            logger.error(f"Error stopping TradingAgency: {e}")
            raise

    async def restart_agent(self, agent_name: str) -> bool:
        """
        Restart a specific agent

        Args:
            agent_name: Name of agent to restart

        Returns:
            True if successful
        """
        agent = self._registry.get_agent(agent_name)
        if not agent:
            logger.error(f"Agent not found: {agent_name}")
            return False

        try:
            logger.info(f"Restarting agent: {agent_name}")

            # Stop
            if agent.is_running:
                await agent.stop()

            # Start
            await agent.start()

            logger.info(f"Agent restarted: {agent_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to restart agent {agent_name}: {e}")
            return False

    async def broadcast_message(
        self,
        msg_type: MessageType | str,
        content: Dict[str, Any],
        exclude: Optional[List[str]] = None,
    ) -> None:
        """
        Broadcast a message to all agents

        Args:
            msg_type: Type of message
            content: Message content
            exclude: List of agent names to exclude
        """
        if isinstance(msg_type, MessageType):
            msg_type = msg_type.value

        message = create_message(
            msg_type=msg_type,
            sender="agency",
            content=content,
        )

        await self._message_bus.broadcast(message, exclude=exclude)

    async def send_to_agent(
        self,
        agent_name: str,
        msg_type: MessageType | str,
        content: Dict[str, Any],
    ) -> bool:
        """
        Send a message to a specific agent

        Args:
            agent_name: Name of recipient agent
            msg_type: Type of message
            content: Message content

        Returns:
            True if message was delivered
        """
        if isinstance(msg_type, MessageType):
            msg_type = msg_type.value

        message = create_message(
            msg_type=msg_type,
            sender="agency",
            content=content,
            recipient=agent_name,
        )

        return await self._message_bus.send_to_agent(message, agent_name)

    def get_status(self) -> Dict[str, Any]:
        """
        Get overall agency status

        Returns:
            Dictionary with agency status
        """
        # Get agent info
        all_info = self._registry.get_all_info()

        # Calculate stats
        total = len(all_info)
        running = sum(1 for info in all_info.values() if info.is_running)
        stopped = sum(1 for info in all_info.values() if info.status == "stopped")
        error = sum(1 for info in all_info.values() if info.status == "error")
        healthy = sum(1 for info in all_info.values() if info.is_healthy)
        unhealthy = total - healthy

        return {
            "agency_running": self._running,
            "uptime_seconds": self.uptime,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "agents": {
                "total": total,
                "running": running,
                "stopped": stopped,
                "error": error,
                "healthy": healthy,
                "unhealthy": unhealthy,
            },
            "agents_detail": {
                name: info.to_dict()
                for name, info in all_info.items()
            },
        }

    def get_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific agent

        Args:
            agent_name: Name of agent

        Returns:
            Agent status dict or None if not found
        """
        info = self._registry.get_agent_info(agent_name)
        if info:
            return info.to_dict()
        return None

    def list_agents(self) -> List[str]:
        """
        Get list of all registered agents

        Returns:
            List of agent names
        """
        return self._registry.list_agents()

    def get_message_bus_stats(self) -> Dict[str, Any]:
        """
        Get message bus statistics

        Returns:
            Dictionary with message bus stats
        """
        return self._message_bus.get_stats()

    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get health summary of all agents

        Returns:
            Dictionary with health summary
        """
        return self._registry.get_health_summary()

    @property
    def message_bus(self) -> AgentMessageBus:
        """Get the message bus instance"""
        return self._message_bus

    @property
    def registry(self) -> AgentRegistry:
        """Get the agent registry instance"""
        return self._registry

    @property
    def uptime(self) -> float:
        """Get agency uptime in seconds"""
        if self._started_at:
            return (datetime.now() - self._started_at).total_seconds()
        return 0.0

    @property
    def is_running(self) -> bool:
        """Check if agency is running"""
        return self._running

    async def emergency_stop(self, reason: str = "") -> None:
        """
        Emergency stop all agents immediately

        Args:
            reason: Reason for emergency stop
        """
        logger.error(f"🚨 EMERGENCY STOP: {reason}")

        # Broadcast emergency stop message
        await self.broadcast_message(
            MessageType.EMERGENCY_STOP,
            {
                "reason": reason or "Emergency stop triggered",
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Force stop all agents
        for agent_name in self._registry.list_agents():
            agent = self._registry.get_agent(agent_name)
            if agent and agent.is_running:
                try:
                    # Force stop without waiting for cleanup
                    agent._status = AgentStatus.STOPPING
                    asyncio.create_task(agent.stop())
                except Exception as e:
                    logger.error(f"Error stopping {agent_name}: {e}")

        # Stop the agency
        await self.stop()

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()

    def __repr__(self) -> str:
        return (
            f"<TradingAgency "
            f"running={self._running} "
            f"agents={len(self.list_agents())}>"
        )
