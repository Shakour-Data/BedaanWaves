"""
Shared pytest fixtures for BedaanWaves backend tests.

Provides reusable fixtures for Tier 1 core services so individual test
modules stay focused on behaviour rather than setup boilerplate.
"""

import pytest

from app.services.core.dependency_container import DependencyContainer
from app.services.core.config_service import ConfigService
from app.services.core.cache_service import CacheService, MemoryCacheBackend
from app.services.core.logger_service import LoggerService
from app.services.core.health_checker import HealthChecker
from app.services.core.database_service import DatabaseService


@pytest.fixture
def container() -> DependencyContainer:
    """Fresh dependency container per test."""
    return DependencyContainer()


@pytest.fixture
def config_service() -> ConfigService:
    """ConfigService that does not auto-discover an .env file."""
    return ConfigService(env_file=None)


@pytest.fixture
def memory_backend() -> MemoryCacheBackend:
    """Fresh in-memory cache backend."""
    return MemoryCacheBackend()


@pytest.fixture
def cache_service() -> CacheService:
    """CacheService backed by memory with a short default TTL."""
    return CacheService(backend="memory", default_ttl=60)


@pytest.fixture
def logger_service(tmp_path) -> LoggerService:
    """LoggerService writing to a temporary directory (no console spam)."""
    return LoggerService(log_level="DEBUG", log_dir=str(tmp_path / "logs"), enable_file=False)


@pytest.fixture
def health_checker() -> HealthChecker:
    """HealthChecker without starting the background monitor loop."""
    return HealthChecker(check_interval_seconds=1)


@pytest.fixture
def database_service() -> DatabaseService:
    """Uninitialized DatabaseService (no real DB connection)."""
    return DatabaseService(
        database_url="postgresql://user:secret@localhost:5432/bedaanwaves_test",
        async_mode=True,
    )
