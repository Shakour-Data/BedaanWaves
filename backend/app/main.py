"""
BedaanWaves Main Application Entry Point
Enhanced with full automation:
- Auto database migration on startup
- Auto database creation if missing
- Auto seed data on fresh database
- Pre-flight health checks
- Directory creation
"""

import asyncio
import logging
import os
import signal
import subprocess
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.middleware import (
    AuthGuardMiddleware,
    CorrelationIdMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
)
from app.api.middleware import SecurityHeadersMiddleware
from app.api.routes import (
    analysis_router,
    auth_router,
    compare_router,
    dashboard_router,
    data_health_router,
    filter_router,
    health_router,
    history_router,
    live_router,
    live_sse_router,
    market_data_router,
    market_router,
    ml_router,
    news_router,
    notifications_router,
    password_reset_router,
    portfolio_router,
    ranking_router,
    settings_router,
    specialized_router,
    stocks_router,
    symbols_router,
    system_router,
    users_router,
    watchlists_router,
)
from app.core.config import get_settings
from app.core.config import get_settings as _live_settings_get
from app.core.utils import utc_now_iso
from app.infrastructure.database.multi_db_manager import MultiDatabaseManager
from app.infrastructure.events.event_bus import InMemoryEventBus, KafkaEventBus
from app.infrastructure.observability.tracing import TracingManager
from app.infrastructure.resilience.bulkhead import Bulkhead, BulkheadConfig
from app.infrastructure.resilience.circuit_breaker import CircuitBreaker
from app.services.analysis.scoring_service import ScoringService
from app.services.core.cache_service import CacheService
from app.services.core.config_service import ConfigService
from app.services.core.database_service import DatabaseService
from app.services.core.dependency_container import (
    DependencyContainer,
    set_global_container,
)
from app.services.core.health_checker import HealthChecker
from app.services.core.logger_service import LoggerService
from app.services.data.ingestion_service import IntelligentIngestionService
from app.services.data.itch_ingestion_service import ITCHOrderBookService
from app.services.data.market_hours_service import MarketHoursService
from app.services.data.nasdaq_ingestion_service import NasdaqIngestionService
from app.services.data.news_service import NewsService
from app.services.data.real_time_market_data_service import RealTimeMarketDataService
from app.services.data.nerk_ingestion_service import NerkIngestionService
from app.services.live import (
    FreshnessValidator,
    LiveDataOrchestrator,
    LivePipelineMetrics,
    PerSymbolCircuitBreaker,
    SLOMonitor,
)
from app.services.ml.coefficient_learning_service import CoefficientLearningService
from app.services.news.continuous_news_ingestion_service import ContinuousNewsIngestionService
from app.services.system.backup_service import BackupService
from app.services.system.data_integrity_service import DataIntegrityService
from app.services.system.logging_service import LoggingService
from app.services.system.metrics_service import MetricsService
from app.services.system.notification_dispatcher_service import NotificationDispatcher
from app.services.system.queue_service import QueueService
from app.services.system.scheduler_service import SchedulerService
from app.services.user.auth_service import ensure_admin_user

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
    engine = None
    try:
        import re

        from sqlalchemy import create_engine, text
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
                from sqlalchemy.schema import CreateDatabase
                from sqlalchemy.dialects.postgresql import base as pg_base
                identifier = pg_base.Identifier(db_name)
                conn.execute(CreateDatabase(identifier))
                logger.info(f"Database '{db_name}' created automatically")
        engine.dispose()
    except Exception as e:
        logger.warning(f"Could not auto-create database: {e}")
    finally:
        if engine is not None:
            engine.dispose()


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
        from sqlalchemy import create_engine, inspect
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

    # DB/lifecycle bypass flag used by the SSE-lag performance benchmark to
    # keep startup fast and independent of Postgres provisioning.
    skip_db = os.environ.get("LIVE_BENCH_SKIP_DB_LIFESPAN", "").lower() in ("1", "true", "yes")
    if skip_db and settings.ENVIRONMENT == "production":
        raise RuntimeError(
            "LIVE_BENCH_SKIP_DB_LIFESPAN cannot be enabled in production"
        )

    # Step 1: Ensure directories exist
    _ensure_directories()

    if not skip_db:
        # Step 2: Auto-create database if missing
        try:
            _ensure_database()
        except Exception as e:
            logger.warning(f"Database auto-creation failed: {e}")

        # Step 3: Auto-run migrations
        try:
            _run_migrations()
        except Exception as e:
            logger.warning(f"Auto-migration failed: {e}")

        # Step 4: Auto-seed if database is empty
        if _needs_seeding():
            _run_seed()

        try:
            await ensure_admin_user()
            logger.info("Admin user ensured")
        except Exception as e:
            logger.warning(f"Could not ensure admin user: {e}")
    else:
        logger.info("LIVE_BENCH_SKIP_DB_LIFESPAN=true: skipping DB create/migrate/seed/admin steps.")

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

        # Resilience and observability infrastructure
        multi_db = MultiDatabaseManager()
        await multi_db.initialize()
        container.register_instance("multi_database_manager", multi_db)

        tracing = TracingManager(service_name=settings.APP_NAME, enabled=settings.TRACING_ENABLED)
        await tracing.initialize()
        container.register_instance("tracing_manager", tracing)

        event_bus: InMemoryEventBus | KafkaEventBus
        if settings.EVENT_BUS_BACKEND == "kafka":
            event_bus = KafkaEventBus(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS, client_id=settings.KAFKA_CLIENT_ID)
        else:
            event_bus = InMemoryEventBus()
        await event_bus.start()
        container.register_instance("event_bus", event_bus)

        market_bulkhead = Bulkhead("market", BulkheadConfig(max_concurrent_calls=10, max_waiting=50, timeout=30.0))
        analysis_bulkhead = Bulkhead("analysis", BulkheadConfig(max_concurrent_calls=5, max_waiting=30, timeout=30.0))
        ml_bulkhead = Bulkhead("ml", BulkheadConfig(max_concurrent_calls=3, max_waiting=10, timeout=60.0))
        container.register_instance("market_bulkhead", market_bulkhead)
        container.register_instance("analysis_bulkhead", analysis_bulkhead)
        container.register_instance("ml_bulkhead", ml_bulkhead)

        circuit_breaker = CircuitBreaker("external-api", failure_threshold=5, recovery_timeout=30.0)
        container.register_instance("circuit_breaker", circuit_breaker)

        data_integrity_svc = DataIntegrityService(event_bus=event_bus)
        container.register_instance("data_integrity_service", data_integrity_svc)

        # Event-driven cache invalidation
        from app.services.core.cache_invalidation_service import CacheInvalidationService
        cache_invalidation_svc = CacheInvalidationService(event_bus=event_bus, cache_service=cache_svc)
        await cache_invalidation_svc.start()
        container.register_instance("cache_invalidation_service", cache_invalidation_svc)

        # Analysis services
        coefficient_svc = CoefficientLearningService()
        scoring_svc = ScoringService()
        container.register_instance("coefficient_learning_service", coefficient_svc)
        container.register_instance("scoring_service", scoring_svc)
        container.register_instance("metrics_service", MetricsService())

        # Data services
        nasdaq_svc = NasdaqIngestionService()
        nerk_svc = NerkIngestionService()
        ingest_svc = IntelligentIngestionService()
        news_svc = NewsService()
        market_hours_svc = MarketHoursService()
        realtime_market_svc = RealTimeMarketDataService(cache_service=cache_svc)
        ingestion_svc = ContinuousNewsIngestionService(
            news_service=news_svc,
        )
        container.register_instance("nasdaq_service", nasdaq_svc)
        container.register_instance("nasdaq_ingestion_service", nasdaq_svc)
        container.register_instance("nerk_service", nerk_svc)
        container.register_instance("nerk_ingestion_service", nerk_svc)
        container.register_instance("data_ingest_service", ingest_svc)
        container.register_instance("news_service", news_svc)
        container.register_instance("continuous_news_ingestion_service", ingestion_svc)
        container.register_instance("market_hours_service", market_hours_svc)
        container.register_instance("real_time_market_data_service", realtime_market_svc)

        # System services
        backup_svc = BackupService()
        container.register_instance("backup_service", backup_svc)

        # Disaster Recovery service
        from app.services.system.disaster_recovery_service import DisasterRecoveryService
        dr_svc = DisasterRecoveryService()
        container.register_instance("disaster_recovery_service", dr_svc)

        logging_svc = LoggingService()
        container.register_instance("logging_service", logging_svc)

        queue_svc = QueueService()
        container.register_instance("queue_service", queue_svc)
        container.register_instance("queue", queue_svc)

        # Self-healing service — register critical services for automatic recovery
        from app.services.system.self_healing_service import SelfHealingService
        self_healing_svc = SelfHealingService()
        self_healing_svc.register_service(
            "DatabaseService",
            database_svc.health_check,
            restart_cmd=os.environ.get("SELF_HEALING_RESTART_CMD", ""),
            critical=True,
        )
        self_healing_svc.register_service(
            "CacheService",
            cache_svc.health_check,
            critical=False,
        )
        self_healing_svc.register_service(
            "HealthChecker",
            health_svc.health_check,
            critical=False,
        )
        self_healing_svc.register_recovery_policy("DatabaseService", {
            "min_instances": 1,
            "max_instances": 1,
            "target_cpu": 0.85,
        })
        container.register_instance("self_healing_service", self_healing_svc)

        # Scheduler with all real services injected
        scheduler_svc = SchedulerService(
            scoring_service=scoring_svc,
            metrics_service=container.get("metrics_service"),
            health_checker=health_svc,
            cache_service=cache_svc,
            nasdaq_service=nasdaq_svc,
            data_ingest_service=ingest_svc,
            data_integrity_service=container.get("data_integrity_service"),
            ml_training_service=coefficient_svc,
            backup_service=backup_svc,
            news_service=news_svc,
            ingestion_service=ingestion_svc,
        )
        container.register_instance("scheduler_service", scheduler_svc)
        container.register_instance("scheduler", scheduler_svc)
        container.register_instance("metrics", container.get("metrics_service"))

        await scheduler_svc.initialize()
        logger.info("SchedulerService started")

        # Schedule periodic self-healing checks (every 30s)
        async def _periodic_self_heal():
            while True:
                try:
                    await asyncio.sleep(30)
                    sh = container.get("self_healing_service")
                    report = await sh.check_and_heal()
                    if report.get("services_healed", 0) > 0:
                        logger.warning("Self-healing actions performed: %s", report.get("details"))
                except Exception as exc:
                    logger.error("Self-healing check failed: %s", exc)

        _periodic_self_heal_task = asyncio.create_task(_periodic_self_heal())
        container.register_instance("_periodic_self_heal_task", _periodic_self_heal_task)
        logger.info("SelfHealingService periodic checks scheduled (interval=30s)")

        # Notification dispatcher (shared, used by SLOMonitor)
        notification_dispatcher_svc = NotificationDispatcher()
        container.register_instance("notification_dispatcher_service", notification_dispatcher_svc)

        # Live streaming services (Tasks 2-6, 13-14)
        _live_settings = _live_settings_get()

        # Task 2 components
        live_freshness_validator = FreshnessValidator(
            market_hours=market_hours_svc,
            settings=_live_settings,
        )
        live_circuit_breaker = PerSymbolCircuitBreaker(
            failure_threshold=_live_settings.LIVE_CIRCUIT_BREAKER_FAILURES,
            halfopen_s=float(_live_settings.LIVE_CIRCUIT_BREAKER_HALFOPEN_S),
        )
        container.register_instance("live_freshness_validator", live_freshness_validator)
        container.register_instance("live_circuit_breaker", live_circuit_breaker)

        # Task 5: Live pipeline metrics
        live_pipeline_metrics = LivePipelineMetrics()
        container.register_instance("live_pipeline_metrics", live_pipeline_metrics)
        # Register with MetricsService registry so /system/metrics can scrape it
        try:
            _metrics_service = container.get("metrics_service")
            if hasattr(_metrics_service, "register_service"):
                _metrics_service.register_service(live_pipeline_metrics.service_name, live_pipeline_metrics)
                live_pipeline_metrics.register_with_metrics_service(_metrics_service)
        except Exception as _e:
            logger.warning("Could not register live metrics with MetricsService: %s", _e)

        # Task 3: Orchestrator with per-key polling + reference counting + derived producers
        orderbook_svc = ITCHOrderBookService()
        container.register_instance("orderbook_service", orderbook_svc)

        live_orchestrator = LiveDataOrchestrator(
            market_data_service=realtime_market_svc,
            market_hours_service=market_hours_svc,
            freshness_validator=live_freshness_validator,
            circuit_breaker=live_circuit_breaker,
            settings=_live_settings,
            metrics_service=live_pipeline_metrics,
            scoring_service=scoring_svc,
            news_service=news_svc,
            orderbook_service=orderbook_svc,
        )
        ingestion_svc._orch = live_orchestrator
        container.register_instance("live_orchestrator", live_orchestrator)

        # Task 6: SLO monitor with notification dispatch + debounce + recovery
        slo_monitor = SLOMonitor(
            notification_dispatcher=notification_dispatcher_svc,
            settings=_live_settings,
        )
        slo_monitor.bind_orchestrator(live_orchestrator)
        # Wire observe_envelope hook so every emitted envelope flows into the SLO monitor
        setattr(live_orchestrator, "slo_monitor_hook", lambda envelope, age, thresh: slo_monitor.observe_envelope(
            envelope, data_age_ms=age, threshold_s=thresh
        ))
        container.register_instance("slo_monitor", slo_monitor)

        # Initialize live services (must be in dependency order)
        await notification_dispatcher_svc.initialize()
        await live_pipeline_metrics.initialize()
        await live_orchestrator.initialize()
        await slo_monitor.initialize()
        logger.info(
            "Live services initialized: orchestrator=%s metrics=%s slo_monitor=%s",
            live_orchestrator.service_name,
            live_pipeline_metrics.service_name,
            slo_monitor.service_name,
        )

        app.state.container = container
        _container = container
        set_global_container(container)

        logger.info("Registered core services in dependency container")

    except Exception as e:
        logger.error("Failed to initialize application: %s", e, exc_info=True)
        raise

    # Register all routers (outside try/except so routes are always available)
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(password_reset_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(stocks_router, prefix="/api/v1/stocks", tags=["stocks"])
    app.include_router(market_router, prefix="/api/v1/market", tags=["market"])
    app.include_router(market_data_router, prefix="/api/v1/market-data", tags=["market-data"])
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
    app.include_router(live_router, prefix="/api/v1/live", tags=["live"])
    app.include_router(live_sse_router, prefix="/api/v1/live", tags=["live-sse"])
    app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
    app.include_router(data_health_router, tags=["data-health"])
    app.include_router(dashboard_router, prefix="/api/v1/analysis", tags=["dashboard"])
    app.include_router(filter_router, prefix="/api/v1/filter", tags=["filter"])
    app.include_router(symbols_router, prefix="/api/v1/symbols", tags=["symbols"])
    app.include_router(settings_router, prefix="/api/v1/settings", tags=["settings"])
    app.include_router(ranking_router, prefix="/api/v1/ranking", tags=["ranking"])
    app.include_router(compare_router, prefix="/api/v1/compare", tags=["compare"])

    logger.info("Registered all API routes")
    logger.info("BedaanWaves application ready")

    yield

    logger.info("Shutting down BedaanWaves application...")
    if hasattr(app.state, 'container'):
        try:
            await app.state.container.shutdown_all()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)

    try:
        if "event_bus" in app.state.container._instances:
            await app.state.container.get("event_bus").stop()
        if "multi_database_manager" in app.state.container._instances:
            await app.state.container.get("multi_database_manager").shutdown()
    except Exception as e:
        logger.error(f"Error during infrastructure shutdown: {e}", exc_info=True)
    logger.info("BedaanWaves application shutdown complete")


