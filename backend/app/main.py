"""
BedaanWaves Main Application Entry Point
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.db.base import engine
from app.services.core.dependency_container import DependencyContainer
from app.api.middleware import (
    CorrelationIdMiddleware,
    RateLimitMiddleware,
    AuthGuardMiddleware,
)
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
    
    # Initialize database (tables should be created via migrations)
    logger.info("Database connection initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down BedaanWaves application...")
    if hasattr(app.state, 'container'):
        await app.state.container.shutdown()


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
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


# Add custom middleware (order matters)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthGuardMiddleware)


# Include API routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(stocks_router, prefix=settings.API_V1_STR)
app.include_router(market_router, prefix=settings.API_V1_STR)
app.include_router(analysis_router, prefix=settings.API_V1_STR)
app.include_router(portfolio_router, prefix=settings.API_V1_STR)
app.include_router(history_router, prefix=settings.API_V1_STR)
app.include_router(news_router, prefix=settings.API_V1_STR)
app.include_router(ml_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(watchlists_router, prefix=settings.API_V1_STR)
app.include_router(notifications_router, prefix=settings.API_V1_STR)
app.include_router(specialized_router, prefix=settings.API_V1_STR)
app.include_router(system_router, prefix=settings.API_V1_STR)
app.include_router(crypto_router, prefix=settings.API_V1_STR)
app.include_router(intl_router, prefix=settings.API_V1_STR)
app.include_router(live_router, prefix=settings.API_V1_STR)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception handler caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "BedaanWaves", "version": settings.APP_VERSION}


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to BedaanWaves API",
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
        "redoc": f"{settings.API_V1_STR}/redoc",
    }