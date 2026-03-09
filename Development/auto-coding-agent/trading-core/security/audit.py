"""
Audit logging for sensitive operations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
from loguru import logger


class AuditEventType(Enum):
    """Types of audit events."""
    # Trading operations
    ORDER_PLACED = "order_placed"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_MODIFIED = "order_modified"
    ORDER_FILLED = "order_filled"
    # Strategy operations
    STRATEGY_STARTED = "strategy_started"
    STRATEGY_STOPPED = "strategy_stopped"
    STRATEGY_MODIFIED = "strategy_modified"
    # Security operations
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"
    PERMISSION_CHANGED = "permission_changed"
    # System operations
    EMERGENCY_STOP = "emergency_stop"
    SETTINGS_MODIFIED = "settings_modified"
    LIMITS_CHANGED = "limits_changed"
    # Data operations
    DATA_EXPORTED = "data_exported"
    REPORT_GENERATED = "report_generated"


class AuditEvent:
    """An audit log entry."""

    def __init__(
        self,
        event_type: AuditEventType,
        user_id: str,
        details: Dict[str, Any],
        timestamp: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        self.event_type = event_type
        self.user_id = user_id
        self.details = details
        self.timestamp = timestamp or datetime.now()
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.success = success
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "success": self.success,
            "error_message": self.error_message,
        }


class AuditLogger:
    """
    Audit logger for sensitive operations.

    Records all important security and trading events.
    """

    def __init__(self, log_dir: str = "logs/audit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._events: List[AuditEvent] = []
        self._buffer_size = 1000

    def log(
        self,
        event_type: AuditEventType,
        user_id: str,
        details: Dict[str, Any],
        success: bool = True,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditEvent:
        """
        Log an audit event.

        Args:
            event_type: Type of event
            user_id: User who performed the action
            details: Additional details about the event
            success: Whether the operation succeeded
            error_message: Error message if failed
            ip_address: IP address of the request
            user_agent: User agent string

        Returns:
            AuditEvent that was created
        """
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
        )

        self._events.append(event)

        # Keep buffer size manageable
        if len(self._events) > self._buffer_size:
            self._events = self._events[-self._buffer_size:]

        # Write to file
        self._write_to_file(event)

        # Log to console for critical events
        if event_type in (
            AuditEventType.EMERGENCY_STOP,
            AuditEventType.ORDER_PLACED,
            AuditEventType.STRATEGY_STARTED,
        ):
            log_func = logger.info if success else logger.warning
            log_func(
                f"Audit: {event_type.value} by {user_id} - "
                f"success={success}, details={details}"
            )

        return event

    def log_order(
        self,
        user_id: str,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        order_id: str,
        success: bool = True,
        **kwargs
    ) -> AuditEvent:
        """Log an order placement."""
        return self.log(
            AuditEventType.ORDER_PLACED,
            user_id,
            {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "order_id": order_id,
                **kwargs,
            },
            success=success,
        )

    def log_strategy_action(
        self,
        event_type: AuditEventType,
        user_id: str,
        strategy_id: str,
        strategy_name: str,
        success: bool = True,
        **kwargs
    ) -> AuditEvent:
        """Log a strategy action."""
        return self.log(
            event_type,
            user_id,
            {
                "strategy_id": strategy_id,
                "strategy_name": strategy_name,
                **kwargs,
            },
            success=success,
        )

    def log_emergency_stop(
        self,
        user_id: str,
        reason: str,
        **kwargs
    ) -> AuditEvent:
        """Log an emergency stop."""
        return self.log(
            AuditEventType.EMERGENCY_STOP,
            user_id,
            {"reason": reason, **kwargs},
            success=True,
        )

    def get_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """
        Get filtered audit events.

        Args:
            user_id: Filter by user
            event_type: Filter by event type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of events to return

        Returns:
            List of matching audit events
        """
        events = self._events

        if user_id:
            events = [e for e in events if e.user_id == user_id]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if start_date:
            events = [e for e in events if e.timestamp >= start_date]
        if end_date:
            events = [e for e in events if e.timestamp <= end_date]

        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]

    def get_failed_events(self, limit: int = 100) -> List[AuditEvent]:
        """Get only failed events."""
        return [e for e in self._events if not e.success][:limit]

    def get_events_by_type(
        self,
        event_type: AuditEventType,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Get events by type."""
        return [
            e for e in self._events
            if e.event_type == event_type
        ][:limit]

    def _write_to_file(self, event: AuditEvent) -> None:
        """Write audit event to file."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"audit_{today}.log"

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def export_to_json(
        self,
        output_path: str,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Export audit log to JSON file.

        Args:
            output_path: Path to output file
            user_id: Optional user filter
        """
        events = self.get_events(user_id=user_id, limit=10000)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in events], f, ensure_ascii=False, indent=2)

        logger.info(f"Audit log exported to {output_path}")


# Global audit logger instance
_global_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _global_audit_logger
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger()
    return _global_audit_logger
