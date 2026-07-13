"""FastAPI Application Entry Point"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.db.base import init_db, close_db
from app.api.middleware import (
    AuthGuardMiddleware,
    CorrelationIdMiddleware,
    RateLimitMiddleware,
    protected_dependencies,
)
from app.api.routes import market, analysis, stocks, portfolios, history, news, auth, ml, live, users, watchlists, notifications, specialized, system, crypto, intl
from app.services.core.dependency_container import get_global_container
from app.services.system.scheduler_service import SchedulerService
from app.services.system.metrics_service import MetricsService
from app.services.system.queue_service import QueueService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Fail-fast: enforce security requirements in production
    if settings.ENVIRONMENT == "production":
        if not settings.REQUIRE_AUTH:
            raise RuntimeError(
                "Refusing to start: REQUIRE_AUTH must be True in production. "
                "Set REQUIRE_AUTH=true or ENVIRONMENT=development."
            )
        if settings.DEBUG:
            raise RuntimeError(
                "Refusing to start: DEBUG must be False in production. "
                "Set DEBUG=false or ENVIRONMENT=development."
            )
    
    await init_db()

    container = get_global_container()
    container.register_instance("scheduler", SchedulerService())
    container.register_instance("metrics", MetricsService())
    container.register_instance("queue", QueueService())

    scheduler = container.get("scheduler")
    metrics = container.get("metrics")
    queue = container.get("queue")
    await scheduler.initialize()
    await metrics.initialize()
    await queue.initialize()

    yield
    # Shutdown
    logger.info("Shutting down application")
    await scheduler.shutdown()
    await metrics.shutdown()
    await queue.shutdown()
    await container.shutdown_all()
    await close_db()
    await live.close_brs_client()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Unified Bedaan Ecosystem - Market Analysis & AI Trading Platform",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZIP compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add global middlewares (order: last added runs closest to the app).
# Correlation id is outermost so every response carries a tracing header.
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(RateLimitMiddleware, enabled=settings.RATE_LIMIT_ENABLED)
app.add_middleware(AuthGuardMiddleware, enabled=settings.REQUIRE_AUTH)


# Health Check Route
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "success",
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/api/v1/docs",
    }


# API Routes
api_v1_prefix = settings.API_V1_STR

# Include routers. The auth router is intentionally excluded from the global
# guard so login/register/refresh stay public. All other routers enforce auth
# (via protected_dependencies) when REQUIRE_AUTH is enabled.
auth_guard = protected_dependencies()
app.include_router(market.router, prefix=api_v1_prefix, dependencies=auth_guard)
app.include_router(analysis.router, prefix=api_v1_prefix, dependencies=auth_guard)
app.include_router(stocks.router, prefix=api_v1_prefix, dependencies=auth_guard)
app.include_router(portfolios.router, prefix=api_v1_prefix, dependencies=auth_guard)
app.include_router(history.router, prefix=api_v1_prefix, dependencies=auth_guard)
app.include_router(news.router, prefix=api_v1_prefix, dependencies=auth_guard)
app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(ml.router, prefix=api_v1_prefix, dependencies=auth_guard)
app.include_router(users.router, prefix=api_v1_prefix, dependencies=auth_guard)
app.include_router(watchlists.router, prefix=api_v1_prefix, dependencies=auth_guard)
app.include_router(notifications.router, prefix=api_v1_prefix, dependencies=auth_guard)
app.include_router(live.router, prefix=api_v1_prefix, dependencies=auth_guard)
app.include_router(specialized.router, prefix=api_v1_prefix, dependencies=auth_guard)
app.include_router(system.router, prefix=api_v1_prefix, dependencies=auth_guard)
app.include_router(crypto.router, prefix=api_v1_prefix, dependencies=auth_guard)
app.include_router(intl.router, prefix=api_v1_prefix, dependencies=auth_guard)

# Error Handlers
@app.exception_handler(RuntimeError)
async def runtime_exception_handler(request, exc):
    """Surface upstream API errors (e.g. BrsApi) as 502."""
    logger.error(f"Runtime error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=502,
        content={
            "status": "error",
            "error_code": "UPSTREAM_ERROR",
            "message": str(exc),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
