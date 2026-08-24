"""
BedaanWaves Main Application Entry Point
"""

import logging
import signal
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import configuration
from app.core.config import get_settings

# Import middleware
from app.api.middleware import (
    RateLimitMiddleware,
    CorrelationIdMiddleware,
    AuthGuardMiddleware,
    RequestLoggingMiddleware,
)

# Import core services
from app.services.core.dependency_container import (
    DependencyContainer,
    set_global_container,
)
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
    symbols_router,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load application settings
settings = get_settings()

# Global container reference for shutdown
_container = None


# Global exception handlers for graceful degradation
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Request
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    global _container
    
    # Startup
    logger.info("Starting BedaanWaves application...")
    
    try:
        # Initialize dependency container
        container = DependencyContainer()
        
        # Register core services
        container.register_instance("config_service", ConfigService())
        container.register_instance("logger_service", LoggerService())
        container.register_instance("database_service", DatabaseService())
        container.register_instance("cache_service", CacheService())
        container.register_instance("health_checker", HealthChecker())
        
        await container.initialize()
        app.state.container = container
        _container = container
        set_global_container(container)
        
        logger.info("Registered core services in dependency container")
        
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
        app.include_router(symbols_router, prefix="/api/v1/symbols", tags=["symbols"])
        
        logger.info("Registered all API routes")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down BedaanWaves application...")
    if hasattr(app.state, 'container'):
        try:
            await app.state.container.shutdown_all()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
    logger.info("BedaanWaves application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    openapi_url=settings.OPENAPI_URL,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
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

# Add correlation ID middleware (first, so it wraps all other middleware)
app.add_middleware(CorrelationIdMiddleware)

# Add auth guard middleware
app.add_middleware(AuthGuardMiddleware, enabled=settings.REQUIRE_AUTH)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware, enabled=settings.RATE_LIMIT_ENABLED)

# Add request logging middleware (last, so it can log all requests)
app.add_middleware(RequestLoggingMiddleware, enabled=settings.LOG_LEVEL.upper() == "INFO")


# Global exception handlers for graceful degradation
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Request


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors with 503 Service Unavailable."""
    logger.error(f"Database error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=503,
        content={
            "status": "error",
            "error_code": "SERVICE_UNAVAILABLE",
            "message": "Service temporarily unavailable - database connection failed",
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions with 500 Internal Server Error."""
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_code": "INTERNAL_ERROR",
            "message": "Internal server error",
        },
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": settings.DOCS_URL
    }


def handle_signal(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    # The lifespan context manager will handle the actual shutdown
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)