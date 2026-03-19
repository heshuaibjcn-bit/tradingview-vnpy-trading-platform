"""
Agent Registry

This module manages agent registration, health checks, and lifecycle.
"""

import asyncio
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from loguru import logger

from .base import BaseAgent, AgentStatus
from .models import AgentInfo, AgentHealth, HealthCheckResult


class AgentRegistry:
    """
    Registry for managing agents

    Provides:
    - Agent registration and discovery
    - Health monitoring
    - Batch start/stop with dependency ordering
    - Agent status queries
    """

    def __init__(
        self,
        health_check_interval: float = 30.0,
        health_check_timeout: float = 5.0,
    ):
        """
        Initialize agent registry

        Args:
            health_check_interval: Seconds between health checks
            health_check_timeout: Timeout for individual health checks
        """
        # Registered agents
        self._agents: Dict[str, BaseAgent] = {}

        # Agent information
        self._agent_info: Dict[str, AgentInfo] = {}

        # Health check configuration
        self._health_check_interval = health_check_interval
        self._health_check_timeout = health_check_timeout

        # Health check task
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False

        # Health check results history
        self._health_history: Dict[str, List[HealthCheckResult]] = {}

        # Event callbacks
        self._on_agent_registered: List[Callable] = []
        self._on_agent_unregistered: List[Callable] = []
        self._on_agent_status_changed: List[Callable] = []

        logger.info(
            f"AgentRegistry initialized "
            f"(health_check_interval={health_check_interval}s)"
        )

    def register(
        self,
        agent: BaseAgent,
    ) -> AgentInfo:
        """
        Register an agent

        Args:
            agent: Agent to register

        Returns:
            AgentInfo for the registered agent
        """
        if agent.name in self._agents:
            logger.warning(f"Agent already registered: {agent.name}")
            return self._agent_info[agent.name]

        # Register agent
        self._agents[agent.name] = agent

        # Create agent info
        info = AgentInfo(
            name=agent.name,
            version=agent.version,
            status=agent.status.value,
            health=AgentHealth.UNKNOWN,
            description=agent.description,
            dependencies=agent.dependencies,
            metadata={},
        )

        self._agent_info[agent.name] = info

        # Initialize health history
        self._health_history[agent.name] = []

        # Notify callbacks
        for callback in self._on_agent_registered:
            try:
                callback(agent)
            except Exception as e:
                logger.error(f"Error in agent registered callback: {e}")

        logger.info(
            f"Agent registered: {agent.name} v{agent.version} "
            f"(dependencies: {agent.dependencies})"
        )

        return info

    def unregister(self, agent_name: str) -> bool:
        """
        Unregister an agent

        Args:
            agent_name: Name of agent to unregister

        Returns:
            True if agent was unregistered, False if not found
        """
        if agent_name not in self._agents:
            logger.warning(f"Agent not found: {agent_name}")
            return False

        agent = self._agents[agent_name]

        # Stop agent if running
        if agent.is_running:
            logger.warning(f"Stopping running agent: {agent_name}")
            asyncio.create_task(agent.stop())

        # Remove from registry
        del self._agents[agent_name]
        del self._agent_info[agent_name]
        del self._health_history[agent_name]

        # Notify callbacks
        for callback in self._on_agent_unregistered:
            try:
                callback(agent_name)
            except Exception as e:
                logger.error(f"Error in agent unregistered callback: {e}")

        logger.info(f"Agent unregistered: {agent_name}")

        return True

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        Get an agent by name

        Args:
            name: Agent name

        Returns:
            BaseAgent or None if not found
        """
        return self._agents.get(name)

    def get_agent_info(self, name: str) -> Optional[AgentInfo]:
        """
        Get agent information

        Args:
            name: Agent name

        Returns:
            AgentInfo or None if not found
        """
        if name in self._agent_info:
            # Update info with latest status
            agent = self._agents.get(name)
            if agent:
                self._agent_info[name] = agent.get_info()

        return self._agent_info.get(name)

    def list_agents(
        self,
        status: Optional[AgentStatus] = None,
    ) -> List[str]:
        """
        List registered agents

        Args:
            status: Optional filter by status

        Returns:
            List of agent names
        """
        agents = list(self._agents.keys())

        if status:
            agents = [
                name for name in agents
                if self._agents[name].status == status
            ]

        return agents

    def get_all_info(self) -> Dict[str, AgentInfo]:
        """
        Get information for all agents

        Returns:
            Dictionary mapping agent names to AgentInfo
        """
        # Update all info
        for name in list(self._agent_info.keys()):
            agent = self._agents.get(name)
            if agent:
                self._agent_info[name] = agent.get_info()

        return self._agent_info.copy()

    async def start_all_agents(self) -> Dict[str, bool]:
        """
        Start all agents in dependency order

        Returns:
            Dictionary mapping agent names to success status
        """
        results = {}

        # Get startup order based on dependencies
        startup_order = self._get_dependency_order()

        logger.info(f"Starting {len(startup_order)} agents in dependency order")

        for agent_name in startup_order:
            agent = self._agents.get(agent_name)
            if not agent:
                results[agent_name] = False
                continue

            try:
                await agent.start()
                results[agent_name] = True

                # Update info
                self._agent_info[agent_name] = agent.get_info()

            except Exception as e:
                logger.error(f"Failed to start agent {agent_name}: {e}")
                results[agent_name] = False

        successful = sum(1 for v in results.values() if v)
        logger.info(f"Started {successful}/{len(results)} agents")

        return results

    async def stop_all_agents(self) -> Dict[str, bool]:
        """
        Stop all agents in reverse dependency order

        Returns:
            Dictionary mapping agent names to success status
        """
        results = {}

        # Get reverse startup order
        startup_order = self._get_dependency_order()
        shutdown_order = list(reversed(startup_order))

        logger.info(f"Stopping {len(shutdown_order)} agents in reverse dependency order")

        for agent_name in shutdown_order:
            agent = self._agents.get(agent_name)
            if not agent:
                results[agent_name] = False
                continue

            try:
                await agent.stop()
                results[agent_name] = True

                # Update info
                self._agent_info[agent_name] = agent.get_info()

            except Exception as e:
                logger.error(f"Failed to stop agent {agent_name}: {e}")
                results[agent_name] = False

        successful = sum(1 for v in results.values() if v)
        logger.info(f"Stopped {successful}/{len(results)} agents")

        return results

    async def start_health_checks(self) -> None:
        """Start periodic health checks"""
        if self._running:
            logger.warning("Health checks already running")
            return

        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())

        logger.info(f"Health checks started (interval={self._health_check_interval}s)")

    async def stop_health_checks(self) -> None:
        """Stop periodic health checks"""
        if not self._running:
            return

        self._running = False

        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        logger.info("Health checks stopped")

    async def _health_check_loop(self) -> None:
        """Health check loop"""
        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self._health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(self._health_check_interval)

    async def _perform_health_checks(self) -> List[HealthCheckResult]:
        """Perform health checks on all agents"""
        results = []

        for agent_name, agent in self._agents.items():
            try:
                # Get current info
                info = agent.get_info()

                # Determine health
                if agent.status == AgentStatus.ERROR:
                    health = AgentHealth.UNHEALTHY
                    message = f"Agent in ERROR state"
                elif agent.status == AgentStatus.RUNNING:
                    # Check if recent errors
                    if info.metrics.errors > 10:
                        health = AgentHealth.DEGRADED
                        message = f"Agent has {info.metrics.errors} errors"
                    else:
                        health = AgentHealth.HEALTHY
                        message = "Agent healthy"
                else:
                    health = AgentHealth.UNKNOWN
                    message = f"Agent status: {agent.status.value}"

                result = HealthCheckResult(
                    agent_name=agent_name,
                    healthy=(health == AgentHealth.HEALTHY),
                    status=health.value,
                    message=message,
                    details={
                        "uptime": info.uptime,
                        "errors": info.metrics.errors,
                        "last_activity": info.metrics.last_activity.isoformat()
                        if info.metrics.last_activity else None,
                    },
                )

                results.append(result)

                # Update health history
                self._health_history[agent_name].append(result)
                if len(self._health_history[agent_name]) > 100:
                    self._health_history[agent_name] = self._health_history[agent_name][-100:]

                # Update agent info health
                self._agent_info[agent_name].health = health
                self._agent_info[agent_name].last_heartbeat = datetime.now()

                # Notify if health changed
                old_health = self._agent_info[agent_name].health
                if old_health != health:
                    for callback in self._on_agent_status_changed:
                        try:
                            callback(agent_name, old_health, health)
                        except Exception as e:
                            logger.error(f"Error in status changed callback: {e}")

            except Exception as e:
                logger.error(f"Error checking health of {agent_name}: {e}")
                results.append(HealthCheckResult(
                    agent_name=agent_name,
                    healthy=False,
                    status="error",
                    message=str(e),
                ))

        return results

    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get summary of agent health

        Returns:
            Dictionary with health summary
        """
        summary = {
            "total_agents": len(self._agents),
            "healthy": 0,
            "degraded": 0,
            "unhealthy": 0,
            "unknown": 0,
            "agents": {},
        }

        for name, info in self._agent_info.items():
            summary["agents"][name] = {
                "health": info.health.value,
                "status": info.status,
                "uptime": info.uptime,
            }

            if info.health == AgentHealth.HEALTHY:
                summary["healthy"] += 1
            elif info.health == AgentHealth.DEGRADED:
                summary["degraded"] += 1
            elif info.health == AgentHealth.UNHEALTHY:
                summary["unhealthy"] += 1
            else:
                summary["unknown"] += 1

        return summary

    def get_unhealthy_agents(self) -> List[str]:
        """
        Get list of unhealthy agent names

        Returns:
            List of unhealthy agent names
        """
        return [
            name for name, info in self._agent_info.items()
            if info.health in (AgentHealth.UNHEALTHY, AgentHealth.DEGRADED)
        ]

    def get_error_agents(self) -> List[str]:
        """
        Get list of agents in ERROR state

        Returns:
            List of error agent names
        """
        return [
            name for name, agent in self._agents.items()
            if agent.status == AgentStatus.ERROR
        ]

    def _get_dependency_order(self) -> List[str]:
        """
        Get agent startup order based on dependencies

        Uses topological sort to determine order

        Returns:
            List of agent names in startup order
        """
        # Build dependency graph
        graph = {name: set(agent.dependencies) for name, agent in self._agents.items()}

        # Topological sort using Kahn's algorithm
        order = []
        no_deps = [name for name, deps in graph.items() if not deps]

        while no_deps:
            node = no_deps.pop(0)
            order.append(node)

            # Remove this node from other dependencies
            for name in list(graph.keys()):
                if node in graph[name]:
                    graph[name].remove(node)
                    if not graph[name]:
                        no_deps.append(name)
                        del graph[name]

        # Handle cycles (just append remaining)
        if graph:
            logger.warning(f"Circular dependencies detected: {list(graph.keys())}")
            order.extend(graph.keys())

        return order

    # Event callbacks

    def on_agent_registered(self, callback: Callable) -> None:
        """Register callback for agent registration"""
        self._on_agent_registered.append(callback)

    def on_agent_unregistered(self, callback: Callable) -> None:
        """Register callback for agent unregistration"""
        self._on_agent_unregistered.append(callback)

    def on_agent_status_changed(self, callback: Callable) -> None:
        """Register callback for agent status change"""
        self._on_agent_status_changed.append(callback)

    async def shutdown(self) -> None:
        """Shutdown the registry"""
        logger.info("Shutting down AgentRegistry...")

        # Stop health checks
        await self.stop_health_checks()

        # Stop all agents
        await self.stop_all_agents()

        logger.info("AgentRegistry shutdown complete")
