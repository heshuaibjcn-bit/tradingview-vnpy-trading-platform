"""
Trade Recorder Agent

Wraps the TradeRecorder in an Agent interface, recording all trading
operations and signals to logs and database.
"""

import asyncio
from typing import Dict, Any, Optional, List
from loguru import logger

from .base import BaseAgent
from .messages import MessageType, AgentMessage
from trade_log.recorder import TradeRecorder, SignalRecorder


class TradeRecorderAgent(BaseAgent):
    """
    Agent wrapper for TradeRecorder and SignalRecorder

    Records all trading operations and signals.
    """

    def __init__(
        self,
        trade_recorder: TradeRecorder,
        signal_recorder: Optional[SignalRecorder] = None,
    ):
        """
        Initialize trade recorder agent

        Args:
            trade_recorder: TradeRecorder instance
            signal_recorder: Optional SignalRecorder instance
        """
        super().__init__(
            name="trade_recorder",
            version="1.0.0",
            description="Records all trading operations and signals",
        )

        self._trade_recorder = trade_recorder
        self._signal_recorder = signal_recorder

        # Subscribe to relevant message types
        self._subscriptions = [
            MessageType.ORDER_FILLED,
            MessageType.SIGNAL_GENERATED,
            MessageType.ORDER_FAILED,
            MessageType.SIGNAL_CANCELLED,
        ]

        # Register message handlers
        self.register_handler(MessageType.ORDER_FILLED, self._on_order_filled)
        self.register_handler(MessageType.SIGNAL_GENERATED, self._on_signal_generated)
        self.register_handler(MessageType.ORDER_FAILED, self._on_order_failed)
        self.register_handler(MessageType.SIGNAL_CANCELLED, self._on_signal_cancelled)

    async def on_start(self) -> None:
        """Called when agent starts"""
        # Subscribe to relevant message types
        for msg_type in self._subscriptions:
            self.subscribe(msg_type)

        logger.info(f"{self.name}: Started")

    async def on_stop(self) -> None:
        """Called when agent stops"""
        logger.info(f"{self.name}: Stopped")

    async def on_message(self, message: AgentMessage) -> None:
        """Called for every message (already handled by specific handlers)"""
        pass

    async def _on_order_filled(self, message: AgentMessage) -> None:
        """Handle order filled message"""
        try:
            content = message.content

            # Log the trade
            trade = self._trade_recorder.log_trade(
                user_id=content.get("user_id", "system"),
                symbol=content["symbol"],
                side=content["side"],
                quantity=content["quantity"],
                price=content["price"],
                order_id=content.get("order_id"),
                strategy_id=content.get("strategy_id"),
                signal_id=content.get("signal_id"),
                commission=content.get("commission", 0.0),
                metadata={
                    "timestamp": content.get("timestamp"),
                    "screenshot_path": content.get("screenshot_path"),
                },
            )

            logger.info(
                f"{self.name}: Trade recorded - {content['side'].upper()} "
                f"{content['quantity']} {content['symbol']} @ {content['price']}"
            )

        except Exception as e:
            logger.error(f"{self.name}: Error recording trade - {e}")

    async def _on_signal_generated(self, message: AgentMessage) -> None:
        """Handle signal generated message"""
        try:
            if not self._signal_recorder:
                return

            content = message.content

            # Log the signal
            signal = self._signal_recorder.log_signal(
                strategy_id=content.get("strategy_id", "unknown"),
                strategy_name=content.get("strategy_name", "unknown"),
                symbol=content["symbol"],
                signal_type=content["signal_type"],
                price=content["price"],
                confidence=content.get("confidence", 1.0),
                indicators=content.get("indicators", {}),
                metadata={
                    "quantity": content.get("quantity"),
                    "reason": content.get("reason", ""),
                },
            )

            logger.info(
                f"{self.name}: Signal recorded - {content['strategy_name']} "
                f"{content['signal_type'].upper()} {content['symbol']} @ {content['price']}"
            )

        except Exception as e:
            logger.error(f"{self.name}: Error recording signal - {e}")

    async def _on_order_failed(self, message: AgentMessage) -> None:
        """Handle order failed message"""
        try:
            content = message.content

            # Log as operation
            self._trade_recorder.log_operation(
                operation_type="ORDER_FAILED",
                message=f"Order failed: {content.get('reason', 'Unknown')}",
                user_id=content.get("user_id", "system"),
                symbol=content.get("symbol"),
                success=False,
                error=content.get("reason"),
                details=content,
            )

            logger.warning(
                f"{self.name}: Failed order recorded - {content.get('symbol')} - "
                f"{content.get('reason', 'Unknown')}"
            )

        except Exception as e:
            logger.error(f"{self.name}: Error recording failed order - {e}")

    async def _on_signal_cancelled(self, message: AgentMessage) -> None:
        """Handle signal cancelled message"""
        try:
            if not self._signal_recorder:
                return

            signal_id = message.content.get("signal_id")

            if signal_id:
                self._signal_recorder.mark_executed(signal_id)

                logger.info(f"{self.name}: Signal marked cancelled - {signal_id}")

        except Exception as e:
            logger.error(f"{self.name}: Error cancelling signal - {e}")

    # Public API methods

    def log_trade(
        self,
        user_id: str,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        **kwargs
    ):
        """Log a trade"""
        return self._trade_recorder.log_trade(
            user_id=user_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            **kwargs
        )

    def log_signal(
        self,
        strategy_id: str,
        strategy_name: str,
        symbol: str,
        signal_type: str,
        price: float,
        **kwargs
    ):
        """Log a signal"""
        if not self._signal_recorder:
            return None

        return self._signal_recorder.log_signal(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            symbol=symbol,
            signal_type=signal_type,
            price=price,
            **kwargs
        )

    def get_trades(
        self,
        user_id: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 100,
    ) -> List:
        """Get trades with optional filters"""
        return self._trade_recorder.get_trades(
            user_id=user_id,
            symbol=symbol,
            limit=limit,
        )

    def get_signals(
        self,
        strategy_id: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 100,
    ) -> List:
        """Get signals with optional filters"""
        if not self._signal_recorder:
            return []

        return self._signal_recorder.get_signals(
            strategy_id=strategy_id,
            symbol=symbol,
            limit=limit,
        )
