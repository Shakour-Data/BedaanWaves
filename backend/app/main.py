"""
BedaanWaves Main Application Entry Point
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import configuration
from app.core.config import get_settings

# Import middleware
from app.api.middleware import RateLimitMiddleware

# Import core services
from app.services.core.dependency_container import DependencyContainer
from app.services.core.config_service import ConfigService
from app.services.core.logger_service import LoggerService
from app.services.core.cache_service import CacheService
from app.services.core.database_service import DatabaseService
from app.services.core.health_checker import HealthChecker

# Import API routes
from app.api.routes import (
    auth_router,
    stocks_router,
    market_router,
    analysis_router,
    portfolio_router,
    history_router,
    news_router,
    ml_router,
    users_router,
    watchlists_router,
    notifications_router,
    specialized_router,
    system_router,
    crypto_router,
    intl_router,
    live_router,
    health_router,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load application settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting BedaanWaves application...")

    # Initialize dependency container
    container = DependencyContainer()
    await container.initialize()
    app.state.container = container

    logger.info("Registered core services in dependency container")

    # Include API routes
    try:
        from app.api.routes import (
            auth_router,
            stocks_router,
            market_router,
            analysis_router,
            portfolio_router,
            history_router,
            news_router,
            ml_router,
            users_router,
            watchlists_router,
            notifications_router,
            specialized_router,
            system_router,
            crypto_router,
            intl_router,
            live_router,
            health_router,
        )

        # Register all routers
        app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
        app.include_router(stocks_router, prefix="/api/v1/stocks", tags=["stocks"])
        app.include_router(market_router, prefix="/api/v1/market", tags=["market"])
        app.include_router(analysis_router, prefix="/api/v1/analysis", tags=["analysis"])
        app.include_router(portfolio_router, prefix="/api/v1/portfolio", tags=["portfolio"])
        app.include_router(history_router, prefix="/api/v1/history", tags=["history"])
        app.include_router(news_router, prefix="/api/v1/news", tags=["news"])
        app.include_router(ml_router, prefix="/api/v1/ml", tags=["ml"])
        app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
        app.include_router(watchlists_router, prefix="/api/v1/watchlists", tags=["watchlists"])
        app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["notifications"])
        app.include_router(specialized_router, prefix="/api/v1/specialized", tags=["specialized"])
        app.include_router(system_router, prefix="/api/v1/system", tags=["system"])
        app.include_router(crypto_router, prefix="/api/v1/crypto", tags=["crypto"])
        app.include_router(intl_router, prefix="/api/v1/intl", tags=["intl"])
        app.include_router(live_router, prefix="/api/v1/live", tags=["live"])
        app.include_router(health_router, prefix="/api/v1/health", tags=["health"])

        logger.info("Registered all API routes")
    except Exception as e:
        logger.warning(f"Could not load all API routes: {e}")
        # Continue anyway for basic functionality

    yield

    # Shutdown
    logger.info("Shutting down BedaanWaves application...")
    if hasattr(app.state, 'container'):
        await app.state.container.shutdown_all()


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware, enabled=settings.RATE_LIMIT_ENABLED)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": "2026-08-04T23:44:00Z"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }