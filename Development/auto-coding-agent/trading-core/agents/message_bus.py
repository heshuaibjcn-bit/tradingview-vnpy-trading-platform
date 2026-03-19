"""
Agent Message Bus

This module implements the message bus for agent communication.
"""

import asyncio
from typing import Dict, Set, Optional, List, Callable, Any
from collections import defaultdict, deque
from datetime import datetime
from loguru import logger

from .messages import AgentMessage, MessageType
from .database import MessageDatabase
from .base import BaseAgent


class MessageFilter:
    """Base class for message filters"""

    def __call__(self, message: AgentMessage) -> bool:
        """
        Check if message passes filter

        Args:
            message: Message to check

        Returns:
            True if message passes filter, False to block
        """
        raise NotImplementedError


class AgentMessageBus:
    """
    Message bus for agent communication

    Provides:
    - Publish/subscribe messaging
    - Point-to-point messaging
    - Message persistence
    - Message history tracking
    - Message filtering
    """

    def __init__(
        self,
        enable_persistence: bool = True,
        db_path: str = "data/messages.db",
        history_size: int = 1000,
    ):
        """
        Initialize message bus

        Args:
            enable_persistence: Whether to persist messages to database
            db_path: Path to message database
            history_size: Maximum number of messages to keep in memory
        """
        # Registered agents
        self._agents: Dict[str, BaseAgent] = {}

        # Subscriptions (topic -> set of agent names)
        self._subscriptions: Dict[str, Set[str]] = defaultdict(set)

        # Message history (in-memory)
        self._message_history: deque[AgentMessage] = deque(maxlen=history_size)

        # Message filters
        self._filters: List[MessageFilter] = []

        # Persistence
        self._enable_persistence = enable_persistence
        self._database: Optional[MessageDatabase] = None

        if enable_persistence:
            self._database = MessageDatabase(db_path)

        # Lock for thread safety
        self._lock = asyncio.Lock()

        # Statistics
        self._messages_sent = 0
        self._messages_received = 0

        logger.info(
            f"AgentMessageBus initialized "
            f"(persistence={enable_persistence}, history_size={history_size})"
        )

    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent with the message bus

        Args:
            agent: Agent to register
        """
        self._agents[agent.name] = agent
        agent.set_message_bus(self)

        logger.info(f"Agent registered: {agent.name}")

    def unregister_agent(self, agent_name: str) -> None:
        """
        Unregister an agent from the message bus

        Args:
            agent_name: Name of agent to unregister
        """
        if agent_name in self._agents:
            del self._agents[agent_name]

            # Remove all subscriptions for this agent
            for topic in list(self._subscriptions.keys()):
                self._subscriptions[topic].discard(agent_name)
                if not self._subscriptions[topic]:
                    del self._subscriptions[topic]

            logger.info(f"Agent unregistered: {agent_name}")

    def subscribe(self, agent_name: str, topic: str) -> None:
        """
        Subscribe an agent to a message topic

        Args:
            agent_name: Name of agent
            topic: Message topic/type to subscribe to
        """
        self._subscriptions[topic].add(agent_name)
        logger.debug(f"{agent_name} subscribed to '{topic}'")

    def unsubscribe(self, agent_name: str, topic: str) -> None:
        """
        Unsubscribe an agent from a message topic

        Args:
            agent_name: Name of agent
            topic: Message topic/type to unsubscribe from
        """
        self._subscriptions[topic].discard(agent_name)

        # Clean up empty subscriptions
        if not self._subscriptions[topic]:
            del self._subscriptions[topic]

        logger.debug(f"{agent_name} unsubscribed from '{topic}'")

    def add_filter(self, filter_func: MessageFilter) -> None:
        """
        Add a message filter

        Args:
            filter_func: MessageFilter instance
        """
        self._filters.append(filter_func)
        logger.info(f"Message filter added: {filter_func.__class__.__name__}")

    def remove_filter(self, filter_func: MessageFilter) -> None:
        """
        Remove a message filter

        Args:
            filter_func: MessageFilter instance
        """
        if filter_func in self._filters:
            self._filters.remove(filter_func)
            logger.info(f"Message filter removed: {filter_func.__class__.__name__}")

    async def publish(
        self,
        message: AgentMessage,
    ) -> bool:
        """
        Publish a message to the bus

        Args:
            message: Message to publish

        Returns:
            True if message was delivered successfully
        """
        async with self._lock:
            # Apply filters
            for filter_func in self._filters:
                try:
                    if not filter_func(message):
                        logger.debug(f"Message filtered out: {message.msg_type}")
                        return False
                except Exception as e:
                    logger.error(f"Error in message filter: {e}")

            # Add to history
            self._message_history.append(message)

            # Persist to database
            if self._database:
                self._database.save_message(message)

            # Route message
            if message.recipient:
                # Point-to-point message
                await self._send_to_recipient(message)
            else:
                # Broadcast message
                await self._broadcast(message)

            self._messages_sent += 1

            return True

    async def broadcast(
        self,
        message: AgentMessage,
        exclude: Optional[List[str]] = None,
    ) -> None:
        """
        Broadcast a message to all subscribers

        Args:
            message: Message to broadcast
            exclude: List of agent names to exclude
        """
        exclude = exclude or []
        message.recipient = None  # Ensure it's a broadcast

        await self.publish(message)

    async def send_to_agent(
        self,
        message: AgentMessage,
        agent_name: str,
    ) -> bool:
        """
        Send a message to a specific agent

        Args:
            message: Message to send
            agent_name: Name of recipient agent

        Returns:
            True if message was delivered
        """
        message.recipient = agent_name
        return await self.publish(message)

    async def _send_to_recipient(self, message: AgentMessage) -> None:
        """Send point-to-point message"""
        recipient = message.recipient

        if recipient not in self._agents:
            logger.warning(f"Recipient not found: {recipient}")
            return

        agent = self._agents[recipient]
        await agent.receive_message(message)
        self._messages_received += 1

    async def _broadcast(self, message: AgentMessage) -> None:
        """Broadcast message to subscribers"""
        msg_type = message.msg_type

        # Get subscribers for this message type
        subscribers = self._subscriptions.get(msg_type, set())

        # Also check for wildcard subscriptions
        wildcard_subscribers = self._subscriptions.get("*", set())
        subscribers = subscribers | wildcard_subscribers

        # Exclude sender from receiving their own broadcast
        subscribers.discard(message.sender)

        # Deliver to all subscribers
        for subscriber_name in subscribers:
            if subscriber_name in self._agents:
                try:
                    agent = self._agents[subscriber_name]
                    await agent.receive_message(message)
                    self._messages_received += 1

                except Exception as e:
                    logger.error(
                        f"Error delivering message to {subscriber_name}: {e}"
                    )

    def get_message_history(
        self,
        msg_type: Optional[str] = None,
        sender: Optional[str] = None,
        limit: int = 100,
    ) -> List[AgentMessage]:
        """
        Get message history from memory

        Args:
            msg_type: Filter by message type
            sender: Filter by sender
            limit: Maximum number of messages to return

        Returns:
            List of messages
        """
        messages = list(self._message_history)

        if msg_type:
            messages = [m for m in messages if m.msg_type == msg_type]

        if sender:
            messages = [m for m in messages if m.sender == sender]

        return messages[-limit:]

    def get_message_history_from_db(
        self,
        msg_type: Optional[str] = None,
        sender: Optional[str] = None,
        limit: int = 100,
    ) -> List[AgentMessage]:
        """
        Get message history from database

        Args:
            msg_type: Filter by message type
            sender: Filter by sender
            limit: Maximum number of messages to return

        Returns:
            List of messages
        """
        if not self._database:
            return []

        return self._database.get_messages(
            msg_type=msg_type,
            sender=sender,
            limit=limit,
        )

    def get_conversation_history(
        self,
        correlation_id: str,
    ) -> List[AgentMessage]:
        """
        Get conversation history by correlation ID

        Args:
            correlation_id: Correlation ID

        Returns:
            List of messages in the conversation
        """
        if not self._database:
            # Return from memory
            return [
                m for m in self._message_history
                if m.correlation_id == correlation_id
            ]

        return self._database.get_conversation(correlation_id)

    def get_subscribers(self, topic: str) -> Set[str]:
        """
        Get all subscribers for a topic

        Args:
            topic: Message topic

        Returns:
            Set of subscriber names
        """
        return self._subscriptions.get(topic, set()).copy()

    def get_agent_subscriptions(self, agent_name: str) -> List[str]:
        """
        Get all topics an agent is subscribed to

        Args:
            agent_name: Agent name

        Returns:
            List of topics
        """
        subscriptions = []

        for topic, subscribers in self._subscriptions.items():
            if agent_name in subscribers:
                subscriptions.append(topic)

        return subscriptions

    def get_stats(self) -> Dict[str, Any]:
        """
        Get message bus statistics

        Returns:
            Dictionary with statistics
        """
        return {
            "registered_agents": len(self._agents),
            "subscriptions": {
                topic: list(subscribers)
                for topic, subscribers in self._subscriptions.items()
            },
            "messages_sent": self._messages_sent,
            "messages_received": self._messages_received,
            "history_size": len(self._message_history),
            "persistence_enabled": self._enable_persistence,
        }

    def clear_history(self) -> None:
        """Clear in-memory message history"""
        self._message_history.clear()
        logger.info("Message history cleared")

    async def shutdown(self) -> None:
        """Shutdown the message bus"""
        logger.info("Shutting down message bus...")

        # Unregister all agents
        for agent_name in list(self._agents.keys()):
            self.unregister_agent(agent_name)

        # Close database
        if self._database:
            self._database.close()

        logger.info("Message bus shutdown complete")


class LogMessageTypeFilter(MessageFilter):
    """Filter that logs all messages"""

    def __init__(self, log_level: str = "DEBUG"):
        self.log_level = log_level

    def __call__(self, message: AgentMessage) -> bool:
        """Log message and pass through"""
        log_func = getattr(logger, self.log_level.lower(), logger.debug)
        log_func(
            f"Message: {message.msg_type} "
            f"{message.sender} -> {message.recipient or 'broadcast'}"
        )
        return True


class MessageTypeFilter(MessageFilter):
    """Filter messages by type"""

    def __init__(self, allowed_types: List[str]):
        self.allowed_types = set(allowed_types)

    def __call__(self, message: AgentMessage) -> bool:
        """Check if message type is allowed"""
        return message.msg_type in self.allowed_types
