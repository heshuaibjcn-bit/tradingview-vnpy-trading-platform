"""
FastAPI Energy Storage Investment Decision System - Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.api.investment import router as investment_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting up...")
    print(f"📍 Debug mode: {settings.DEBUG}")
    print(f"🌐 API will be available at: http://{settings.HOST}:{settings.PORT}{settings.API_PREFIX}")
    yield
    # Shutdown
    print("👋 Shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API for energy storage investment decision analysis",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(investment_router, prefix=settings.API_PREFIX)


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint - API information
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Energy Storage Investment Decision API",
        "docs_url": "/docs",
        "api_prefix": settings.API_PREFIX,
        "endpoints": {
            "investment": {
                "calculate": "POST /api/v1/investment/calculate",
                "generate_report": "POST /api/v1/investment/report/generate",
                "download_report": "GET /api/v1/investment/report/download/{filename}",
                "scenarios": "GET /api/v1/investment/scenarios",
                "health": "GET /api/v1/investment/health",
            }
        }
    }


@app.get("/health", tags=["health"])
async def health():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
