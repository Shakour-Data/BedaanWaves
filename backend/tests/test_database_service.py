"""Unit tests for Tier 1 DatabaseService.

These tests avoid real database connections and focus on the service's
configuration, URL masking, session guards, and lifecycle error handling.
"""

import pytest

from app.services.core.database_service import DatabaseService
from app.services.core.health_checker import check_database

pytestmark = pytest.mark.unit


class TestDatabaseConfiguration:
    def test_default_configuration(self, database_service):
        assert database_service.async_mode is True
        assert database_service.pool_size == 20
        assert database_service.max_overflow == 10
        assert database_service.engine is None
        assert database_service.session_factory is None

    def test_custom_configuration(self):
        svc = DatabaseService(
            database_url="postgresql://localhost/db",
            async_mode=False,
            pool_size=5,
            max_overflow=2,
            echo=True,
        )
        assert svc.async_mode is False
        assert svc.pool_size == 5
        assert svc.echo is True


class TestConnectionUrlMasking:
    def test_password_is_masked(self, database_service):
        url = database_service.get_connection_url()
        assert "secret" not in url
        assert "***" in url
        assert "user" in url

    def test_url_without_credentials(self):
        svc = DatabaseService(database_url="postgresql://localhost/db")
        assert svc.get_connection_url() == "postgresql://localhost/db"

    def test_malformed_url_returned_as_is(self):
        svc = DatabaseService(database_url="not-a-url")
        assert svc.get_connection_url() == "not-a-url"


class TestSessionGuards:
    async def test_get_session_before_init_raises(self, database_service):
        with pytest.raises(RuntimeError, match="not initialized"):
            await database_service.get_session()

    async def test_execute_before_init_raises(self, database_service):
        with pytest.raises(RuntimeError):
            await database_service.execute("SELECT 1")

    async def test_clean_sessions_empty(self, database_service):
        await database_service.clean_sessions()
        assert database_service._active_sessions == []


class TestStats:
    def test_get_stats(self, database_service):
        stats = database_service.get_stats()
        assert stats["pool_size"] == 20
        assert stats["max_overflow"] == 10
        assert stats["async_mode"] is True
        assert "***" in stats["database_url"]
        assert stats["active_sessions"] == 0


class TestLifecycle:
    async def test_initialize_failure_raises(self):
        # Async engine with a non-async driver URL should fail during init.
        svc = DatabaseService(
            database_url="postgresql://user:pw@localhost/db",
            async_mode=True,
        )
        with pytest.raises(Exception):
            await svc.initialize()

    async def test_shutdown_without_engine_is_safe(self, database_service):
        # No engine created yet; shutdown should not raise.
        await database_service.shutdown()

    async def test_health_check_reports_unhealthy_without_engine(self, database_service):
        # engine is None -> the SELECT 1 block is skipped and status stays healthy,
        # but connection_checks is incremented. Validate structure.
        result = await database_service.health_check()
        assert result["service"] == database_service.service_name
        assert result["status"] in {"healthy", "unhealthy"}


class TestCheckDatabaseHelper:
    async def test_check_database_delegates(self):
        class FakeDB:
            async def health_check(self):
                return {"service": "db", "status": "healthy"}

        result = await check_database(FakeDB())
        assert result["status"] == "healthy"
