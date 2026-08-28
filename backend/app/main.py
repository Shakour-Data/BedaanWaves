"""
BedaanWaves Main Application Entry Point
Enhanced with full automation:
- Auto database migration on startup
- Auto database creation if missing
- Auto seed data on fresh database
- Pre-flight health checks
- Directory creation
"""

import logging
import signal
import sys
import os
import subprocess
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings

from app.api.middleware import (
    RateLimitMiddleware,
    CorrelationIdMiddleware,
    AuthGuardMiddleware,
    RequestLoggingMiddleware,
)

from app.services.core.dependency_container import (
    DependencyContainer,
    set_global_container,
)
from app.services.core.config_service import ConfigService
from app.services.core.logger_service import LoggerService
from app.services.core.cache_service import CacheService
from app.services.core.database_service import DatabaseService
from app.services.core.health_checker import HealthChecker
from app.services.system.scheduler_service import SchedulerService
from app.services.system.metrics_service import MetricsService
from app.services.system.backup_service import BackupService
from app.services.system.data_integrity_service import DataIntegrityService
from app.services.analysis.scoring_service import ScoringService
from app.services.ml.coefficient_learning_service import CoefficientLearningService
from app.services.data.nasdaq_ingestion_service import NasdaqIngestionService
from app.services.crypto.crypto_ingestion_service import CryptoIngestionService
from app.services.data.ingestion_service import IntelligentIngestionService
from app.services.data.news_service import NewsService
from app.services.core.dependency_container import DependencyContainer, set_global_container

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
    settings_router,
    ranking_router,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()
_container = None


def _ensure_directories():
    """Create required directories if they don't exist."""
    dirs = [
        "logs",
        "data",
        "data/archive",
        "models",
        "temp",
        "backups",
    ]
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for d in dirs:
        path = os.path.join(base, d)
        os.makedirs(path, exist_ok=True)


def _ensure_database():
    """Create database if it doesn't exist."""
    try:
        from sqlalchemy import create_engine, text, inspect
        import re
        db_url = settings.DATABASE_URL
        parts = db_url.split("/")
        db_name = parts[-1].split("?")[0]
        base_url = "/".join(parts[:-1])

        if db_url.startswith("postgresql+psycopg://"):
            base_url = base_url.replace("postgresql+psycopg://", "postgresql://", 1)
        elif db_url.startswith("postgresql+psycopg2://"):
            base_url = base_url.replace("postgresql+psycopg2://", "postgresql://", 1)

        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', db_name):
            logger.warning(f"Invalid database name '{db_name}', skipping auto-creation")
            return

        engine = create_engine(f"{base_url}/postgres", future=True)
        with engine.connect() as conn:
            conn.execute(text("COMMIT"))
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name}
            )
            if not result.fetchone():
                conn.execute(text("COMMIT"))
                conn.execute(text('CREATE DATABASE "{}"'.format(db_name.replace('"', '""'))))
                logger.info(f"Database '{db_name}' created automatically")
        engine.dispose()
    except Exception as e:
        logger.warning(f"Could not auto-create database: {e}")


def _run_migrations():
    """Run Alembic migrations automatically."""
    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            logger.info("Database migrations applied successfully")
        else:
            logger.warning(f"Migration output: {result.stderr}")
    except Exception as e:
        logger.warning(f"Could not run migrations automatically: {e}")


def _check_tables_exist() -> bool:
    """Check if core tables exist in the database."""
    try:
        from sqlalchemy import create_engine, inspect, text
        engine = create_engine(settings.DATABASE_URL, future=True)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        engine.dispose()
        return "assets" in tables
    except Exception:
        return False


