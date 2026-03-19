"""
StockAutoTrader - REST API Server
提供HTTP API接口给前端调用
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

from config.settings import get_settings
from market.fetcher import (
    MarketDataFetcher,
    MarketDataSource,
    RealtimeQuote,
    OHLCV,
)
from utils.logger import logger


settings = get_settings()


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting API Server")

    # Initialize market data fetcher
    market_fetcher = MarketDataFetcher(
        primary_source=MarketDataSource.EASTMONEY,
        fallback_sources=[MarketDataSource.SINA]
    )

    # Store in app state
    app.state.market_fetcher = market_fetcher

    # Import and include agents API if agent architecture is enabled
    if settings.USE_AGENT_ARCHITECTURE:
        try:
            from api.agents import router as agents_router, set_agency
            from api.messages import router as messages_router
            from api.performance import router as performance_router
            from api.strategies import router as strategies_router
            from api.config import router as config_router
            from api.dynamic_agents import router as dynamic_agents_router
            from agents import TradingAgency

            # Create agency instance (will be initialized by main.py)
            # For API access, we'll set it later
            app.include_router(agents_router)
            app.include_router(messages_router)
            app.include_router(performance_router)
            app.include_router(strategies_router)
            app.include_router(config_router)
            app.include_router(dynamic_agents_router)
            logger.info("✅ Agent management API enabled")
            logger.info("✅ Message management API enabled")
            logger.info("✅ Performance monitoring API enabled")
            logger.info("✅ Strategy hot reload API enabled")
            logger.info("✅ Config hot reload API enabled")
            logger.info("✅ Dynamic agents API enabled")
        except ImportError as e:
            logger.warning(f"Could not import agents API: {e}")

    logger.info("✅ API Server ready")

    yield

    logger.info("🛑 Shutting down API Server")


# Create FastAPI app
app = FastAPI(
    title="StockAutoTrader API",
    description="Automated Stock Trading System API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "file://",  # For opening HTML file directly
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Response models
class QuoteResponse(BaseModel):
    """Realtime quote response"""
    symbol: str
    name: str = ""
    price: float
    change: float
    change_percent: float
    open: float
    high: float
    low: float
    volume: int
    amount: float
    bid_price: float
    ask_price: float
    timestamp: str


class KlineResponse(BaseModel):
    """K-line data response"""
    symbol: str
    period: str
    data: List[dict]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    data_source: str


# API Endpoints
@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        data_source="realtime"
    )


@app.get("/api/quote", response_model=QuoteResponse)
async def get_quote(
    symbol: str = Query(..., description="Stock code (e.g., 600000, 000001)")
):
    """
    Get realtime quote for a stock

    Args:
        symbol: Stock code without market prefix

    Returns:
        RealtimeQuote data
    """
    try:
        fetcher: MarketDataFetcher = app.state.market_fetcher
        quote = await fetcher.get_realtime_quote(symbol)

        if not quote:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to fetch quote for symbol: {symbol}"
            )

        return QuoteResponse(
            symbol=quote.symbol,
            name=quote.name,
            price=quote.price,
            change=quote.change,
            change_percent=quote.change_percent,
            open=quote.open,
            high=quote.high,
            low=quote.low,
            volume=quote.volume,
            amount=quote.amount,
            bid_price=quote.bid_price,
            ask_price=quote.ask_price,
            timestamp=quote.timestamp.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quote: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/kline", response_model=KlineResponse)
async def get_kline(
    symbol: str = Query(..., description="Stock code"),
    period: str = Query("101", description="Period code (101=daily, 5=1min, 15=5min, etc.)"),
    count: int = Query(100, description="Number of data points", ge=1, le=1000)
):
    """
    Get K-line data for a stock

    Args:
        symbol: Stock code
        period: Period code (101=daily, 102=week, 103=month, 5=1min, 15=5min, 30=30min, 60=60min)
        count: Number of data points to return

    Returns:
        List of OHLCV data
    """
    try:
        fetcher: MarketDataFetcher = app.state.market_fetcher
        ohlcv_list = await fetcher.get_kline(symbol, period, count)

        if not ohlcv_list:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to fetch K-line data for symbol: {symbol}"
            )

        # Convert to dict format
        data = [
            {
                "timestamp": ohlcv.timestamp.isoformat(),
                "open": ohlcv.open,
                "high": ohlcv.high,
                "low": ohlcv.low,
                "close": ohlcv.close,
                "volume": ohlcv.volume,
                "amount": ohlcv.amount
            }
            for ohlcv in ohlcv_list
        ]

        return KlineResponse(
            symbol=symbol,
            period=period,
            data=data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching K-line: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/quotes/batch", response_model=List[QuoteResponse])
async def get_batch_quotes(
    symbols: str = Query(..., description="Comma-separated stock codes")
):
    """
    Get realtime quotes for multiple stocks

    Args:
        symbols: Comma-separated stock codes (e.g., "600000,000001,000002")

    Returns:
        List of RealtimeQuote data
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(",")]
        fetcher: MarketDataFetcher = app.state.market_fetcher

        # Fetch quotes concurrently
        quotes_dict = await fetcher.get_batch_quotes(symbol_list)

        # Filter out None values and convert to response format
        responses = []
        for symbol, quote in quotes_dict.items():
            if quote:
                responses.append(QuoteResponse(
                    symbol=quote.symbol,
                    name=quote.name,
                    price=quote.price,
                    change=quote.change,
                    change_percent=quote.change_percent,
                    open=quote.open,
                    high=quote.high,
                    low=quote.low,
                    volume=quote.volume,
                    amount=quote.amount,
                    bid_price=quote.bid_price,
                    ask_price=quote.ask_price,
                    timestamp=quote.timestamp.isoformat()
                ))

        return responses

    except Exception as e:
        logger.error(f"Error fetching batch quotes: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/sources")
async def get_data_sources():
    """Get available market data sources"""
    return {
        "sources": [
            {
                "id": "eastmoney",
                "name": "东方财富",
                "description": "EastMoney Market Data",
                "enabled": True
            },
            {
                "id": "sina",
                "name": "新浪财经",
                "description": "Sina Finance Market Data",
                "enabled": True
            }
        ],
        "primary": "eastmoney",
        "fallback": ["sina"]
    }


@app.get("/api/agent-architecture")
async def get_agent_architecture_info():
    """Get agent architecture information"""
    return {
        "enabled": settings.USE_AGENT_ARCHITECTURE,
        "message_db_path": settings.AGENT_MESSAGE_DB_PATH,
        "health_check_interval": settings.AGENT_HEALTH_CHECK_INTERVAL,
        "message_retention_days": settings.AGENT_MESSAGE_RETENTION_DAYS,
        "message_history_size": settings.AGENT_MESSAGE_HISTORY_SIZE,
        "persistence_enabled": settings.AGENT_ENABLE_PERSISTENCE,
        "timestamp": datetime.now().isoformat()
    }


def main():
    """Run the API server"""
    import uvicorn

    logger.info(f"🚀 Starting {settings.app_name} API Server")

    uvicorn.run(
        "api_server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
