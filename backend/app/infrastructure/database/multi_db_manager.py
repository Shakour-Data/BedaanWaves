import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""


settings = get_settings()
logger = logging.getLogger(__name__)


class DatabaseRole(StrEnum):
    CORE = "core"
    MARKET = "market"
    ML = "ml"


@dataclass
class DatabaseConfig:
    role: DatabaseRole
    url: str
    pool_size: int = 10
    max_overflow: int = 5
    echo: bool = False


class MultiDatabaseManager:
    def __init__(self):
        self._engines: dict[DatabaseRole, Any] = {}
        self._session_factories: dict[DatabaseRole, async_sessionmaker[AsyncSession]] = {}
        self._initialized = False
        self._pool_stats: dict[DatabaseRole, dict[str, Any]] = {}

    def _build_config(self, role: DatabaseRole) -> DatabaseConfig:
        base_url = getattr(settings, f"DATABASE_URL_{role.value.upper()}", None)
        if not base_url:
            logger.warning(
                f"DATABASE_URL_{role.value.upper()} is not configured. "
                f"Falling back to default DATABASE_URL for role={role.value}. "
                f"Set DATABASE_URL_{role.value.upper()} in .env for production deployments."
            )
            base_url = settings.DATABASE_URL
        return DatabaseConfig(
            role=role,
            url=base_url,
            pool_size=getattr(settings, f"DATABASE_POOL_SIZE_{role.value.upper()}", settings.DATABASE_POOL_SIZE),
            max_overflow=getattr(settings, f"DATABASE_MAX_OVERFLOW_{role.value.upper()}", settings.DATABASE_MAX_OVERFLOW),
            echo=settings.DATABASE_ECHO,
        )

    async def initialize(self) -> None:
        if self._initialized:
            return
        for role in DatabaseRole:
            config = self._build_config(role)
            db_url = config.url
            if db_url.startswith("postgresql://"):
                db_url = "postgresql+asyncpg://" + db_url[len("postgresql://"):]

            # Enhanced pool configuration for high-concurrency workloads
            pool_size = config.pool_size
            max_overflow = config.max_overflow

            # Scale pool size based on role for optimal resource utilization
            if role == DatabaseRole.MARKET:
                # Market data has highest read volume
                pool_size = max(pool_size, 50)
                max_overflow = max(max_overflow, 30)
            elif role == DatabaseRole.CORE:
                # Core has mixed read/write with transactional needs
                pool_size = max(pool_size, 30)
                max_overflow = max(max_overflow, 20)
            elif role == DatabaseRole.ML:
                # ML workloads are batch-oriented, can use smaller pool
                pool_size = max(pool_size, 15)
                max_overflow = max(max_overflow, 10)

            engine = create_async_engine(
                db_url,
                echo=config.echo,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,
                pool_recycle=1800,  # Recycle connections every 30 min
                pool_timeout=10,    # Wait max 10s for a connection
                connect_args={
                    "command_timeout": 5,
                    "server_settings": {
                        "application_name": f"bedaanwaves-{role.value}",
                        "jit": "off",  # Disable JIT for predictable latency
                    },
                },
            )
            factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            self._engines[role] = engine
            self._session_factories[role] = factory

            # Track pool stats
            self._pool_stats[role] = {
                "pool_size": pool_size,
                "max_overflow": max_overflow,
                "url": config.url.split("@")[-1],
            }
            logger.info(
                "Initialized database role=%s pool_size=%d max_overflow=%d url=%s",
                role.value, pool_size, max_overflow, config.url.split("@")[-1],
            )
        self._initialized = True

    async def shutdown(self) -> None:
        for role, engine in self._engines.items():
            try:
                await engine.dispose()
                logger.info("Disposed database engine role=%s", role.value)
            except Exception as exc:
                logger.error("Error disposing database engine role=%s: %s", role.value, exc)
        self._engines.clear()
        self._session_factories.clear()
        self._pool_stats.clear()
        self._initialized = False

    def get_session_factory(self, role: DatabaseRole) -> async_sessionmaker[AsyncSession]:
        if not self._initialized:
            raise RuntimeError("MultiDatabaseManager not initialized")
        return self._session_factories[role]

    def get_pool_stats(self) -> dict[str, Any]:
        """Return detailed pool statistics for monitoring."""
        stats = {}
        for role, engine in self._engines.items():
            pool = engine.pool
            stats[role.value] = {
                "pool_size": pool.size(),
                "max_overflow": pool._max_overflow,
                "checked_out": pool.checkedout(),
                "checked_in": pool.checkedin(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
            }
        return stats

    @staticmethod
    @asynccontextmanager
    async def session(factory: async_sessionmaker[AsyncSession]):
        session = factory()
        try:
            yield session
        finally:
            try:
                await session.close()
            except Exception as exc:
                logger.debug("Session close error: %s", exc)

    def get_stats(self) -> dict[str, Any]:
        return {
            "initialized": self._initialized,
            "roles": [role.value for role in self._engines.keys()],
            "pool_stats": self._pool_stats,
        }
