"""
Alert Engine

Monitors market data and triggers alerts based on configured rules.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Callable, Any, Optional
from loguru import logger
import pandas as pd


class AlertType(str, Enum):
    """Types of alerts."""
    PRICE_ABOVE = "price_above"           # Price crosses above threshold
    PRICE_BELOW = "price_below"           # Price crosses below threshold
    PRICE_CHANGE_PERCENT = "price_change" # Price changes by percentage
    VOLUME_SPIKE = "volume_spike"         # Volume increases by percentage
    GAP_UP = "gap_up"                    # Price gaps up at open
    GAP_DOWN = "gap_down"                # Price gaps down at open
    RSI_OVERBOUGHT = "rsi_overbought"    # RSI exceeds threshold
    RSI_OVERSOLD = "rsi_oversold"        # RSI below threshold
    CUSTOM = "custom"                    # Custom condition


class AlertCondition(str, Enum):
    """Alert condition operators."""
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_EQUAL = "gte"
    LESS_EQUAL = "lte"
    EQUALS = "eq"
    CROSSES_ABOVE = "crosses_above"
    CROSSES_BELOW = "crosses_below"


@dataclass
class AlertRule:
    """Configuration for an alert rule."""
    id: str
    user_id: str
    symbol: str
    alert_type: AlertType
    condition: AlertCondition
    threshold: float
    # Additional parameters
    params: Dict[str, Any] = field(default_factory=dict)
    # Notification settings
    enabled: bool = True
    notification_methods: List[str] = field(default_factory=lambda: ["browser"])
    # Metadata
    name: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    # One-time alert (auto-disable after triggering)
    one_time: bool = False

    def matches(self, current_price: float, previous_price: float,
                volume: int, indicators: Dict[str, float]) -> bool:
        """Check if current market conditions match this alert rule."""
        if not self.enabled:
            return False

        if self.alert_type == AlertType.PRICE_ABOVE:
            if self.condition == AlertCondition.CROSSES_ABOVE:
                return previous_price <= self.threshold < current_price
            return current_price > self.threshold

        elif self.alert_type == AlertType.PRICE_BELOW:
            if self.condition == AlertCondition.CROSSES_BELOW:
                return previous_price >= self.threshold > current_price
            return current_price < self.threshold

        elif self.alert_type == AlertType.PRICE_CHANGE_PERCENT:
            change = (current_price - previous_price) / previous_price * 100
            return abs(change) >= self.threshold

        elif self.alert_type == AlertType.VOLUME_SPIKE:
            avg_volume = self.params.get("avg_volume", 0)
            return avg_volume > 0 and (volume / avg_volume) >= self.threshold

        elif self.alert_type == AlertType.RSI_OVERBOUGHT:
            rsi = indicators.get("rsi", 50)
            return rsi >= self.threshold

        elif self.alert_type == AlertType.RSI_OVERSOLD:
            rsi = indicators.get("rsi", 50)
            return rsi <= self.threshold

        return False


@dataclass
class Alert:
    """Triggered alert."""
    id: str
    rule_id: str
    user_id: str
    symbol: str
    alert_type: AlertType
    message: str
    value: float
    threshold: float
    triggered_at: datetime
    acknowledged: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlertEngine:
    """
    Monitors market data and triggers alerts based on configured rules.
    """

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: List[Alert] = []
        self._callbacks: List[Callable[[Alert], None]] = []
        self._running = False

    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self.rules[rule.id] = rule
        logger.info(f"Added alert rule: {rule.name or rule.id} for {rule.symbol}")

    def remove_rule(self, rule_id: str) -> None:
        """Remove an alert rule."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")

    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get an alert rule by ID."""
        return self.rules.get(rule_id)

    def get_user_rules(self, user_id: str) -> List[AlertRule]:
        """Get all alert rules for a user."""
        return [r for r in self.rules.values() if r.user_id == user_id]

    def get_user_alerts(self, user_id: str, limit: int = 100) -> List[Alert]:
        """Get recent alerts for a user."""
        user_alerts = [a for a in self.alerts if a.user_id == user_id]
        return sorted(user_alerts, key=lambda a: a.triggered_at, reverse=True)[:limit]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark an alert as acknowledged."""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def add_callback(self, callback: Callable[[Alert], None]) -> None:
        """Add a callback function to be called when alerts are triggered."""
        self._callbacks.append(callback)

    def check_market_data(
        self,
        symbol: str,
        current_price: float,
        previous_price: float,
        volume: int,
        indicators: Optional[Dict[str, float]] = None
    ) -> List[Alert]:
        """Check market data against all rules and return triggered alerts."""
        if indicators is None:
            indicators = {}

        triggered = []
        indicators["rsi"] = self._calculate_rsi(current_price, previous_price)

        for rule in self.rules.values():
            if rule.symbol == symbol or rule.symbol == "*":  # * means all symbols
                if rule.matches(current_price, previous_price, volume, indicators):
                    alert = Alert(
                        id=f"alert_{datetime.now().timestamp()}",
                        rule_id=rule.id,
                        user_id=rule.user_id,
                        symbol=symbol,
                        alert_type=rule.alert_type,
                        message=self._format_alert_message(rule, current_price),
                        value=current_price,
                        threshold=rule.threshold,
                        triggered_at=datetime.now(),
                    )
                    triggered.append(alert)
                    self.alerts.append(alert)

                    # Disable one-time alerts
                    if rule.one_time:
                        rule.enabled = False

                    # Notify callbacks
                    for callback in self._callbacks:
                        try:
                            callback(alert)
                        except Exception as e:
                            logger.error(f"Error in alert callback: {e}")

                    logger.info(f"Alert triggered: {alert.message}")

        return triggered

    def _format_alert_message(self, rule: AlertRule, current_price: float) -> str:
        """Format a human-readable alert message."""
        type_names = {
            AlertType.PRICE_ABOVE: "价格突破上限",
            AlertType.PRICE_BELOW: "价格跌破下限",
            AlertType.PRICE_CHANGE_PERCENT: "价格异动",
            AlertType.VOLUME_SPIKE: "成交量异常",
            AlertType.RSI_OVERBOUGHT: "RSI超买",
            AlertType.RSI_OVERSOLD: "RSI超卖",
        }

        type_name = type_names.get(rule.alert_type, "价格提醒")

        if rule.description:
            return f"{rule.symbol} {rule.description}"
        else:
            return f"{rule.symbol} {type_name}: 当前价格 ¥{current_price:.2f}, 阈值 ¥{rule.threshold:.2f}"

    def _calculate_rsi(self, current_price: float, previous_price: float) -> float:
        """
        Simple RSI calculation (placeholder).

        In production, this would use historical price data.
        """
        # Simplified: just return a value based on price change
        change = (current_price - previous_price) / previous_price
        # Map -5% to +5% change to 0-100 RSI
        rsi = 50 + (change * 1000)
        return max(0, min(100, rsi))

    async def start_monitoring(self, market_data_callback: Callable, interval: int = 5) -> None:
        """
        Start continuous market monitoring.

        Args:
            market_data_callback: Async function that returns current market data
            interval: Check interval in seconds
        """
        self._running = True

        while self._running:
            try:
                # Fetch current market data
                data = await market_data_callback()

                for symbol, data_point in data.items():
                    self.check_market_data(
                        symbol=symbol,
                        current_price=data_point.get("price", 0),
                        previous_price=data_point.get("previous_price", 0),
                        volume=data_point.get("volume", 0),
                    )

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            await asyncio.sleep(interval)

    def stop_monitoring(self) -> None:
        """Stop continuous monitoring."""
        self._running = False

    def clear_old_alerts(self, days: int = 30) -> int:
        """Remove alerts older than specified days."""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        original_count = len(self.alerts)
        self.alerts = [a for a in self.alerts if a.triggered_at.timestamp() > cutoff]
        return original_count - len(self.alerts)
