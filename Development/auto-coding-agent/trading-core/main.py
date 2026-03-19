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

# Import based on architecture flag
if get_settings().USE_AGENT_ARCHITECTURE:
    # New Agent-based architecture
    from agents import TradingAgency
    from agents.strategy_agent import StrategyAgent
    from agents.market_agent import MarketDataAgent
    from agents.trader_agent import THSTraderAgent
    from agents.risk_agent import RiskManagerAgent
    from agents.monitor_agent import SystemMonitorAgent
    from agents.alert_agent import AlertEngineAgent
    from agents.recorder_agent import TradeRecorderAgent
    from agents.audit_agent import AuditLoggerAgent

    # Original components
    from strategies.engine import StrategyEngine
    from market.fetcher import MarketDataFetcher
    from automation.trader import THSTrader
    from risk.manager import RiskManager
    from monitoring.monitor import get_global_monitor
    from alerts.engine import AlertEngine
    from trade_log.recorder import TradeRecorder, SignalRecorder
    from security.audit import get_audit_logger

    # Performance monitoring
    from monitoring.metrics import init_metrics_collector
    from monitoring.alerts import AlertEngine as PerfAlertEngine
    from monitoring.reports import ReportGenerator
else:
    # Legacy architecture
    from strategies.engine import StrategyEngine
    from market.fetcher import MarketDataFetcher


# Global flag for shutdown
_shutdown_event = asyncio.Event()


def handle_shutdown(signum, frame):
    """Handle shutdown signal."""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    _shutdown_event.set()


async def main_legacy():
    """Legacy main entry point (pre-Agent architecture)"""
    settings = get_settings()

    # 初始化核心模块
    market_fetcher = MarketDataFetcher()

    # 启动 WebSocket 服务器
    logger.info(f"🔌 Starting WebSocket server on {settings.WS_HOST}:{settings.WS_PORT}")
    ws_server = await start_server(
        host=settings.WS_HOST,
        port=settings.WS_PORT
    )

    # 初始化策略引擎
    strategy_engine = StrategyEngine(market_fetcher=market_fetcher)

    logger.info("✅ System ready (legacy mode)")
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


