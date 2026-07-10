"""
Shared pytest fixtures for BedaanWaves backend tests.

Provides reusable fixtures for Tier 1 core services so individual test
modules stay focused on behaviour rather than setup boilerplate.
"""

import datetime as _dt
import uuid as _uuid

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


class _FakeBrsClient:
    async def get_stock_info(self, ticker: str):
        return {"ticker": ticker, "name": f"Stock {ticker}"}

    async def get_stock_price(self, ticker: str):
        return {"ticker": ticker, "price": 100.0}

    async def get_stock_history(self, ticker, start_date, end_date, interval):
        return {"ticker": ticker, "history": []}

    async def search_stocks(self, query: str):
        return [{"symbol": query}]

    async def get_market_indices(self):
        return [{"name": "TSE", "value": 1000}]

    async def get_market_stats(self):
        return {"volume": 1000}

    async def get_top_gainers(self, limit: int = 10):
        return []

    async def get_top_losers(self, limit: int = 10):
        return []

    async def get_most_active(self, limit: int = 10):
        return []


class _FakeNewsClient:
    async def get_news(self, *args, **kwargs):
        return []

    async def search(self, *args, **kwargs):
        return []


@pytest.fixture
def brs_client() -> _FakeBrsClient:
    return _FakeBrsClient()


@pytest.fixture
def news_client() -> _FakeNewsClient:
    return _FakeNewsClient()


@pytest.fixture
def mock_db_service():
    class MockDB:
        async def health_check(self):
            return {"status": "healthy"}

    return MockDB()


class FakeAsyncSession:
    """Minimal in-memory async SQLAlchemy session for unit tests.

    Supports the small subset of the async session API used by the user
    services: add/commit/refresh/delete/execute with equality and IN filters.
    """

    def __init__(self):
        self._store: dict = {}

    def _model_for_select(self, stmt):
        froms = stmt.get_final_froms()
        table = getattr(froms[0], "table", froms[0])
        tname = getattr(table, "name", None)
        for model in self._store:
            if getattr(model, "__tablename__", None) == tname:
                return model
        return None

    def _apply_criteria(self, rows, criteria):
        from sqlalchemy.sql import operators
        from sqlalchemy.sql.elements import BooleanClauseList

        for crit in criteria:
            op = getattr(crit, "operator", None)
            if op is operators.eq:
                key = crit.left.key
                val = crit.right.value if hasattr(crit.right, "value") else crit.right
                rows = [r for r in rows if getattr(r, key, None) == val]
            elif op is operators.in_op:
                key = crit.left.key
                vals = crit.right.value if hasattr(crit.right, "value") else crit.right
                rows = [r for r in rows if getattr(r, key, None) in list(vals)]
            elif isinstance(crit, BooleanClauseList) and crit.operator is operators.and_:
                for sub in crit.clauses:
                    rows = self._apply_single(rows, sub)
        return rows

    def _apply_single(self, rows, crit):
        from sqlalchemy.sql import operators

        op = getattr(crit, "operator", None)
        if op is operators.eq:
            key = crit.left.key
            val = crit.right.value if hasattr(crit.right, "value") else crit.right
            return [r for r in rows if getattr(r, key, None) == val]
        if op is operators.in_op:
            key = crit.left.key
            vals = crit.right.value if hasattr(crit.right, "value") else crit.right
            return [r for r in rows if getattr(r, key, None) in list(vals)]
        if op is operators.is_:
            key = crit.left.key
            right = crit.right
            target = right.value if hasattr(right, "value") else right
            if target is False:
                return [r for r in rows if getattr(r, key, None) is False]
            if target is True:
                return [r for r in rows if getattr(r, key, None) is True]
            return [r for r in rows if getattr(r, key, None) is None]
        return rows

    async def execute(self, stmt):
        model = self._model_for_select(stmt)
        rows = list(self._store.get(model, []))
        rows = self._apply_criteria(rows, stmt._where_criteria)
        return _FakeResult(rows)

    async def scalar(self, stmt):
        result = await self.execute(stmt)
        return result.scalars().first()

    def add(self, obj):
        cls = type(obj)
        self._apply_defaults(obj)
        self._store.setdefault(cls, []).append(obj)

    def _apply_defaults(self, obj):
        """Apply SQLAlchemy column defaults the way a real INSERT would."""
        from sqlalchemy import inspect as orm_inspect

        mapper = orm_inspect(type(obj))
        for col in mapper.columns:
            current = getattr(obj, col.key, None)
            if current is not None or col.default is None:
                continue
            default = col.default.arg
            if callable(default):
                try:
                    default = default()
                except Exception:
                    continue
            try:
                setattr(obj, col.key, default)
            except Exception:
                pass

    async def commit(self):
        return None

    async def flush(self):
        return None

    async def refresh(self, obj):
        return None

    async def delete(self, obj):
        cls = type(obj)
        if obj in self._store.get(cls, []):
            self._store[cls].remove(obj)

    async def close(self):
        return None


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return list(self._rows)

    def first(self):
        return self._rows[0] if self._rows else None

    def scalar(self):
        return self._rows[0] if self._rows else None


@pytest.fixture
def fake_session() -> FakeAsyncSession:
    """Fresh in-memory fake async session per test."""
    return FakeAsyncSession()
