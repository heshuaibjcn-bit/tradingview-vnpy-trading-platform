"""
Market Data Agent

Wraps the MarketDataFetcher in an Agent interface, providing market data
to other agents through the message bus.
"""

import asyncio
from typing import Dict, Any, Optional, List
from loguru import logger

from .base import BaseAgent
from .messages import MessageType, AgentMessage, create_market_data_update
from market.fetcher import MarketDataFetcher, RealtimeQuote


class MarketDataAgent(BaseAgent):
    """
    Agent wrapper for MarketDataFetcher

    Fetches and distributes market data to other agents.
    """

    def __init__(
        self,
        fetcher: MarketDataFetcher,
        update_interval: float = 1.0,
        symbols: Optional[List[str]] = None,
    ):
        """
        Initialize market data agent

        Args:
            fetcher: MarketDataFetcher instance to wrap
            update_interval: Seconds between market data updates
            symbols: List of symbols to track (None for all)
        """
        super().__init__(
            name="market_fetcher",
            version="1.0.0",
            description="Fetches and distributes market data",
        )

        self._fetcher = fetcher
        self._update_interval = update_interval
        self._symbols = symbols or []

        # Background update task
        self._update_task: Optional[asyncio.Task] = None

        # Last known prices (for calculating change)
        self._last_prices: Dict[str, float] = {}

        # Register message handlers
        self.register_handler(MessageType.MARKET_DATA_REQUEST, self._on_data_request)
        self.register_handler(MessageType.KLINE_REQUEST, self._on_kline_request)

    async def on_start(self) -> None:
        """Called when agent starts"""
        # Start background update task
        self._update_task = asyncio.create_task(self._update_loop())

        logger.info(
            f"{self.name}: Started "
            f"(update_interval={self._update_interval}s, "
            f"symbols={len(self._symbols) if self._symbols else 'all'})"
        )

    async def on_stop(self) -> None:
        """Called when agent stops"""
        # Stop background task
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

        logger.info(f"{self.name}: Stopped")

    async def on_message(self, message: AgentMessage) -> None:
        """Called for every message (already handled by specific handlers)"""
        pass

    async def _update_loop(self) -> None:
        """Background task to periodically fetch and broadcast market data"""
        while True:
            try:
                if self._symbols:
                    # Fetch specific symbols
                    await self._update_symbols(self._symbols)
                else:
                    # No specific symbols, just handle requests
                    pass

                await asyncio.sleep(self._update_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{self.name}: Error in update loop - {e}")
                await asyncio.sleep(self._update_interval)

    async def _update_symbols(self, symbols: List[str]) -> None:
        """
        Fetch and broadcast market data for symbols

        Args:
            symbols: List of stock symbols
        """
        try:
            # Fetch batch quotes
            quotes = await self._fetcher.get_batch_quotes(symbols)

            # Broadcast each quote
            for symbol, quote in quotes.items():
                if quote:
                    await self._broadcast_quote(quote)

        except Exception as e:
            logger.error(f"{self.name}: Error updating symbols - {e}")

    async def _broadcast_quote(self, quote: RealtimeQuote) -> None:
        """
        Broadcast a market data update

        Args:
            quote: RealtimeQuote to broadcast
        """
        try:
            # Calculate change if we have previous price
            previous_price = self._last_prices.get(quote.symbol)
            if previous_price is None:
                previous_price = quote.price - quote.change

            # Store current price for next time
            self._last_prices[quote.symbol] = quote.price

            # Create and send message
            message = create_market_data_update(
                sender=self.name,
                symbol=quote.symbol,
                price=quote.price,
                volume=quote.volume,
                change=quote.change,
                change_percent=quote.change_percent,
            )

            await self.send_message(
                MessageType.MARKET_DATA_UPDATE,
                message.content,
            )

            logger.debug(
                f"{self.name}: Market data update - {quote.symbol} = {quote.price}"
            )

        except Exception as e:
            logger.error(f"{self.name}: Error broadcasting quote - {e}")

    async def _on_data_request(self, message: AgentMessage) -> None:
        """
        Handle market data request

        Fetches and sends market data for requested symbols.
        """
        try:
            content = message.content
            symbols = content.get("symbols", [])

            if not symbols:
                symbol = content.get("symbol")
                if symbol:
                    symbols = [symbol]

            if not symbols:
                logger.warning(f"{self.name}: No symbols in request")
                return

            # Fetch quotes
            quotes = await self._fetcher.get_batch_quotes(symbols)

            # Send each quote as a response
            for symbol, quote in quotes.items():
                if quote:
                    await self._broadcast_quote(quote)

                    # If this was a direct request, also send to specific recipient
                    if message.recipient == self.name:
                        await self.send_message(
                            MessageType.MARKET_DATA_UPDATE,
                            {
                                "symbol": quote.symbol,
                                "price": quote.price,
                                "volume": quote.volume,
                                "change": quote.change,
                                "change_percent": quote.change_percent,
                            },
                            recipient=message.sender,
                        )

        except Exception as e:
            logger.error(f"{self.name}: Error handling data request - {e}")

    async def _on_kline_request(self, message: AgentMessage) -> None:
        """
        Handle K-line data request

        Fetches historical K-line data and sends it as a response.
        """
        try:
            content = message.content
            symbol = content.get("symbol")
            period = content.get("period", "101")
            count = content.get("count", 100)

            if not symbol:
                logger.warning(f"{self.name}: No symbol in K-line request")
                return

            # Fetch K-line data
            kline_data = await self._fetcher.get_kline(symbol, period, count)

            # Convert to list of dicts
            kline_list = [
                {
                    "symbol": k.symbol,
                    "timestamp": k.timestamp.isoformat(),
                    "open": k.open,
                    "high": k.high,
                    "low": k.low,
                    "close": k.close,
                    "volume": k.volume,
                    "amount": k.amount,
                }
                for k in kline_data
            ]

            # Send response
            await self.send_message(
                MessageType.KLINE_RESPONSE,
                {
                    "symbol": symbol,
                    "period": period,
                    "kline_data": kline_list,
                },
                recipient=message.sender,
                correlation_id=message.correlation_id,
            )

            logger.info(
                f"{self.name}: Sent {len(kline_list)} K-line data points for {symbol}"
            )

        except Exception as e:
            logger.error(f"{self.name}: Error handling K-line request - {e}")

    # Public API methods

    async def get_quote(self, symbol: str) -> Optional[RealtimeQuote]:
        """
        Get current quote for a symbol

        Args:
            symbol: Stock symbol

        Returns:
            RealtimeQuote or None
        """
        return await self._fetcher.get_realtime_quote(symbol)

    async def get_kline(
        self,
        symbol: str,
        period: str = "101",
        count: int = 100,
    ) -> List:
        """
        Get K-line data for a symbol

        Args:
            symbol: Stock symbol
            period: K-line period
            count: Number of data points

        Returns:
            List of OHLCV data
        """
        return await self._fetcher.get_kline(symbol, period, count)

    def add_symbol(self, symbol: str) -> None:
        """Add a symbol to track"""
        if symbol not in self._symbols:
            self._symbols.append(symbol)
            logger.info(f"{self.name}: Now tracking {symbol}")

    def remove_symbol(self, symbol: str) -> None:
        """Remove a symbol from tracking"""
        if symbol in self._symbols:
            self._symbols.remove(symbol)
            logger.info(f"{self.name}: Stopped tracking {symbol}")

    def set_symbols(self, symbols: List[str]) -> None:
        """Set the list of symbols to track"""
        self._symbols = symbols.copy()
        logger.info(f"{self.name}: Now tracking {len(symbols)} symbols")

    def clear_cache(self) -> None:
        """Clear the fetcher's quote cache"""
        self._fetcher.clear_cache()
        logger.info(f"{self.name}: Quote cache cleared")
