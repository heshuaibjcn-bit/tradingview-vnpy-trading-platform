"""
THS Trader Agent

Wraps the THSTrader (Tonghuashun automation trader) in an Agent interface.
"""

import asyncio
from typing import Dict, Any, Optional
from loguru import logger

from .base import BaseAgent
from .messages import MessageType, AgentMessage
from automation.trader import THSTrader, TradingResult, OrderType


class THSTraderAgent(BaseAgent):
    """
    Agent wrapper for THSTrader

    Handles order execution through Tonghuashun automation.
    """

    def __init__(
        self,
        trader: THSTrader,
        risk_manager_agent: str = "risk_manager",
    ):
        """
        Initialize THS trader agent

        Args:
            trader: THSTrader instance to wrap
            risk_manager_agent: Name of the risk manager agent
        """
        super().__init__(
            name="ths_trader",
            version="1.0.0",
            description="Executes trades through Tonghuashun automation",
            dependencies=[risk_manager_agent] if risk_manager_agent else [],
        )

        self._trader = trader
        self._risk_manager_agent = risk_manager_agent

        # Track pending orders awaiting risk check
        self._pending_orders: Dict[str, Dict[str, Any]] = {}

        # Register message handlers
        self.register_handler(MessageType.ORDER_REQUEST, self._on_order_request)
        self.register_handler(MessageType.RISK_CHECK_RESPONSE, self._on_risk_response)
        self.register_handler(MessageType.ORDER_CANCELLED, self._on_order_cancel)

    async def on_start(self) -> None:
        """Called when agent starts"""
        # Connect to Tonghuashun window
        result = self._trader.connect()

        if not result.success:
            raise RuntimeError(
                f"Failed to connect to Tonghuashun: {result.message}"
            )

        logger.info(f"{self.name}: Connected to Tonghuashun")

    async def on_stop(self) -> None:
        """Called when agent stops"""
        # Cancel any pending orders
        for order_id, order_info in list(self._pending_orders.items()):
            logger.warning(f"{self.name}: Cancelling pending order: {order_id}")

        logger.info(f"{self.name}: Stopped")

    async def on_message(self, message: AgentMessage) -> None:
        """Called for every message (already handled by specific handlers)"""
        pass

    async def _on_order_request(self, message: AgentMessage) -> None:
        """
        Handle order request

        Forwards order to risk manager for checking before execution.
        """
        try:
            content = message.content

            # Store pending order info
            order_id = f"order_{message.id}"
            self._pending_orders[order_id] = {
                "symbol": content.get("symbol"),
                "side": content.get("side"),
                "quantity": content.get("quantity"),
                "price": content.get("price"),
                "order_type": content.get("order_type", "limit"),
                "user_id": content.get("user_id", "system"),
                "original_message": message,
            }

            # Forward to risk manager
            if self._risk_manager_agent:
                await self.send_message(
                    MessageType.RISK_CHECK_REQUEST,
                    {
                        "order_id": order_id,
                        "symbol": content.get("symbol"),
                        "side": content.get("side"),
                        "quantity": content.get("quantity"),
                        "price": content.get("price"),
                        "user_id": content.get("user_id", "system"),
                        "capital": content.get("capital", 100000.0),
                        "current_positions": content.get("current_positions", 0.0),
                    },
                    recipient=self._risk_manager_agent,
                    correlation_id=order_id,
                )
            else:
                # No risk manager, execute directly
                await self._execute_order(order_id)

        except Exception as e:
            logger.error(f"{self.name}: Error handling order request - {e}")

    async def _on_risk_response(self, message: AgentMessage) -> None:
        """
        Handle risk check response

        Executes order if risk check passed.
        """
        try:
            content = message.content
            correlation_id = message.correlation_id

            if not correlation_id or correlation_id not in self._pending_orders:
                logger.warning(f"{self.name}: Unknown order correlation ID: {correlation_id}")
                return

            if content.get("passed", False):
                # Risk check passed, execute order
                await self._execute_order(correlation_id)
            else:
                # Risk check failed
                reason = content.get("reason", "Risk check failed")
                await self._send_order_failed(
                    correlation_id,
                    reason=f"Risk check rejected: {reason}"
                )

                # Remove from pending
                del self._pending_orders[correlation_id]

        except Exception as e:
            logger.error(f"{self.name}: Error handling risk response - {e}")

    async def _on_order_cancel(self, message: AgentMessage) -> None:
        """Handle order cancellation request"""
        try:
            order_id = message.content.get("order_id")

            if not order_id:
                return

            # Cancel via THSTrader
            result = self._trader.cancel_order(order_id)

            if result.success:
                await self.send_message(
                    MessageType.ORDER_CANCELLED,
                    {
                        "order_id": order_id,
                        "reason": "Order cancelled successfully",
                        "timestamp": result.timestamp.isoformat(),
                    },
                )

                logger.info(f"{self.name}: Order cancelled: {order_id}")
            else:
                logger.error(f"{self.name}: Failed to cancel order: {result.message}")

        except Exception as e:
            logger.error(f"{self.name}: Error cancelling order - {e}")

    async def _execute_order(self, order_id: str) -> None:
        """
        Execute an order

        Args:
            order_id: Internal order ID
        """
        if order_id not in self._pending_orders:
            logger.error(f"{self.name}: Order not found: {order_id}")
            return

        order_info = self._pending_orders[order_id]

        try:
            # Execute order via THSTrader
            if order_info["side"] == "buy":
                result = self._trader.buy(
                    code=order_info["symbol"],
                    price=order_info["price"],
                    quantity=order_info["quantity"],
                    order_type=OrderType(order_info["order_type"]),
                )
            elif order_info["side"] == "sell":
                result = self._trader.sell(
                    code=order_info["symbol"],
                    price=order_info["price"],
                    quantity=order_info["quantity"],
                    order_type=OrderType(order_info["order_type"]),
                )
            else:
                raise ValueError(f"Invalid order side: {order_info['side']}")

            # Send result message
            if result.success:
                await self.send_message(
                    MessageType.ORDER_FILLED,
                    {
                        "order_id": order_id,
                        "symbol": order_info["symbol"],
                        "side": order_info["side"],
                        "quantity": order_info["quantity"],
                        "price": order_info["price"],
                        "timestamp": result.timestamp.isoformat(),
                        "screenshot_path": result.screenshot_path,
                    },
                )

                logger.info(
                    f"{self.name}: Order filled - {order_info['side'].upper()} "
                    f"{order_info['quantity']} {order_info['symbol']} @ {order_info['price']}"
                )
            else:
                await self._send_order_failed(
                    order_id,
                    reason=result.message or "Order execution failed",
                )

        except Exception as e:
            logger.error(f"{self.name}: Error executing order - {e}")
            await self._send_order_failed(order_id, reason=str(e))

        finally:
            # Remove from pending
            if order_id in self._pending_orders:
                del self._pending_orders[order_id]

    async def _send_order_failed(self, order_id: str, reason: str) -> None:
        """Send order failed message"""
        order_info = self._pending_orders.get(order_id, {})

        await self.send_message(
            MessageType.ORDER_FAILED,
            {
                "order_id": order_id,
                "symbol": order_info.get("symbol", ""),
                "side": order_info.get("side", ""),
                "reason": reason,
            },
        )

        logger.warning(f"{self.name}: Order failed - {reason}")

    # Public API methods

    def is_connected(self) -> bool:
        """Check if connected to Tonghuashun"""
        return self._trader.window is not None

    def get_pending_orders(self) -> list:
        """Get list of pending orders"""
        return list(self._pending_orders.keys())
