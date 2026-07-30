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
from app.services.crypto.crypto_ingestion_service import CryptoIngestionService
from app.services.data.market_data_processing import MarketDataProcessingService
from app.services.ml.coefficient_learning_service import CoefficientLearningService
from app.services.analysis.crypto_fundamental_service import CryptoFundamentalAnalysisService
from sqlalchemy import select

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
    
    # Register core services
    container.register_instance("scheduler", SchedulerService())
    container.register_instance("metrics", MetricsService())
    container.register_instance("queue", QueueService())
    container.register_instance("crypto_ingestion", CryptoIngestionService())
    container.register_instance("market_data_processing", MarketDataProcessingService())
    
    # Register ML coefficient learning service
    coefficient_service = CoefficientLearningService()
    container.register_instance("coefficient_learning_service", coefficient_service)
    
    # Initialize services
    scheduler = container.get("scheduler")
    metrics = container.get("metrics")
    queue = container.get("queue")
    crypto_ingestion = container.get("crypto_ingestion")
    market_data_processing = container.get("market_data_processing")
    coefficient_service = container.get("coefficient_learning_service")
    
    await scheduler.initialize()
    await metrics.initialize()
    await queue.initialize()
    await crypto_ingestion.initialize()
    await market_data_processing.initialize()
    await coefficient_service.initialize()
    
    # Register crypto data pipeline jobs
    from app.db.base import async_session_maker
    from app.models.models import Asset

    async def run_crypto_pipeline():
        """Run crypto ingestion and processing pipeline."""
        async with async_session_maker() as session:
            # Fetch all crypto assets
            stmt = select(Asset).where(Asset.market == "CRYPTO")
            result = await session.execute(stmt)
            crypto_assets = result.scalars().all()

            if not crypto_assets:
                logger.warning("No crypto assets found in database")
                return {"status": "no_assets", "count": 0}

            # Ingest raw data
            ingestion_result = await crypto_ingestion.ingest_raw_data(
                crypto_assets, session
            )

            # Process to snapshots
            processing_result = await market_data_processing.process_all_crypto_assets(
                session
            )

            return {
                "status": "success",
                "ingested": ingestion_result,
                "snapshots_created": processing_result,
                "assets_processed": len(crypto_assets),
            }

    # Register job: every 5 minutes
    scheduler.register_job(
        name="crypto_data_pipeline",
        coroutine_func=run_crypto_pipeline,
        interval_seconds=300,  # 5 minutes
    )
    
    # Register coefficient learning job: run daily after market close (22:00 Tehran time)
    async def update_coefficients():
        """Update ML coefficients using latest performance data"""
        try:
            # This would typically fetch historical performance data from the database
            # For now, we'll use a placeholder that returns empty list (will use fallback weights)
            # In a real implementation, this would query the database for:
            # - Historical dimension/sub-dimension/aspect/sub-aspect scores
            # - Corresponding future performance metrics (returns, Sharpe ratio, etc.)
            
            # Placeholder: get performance data from database/service
            performance_data = []  # TODO: Implement actual data retrieval
            
            if len(performance_data) >= coefficient_service.min_samples_for_training:
                logger.info(f"Training coefficient models with {len(performance_data)} samples")
                await coefficient_service.learn_coefficients(performance_data)
            else:
                logger.info(f"Insufficient data for coefficient training: {len(performance_data)} samples")
                
        except Exception as e:
            logger.error(f"Error updating coefficients: {e}")
    
    # Schedule daily coefficient update at 22:00 Tehran time (UTC+3:30)
    # Which is 18:30 UTC
    # We'll run it every 24 hours for simplicity (exact cron scheduling would be more complex)
    scheduler.register_job(
        name="coefficient_learning_update",
        coroutine_func=update_coefficients,
        interval_seconds=24 * 60 * 60,  # 24 hours
    )
    
    logger.info("All services initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    await coefficient_service.shutdown()
    await scheduler.shutdown()
    await metrics.shutdown()
    await queue.shutdown()
    await crypto_ingestion.shutdown()
    await market_data_processing.shutdown()
    await container.shutdown_all()
    await close_db()
    await live.close_brs_client()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Unified Bedaan Ecosystem - Market Analysis & AI Trading Platform",
    docs_url="/api/v1/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/v1/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/api/v1/openapi.json" if settings.ENVIRONMENT != "production" else None,
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