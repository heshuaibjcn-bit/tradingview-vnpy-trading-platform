"""
Strategy Agent

Wraps the StrategyEngine in an Agent interface, enabling it to participate
in the message-based architecture.
"""

import asyncio
from typing import Dict, Any, Optional, List
from loguru import logger

from .base import BaseAgent
from .messages import MessageType, AgentMessage, create_signal_generated
from strategies.engine import StrategyEngine
from strategies.base import Signal as StrategySignal


class StrategyAgent(BaseAgent):
    """
    Agent wrapper for StrategyEngine

    Subscribes to market data updates and generates trading signals.
    """

    def __init__(
        self,
        strategy_engine: StrategyEngine,
        market_data_agent: str = "market_fetcher",
    ):
        """
        Initialize strategy agent

        Args:
            strategy_engine: StrategyEngine instance to wrap
            market_data_agent: Name of the market data agent
        """
        super().__init__(
            name="strategy_engine",
            version="1.0.0",
            description="Executes trading strategies and generates signals",
            dependencies=[market_data_agent] if market_data_agent else [],
        )

        self._engine = strategy_engine
        self._market_data_agent = market_data_agent

        # Market data cache for strategies
        self._market_data: Dict[str, Dict[str, Any]] = {}

        # Register message handlers
        self.register_handler(MessageType.MARKET_DATA_UPDATE, self._on_market_data)
        self.register_handler(MessageType.STRATEGY_START, self._on_strategy_start)
        self.register_handler(MessageType.STRATEGY_STOP, self._on_strategy_stop)
        self.register_handler(MessageType.KLINE_RESPONSE, self._on_kline_data)

        # Background task for periodic execution
        self._execution_task: Optional[asyncio.Task] = None

    async def on_start(self) -> None:
        """Called when agent starts"""
        # Subscribe to market data updates
        if self._market_data_agent:
            self.subscribe(MessageType.MARKET_DATA_UPDATE)

        # Register signal listener to dispatch signals as messages
        self._engine.add_signal_listener(self._on_strategy_signal)

        logger.info(
            f"{self.name}: Started with {len(self._engine.list_strategies())} strategies"
        )

    async def on_stop(self) -> None:
        """Called when agent stops"""
        # Stop background task
        if self._execution_task:
            self._execution_task.cancel()
            try:
                await self._execution_task
            except asyncio.CancelledError:
                pass

        # Stop the engine if it's running
        if self._engine._is_running:
            await self._engine.stop()

        logger.info(f"{self.name}: Stopped")

    async def on_message(self, message: AgentMessage) -> None:
        """Called for every message (already handled by specific handlers)"""
        pass  # All messages are handled by specific handlers

    async def _on_market_data(self, message: AgentMessage) -> None:
        """
        Handle market data update

        Stores market data for use by strategies and triggers
        strategy execution if engine is running.
        """
        try:
            content = message.content
            symbol = content.get("symbol")

            if not symbol:
                return

            # Store market data
            self._market_data[symbol] = {
                "price": content.get("price"),
                "volume": content.get("volume", 0),
                "change": content.get("change", 0.0),
                "change_percent": content.get("change_percent", 0.0),
                "timestamp": message.timestamp,
            }

            # If engine is running, execute strategies
            if self._engine._is_running:
                await self._execute_strategies_for_symbol(symbol)

        except Exception as e:
            logger.error(f"{self.name}: Error handling market data - {e}")

    async def _on_strategy_start(self, message: AgentMessage) -> None:
        """Handle strategy start request"""
        try:
            strategy_name = message.content.get("strategy_name")
            parameters = message.content.get("parameters", {})

            if strategy_name:
                # Start specific strategy
                strategy = self._engine.get_strategy(strategy_name)
                if strategy:
                    strategy.is_enabled = True
                    logger.info(f"{self.name}: Strategy enabled: {strategy_name}")

                    # Update parameters if provided
                    if parameters:
                        for key, value in parameters.items():
                            setattr(strategy, key, value)
            else:
                # Start all strategies
                await self._engine.start()
                logger.info(f"{self.name}: Strategy engine started")

        except Exception as e:
            logger.error(f"{self.name}: Error starting strategy - {e}")

    async def _on_strategy_stop(self, message: AgentMessage) -> None:
        """Handle strategy stop request"""
        try:
            strategy_name = message.content.get("strategy_name")

            if strategy_name:
                # Stop specific strategy
                strategy = self._engine.get_strategy(strategy_name)
                if strategy:
                    strategy.is_enabled = False
                    logger.info(f"{self.name}: Strategy disabled: {strategy_name}")
            else:
                # Stop all strategies
                await self._engine.stop()
                logger.info(f"{self.name}: Strategy engine stopped")

        except Exception as e:
            logger.error(f"{self.name}: Error stopping strategy - {e}")

    async def _on_kline_data(self, message: AgentMessage) -> None:
        """Handle K-line data response"""
        try:
            kline_data = message.content.get("kline_data", [])
            # Store or process K-line data as needed
            # This could be used for technical indicators that need historical data
            logger.debug(f"{self.name}: Received {len(kline_data)} K-line data points")

        except Exception as e:
            logger.error(f"{self.name}: Error handling K-line data - {e}")

    def _on_strategy_signal(self, signal: StrategySignal) -> None:
        """
        Handle signal generated by strategy

        Called by the strategy engine's signal listener mechanism.
        """
        try:
            # Convert strategy signal to agent message
            message = create_signal_generated(
                sender=self.name,
                symbol=signal.symbol,
                signal_type=signal.signal_type.value,
                price=signal.price,
                strategy_name=signal.strategy_name,
                confidence=signal.confidence or 1.0,
                quantity=signal.quantity,
                reason=signal.reason or "",
            )

            # Publish signal message
            asyncio.create_task(self.send_message(
                MessageType.SIGNAL_GENERATED,
                message.content,
            ))

            logger.info(
                f"{self.name}: Signal generated - {signal.strategy_name} "
                f"{signal.signal_type.value} {signal.symbol} @ {signal.price}"
            )

        except Exception as e:
            logger.error(f"{self.name}: Error dispatching signal - {e}")

    async def _execute_strategies_for_symbol(self, symbol: str) -> None:
        """Execute all strategies for a specific symbol"""
        try:
            # Get market data for this symbol
            if symbol not in self._market_data:
                return

            # Execute all enabled strategies
            results = await self._engine.execute_all_strategies()

            # Results are handled by the signal listener (_on_strategy_signal)

        except Exception as e:
            logger.error(f"{self.name}: Error executing strategies for {symbol} - {e}")

    async def request_kline_data(
        self,
        symbol: str,
        period: str = "101",
        count: int = 100,
    ) -> None:
        """
        Request K-line data for a symbol

        Args:
            symbol: Stock symbol
            period: K-line period
            count: Number of data points
        """
        if self._market_data_agent:
            await self.send_message(
                MessageType.KLINE_REQUEST,
                {
                    "symbol": symbol,
                    "period": period,
                    "count": count,
                },
                recipient=self._market_data_agent,
            )

    # Public API methods

    def add_strategy(self, strategy) -> None:
        """Add a strategy to the engine"""
        self._engine.add_strategy(strategy)

    def remove_strategy(self, name: str) -> bool:
        """Remove a strategy from the engine"""
        return self._engine.remove_strategy(name)

    def get_strategy(self, name: str):
        """Get a strategy by name"""
        return self._engine.get_strategy(name)

    def list_strategies(self) -> List[str]:
        """Get list of strategy names"""
        return self._engine.list_strategies()

    async def start_strategies(self, interval: float = 5.0) -> None:
        """Start the strategy engine"""
        await self._engine.start(interval)

    async def stop_strategies(self) -> None:
        """Stop the strategy engine"""
        await self._engine.stop()
