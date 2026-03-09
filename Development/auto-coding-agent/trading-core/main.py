"""
StockAutoTrader - Python Trading Core
主程序入口
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger

from config import settings
from websocket.server import start_websocket_server
from strategies.engine import StrategyEngine
from market.fetcher import MarketDataFetcher
from risk import RiskController


async def main():
    """主程序入口"""
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

    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📝 Log level: {settings.LOG_LEVEL}")

    # 初始化核心模块
    risk_controller = RiskController()
    market_fetcher = MarketDataFetcher()
    strategy_engine = StrategyEngine(
        risk_controller=risk_controller,
        market_fetcher=market_fetcher
    )

    # 启动 WebSocket 服务器
    logger.info(f"🔌 Starting WebSocket server on {settings.WS_HOST}:{settings.WS_PORT}")
    ws_server = await start_websocket_server(
        strategy_engine=strategy_engine,
        market_fetcher=market_fetcher,
        risk_controller=risk_controller
    )

    # 启动策略引擎
    if settings.ENABLE_RISK_CONTROL:
        logger.info("✅ Risk control enabled")
    else:
        logger.warning("⚠️  Risk control DISABLED")

    logger.info("✅ System ready")
    logger.info("Press Ctrl+C to stop")

    try:
        # 保持运行
        await ws_server.wait_closed()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
        strategy_engine.stop()
        await ws_server.close()
        logger.info("✅ Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bye!")
