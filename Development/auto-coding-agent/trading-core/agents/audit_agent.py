"""
Audit Logger Agent

Wraps the AuditLogger in an Agent interface, recording all important
system events for security and compliance.
"""

import asyncio
from typing import Dict, Any, Optional, List
from loguru import logger

from .base import BaseAgent
from .messages import MessageType, AgentMessage
from security.audit import AuditLogger, AuditEventType


class AuditLoggerAgent(BaseAgent):
    """
    Agent wrapper for AuditLogger

    Records audit events for all system operations.
    """

    def __init__(
        self,
        audit_logger: AuditLogger,
    ):
        """
        Initialize audit logger agent

        Args:
            audit_logger: AuditLogger instance to wrap
        """
        super().__init__(
            name="audit_logger",
            version="1.0.0",
            description="Records audit events for security and compliance",
        )

        self._audit = audit_logger

        # Subscribe to all message types for audit logging
        self._important_message_types = {
            # Trading operations
            MessageType.ORDER_REQUEST,
            MessageType.ORDER_FILLED,
            MessageType.ORDER_FAILED,
            MessageType.ORDER_CANCELLED,

            # Strategy operations
            MessageType.STRATEGY_START,
            MessageType.STRATEGY_STOP,
            MessageType.SIGNAL_GENERATED,
            MessageType.SIGNAL_CANCELLED,

            # Risk management
            MessageType.RISK_LIMIT_BREACHED,

            # System control
            MessageType.SYSTEM_START,
            MessageType.SYSTEM_STOP,
            MessageType.EMERGENCY_STOP,

            # Agent lifecycle
            MessageType.AGENT_STARTED,
            MessageType.AGENT_STOPPED,
            MessageType.AGENT_ERROR,
        }

        # Register handlers for critical messages
        self.register_handler(MessageType.ORDER_REQUEST, self._on_order_request)
        self.register_handler(MessageType.STRATEGY_START, self._on_strategy_action)
        self.register_handler(MessageType.STRATEGY_STOP, self._on_strategy_action)
        self.register_handler(MessageType.EMERGENCY_STOP, self._on_emergency_stop)
        self.register_handler(MessageType.AGENT_ERROR, self._on_agent_error)

    async def on_start(self) -> None:
        """Called when agent starts"""
        # Subscribe to all important message types
        for msg_type in self._important_message_types:
            self.subscribe(msg_type)

        logger.info(f"{self.name}: Started (subscribed to {len(self._important_message_types)} message types)")

    async def on_stop(self) -> None:
        """Called when agent stops"""
        logger.info(f"{self.name}: Stopped")

    async def on_message(self, message: AgentMessage) -> None:
        """
        Called for every message

        Logs important messages as audit events.
        """
        try:
            # Only log important message types
            if message.msg_type in self._important_message_types:
                await self._audit_log_message(message)

        except Exception as e:
            logger.error(f"{self.name}: Error auditing message - {e}")

    async def _audit_log_message(self, message: AgentMessage) -> None:
        """Log a message as an audit event"""
        try:
            # Map message types to audit event types
            event_type = self._map_message_to_event_type(message.msg_type)

            if not event_type:
                return

            # Create audit details
            details = {
                "msg_type": message.msg_type,
                "sender": message.sender,
                "recipient": message.recipient,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
            }

            # Log audit event
            self._audit.log(
                event_type=event_type,
                user_id=message.content.get("user_id", "system"),
                details=details,
                success=message.content.get("success", True),
                error_message=message.content.get("error"),
            )

        except Exception as e:
            logger.error(f"{self.name}: Error in audit log - {e}")

    async def _on_order_request(self, message: AgentMessage) -> None:
        """Handle order request - log as order placement"""
        try:
            content = message.content

            self._audit.log_order(
                user_id=content.get("user_id", "system"),
                symbol=content["symbol"],
                side=content["side"],
                quantity=content["quantity"],
                price=content["price"],
                order_id=content.get("order_id", f"pending_{message.id}"),
                success=True,
            )

        except Exception as e:
            logger.error(f"{self.name}: Error logging order request - {e}")

    async def _on_strategy_action(self, message: AgentMessage) -> None:
        """Handle strategy action"""
        try:
            # Map message type to event type
            if message.msg_type == MessageType.STRATEGY_START:
                event_type = AuditEventType.STRATEGY_STARTED
            elif message.msg_type == MessageType.STRATEGY_STOP:
                event_type = AuditEventType.STRATEGY_STOPPED
            else:
                return

            content = message.content

            self._audit.log_strategy_action(
                event_type=event_type,
                user_id=content.get("user_id", "system"),
                strategy_id=content.get("strategy_id", "unknown"),
                strategy_name=content.get("strategy_name", content.get("strategy_name", "unknown")),
                success=True,
            )

        except Exception as e:
            logger.error(f"{self.name}: Error logging strategy action - {e}")

    async def _on_emergency_stop(self, message: AgentMessage) -> None:
        """Handle emergency stop"""
        try:
            content = message.content

            self._audit.log_emergency_stop(
                user_id=content.get("initiated_by", "system"),
                reason=content.get("reason", "Emergency stop triggered"),
            )

        except Exception as e:
            logger.error(f"{self.name}: Error logging emergency stop - {e}")

    async def _on_agent_error(self, message: AgentMessage) -> None:
        """Handle agent error"""
        try:
            content = message.content

            self._audit.log(
                event_type=AuditEventType.STRATEGY_MODIFIED,  # Using existing type
                user_id="system",
                details={
                    "agent_name": content.get("agent_name"),
                    "error": content.get("error"),
                },
                success=False,
                error_message=content.get("error"),
            )

        except Exception as e:
            logger.error(f"{self.name}: Error logging agent error - {e}")

    def _map_message_to_event_type(self, msg_type: str) -> Optional[AuditEventType]:
        """Map message type to audit event type"""
        mapping = {
            MessageType.ORDER_REQUEST: AuditEventType.ORDER_PLACED,
            MessageType.ORDER_FILLED: AuditEventType.ORDER_FILLED,
            MessageType.ORDER_CANCELLED: AuditEventType.ORDER_CANCELLED,
            MessageType.STRATEGY_START: AuditEventType.STRATEGY_STARTED,
            MessageType.STRATEGY_STOP: AuditEventType.STRATEGY_STOPPED,
            MessageType.SIGNAL_GENERATED: AuditEventType.STRATEGY_MODIFIED,
            MessageType.EMERGENCY_STOP: AuditEventType.EMERGENCY_STOP,
        }

        return mapping.get(msg_type)

    # Public API methods

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        details: Dict[str, Any],
        **kwargs
    ):
        """Log an audit event"""
        return self._audit.log(
            event_type=event_type,
            user_id=user_id,
            details=details,
            **kwargs
        )

    def log_order(
        self,
        user_id: str,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        **kwargs
    ):
        """Log an order"""
        return self._audit.log_order(
            user_id=user_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            **kwargs
        )

    def log_strategy_action(
        self,
        event_type: AuditEventType,
        user_id: str,
        strategy_id: str,
        strategy_name: str,
        **kwargs
    ):
        """Log a strategy action"""
        return self._audit.log_strategy_action(
            event_type=event_type,
            user_id=user_id,
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            **kwargs
        )

    def log_emergency_stop(
        self,
        user_id: str,
        reason: str,
        **kwargs
    ):
        """Log an emergency stop"""
        return self._audit.log_emergency_stop(
            user_id=user_id,
            reason=reason,
            **kwargs
        )

    def get_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        limit: int = 100,
    ) -> List:
        """Get audit events"""
        return self._audit.get_events(
            user_id=user_id,
            event_type=event_type,
            limit=limit,
        )

    def get_failed_events(self, limit: int = 100) -> List:
        """Get failed events"""
        return self._audit.get_failed_events(limit)

    def export_to_json(self, output_path: str, user_id: Optional[str] = None) -> None:
        """Export audit log to JSON"""
        self._audit.export_to_json(output_path, user_id)
