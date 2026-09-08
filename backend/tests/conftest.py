"""
Shared pytest fixtures for BedaanWaves backend tests.

Provides reusable fixtures for Tier 1 core services so individual test
modules stay focused on behaviour rather than setup boilerplate.
"""

import datetime as _dt
import logging
import re
import time
import uuid as _uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import pytest

from app.services.core.dependency_container import DependencyContainer
from app.services.core.config_service import ConfigService
from app.services.core.cache_service import CacheService, MemoryCacheBackend
from app.services.core.logger_service import LoggerService
from app.services.core.health_checker import HealthChecker
from app.services.core.database_service import DatabaseService

from app.core.config import Settings, get_settings
from app.services.data.market_hours_service import MarketHoursService
from app.services.data.real_time_market_data_service import RealTimeMarketDataService
from app.services.live.freshness_validator import FreshnessValidator
from app.services.live.provider_circuit import PerSymbolCircuitBreaker
from app.services.live.orchestrator import LiveDataOrchestrator
from app.services.live.pipeline_metrics import LivePipelineMetrics
from app.services.live.slo_monitor import SLOMonitor


@pytest.fixture
def container() -> DependencyContainer:
    return DependencyContainer()


@pytest.fixture
def config_service() -> ConfigService:
    return ConfigService(env_file=None)


@pytest.fixture
def memory_backend() -> MemoryCacheBackend:
    return MemoryCacheBackend()


@pytest.fixture
def cache_service() -> CacheService:
    return CacheService(backend="memory", default_ttl=60)


@pytest.fixture
def logger_service(tmp_path) -> LoggerService:
    return LoggerService(log_level="DEBUG", log_dir=str(tmp_path / "logs"), enable_file=False)


@pytest.fixture
def health_checker() -> HealthChecker:
    return HealthChecker(check_interval_seconds=1)


@pytest.fixture
def database_service() -> DatabaseService:
    return DatabaseService(
        database_url="postgresql://user:secret@localhost:5432/bedaanwaves_test",
        async_mode=True,
    )


class _FakeNewsClient:
    async def get_market_news(self, *args, **kwargs):
        return []

    async def get_stock_news(self, *args, **kwargs):
        return []

    async def search(self, *args, **kwargs):
        return []

    async def get_related_news(self, *args, **kwargs):
        return []


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
            elif op is operators.is_:
                key = crit.left.key
                right = crit.right
                target = right.value if hasattr(right, "value") else right
                rname = type(right).__name__
                if rname == "False_" or target is False:
                    rows = [r for r in rows if getattr(r, key, None) is False]
                elif rname == "True_" or target is True:
                    rows = [r for r in rows if getattr(r, key, None) is True]
                else:
                    rows = [r for r in rows if getattr(r, key, None) is None]
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
            rname = type(right).__name__
            if rname == "False_" or target is False:
                return [r for r in rows if getattr(r, key, None) is False]
            if rname == "True_" or target is True:
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
        from sqlalchemy import inspect as orm_inspect
        mapper = orm_inspect(type(obj))
        for col in mapper.columns:
            current = getattr(obj, col.key, None)
            if current is not None or col.default is None:
                continue
            if col.key == "id":
                setattr(obj, col.key, _uuid.uuid4())
            elif col.key in ("created_at", "updated_at"):
                setattr(obj, col.key, _dt.datetime.now(_dt.timezone.utc))
            elif not callable(col.default.arg):
                setattr(obj, col.key, col.default.arg)

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


from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.api.routes.health import router as health_router
    _app = FastAPI()
    _app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
    _app.include_router(health_router, prefix="/health", tags=["health"])
    return TestClient(_app)


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

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None

    def mappings(self):
        return self


@pytest.fixture
def fake_session() -> FakeAsyncSession:
    return FakeAsyncSession()


# ======================================================================
# Task 10: Live streaming test fixtures
# ======================================================================