app = FastAPI(
    title=settings.API_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    terms_of_service="https://bedaanwaves.com/terms/",
    contact={
        "name": "BedaanWaves Team",
        "url": "https://bedaanwaves.com/support",
        "email": "support@bedaanwaves.com",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://bedaanwaves.com/license",
    },
    docs_url=settings.DOCS_URL if getattr(settings, "ENABLE_DOCS", True) else None,
    redoc_url=settings.REDOC_URL if getattr(settings, "ENABLE_DOCS", True) else None,
    openapi_url=settings.OPENAPI_URL if getattr(settings, "ENABLE_DOCS", True) else None,
    swagger_ui_parameters={
        "syntaxHighlight": True,
        "syntaxHighlight.activate": True,
        "tryItOutEnabled": True,
        "displayOperationId": True,
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "docExpansion": "list",
        "defaultModelsExpandDepth": 2,
        "defaultModelExpandDepth": 2,
        "persistAuthorization": True,
        "withCredentials": True,
    },
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(AuthGuardMiddleware, enabled=settings.REQUIRE_AUTH)
app.add_middleware(RateLimitMiddleware, enabled=settings.RATE_LIMIT_ENABLED)
app.add_middleware(RequestLoggingMiddleware, enabled=settings.LOG_LEVEL.upper() == "INFO")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        license_info=app.license_info,
        contact=app.contact,
        terms_of_service=app.terms_of_service,
    )

    openapi_schema["servers"] = [
        {
            "url": "/api/v1",
            "description": "Relative to current host (works in dev & prod)",
        },
        {
            "url": "http://localhost:3000",
            "description": "Backend direct (dev)",
        },
    ]

    if settings.ENVIRONMENT == "staging":
        openapi_schema["servers"].append({
            "url": "https://staging-api.bedaanwaves.com",
            "description": "Staging environment",
        })
    elif settings.ENVIRONMENT == "production":
        openapi_schema["servers"].append({
            "url": "https://api.bedaanwaves.com",
            "description": "Production environment",
        })

    openapi_schema.setdefault("components", {})
    openapi_schema["components"].setdefault("securitySchemes", {})
    openapi_schema["components"].setdefault("schemas", {})

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter the access token obtained from `/api/v1/auth/login`",
        },
        "CookieAuth": {
            "type": "apiKey",
            "in": "cookie",
            "name": "refresh_token",
            "description": "Optional refresh token cookie for session renewal",
        },
    }

    openapi_schema["components"]["schemas"]["ErrorResponse"] = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "example": "error"},
            "error_code": {"type": "string", "example": "NOT_FOUND"},
            "message": {"type": "string", "example": "Resource not found"},
            "details": {"type": "object", "example": {"field": "validation error"}},
        },
        "required": ["status", "error_code", "message"],
    }

    openapi_schema["components"]["schemas"]["SuccessResponse"] = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "example": "success"},
            "data": {"type": "object"},
            "message": {"type": "string", "example": "Operation completed successfully"},
        },
        "required": ["status"],
    }

    openapi_schema["components"]["schemas"]["PaginationMetadata"] = {
        "type": "object",
        "properties": {
            "total": {"type": "integer", "example": 100},
            "skip": {"type": "integer", "example": 0},
            "limit": {"type": "integer", "example": 50},
        },
        "required": ["total", "skip", "limit"],
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error("Database error on %s %s: %s", request.method, request.url.path, exc)
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
    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {
        "status": status,
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": utc_now_iso(),
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
