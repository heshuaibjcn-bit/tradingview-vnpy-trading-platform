"""
Message Type Definitions for Agent Communication

This module defines all standard message types used in the trading system's
agent-based architecture. All messages between agents follow a standard format.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json


class MessageType(str, Enum):
    """Standard message types for agent communication"""

    # Market Data
    MARKET_DATA_UPDATE = "market_data_update"
    MARKET_DATA_REQUEST = "market_data_request"
    KLINE_REQUEST = "kline_request"
    KLINE_RESPONSE = "kline_response"

    # Trading Signals
    SIGNAL_GENERATED = "signal_generated"
    SIGNAL_EXECUTED = "signal_executed"
    SIGNAL_CANCELLED = "signal_cancelled"

    # Trading Execution
    ORDER_REQUEST = "order_request"
    ORDER_FILLED = "order_filled"
    ORDER_FAILED = "order_failed"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_STATUS_REQUEST = "order_status_request"
    ORDER_STATUS_RESPONSE = "order_status_response"

    # Risk Management
    RISK_CHECK_REQUEST = "risk_check_request"
    RISK_CHECK_RESPONSE = "risk_check_response"
    RISK_LIMIT_BREACHED = "risk_limit_breached"

    # Strategy Management
    STRATEGY_START = "strategy_start"
    STRATEGY_STOP = "strategy_stop"
    STRATEGY_UPDATE = "strategy_update"
    STRATEGY_STATUS_REQUEST = "strategy_status_request"
    STRATEGY_STATUS_RESPONSE = "strategy_status_response"

    # Alerts
    ALERT_TRIGGERED = "alert_triggered"
    ALERT_ACKNOWLEDGED = "alert_acknowledged"
    ALERT_RULE_ADD = "alert_rule_add"
    ALERT_RULE_REMOVE = "alert_rule_remove"

    # Monitoring
    HEALTH_CHECK = "health_check"
    HEALTH_STATUS = "health_status"
    SERVICE_STATUS_CHANGED = "service_status_changed"

    # Audit
    AUDIT_LOG = "audit_log"
    AUDIT_QUERY = "audit_query"
    AUDIT_RESPONSE = "audit_response"

    # System Control
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    EMERGENCY_STOP = "emergency_stop"
    SYSTEM_STATUS_REQUEST = "system_status_request"
    SYSTEM_STATUS_RESPONSE = "system_status_response"

    # Agent Management
    AGENT_REGISTER = "agent_register"
    AGENT_UNREGISTER = "agent_unregister"
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    AGENT_ERROR = "agent_error"

    # Internal
    ERROR = "error"
    ACK = "ack"


@dataclass
class AgentMessage:
    """
    Standard message format for agent communication

    Attributes:
        msg_type: Type of message (from MessageType enum)
        sender: Name of the sending agent
        content: Message payload (dictionary)
        recipient: Optional recipient agent name (None for broadcast)
        correlation_id: Optional ID for correlating request/response
        reply_to: Optional message ID this message is replying to
        timestamp: When the message was created
        id: Unique message identifier
    """

    msg_type: str
    sender: str
    content: Dict[str, Any]
    recipient: Optional[str] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "id": self.id,
            "msg_type": self.msg_type,
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Create message from dictionary"""
        timestamp = data.get("timestamp")
        if timestamp:
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
        else:
            timestamp = datetime.now()

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            msg_type=data["msg_type"],
            sender=data["sender"],
            recipient=data.get("recipient"),
            content=data["content"],
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to"),
            timestamp=timestamp,
        )

    def reply(self, content: Dict[str, Any], sender: str) -> "AgentMessage":
        """Create a reply to this message"""
        return AgentMessage(
            msg_type=MessageType.ACK.value,
            sender=sender,
            recipient=self.sender,
            content=content,
            correlation_id=self.correlation_id or self.id,
            reply_to=self.id,
        )

    def is_broadcast(self) -> bool:
        """Check if this is a broadcast message"""
        return self.recipient is None

    def is_reply(self) -> bool:
        """Check if this is a reply message"""
        return self.reply_to is not None


def create_message(
    msg_type: MessageType | str,
    sender: str,
    content: Dict[str, Any],
    recipient: Optional[str] = None,
    correlation_id: Optional[str] = None,
    reply_to: Optional[str] = None,
) -> AgentMessage:
    """
    Helper function to create an AgentMessage

    Args:
        msg_type: Type of message
        sender: Name of the sending agent
        content: Message payload
        recipient: Optional recipient name
        correlation_id: Optional correlation ID
        reply_to: Optional message ID being replied to

    Returns:
        AgentMessage instance
    """
    if isinstance(msg_type, MessageType):
        msg_type = msg_type.value

    return AgentMessage(
        msg_type=msg_type,
        sender=sender,
        content=content,
        recipient=recipient,
        correlation_id=correlation_id,
        reply_to=reply_to,
    )


