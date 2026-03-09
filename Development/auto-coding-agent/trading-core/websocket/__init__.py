"""
WebSocket module for real-time communication.

Exports:
- WebSocketServer: Main server class
- MessageType: Message type enum
- WSMessage: Message dataclass
- get_server: Get/create server instance
- start_server: Start the server
- stop_server: Stop the server
"""

from .server import (
    WebSocketServer,
    MessageType,
    WSMessage,
    get_server,
    start_server,
    stop_server,
)

__all__ = [
    "WebSocketServer",
    "MessageType",
    "WSMessage",
    "get_server",
    "start_server",
    "stop_server",
]
