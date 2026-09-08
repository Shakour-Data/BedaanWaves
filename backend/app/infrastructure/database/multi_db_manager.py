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

    def _build_config(self, role: DatabaseRole) -> DatabaseConfig:
        base_url = getattr(settings, f"DATABASE_URL_{role.value.upper()}", None)
        if not base_url:
            raise ConfigurationError(
                f"DATABASE_URL_{role.value.upper()} is not configured. "
                f"Set it in .env (e.g. DATABASE_URL_CORE=postgresql+asyncpg://...). "
                f"Refusing to silently fall back to the default DATABASE_URL — "
                f"that would collapse all roles into a single database (SPOF)."
            )
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

            engine = create_async_engine(
                db_url,
                echo=config.echo,
                pool_size=config.pool_size,
                max_overflow=config.max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={"command_timeout": 5},
            )
            factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            self._engines[role] = engine
            self._session_factories[role] = factory
            logger.info("Initialized database role=%s url=%s", role.value, config.url.split("@")[-1])
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
        self._initialized = False

    def get_session_factory(self, role: DatabaseRole) -> async_sessionmaker[AsyncSession]:
        if not self._initialized:
            raise RuntimeError("MultiDatabaseManager not initialized")
        return self._session_factories[role]

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
        }
