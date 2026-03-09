"""
StockAutoTrader - Python Trading Core
主程序入口
"""

import asyncio
import sys
import signal
from pathlib import Path
from loguru import logger

from config.settings import get_settings
from websocket import start_server, stop_server, get_server
from strategies.engine import StrategyEngine
from market.fetcher import MarketDataFetcher


# Global flag for shutdown
_shutdown_event = asyncio.Event()


def handle_shutdown(signum, frame):
    """Handle shutdown signal."""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    _shutdown_event.set()


async def main():
    """主程序入口"""
    settings = get_settings()

    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )
    logger.add(
        settings.log_path,
        level=settings.LOG_LEVEL,
        rotation="1 day",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
    )

    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"📝 Log level: {settings.LOG_LEVEL}")

    # 初始化核心模块
    market_fetcher = MarketDataFetcher()

    # 启动 WebSocket 服务器
    logger.info(f"🔌 Starting WebSocket server on {settings.ws_host}:{settings.ws_port}")
    ws_server = await start_server(
        host=settings.ws_host,
        port=settings.ws_port
    )

    # 初始化策略引擎
    strategy_engine = StrategyEngine(market_fetcher=market_fetcher)

    # 注册信号监听器
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, handle_shutdown)

    logger.info("✅ System ready")
    logger.info(f"✅ WebSocket server running on ws://{settings.ws_host}:{settings.ws_port}")
    logger.info("Press Ctrl+C to stop")

    # 启动策略引擎
    strategy_engine.start()

    try:
        # 等待关闭信号
        await _shutdown_event.wait()
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("🛑 Shutting down...")
        strategy_engine.stop()
        await stop_server()
        logger.info("✅ Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bye!")
