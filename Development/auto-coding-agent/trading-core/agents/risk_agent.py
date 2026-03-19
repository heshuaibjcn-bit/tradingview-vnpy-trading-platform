"""
Risk Manager Agent

Wraps the RiskManager in an Agent interface, providing risk checking
for all trading decisions.
"""

import asyncio
from typing import Dict, Any, Optional, List
from loguru import logger

from .base import BaseAgent
from .messages import MessageType, AgentMessage
from risk.manager import RiskManager, RiskCheck


class RiskManagerAgent(BaseAgent):
    """
    Agent wrapper for RiskManager

    Performs risk checks on all trading decisions.
    """

    def __init__(
        self,
        risk_manager: RiskManager,
    ):
        """
        Initialize risk manager agent

        Args:
            risk_manager: RiskManager instance to wrap
        """
        super().__init__(
            name="risk_manager",
            version="1.0.0",
            description="Performs risk checks on trading decisions",
        )

        self._manager = risk_manager

        # Track current positions and capital
        self._capital: float = 100000.0
        self._positions_value: float = 0.0

        # Register message handlers
        self.register_handler(MessageType.RISK_CHECK_REQUEST, self._on_risk_check_request)
        self.register_handler(MessageType.ORDER_FILLED, self._on_order_filled)
        self.register_handler(MessageType.SYSTEM_START, self._on_system_start)
        self.register_handler(MessageType.EMERGENCY_STOP, self._on_emergency_stop)

    async def on_start(self) -> None:
        """Called when agent starts"""
        # Reset daily limits
        self._manager.reset_daily_limits()

        logger.info(f"{self.name}: Started")

    async def on_stop(self) -> None:
        """Called when agent stops"""
        logger.info(f"{self.name}: Stopped")

    async def on_message(self, message: AgentMessage) -> None:
        """Called for every message (already handled by specific handlers)"""
        pass

    async def _on_risk_check_request(self, message: AgentMessage) -> None:
        """
        Handle risk check request

        Performs risk check and sends response.
        """
        try:
            content = message.content

            # Extract request parameters
            symbol = content.get("symbol")
            side = content.get("side")
            quantity = content.get("quantity")
            price = content.get("price")
            user_id = content.get("user_id", "system")
            capital = content.get("capital", self._capital)
            current_positions = content.get("current_positions", self._positions_value)

            # Perform risk check
            risk_check = self._manager.check_trade(
                user_id=user_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                current_positions_value=current_positions,
                capital=capital,
            )

            # Send response
            await self.send_message(
                MessageType.RISK_CHECK_RESPONSE,
                {
                    "passed": risk_check.passed,
                    "reason": risk_check.reason,
                    "warnings": risk_check.warnings,
                },
                recipient=message.sender,
                correlation_id=message.correlation_id,
            )

            if risk_check.passed:
                logger.info(
                    f"{self.name}: Risk check PASSED - {side.upper()} "
                    f"{quantity} {symbol} @ {price}"
                )
            else:
                logger.warning(
                    f"{self.name}: Risk check FAILED - {side.upper()} "
                    f"{quantity} {symbol} @ {price} - {risk_check.reason}"
                )

                # Send risk limit breached message if appropriate
                if "limit" in risk_check.reason.lower():
                    await self.send_message(
                        MessageType.RISK_LIMIT_BREACHED,
                        {
                            "symbol": symbol,
                            "side": side,
                            "quantity": quantity,
                            "price": price,
                            "reason": risk_check.reason,
                            "warnings": risk_check.warnings,
                        },
                    )

        except Exception as e:
            logger.error(f"{self.name}: Error performing risk check - {e}")

            # Send failure response
            await self.send_message(
                MessageType.RISK_CHECK_RESPONSE,
                {
                    "passed": False,
                    "reason": f"Error in risk check: {str(e)}",
                    "warnings": [],
                },
                recipient=message.sender,
                correlation_id=message.correlation_id,
            )

    async def _on_order_filled(self, message: AgentMessage) -> None:
        """
        Handle order filled message

        Records the trade in risk manager for limit tracking.
        """
        try:
            content = message.content

            self._manager.record_trade(
                user_id=content.get("user_id", "system"),
                symbol=content["symbol"],
                quantity=content["quantity"],
                price=content["price"],
                realized_pnl=0.0,  # Would calculate for close orders
            )

            # Update positions
            if content["side"] == "buy":
                self._positions_value += content["quantity"] * content["price"]
            elif content["side"] == "sell":
                self._positions_value -= content["quantity"] * content["price"]

            logger.info(
                f"{self.name}: Trade recorded - {content['side'].upper()} "
                f"{content['quantity']} {content['symbol']} @ {content['price']}"
            )

        except Exception as e:
            logger.error(f"{self.name}: Error recording trade - {e}")

    async def _on_system_start(self, message: AgentMessage) -> None:
        """Handle system start message"""
        # Reset daily limits
        self._manager.reset_daily_limits()

        logger.info(f"{self.name}: Daily limits reset on system start")

    async def _on_emergency_stop(self, message: AgentMessage) -> None:
        """Handle emergency stop"""
        logger.warning(
            f"{self.name}: Emergency stop triggered - {message.content.get('reason', 'Unknown')}"
        )

    # Public API methods

    def set_capital(self, capital: float) -> None:
        """Set total capital"""
        self._capital = capital
        logger.info(f"{self.name}: Capital set to {capital}")

    def set_positions_value(self, value: float) -> None:
        """Set current positions value"""
        self._positions_value = value

    def get_capital(self) -> float:
        """Get total capital"""
        return self._capital

    def get_positions_value(self) -> float:
        """Get current positions value"""
        return self._positions_value

    def add_limit(self, limit) -> None:
        """Add a custom risk limit"""
        self._manager.add_limit(limit)

    def remove_limit(self, limit_id: str) -> bool:
        """Remove a custom risk limit"""
        return self._manager.remove_limit(limit_id)

    def reset_daily_limits(self) -> None:
        """Reset daily trading limits"""
        self._manager.reset_daily_limits()

    def get_risk_summary(self, user_id: str = "system") -> Dict[str, Any]:
        """Get risk management summary"""
        return self._manager.get_risk_summary(user_id, self._capital)

    def check_trade(
        self,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        user_id: str = "system",
    ) -> RiskCheck:
        """
        Perform a risk check

        Args:
            symbol: Stock symbol
            side: Order side (buy/sell)
            quantity: Order quantity
            price: Order price
            user_id: User ID

        Returns:
            RiskCheck result
        """
        return self._manager.check_trade(
            user_id=user_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            current_positions_value=self._positions_value,
            capital=self._capital,
        )