class TestAppSettings(Settings):
    class Config:
        env_file = None
        case_sensitive = True
        extra = "ignore"

    LIVE_POLL_INTERVAL_OPEN_S: int = 1
    LIVE_POLL_INTERVAL_CLOSED_S: int = 1
    LIVE_INTRADAY_POLL_INTERVAL_OPEN_S: int = 1
    LIVE_PING_INTERVAL_S: int = 2
    LIVE_IDLE_UNSUBSCRIBE_S: int = 2
    LIVE_MAX_QUOTE_AGE_OPEN_S: int = 60
    LIVE_MAX_QUOTE_AGE_CLOSED_S: int = 900
    LIVE_CIRCUIT_BREAKER_FAILURES: int = 5
    LIVE_CIRCUIT_BREAKER_HALFOPEN_S: int = 1
    LIVE_POLL_EXECUTOR_MAX: int = 4
    LIVE_BACKOFF_BASE_S: float = 0.05
    LIVE_BACKOFF_MAX_S: float = 2.0
    LIVE_SLO_WARN_MULTIPLIER: float = 1.5
    LIVE_SLO_ERROR_MULTIPLIER: float = 3.0
    REQUIRE_AUTH: bool = False
    SECRET_KEY: str = "test-secret-key-min-32-chars-xxxxxxxxxxxxx"
    JWT_SECRET: str = "test-jwt-secret-min-32-chars-xxxxxxxxxxxx"


def _make_test_settings() -> TestAppSettings:
    return TestAppSettings()


class FakeProviderState:
    def __init__(self):
        self.quote_call_count: Dict[str, int] = {}
        self.intraday_call_count: Dict[str, int] = {}
        self.base_prices: Dict[str, float] = {}
        self.quote_raises: bool = False
        self.intraday_raises: bool = False
        self.always_raise: bool = False
        self.raise_exception_cls: type = ValueError
        self.raise_exception_msg: str = "Provider error"

    def make_fake_quote(self, symbol: str) -> Dict[str, Any]:
        sym = symbol.upper()
        self.quote_call_count[sym] = self.quote_call_count.get(sym, 0) + 1
        n = self.quote_call_count[sym]
        base = self.base_prices.get(sym, 100.0)
        current = round(base + (n * 0.01), 4)
        open_p = base
        high = round(base + 1.0, 4)
        low = round(base - 0.5, 4)
        prev_close = round(base - 0.2, 4)
        change = round(current - prev_close, 4)
        change_pct = round((change / prev_close) * 100.0, 4)
        volume = 1_000_000 + n
        return {
            "symbol": sym,
            "current_price": current,
            "change_value": change,
            "change_percent": change_pct,
            "open": open_p,
            "high": high,
            "low": low,
            "previous_close": prev_close,
            "volume": volume,
            "adjusted_close": current,
            "market_status": "regular",
            "freshness_label": "Live",
            "is_delayed": False,
            "data_source": "yfinance",
            "freshness_ts": datetime.now(timezone.utc),
        }

    def make_fake_intraday(self, symbol: str, interval: str = "5m") -> Dict[str, Any]:
        sym = symbol.upper()
        key = f"{sym}:{interval}"
        self.intraday_call_count[key] = self.intraday_call_count.get(key, 0) + 1
        n = self.intraday_call_count[key]
        base = self.base_prices.get(sym, 100.0)
        now = datetime.now(timezone.utc)
        candles: List[Dict[str, Any]] = []
        for i in range(5):
            ts = now - _dt.timedelta(minutes=(5 - i) * 5)
            o = round(base + (n - 1) * 0.01 + i * 0.002, 4)
            h = round(o + 0.3, 4)
            l = round(o - 0.1, 4)
            c = round(o + 0.15, 4)
            candles.append({
                "timestamp": ts,
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "adjusted_close": c,
                "volume": 10000 + i,
                "split_ratio": None,
                "source": "yfinance",
            })
        return {
            "symbol": sym,
            "interval": interval,
            "candles": candles,
            "market_status": "regular",
            "freshness_label": "Live",
            "data_source": "yfinance",
            "freshness_ts": candles[-1]["timestamp"],
        }