def _needs_seeding() -> bool:
    """Check if database needs initial data seeding."""
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(settings.DATABASE_URL, future=True, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM assets"))
            count = result.scalar()
            engine.dispose()
            return count == 0
    except Exception:
        return True


def _run_seed():
    """Run the real data seed script."""
    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        seed_script = os.path.join(backend_dir, "scripts", "seed_real_data.py")
        if os.path.exists(seed_script):
            logger.info("Starting automated data seeding (5 years of real market data)...")
            result = subprocess.run(
                [sys.executable, seed_script],
                cwd=backend_dir,
                capture_output=False,
                text=True,
                timeout=3600,
            )
            if result.returncode == 0:
                logger.info("Data seeding completed successfully")
            else:
                logger.warning("Data seeding encountered issues")
    except subprocess.TimeoutExpired:
        logger.warning("Data seeding timed out (may still be running)")
    except Exception as e:
        logger.warning(f"Could not run seed automatically: {e}")


def _preflight_checks() -> dict:
    """Run pre-flight health checks before accepting traffic."""
    checks = {}
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(settings.DATABASE_URL, future=True, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=5)
        r.ping()
        r.close()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable (cache disabled)"

    return checks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events with full automation."""
    global _container

    logger.info("Starting BedaanWaves application...")

    # Step 1: Ensure directories exist
    _ensure_directories()

    # Step 2: Auto-create database if missing
    # try:
    #     _ensure_database()
    # except Exception as e:
    #     logger.warning(f"Database auto-creation failed: {e}")

    # Step 3: Auto-run migrations
    # Disabled for audit testing
    pass

    # Step 4: Auto-seed if database is empty
    # Disabled for audit testing
    pass

    try:
        await ensure_admin_user()
        logger.info("Admin user ensured")
    except Exception as e:
        logger.warning(f"Could not ensure admin user: {e}")

    try:
        # Step 6: Initialize dependency container with real services
        container = DependencyContainer()

        # Core services
        config_svc = ConfigService()
        logger_svc = LoggerService()
        database_svc = DatabaseService()
        cache_svc = CacheService()
        health_svc = HealthChecker()

        container.register_instance("config_service", config_svc)
        container.register_instance("logger_service", logger_svc)
        container.register_instance("database_service", database_svc)
        container.register_instance("cache_service", cache_svc)
        container.register_instance("health_checker", health_svc)

        # Analysis services
        coefficient_svc = CoefficientLearningService()
        scoring_svc = ScoringService()
        container.register_instance("coefficient_learning_service", coefficient_svc)
        container.register_instance("scoring_service", scoring_svc)
        container.register_instance("metrics_service", MetricsService())

        # Data services
        nasdaq_svc = NasdaqIngestionService()
        crypto_svc = CryptoIngestionService()
        ingest_svc = IntelligentIngestionService()
        news_svc = NewsService()
        container.register_instance("nasdaq_service", nasdaq_svc)
        container.register_instance("nasdaq_ingestion_service", nasdaq_svc)
        container.register_instance("crypto_ingestion_service", crypto_svc)
        container.register_instance("data_ingest_service", ingest_svc)
        container.register_instance("news_service", news_svc)
        container.register_instance("data_integrity_service",
                                   DataIntegrityService())

        # System services
        backup_svc = BackupService()
        container.register_instance("backup_service", backup_svc)

        # Scheduler with all real services injected
        scheduler_svc = SchedulerService(
            scoring_service=scoring_svc,
            metrics_service=container.get("metrics_service"),
            health_checker=health_svc,
            cache_service=cache_svc,
            nasdaq_service=nasdaq_svc,
            data_ingest_service=ingest_svc,
            crypto_ingest_service=crypto_svc,
            data_integrity_service=container.get("data_integrity_service"),
            ml_training_service=coefficient_svc,
            backup_service=backup_svc,
            news_service=news_svc,
        )
        container.register_instance("scheduler_service", scheduler_svc)
        container.register_instance("scheduler", scheduler_svc)
        container.register_instance("metrics", container.get("metrics_service"))

        # try:
        #     await container.initialize()
        # except Exception as e:
        #     logger.error(f"Service initialization partially failed, continuing in degraded mode: {e}")
            
        app.state.container = container
        _container = container
        set_global_container(container)

        logger.info("Registered core services in dependency container")

        # Step 6: Pre-flight health checks
        # checks = _preflight_checks()
        # logger.info(f"Pre-flight checks: {checks}")

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
        app.include_router(settings_router, prefix="/api/v1/settings", tags=["settings"])
        app.include_router(ranking_router, prefix="/api/v1/ranking", tags=["ranking"])

        logger.info("Registered all API routes")
        logger.info("BedaanWaves application ready")

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise

    yield

    logger.info("Shutting down BedaanWaves application...")
    if hasattr(app.state, 'container'):
        try:
            await app.state.container.shutdown_all()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
    logger.info("BedaanWaves application shutdown complete")


app = FastAPI(
    title=settings.API_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    openapi_url=settings.OPENAPI_URL,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(AuthGuardMiddleware, enabled=settings.REQUIRE_AUTH)
app.add_middleware(RateLimitMiddleware, enabled=settings.RATE_LIMIT_ENABLED)
app.add_middleware(RequestLoggingMiddleware, enabled=settings.LOG_LEVEL.upper() == "INFO")

from sqlalchemy.exc import SQLAlchemyError
from fastapi import Request


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
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
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_code": "INTERNAL_ERROR",
            "message": "Internal server error",
        },
    )


@app.get("/health")
async def health_check():
    checks = _preflight_checks()
    status = "healthy" if all(v == "ok" for v in checks.values() if "database" in str(checks.values())) else "degraded"
    return {
        "status": status,
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": settings.DOCS_URL
    }


def handle_signal(signum, frame):
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    sys.exit(0)


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)