async def main_agent_architecture():
    """New Agent-based architecture main entry point"""
    settings = get_settings()

    logger.info("🏗️  Using Agent Architecture")

    # Initialize original components
    market_fetcher = MarketDataFetcher()
    strategy_engine = StrategyEngine()
    ths_trader = THSTrader()
    risk_manager = RiskManager()
    system_monitor = get_global_monitor()
    alert_engine = AlertEngine()
    trade_recorder = TradeRecorder()
    signal_recorder = SignalRecorder()
    audit_logger = get_audit_logger()

    # Create the agency
    agency = TradingAgency(
        enable_persistence=settings.AGENT_ENABLE_PERSISTENCE,
        db_path=settings.AGENT_MESSAGE_DB_PATH,
        health_check_interval=settings.AGENT_HEALTH_CHECK_INTERVAL,
        message_history_size=settings.AGENT_MESSAGE_HISTORY_SIZE,
        enable_batch_processing=settings.ENABLE_BATCH_PROCESSING,
        batch_max_size=settings.BATCH_MAX_SIZE,
        batch_max_wait_time=settings.BATCH_MAX_WAIT_TIME,
    )

    # Initialize performance monitoring
    metrics_collector = init_metrics_collector(
        collection_interval=10.0,
        retention_hours=24,
    )

    # Load persisted metrics
    metrics_collector.load_persisted_metrics()

    # Register gauges with metrics collector
    def get_message_count():
        status = agency.get_status()
        return status.get("message_bus", {}).get("messages_sent", 0)

    def get_active_agents():
        status = agency.get_status()
        agents = status.get("agents", {})
        return agents.get("running", 0)

    def get_healthy_agents():
        health = agency.get_health_summary()
        return health.get("healthy", 0)

    def get_unhealthy_agents():
        health = agency.get_health_summary()
        return health.get("unhealthy", 0)

    def get_total_messages():
        status = agency.get_status()
        return status.get("message_bus", {}).get("messages_sent", 0)

    metrics_collector.register_gauge('message_count', get_message_count)
    metrics_collector.register_gauge('active_agents', get_active_agents)
    metrics_collector.register_gauge('healthy_agents', get_healthy_agents)
    metrics_collector.register_gauge('unhealthy_agents', get_unhealthy_agents)
    metrics_collector.register_gauge('total_messages', get_total_messages)

    # Create alert engine
    from monitoring.alerts import AlertEngine as PerfAlertEngine
    perf_alert_engine = PerfAlertEngine(metrics_collector)

    # Set global instances for API access
    import api.performance
    api.performance.get_metrics_collector = lambda: metrics_collector
    api.performance.get_alert_engine = lambda: perf_alert_engine

    # Start metrics collection
    await metrics_collector.start()

    logger.info("✅ Performance monitoring initialized")

    # Create and register agents
    agency.register_agent(MarketDataAgent(
        fetcher=market_fetcher,
        update_interval=1.0,
        symbols=["000001", "000002", "600000"],  # Default symbols to track
    ))

    agency.register_agent(StrategyAgent(
        strategy_engine=strategy_engine,
        market_data_agent="market_fetcher",
    ))

    agency.register_agent(THSTraderAgent(
        trader=ths_trader,
        risk_manager_agent="risk_manager",
    ))

    agency.register_agent(RiskManagerAgent(
        risk_manager=risk_manager,
    ))

    agency.register_agent(SystemMonitorAgent(
        system_monitor=system_monitor,
        monitor_interval=settings.AGENT_HEALTH_CHECK_INTERVAL,
    ))

    agency.register_agent(AlertEngineAgent(
        alert_engine=alert_engine,
    ))

    agency.register_agent(TradeRecorderAgent(
        trade_recorder=trade_recorder,
        signal_recorder=signal_recorder,
    ))

    agency.register_agent(AuditLoggerAgent(
        audit_logger=audit_logger,
    ))

    # 启动 API 服务器 (in background)
    logger.info(f"🌐 Starting API server on http://127.0.0.1:8000")
    import uvicorn
    api_config = uvicorn.Config(
        app="api_server:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        access_log=False
    )
    api_server = uvicorn.Server(api_config)

    # 启动 API 服务器任务
    api_task = asyncio.create_task(api_server.serve())

    # Import agents API and set agency reference
    try:
        from api.agents import set_agency
        set_agency(agency)
        logger.info("✅ Agency reference set for API")
    except ImportError as e:
        logger.warning(f"Could not set agency reference: {e}")

    # 启动 WebSocket 服务器
    logger.info(f"🔌 Starting WebSocket server on {settings.WS_HOST}:{settings.WS_PORT}")
    ws_server = await start_server(
        host=settings.WS_HOST,
        port=settings.WS_PORT
    )

    # Connect agency to WebSocket server for agent status updates
    ws_server.set_agency(agency)

    # Now set up alert engine with agency running
    from monitoring.alerts import AlertEngine as PerfAlertEngine
    alert_engine = PerfAlertEngine(metrics_collector)
    api.performance.get_alert_engine = lambda: alert_engine

    logger.info("✅ System ready (agent architecture)")
    logger.info(f"✅ WebSocket server running on ws://{settings.WS_HOST}:{settings.WS_PORT}")
    logger.info(f"✅ API server running on http://127.0.0.1:8000")
    logger.info(f"✅ Registered {len(agency.list_agents())} agents")
    logger.info(f"✅ Dashboard: open dashboard/index.html or run ./start-dashboard.sh")
    logger.info("Press Ctrl+C to stop")

    # Start the agency
    await agency.start()

    try:
        # 等待关闭信号
        await _shutdown_event.wait()
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("🛑 Shutting down...")
        await agency.stop()

        # Stop performance monitoring
        if 'metrics_collector' in locals():
            await metrics_collector.stop()

        await stop_server()

        # Stop API server
        api_task.cancel()
        try:
            await api_task
        except asyncio.CancelledError:
            pass

        logger.info("✅ Shutdown complete")


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

    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📝 Log level: {settings.LOG_LEVEL}")

    # 注册信号监听器
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, handle_shutdown)

    # Choose architecture based on settings
    if settings.USE_AGENT_ARCHITECTURE:
        await main_agent_architecture()
    else:
        await main_legacy()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bye!")
