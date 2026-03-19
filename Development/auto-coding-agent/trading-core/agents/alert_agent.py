"""
Alert Engine Agent

Wraps the AlertEngine in an Agent interface, monitoring market data
and triggering alerts based on configured rules.
"""

import asyncio
from typing import Dict, Any, Optional, List
from loguru import logger

from .base import BaseAgent
from .messages import MessageType, AgentMessage
from alerts.engine import AlertEngine, AlertRule, Alert, AlertType, AlertCondition


class AlertEngineAgent(BaseAgent):
    """
    Agent wrapper for AlertEngine

    Monitors market data and triggers alerts.
    """

    def __init__(
        self,
        alert_engine: AlertEngine,
    ):
        """
        Initialize alert engine agent

        Args:
            alert_engine: AlertEngine instance to wrap
        """
        super().__init__(
            name="alert_engine",
            version="1.0.0",
            description="Monitors market data and triggers alerts",
        )

        self._engine = alert_engine

        # Track previous prices for each symbol
        self._previous_prices: Dict[str, float] = {}

        # Track previous volumes for volume spike detection
        self._avg_volumes: Dict[str, float] = {}

        # Register message handlers
        self.register_handler(MessageType.MARKET_DATA_UPDATE, self._on_market_data)
        self.register_handler(MessageType.ALERT_RULE_ADD, self._on_add_rule)
        self.register_handler(MessageType.ALERT_RULE_REMOVE, self._on_remove_rule)
        self.register_handler(MessageType.ALERT_ACKNOWLEDGED, self._on_acknowledge)

    async def on_start(self) -> None:
        """Called when agent starts"""
        # Subscribe to market data updates
        self.subscribe(MessageType.MARKET_DATA_UPDATE)

        logger.info(
            f"{self.name}: Started with {len(self._engine.rules)} alert rules"
        )

    async def on_stop(self) -> None:
        """Called when agent stops"""
        # Stop monitoring if running
        self._engine.stop_monitoring()

        logger.info(f"{self.name}: Stopped")

    async def on_message(self, message: AgentMessage) -> None:
        """Called for every message (already handled by specific handlers)"""
        pass

    async def _on_market_data(self, message: AgentMessage) -> None:
        """
        Handle market data update

        Checks against alert rules and triggers alerts if conditions met.
        """
        try:
            content = message.content
            symbol = content.get("symbol")

            if not symbol:
                return

            current_price = content.get("price", 0.0)
            volume = content.get("volume", 0)

            # Get previous price
            previous_price = self._previous_prices.get(symbol, current_price)

            # Check market data against rules
            triggered_alerts = self._engine.check_market_data(
                symbol=symbol,
                current_price=current_price,
                previous_price=previous_price,
                volume=volume,
                indicators={},  # Could calculate RSI, etc.
            )

            # Process triggered alerts
            for alert in triggered_alerts:
                await self._dispatch_alert(alert)

            # Update previous price
            self._previous_prices[symbol] = current_price

        except Exception as e:
            logger.error(f"{self.name}: Error processing market data - {e}")

    async def _on_add_rule(self, message: AgentMessage) -> None:
        """Handle add alert rule request"""
        try:
            content = message.content

            # Create alert rule
            rule = AlertRule(
                id=content.get("rule_id", f"rule_{message.id}"),
                user_id=content.get("user_id", "system"),
                symbol=content.get("symbol", "*"),
                alert_type=AlertType(content.get("alert_type")),
                condition=AlertCondition(content.get("condition", "GREATER_THAN")),
                threshold=content.get("threshold", 0.0),
                params=content.get("params", {}),
                enabled=content.get("enabled", True),
                notification_methods=content.get("notification_methods", ["browser"]),
                name=content.get("name", ""),
                description=content.get("description", ""),
                one_time=content.get("one_time", False),
            )

            self._engine.add_rule(rule)

            logger.info(f"{self.name}: Alert rule added - {rule.name or rule.id}")

        except Exception as e:
            logger.error(f"{self.name}: Error adding alert rule - {e}")

    async def _on_remove_rule(self, message: AgentMessage) -> None:
        """Handle remove alert rule request"""
        try:
            rule_id = message.content.get("rule_id")

            if rule_id:
                self._engine.remove_rule(rule_id)
                logger.info(f"{self.name}: Alert rule removed - {rule_id}")

        except Exception as e:
            logger.error(f"{self.name}: Error removing alert rule - {e}")

    async def _on_acknowledge(self, message: AgentMessage) -> None:
        """Handle alert acknowledge"""
        try:
            alert_id = message.content.get("alert_id")

            if alert_id:
                self._engine.acknowledge_alert(alert_id)
                logger.info(f"{self.name}: Alert acknowledged - {alert_id}")

        except Exception as e:
            logger.error(f"{self.name}: Error acknowledging alert - {e}")

    async def _dispatch_alert(self, alert: Alert) -> None:
        """
        Dispatch triggered alert to message bus

        Args:
            alert: Alert that was triggered
        """
        try:
            await self.send_message(
                MessageType.ALERT_TRIGGERED,
                {
                    "alert_id": alert.id,
                    "rule_id": alert.rule_id,
                    "user_id": alert.user_id,
                    "symbol": alert.symbol,
                    "alert_type": alert.alert_type.value,
                    "message": alert.message,
                    "value": alert.value,
                    "threshold": alert.threshold,
                    "triggered_at": alert.triggered_at.isoformat(),
                    "acknowledged": alert.acknowledged,
                    "metadata": alert.metadata,
                },
            )

            logger.warning(
                f"{self.name}: Alert triggered - {alert.symbol} {alert.message}"
            )

        except Exception as e:
            logger.error(f"{self.name}: Error dispatching alert - {e}")

    # Public API methods

    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule"""
        self._engine.add_rule(rule)

    def remove_rule(self, rule_id: str) -> None:
        """Remove an alert rule"""
        self._engine.remove_rule(rule_id)

    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get an alert rule by ID"""
        return self._engine.get_rule(rule_id)

    def get_user_rules(self, user_id: str) -> List[AlertRule]:
        """Get all rules for a user"""
        return self._engine.get_user_rules(user_id)

    def get_user_alerts(self, user_id: str, limit: int = 100) -> List[Alert]:
        """Get recent alerts for a user"""
        return self._engine.get_user_alerts(user_id, limit)

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        return self._engine.acknowledge_alert(alert_id)

    def add_callback(self, callback) -> None:
        """Add a callback for triggered alerts"""
        self._engine.add_callback(callback)

    def clear_old_alerts(self, days: int = 30) -> int:
        """Clear old alerts"""
        return self._engine.clear_old_alerts(days)
