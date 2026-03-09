"""
WebSocket Server for real-time communication with frontend.

Handles:
- Market data streaming
- Trade status updates
- Strategy signals
- Alerts and notifications
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Set, Dict, List
import websockets
from websockets.server import WebSocketServerProtocol

from ..config.settings import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class MessageType(str, Enum):
    """WebSocket message types."""
    # Market data
    MARKET_QUOTE = "market_quote"
    MARKET_KLINE = "market_kline"

    # Trade updates
    TRADE_STATUS = "trade_status"
    ORDER_UPDATE = "order_update"
    POSITION_UPDATE = "position_update"
    TRADE_FILLED = "trade_filled"

    # Strategy signals
    STRATEGY_SIGNAL = "strategy_signal"
    STRATEGY_STATUS = "strategy_status"

    # Alerts
    ALERT_TRIGGERED = "alert_triggered"

    # System
    SYSTEM_STATUS = "system_status"
    ERROR = "error"
    PONG = "pong"


@dataclass
class WSMessage:
    """Base WebSocket message structure."""
    type: MessageType
    data: Dict[str, Any]
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps({
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp
        })


class WebSocketServer:
    """
    WebSocket server for real-time communication with frontend.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self._server = None
        self._running = False

    async def register(self, websocket: WebSocketServerProtocol) -> None:
        """Register a new client connection."""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")

        # Send welcome message
        await self.send_to_client(websocket, WSMessage(
            type=MessageType.SYSTEM_STATUS,
            data={"status": "connected", "message": "Connected to trading server"}
        ))

    async def unregister(self, websocket: WebSocketServerProtocol) -> None:
        """Unregister a client connection."""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

    async def send_to_client(self, websocket: WebSocketServerProtocol, message: WSMessage) -> bool:
        """Send a message to a specific client."""
        try:
            await websocket.send(message.to_json())
            return True
        except Exception as e:
            logger.error(f"Failed to send message to client: {e}")
            return False

    async def broadcast(self, message: WSMessage) -> None:
        """Broadcast a message to all connected clients."""
        if not self.clients:
            return

        # Send to all clients concurrently
        tasks = [self.send_to_client(client, message) for client in self.clients]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_market_quote(self, symbol: str, price: float, change: float,
                                     volume: int, high: float, low: float) -> None:
        """Broadcast market quote update."""
        message = WSMessage(
            type=MessageType.MARKET_QUOTE,
            data={
                "symbol": symbol,
                "price": price,
                "change": change,
                "change_percent": (change / (price - change) * 100) if price != change else 0,
                "volume": volume,
                "high": high,
                "low": low,
            }
        )
        await self.broadcast(message)

    async def broadcast_order_update(self, order_id: str, status: str, symbol: str,
                                     side: str, quantity: int, price: float,
                                     filled_quantity: int = 0) -> None:
        """Broadcast order status update."""
        message = WSMessage(
            type=MessageType.ORDER_UPDATE,
            data={
                "order_id": order_id,
                "status": status,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "filled_quantity": filled_quantity,
            }
        )
        await self.broadcast(message)

    async def broadcast_position_update(self, symbol: str, quantity: int,
                                        cost_price: float, current_price: float,
                                        profit_loss: float) -> None:
        """Broadcast position update."""
        message = WSMessage(
            type=MessageType.POSITION_UPDATE,
            data={
                "symbol": symbol,
                "quantity": quantity,
                "cost_price": cost_price,
                "current_price": current_price,
                "profit_loss": profit_loss,
                "profit_loss_percent": (profit_loss / (cost_price * quantity) * 100) if quantity > 0 else 0,
            }
        )
        await self.broadcast(message)

    async def broadcast_strategy_signal(self, strategy_id: str, strategy_name: str,
                                        symbol: str, signal_type: str, price: float,
                                        confidence: float) -> None:
        """Broadcast strategy signal."""
        message = WSMessage(
            type=MessageType.STRATEGY_SIGNAL,
            data={
                "strategy_id": strategy_id,
                "strategy_name": strategy_name,
                "symbol": symbol,
                "signal_type": signal_type,  # "BUY", "SELL", "HOLD"
                "price": price,
                "confidence": confidence,
            }
        )
        await self.broadcast(message)

    async def broadcast_alert(self, alert_id: str, symbol: str, alert_type: str,
                             message: str, triggered_at: str) -> None:
        """Broadcast alert trigger."""
        ws_message = WSMessage(
            type=MessageType.ALERT_TRIGGERED,
            data={
                "alert_id": alert_id,
                "symbol": symbol,
                "alert_type": alert_type,
                "message": message,
                "triggered_at": triggered_at,
            }
        )
        await self.broadcast(ws_message)

    async def handle_client_message(self, websocket: WebSocketServerProtocol,
                                    message: str) -> None:
        """Handle incoming message from client."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "ping":
                await self.send_to_client(websocket, WSMessage(
                    type=MessageType.PONG,
                    data={}
                ))
            elif msg_type == "subscribe":
                # Handle subscription requests
                symbols = data.get("symbols", [])
                await self.send_to_client(websocket, WSMessage(
                    type=MessageType.SYSTEM_STATUS,
                    data={"status": "subscribed", "symbols": symbols}
                ))
            else:
                logger.warning(f"Unknown message type: {msg_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from client: {message}")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")

    async def handler(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """Handle WebSocket connection."""
        await self.register(websocket)

        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed by client")
        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}")
        finally:
            await self.unregister(websocket)

    async def start(self) -> None:
        """Start the WebSocket server."""
        self._running = True
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")

        self._server = await websockets.serve(
            self.handler,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=20,
        )

        logger.info(f"WebSocket server running on ws://{self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        self._running = False

        # Close all client connections
        for client in self.clients:
            await client.close()

        self.clients.clear()

        if self._server:
            self._server.close()
            await self._server.wait_closed()

        logger.info("WebSocket server stopped")

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running

    @property
    def client_count(self) -> int:
        """Get number of connected clients."""
        return len(self.clients)


# Global server instance
_server_instance: Optional[WebSocketServer] = None


def get_server(host: str = "127.0.0.1", port: int = 8765) -> WebSocketServer:
    """Get or create the global WebSocket server instance."""
    global _server_instance
    if _server_instance is None:
        _server_instance = WebSocketServer(host, port)
    return _server_instance


async def start_server(host: str = "127.0.0.1", port: int = 8765) -> WebSocketServer:
    """Start the WebSocket server and return the instance."""
    server = get_server(host, port)
    await server.start()
    return server


async def stop_server() -> None:
    """Stop the WebSocket server."""
    global _server_instance
    if _server_instance:
        await _server_instance.stop()
        _server_instance = None