@pytest.fixture
def fake_yfinance_provider(monkeypatch):
    state = FakeProviderState()

    async def _fake_quote_no_cache(self, symbol: str):
        if state.always_raise or state.quote_raises:
            state.quote_raises = False
            raise state.raise_exception_cls(state.raise_exception_msg)
        return state.make_fake_quote(symbol)

    async def _fake_intraday_no_cache(self, symbol: str, interval: str = "5m"):
        if state.always_raise or state.intraday_raises:
            state.intraday_raises = False
            raise state.raise_exception_cls(state.raise_exception_msg)
        return state.make_fake_intraday(symbol, interval)

    monkeypatch.setattr(
        RealTimeMarketDataService,
        "fetch_quote_no_cache",
        _fake_quote_no_cache,
    )
    monkeypatch.setattr(
        RealTimeMarketDataService,
        "fetch_intraday_no_cache",
        _fake_intraday_no_cache,
    )
    return state


class _FakeMarketHoursAlwaysOpen:
    def get_market_status(self) -> dict:
        return {
            "status": "regular",
            "freshness_label": "Live",
            "is_trading": True,
            "is_delayed": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class _FakeMarketHoursAlwaysClosed:
    def get_market_status(self) -> dict:
        return {
            "status": "closed",
            "freshness_label": "Market Closed",
            "is_trading": False,
            "is_delayed": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class _FakeNotificationDispatcher:
    def __init__(self):
        self.calls: List[Dict[str, Any]] = []

    async def publish_event(self, **kwargs):
        self.calls.append(dict(kwargs))
        return {"dispatched": True, "id": str(_uuid.uuid4())}

    def call_count(self) -> int:
        return len(self.calls)

    def last_call(self) -> Optional[Dict[str, Any]]:
        return self.calls[-1] if self.calls else None

    def calls_with_severity(self, severity: str) -> List[Dict[str, Any]]:
        out = []
        sev = severity.upper()
        for c in self.calls:
            payload = c.get("payload") or {}
            if str(payload.get("severity", "")).upper() == sev:
                out.append(c)
        return out


@dataclass
class InMemoryOrchestratorBundle:
    settings: TestAppSettings
    market_hours_open: Any
    market_hours_closed: Any
    freshness_validator: FreshnessValidator
    circuit_breaker: PerSymbolCircuitBreaker
    pipeline_metrics: LivePipelineMetrics
    orchestrator: LiveDataOrchestrator
    slo_monitor: SLOMonitor
    notification_dispatcher: _FakeNotificationDispatcher
    market_data_service: RealTimeMarketDataService


@pytest.fixture
def in_memory_orchestrator(fake_yfinance_provider):
    settings = _make_test_settings()
    market_hours_open = _FakeMarketHoursAlwaysOpen()
    market_hours_closed = _FakeMarketHoursAlwaysClosed()
    dispatcher = _FakeNotificationDispatcher()

    fv = FreshnessValidator(market_hours=market_hours_open, settings=settings)
    cb = PerSymbolCircuitBreaker(
        failure_threshold=settings.LIVE_CIRCUIT_BREAKER_FAILURES,
        halfopen_s=float(settings.LIVE_CIRCUIT_BREAKER_HALFOPEN_S),
    )
    pm = LivePipelineMetrics()
    rt = RealTimeMarketDataService(cache_service=None)
    orch = LiveDataOrchestrator(
        market_data_service=rt,
        market_hours_service=market_hours_open,
        freshness_validator=fv,
        circuit_breaker=cb,
        settings=settings,
        metrics_service=pm,
        scoring_service=None,
        news_service=None,
    )
    slo = SLOMonitor(notification_dispatcher=dispatcher, settings=settings)
    slo.bind_orchestrator(orch)

    def _slo_hook(env, age, thresh):
        try:
            slo.observe_envelope(env, data_age_ms=age, threshold_s=thresh)
        except Exception:
            pass

    orch.slo_monitor_hook = _slo_hook

    return InMemoryOrchestratorBundle(
        settings=settings,
        market_hours_open=market_hours_open,
        market_hours_closed=market_hours_closed,
        freshness_validator=fv,
        circuit_breaker=cb,
        pipeline_metrics=pm,
        orchestrator=orch,
        slo_monitor=slo,
        notification_dispatcher=dispatcher,
        market_data_service=rt,
    )


@dataclass
class SSEEvent:
    event: str
    data: Dict[str, Any]
    raw: str = ""


class LiveSSEClient:
    def __init__(self, client: Any):
        self._client = client

    async def collect_events(
        self,
        url: str,
        count: int = 3,
        timeout_s: float = 5.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> List[SSEEvent]:
        events: List[SSEEvent] = []
        deadline = time.monotonic() + timeout_s
        merged_headers = dict(headers or {})
        merged_headers.setdefault("Accept", "text/event-stream")
        import json as _json

        async with self._client.stream(
            "GET", url, headers=merged_headers, timeout=timeout_s + 1.0
        ) as resp:
            buffer = ""
            async for chunk in resp.aiter_text():
                if time.monotonic() >= deadline:
                    break
                buffer += chunk
                while "\n\n" in buffer:
                    block, buffer = buffer.split("\n\n", 1)
                    parsed = self._parse_block(block, _json)
                    if parsed is not None:
                        events.append(parsed)
                        if len(events) >= count:
                            return events
                if len(events) >= count:
                    break
        return events

    @staticmethod
    def _parse_block(block: str, _json: Any) -> Optional[SSEEvent]:
        event_name = "message"
        data_lines: List[str] = []
        for line in block.split("\n"):
            if not line or line.startswith(":"):
                continue
            if line.startswith("event:"):
                event_name = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data_lines.append(line[len("data:"):].strip())
        if not data_lines:
            return None
        try:
            data_obj = _json.loads("\n".join(data_lines)) if data_lines else {}
        except (_json.JSONDecodeError, ValueError):
            data_obj = {"_raw": "\n".join(data_lines)}
        if not isinstance(data_obj, dict):
            data_obj = {"value": data_obj}
        return SSEEvent(event=event_name, data=data_obj, raw=block)


@pytest.fixture
async def live_sse_client():
    httpx = pytest.importorskip("httpx")
    async with httpx.AsyncClient() as client:
        yield LiveSSEClient(client)


@dataclass
class ScrubbedLogsCapture:
    records: List[str] = field(default_factory=list)
    _handler: Optional[logging.Handler] = None
    _loggers: List[logging.Logger] = field(default_factory=list)

    def assert_no_token(self, token: str) -> None:
        if not token:
            return
        matches = [line for line in self.records if token in line]
        assert not matches, (
            f"Found token {token!r} in logs ({len(matches)} occurrences):\n"
            + "\n".join(matches[:5])
        )

    def contains(self, substring: str) -> bool:
        return any(substring in line for line in self.records)


@pytest.fixture
def scrubbed_logs_cap():
    capture = ScrubbedLogsCapture()

    class _ListHandler(logging.Handler):
        def __init__(self, cap: ScrubbedLogsCapture):
            super().__init__(level=logging.DEBUG)
            self._cap = cap

        def emit(self, record: logging.LogRecord) -> None:
            try:
                msg = self.format(record)
            except Exception:
                msg = record.getMessage()
            self._cap.records.append(msg)

    handler = _ListHandler(capture)
    formatter = logging.Formatter("%(name)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    capture._handler = handler

    logger_names = [
        "app.services.live",
        "app.services.live.orchestrator",
        "app.services.live.freshness_validator",
        "app.services.live.provider_circuit",
        "app.services.live.pipeline_metrics",
        "app.services.live.slo_monitor",
        "app.api.routes.live_sse",
        "app.api.routes.live",
    ]
    for name in logger_names:
        lg = logging.getLogger(name)
        lg.addHandler(handler)
        lg.setLevel(logging.DEBUG)
        lg.propagate = False
        capture._loggers.append(lg)

    try:
        yield capture
    finally:
        for lg in capture._loggers:
            lg.removeHandler(handler)