# Message content validation schemas
MESSAGE_SCHEMAS: Dict[str, Dict[str, Any]] = {
    # Market Data
    MessageType.MARKET_DATA_UPDATE: {
        "required": ["symbol", "price"],
        "optional": ["volume", "change", "change_percent", "timestamp"],
    },
    MessageType.KLINE_REQUEST: {
        "required": ["symbol"],
        "optional": ["period", "count"],
    },
    # Trading Signals
    MessageType.SIGNAL_GENERATED: {
        "required": ["symbol", "signal_type", "price", "strategy_name"],
        "optional": ["confidence", "quantity", "reason"],
    },
    # Trading Execution
    MessageType.ORDER_REQUEST: {
        "required": ["symbol", "side", "quantity", "price"],
        "optional": ["order_type", "user_id"],
    },
    MessageType.ORDER_FILLED: {
        "required": ["order_id", "symbol", "side", "quantity", "price"],
        "optional": ["commission", "timestamp"],
    },
    # Risk Management
    MessageType.RISK_CHECK_REQUEST: {
        "required": ["symbol", "side", "quantity", "price"],
        "optional": ["user_id", "capital", "current_positions"],
    },
    MessageType.RISK_CHECK_RESPONSE: {
        "required": ["passed", "reason"],
        "optional": ["warnings"],
    },
    # Strategy Management
    MessageType.STRATEGY_START: {
        "required": ["strategy_name"],
        "optional": ["parameters"],
    },
    # System Control
    MessageType.EMERGENCY_STOP: {
        "required": ["reason"],
        "optional": ["initiated_by"],
    },
}


def validate_message_content(msg_type: str, content: Dict[str, Any]) -> bool:
    """
    Validate message content against schema

    Args:
        msg_type: Message type
        content: Message content dictionary

    Returns:
        True if content is valid, False otherwise
    """
    schema = MESSAGE_SCHEMAS.get(msg_type)
    if not schema:
        # No schema defined for this message type
        return True

    # Check required fields
    for field in schema.get("required", []):
        if field not in content:
            return False

    return True


# Helper functions for creating specific message types
def create_market_data_update(
    sender: str,
    symbol: str,
    price: float,
    volume: int = 0,
    change: float = 0.0,
    change_percent: float = 0.0,
) -> AgentMessage:
    """Create a market data update message"""
    return create_message(
        MessageType.MARKET_DATA_UPDATE,
        sender,
        {
            "symbol": symbol,
            "price": price,
            "volume": volume,
            "change": change,
            "change_percent": change_percent,
        },
    )


def create_signal_generated(
    sender: str,
    symbol: str,
    signal_type: str,
    price: float,
    strategy_name: str,
    confidence: float = 1.0,
    quantity: Optional[int] = None,
    reason: str = "",
) -> AgentMessage:
    """Create a signal generated message"""
    content = {
        "symbol": symbol,
        "signal_type": signal_type,
        "price": price,
        "strategy_name": strategy_name,
        "confidence": confidence,
        "reason": reason,
    }
    if quantity is not None:
        content["quantity"] = quantity

    return create_message(MessageType.SIGNAL_GENERATED, sender, content)


def create_order_request(
    sender: str,
    symbol: str,
    side: str,
    quantity: int,
    price: float,
    order_type: str = "limit",
    user_id: str = "system",
) -> AgentMessage:
    """Create an order request message"""
    return create_message(
        MessageType.ORDER_REQUEST,
        sender,
        {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "order_type": order_type,
            "user_id": user_id,
        },
    )


def create_risk_check_request(
    sender: str,
    symbol: str,
    side: str,
    quantity: int,
    price: float,
    user_id: str = "system",
    capital: float = 100000.0,
    current_positions: float = 0.0,
) -> AgentMessage:
    """Create a risk check request message"""
    return create_message(
        MessageType.RISK_CHECK_REQUEST,
        sender,
        {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "user_id": user_id,
            "capital": capital,
            "current_positions": current_positions,
        },
    )


def create_risk_check_response(
    sender: str,
    original_request: AgentMessage,
    passed: bool,
    reason: str,
    warnings: Optional[List[str]] = None,
) -> AgentMessage:
    """Create a risk check response message"""
    return original_request.reply(
        {
            "passed": passed,
            "reason": reason,
            "warnings": warnings or [],
        },
        sender,
    )


def create_alert_triggered(
    sender: str,
    symbol: str,
    alert_type: str,
    message: str,
    value: float,
    threshold: float,
) -> AgentMessage:
    """Create an alert triggered message"""
    return create_message(
        MessageType.ALERT_TRIGGERED,
        sender,
        {
            "symbol": symbol,
            "alert_type": alert_type,
            "message": message,
            "value": value,
            "threshold": threshold,
        },
    )
