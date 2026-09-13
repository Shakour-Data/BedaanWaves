"""
Unit tests for enhanced SEC EDGAR financial statement ingestion.

Covers the ``min_quarters`` / ``skip_if_sufficient`` parameters,
the ``count_quarters_in_db`` helper, and the return-value structure
for the bulk-enrichment path.
"""

import uuid

import pytest

pytestmark = pytest.mark.unit


class FakeScalarResult:
    def __init__(self, val: int | None):
        self._val = val

    def scalar(self):
        return self._val


class FakeAsyncSession:
    """Minimal async session stub that returns pre-seeded row counts."""

    def __init__(self, count: int = 0):
        self._count = count
        self.committed = False

    async def execute(self, stmt):
        return FakeScalarResult(self._count)

    async def commit(self):
        self.committed = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False


class FakeAsyncSessionMaker:
    """Callable that mimics ``async_sessionmaker`` returning a fake session."""

    def __init__(self, count: int = 0):
        self._count = count

    def __call__(self):
        return FakeAsyncSession(self._count)


class TestCountQuartersInDb:
    async def test_returns_zero_when_no_data(self, monkeypatch):
        from app.services.data import sec_edgar_client as sec_mod

        monkeypatch.setattr(sec_mod, "async_session_maker", FakeAsyncSessionMaker(count=0))

        svc = sec_mod.SEDGARFinancialService()
        count = await svc.count_quarters_in_db(str(uuid.uuid4()))
        assert count == 0

    async def test_returns_actual_count(self, monkeypatch):
        from app.services.data import sec_edgar_client as sec_mod

        monkeypatch.setattr(sec_mod, "async_session_maker", FakeAsyncSessionMaker(count=23))

        svc = sec_mod.SEDGARFinancialService()
        count = await svc.count_quarters_in_db(str(uuid.uuid4()))
        assert count == 23


class TestIngestSecFinancialsParams:
    async def test_skip_when_sufficient(self, monkeypatch):
        from app.services.data import sec_edgar_client as sec_mod

        monkeypatch.setattr(sec_mod, "async_session_maker", FakeAsyncSessionMaker(count=25))

        svc = sec_mod.SEDGARFinancialService()

        fetch_called = False

        async def _fake_fetch(cik):
            nonlocal fetch_called
            fetch_called = True
            return None

        async def _fake_lookup_cik(symbol, company_name=""):
            return "0000320193"

        monkeypatch.setattr(svc, "fetch_company_facts", _fake_fetch)
        monkeypatch.setattr(svc, "lookup_cik", _fake_lookup_cik)

        result = await svc.ingest_sec_financials(
            "AAPL", str(uuid.uuid4()),
            min_quarters=20, skip_if_sufficient=True,
        )
        assert result.get("skipped") is True
        assert result["statements"] == 0
        assert fetch_called is False

    async def test_proceeds_when_insufficient(self, monkeypatch):
        from app.services.data import sec_edgar_client as sec_mod

        monkeypatch.setattr(sec_mod, "async_session_maker", FakeAsyncSessionMaker(count=3))

        svc = sec_mod.SEDGARFinancialService()

        async def _fake_fetch(cik):
            return {"facts": {"us-gaap": {}}}

        async def _fake_lookup_cik(symbol, company_name=""):
            return "0000320193"

        monkeypatch.setattr(svc, "fetch_company_facts", _fake_fetch)
        monkeypatch.setattr(svc, "lookup_cik", _fake_lookup_cik)
        monkeypatch.setattr(svc, "_save_cik_cache", lambda: None)

        result = await svc.ingest_sec_financials(
            "AAPL", str(uuid.uuid4()),
            min_quarters=20, skip_if_sufficient=True,
        )
        assert not result.get("skipped")
        assert "statements" in result

    async def test_no_skip_when_min_quarters_zero(self, monkeypatch):
        from app.services.data import sec_edgar_client as sec_mod

        monkeypatch.setattr(sec_mod, "async_session_maker", FakeAsyncSessionMaker(count=100))

        svc = sec_mod.SEDGARFinancialService()

        async def _fake_fetch(cik):
            return {"facts": {"us-gaap": {}}}

        async def _fake_lookup_cik(symbol, company_name=""):
            return "0000320193"

        monkeypatch.setattr(svc, "fetch_company_facts", _fake_fetch)
        monkeypatch.setattr(svc, "lookup_cik", _fake_lookup_cik)

        result = await svc.ingest_sec_financials(
            "AAPL", str(uuid.uuid4()),
            min_quarters=0, skip_if_sufficient=False,
        )
        assert not result.get("skipped")
