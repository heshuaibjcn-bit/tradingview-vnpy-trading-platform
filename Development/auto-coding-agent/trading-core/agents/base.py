"""
Base Agent Class

This module defines the abstract BaseAgent class that all agents inherit from.
"""

import asyncio
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Callable, Optional, Any, List, Coroutine
from datetime import datetime
from loguru import logger

from .messages import AgentMessage, MessageType
from .models import AgentInfo, AgentMetrics, AgentHealth


class AgentStatus(str, Enum):
    """Agent lifecycle status"""
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the trading system.

    All agents must inherit from this class and implement the abstract methods:
    - on_start(): Called when agent starts
    - on_stop(): Called when agent stops
    - on_message(): Called when message is received

    Example:
        class MyAgent(BaseAgent):
            async def on_start(self):
                logger.info(f"{self.name} starting")

            async def on_stop(self):
                logger.info(f"{self.name} stopping")

            async def on_message(self, message: AgentMessage):
                logger.info(f"{self.name} received: {message.msg_type}")
    """

    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = "",
        dependencies: Optional[List[str]] = None,
    ):
        """
        Initialize base agent

        Args:
            name: Unique agent name
            version: Agent version
            description: Agent description
            dependencies: List of agent names this agent depends on
        """
        self.name = name
        self.version = version
        self.description = description
        self.dependencies = dependencies or []

        # Agent state
        self._status = AgentStatus.INITIALIZED
        self._message_bus: Optional[Any] = None  # Avoid circular import
        self._message_handlers: Dict[str, Callable] = {}
        self._async_message_handlers: Dict[str, Callable] = {}

        # Metrics
        self._metrics = AgentMetrics()
        self._started_at: Optional[datetime] = None

        # Message history (in-memory, limited size)
        self._message_history: List[AgentMessage] = []
        self._max_history_size = 100

        # Metadata
        self._metadata: Dict[str, Any] = {}

        logger.info(
            f"Agent initialized: {self.name} v{self.version}"
        )

    @property
    def status(self) -> AgentStatus:
        """Get agent status"""
        return self._status

    @property
    def is_running(self) -> bool:
        """Check if agent is running"""
        return self._status == AgentStatus.RUNNING

    @property
    def metrics(self) -> AgentMetrics:
        """Get agent metrics"""
        self._update_metrics()
        return self._metrics

    @property
    def uptime(self) -> float:
        """Get agent uptime in seconds"""
        if self._started_at:
            return (datetime.now() - self._started_at).total_seconds()
        return 0.0

    def get_info(self) -> AgentInfo:
        """Get agent information"""
        return AgentInfo(
            name=self.name,
            version=self.version,
            status=self._status.value,
            health=self._get_health(),
            description=self.description,
            dependencies=self.dependencies,
            metrics=self.metrics,
            started_at=self._started_at,
            last_heartbeat=datetime.now(),
            metadata=self._metadata.copy(),
        )

    def set_message_bus(self, message_bus: Any) -> None:
        """
        Set the message bus for this agent

        Args:
            message_bus: AgentMessageBus instance
        """
        self._message_bus = message_bus

    def register_handler(
        self,
        msg_type: str | MessageType,
        handler: Callable[[AgentMessage], Any] | Callable[[AgentMessage], Coroutine[Any, Any, Any]],
    ) -> None:
        """
        Register a message handler

        Args:
            msg_type: Message type to handle
            handler: Handler function (sync or async)
        """
        if isinstance(msg_type, MessageType):
            msg_type = msg_type.value

        if asyncio.iscoroutinefunction(handler):
            self._async_message_handlers[msg_type] = handler
        else:
            self._message_handlers[msg_type] = handler

        logger.debug(f"{self.name}: Registered handler for '{msg_type}'")

    def unregister_handler(self, msg_type: str | MessageType) -> None:
        """
        Unregister a message handler

        Args:
            msg_type: Message type
        """
        if isinstance(msg_type, MessageType):
            msg_type = msg_type.value

        self._message_handlers.pop(msg_type, None)
        self._async_message_handlers.pop(msg_type, None)

        logger.debug(f"{self.name}: Unregistered handler for '{msg_type}'")

    async def start(self) -> None:
        """
        Start the agent

        This method:
        1. Updates status to STARTING
        2. Calls on_start() (implemented by subclass)
        3. Updates status to RUNNING
        4. Subscribes to default message types
        """
        if self._status == AgentStatus.RUNNING:
            logger.warning(f"{self.name}: Already running")
            return

        try:
            logger.info(f"{self.name}: Starting...")
            self._status = AgentStatus.STARTING

            # Call subclass start logic
            await self.on_start()

            # Update state
            self._status = AgentStatus.RUNNING
            self._started_at = datetime.now()

            logger.info(f"{self.name}: Started successfully")

        except Exception as e:
            logger.error(f"{self.name}: Failed to start - {e}")
            self._status = AgentStatus.ERROR
            raise

    async def stop(self) -> None:
        """
        Stop the agent

        This method:
        1. Updates status to STOPPING
        2. Calls on_stop() (implemented by subclass)
        3. Updates status to STOPPED
        """
        if self._status == AgentStatus.STOPPED:
            logger.warning(f"{self.name}: Already stopped")
            return

        try:
            logger.info(f"{self.name}: Stopping...")
            self._status = AgentStatus.STOPPING

            # Call subclass stop logic
            await self.on_stop()

            # Update state
            self._status = AgentStatus.STOPPED

            logger.info(f"{self.name}: Stopped successfully")

        except Exception as e:
            logger.error(f"{self.name}: Failed to stop - {e}")
            self._status = AgentStatus.ERROR
            raise

    async def send_message(
        self,
        msg_type: str | MessageType,
        content: Dict[str, Any],
        recipient: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Send a message through the message bus

        Args:
            msg_type: Type of message
            content: Message content
            recipient: Optional recipient name (None for broadcast)
            correlation_id: Optional correlation ID for request/response tracking
        """
        if not self._message_bus:
            raise RuntimeError(f"{self.name}: Message bus not set")

        if isinstance(msg_type, MessageType):
            msg_type = msg_type.value

        message = AgentMessage(
            msg_type=msg_type,
            sender=self.name,
            content=content,
            recipient=recipient,
            correlation_id=correlation_id,
        )

        await self._message_bus.publish(message)

        # Update metrics
        self._metrics.messages_sent += 1
        self._metrics.last_activity = datetime.now()

        logger.debug(
            f"{self.name}: Sent '{msg_type}'"
            + (f" to {recipient}" if recipient else " (broadcast)")
        )

    async def receive_message(self, message: AgentMessage) -> None:
        """
        Receive and process a message

        This method:
        1. Updates metrics
        2. Adds to message history
        3. Routes to registered handler
        4. Calls on_message() (implemented by subclass)

        Args:
            message: Incoming message
        """
        # Update metrics
        self._metrics.messages_received += 1
        self._metrics.last_activity = datetime.now()

        # Add to history
        self._add_to_history(message)

        # Route to registered handler
        handler = self._async_message_handlers.get(message.msg_type) or \
                  self._message_handlers.get(message.msg_type)

        try:
            if handler:
                # Call registered handler
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)

            # Always call on_message for subclass processing
            await self.on_message(message)

        except Exception as e:
            logger.error(f"{self.name}: Error processing message - {e}")
            self._metrics.errors += 1

    def subscribe(self, msg_type: str | MessageType) -> None:
        """
        Subscribe to a message type

        Args:
            msg_type: Message type to subscribe to
        """
        if not self._message_bus:
            raise RuntimeError(f"{self.name}: Message bus not set")

        if isinstance(msg_type, MessageType):
            msg_type = msg_type.value

        self._message_bus.subscribe(self.name, msg_type)
        logger.debug(f"{self.name}: Subscribed to '{msg_type}'")

    def unsubscribe(self, msg_type: str | MessageType) -> None:
        """
        Unsubscribe from a message type

        Args:
            msg_type: Message type to unsubscribe from
        """
        if not self._message_bus:
            raise RuntimeError(f"{self.name}: Message bus not set")

        if isinstance(msg_type, MessageType):
            msg_type = msg_type.value

        self._message_bus.unsubscribe(self.name, msg_type)
        logger.debug(f"{self.name}: Unsubscribed from '{msg_type}'")

    # Abstract methods (must be implemented by subclasses)

    @abstractmethod
    async def on_start(self) -> None:
        """
        Called when agent starts

        Implement this method to perform initialization logic,
        subscribe to message types, start background tasks, etc.
        """
        pass

    @abstractmethod
    async def on_stop(self) -> None:
        """
        Called when agent stops

        Implement this method to perform cleanup logic,
        stop background tasks, release resources, etc.
        """
        pass

    @abstractmethod
    async def on_message(self, message: AgentMessage) -> None:
        """
        Called for every message received

        Implement this method to handle messages that are not
        handled by specific message type handlers.

        Args:
            message: Received message
        """
        pass

    # Helper methods

    def _get_health(self) -> AgentHealth:
        """Get agent health status"""
        if self._status == AgentStatus.ERROR:
            return AgentHealth.UNHEALTHY
        elif self._status == AgentStatus.RUNNING:
            # Check if recent errors
            if self._metrics.errors > 10:
                return AgentHealth.DEGRADED
            return AgentHealth.HEALTHY
        else:
            return AgentHealth.UNKNOWN

    def _update_metrics(self) -> None:
        """Update agent metrics"""
        if self._started_at:
            self._metrics.uptime_seconds = self.uptime

        # Update CPU and memory (placeholder - would use psutil in production)
        # self._metrics.memory_mb = ...
        # self._metrics.cpu_percent = ...

    def _add_to_history(self, message: AgentMessage) -> None:
        """Add message to in-memory history"""
        self._message_history.append(message)

        # Limit history size
        if len(self._message_history) > self._max_history_size:
            self._message_history = self._message_history[-self._max_history_size:]

    def get_message_history(self, limit: int = 10) -> List[AgentMessage]:
        """
        Get recent message history

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of recent messages
        """
        return self._message_history[-limit:]

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value"""
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value"""
        return self._metadata.get(key, default)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} status={self._status.value}>"
