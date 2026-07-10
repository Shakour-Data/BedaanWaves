"""Unit tests for Tier 2 BrsApiClient and RateLimiter."""

import time

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.data.brs_api_client import BrsApiClient, RateLimiter

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# RateLimiter tests
# ---------------------------------------------------------------------------


class TestRateLimiterStatus:
    def test_initial_status(self):
        limiter = RateLimiter(max_daily_requests=10, max_window_requests=5, window_seconds=60)
        status = limiter.status()
        assert status["daily_used"] == 0
        assert status["daily_limit"] == 10
        assert status["window_limit"] == 5


class TestRateLimiterAcquire:
    def test_acquire_within_limits(self):
        limiter = RateLimiter(max_daily_requests=10, max_window_requests=5, window_seconds=60)
        limiter.acquire()
        status = limiter.status()
        assert status["daily_used"] == 1
        assert status["window_used"] == 1

    def test_acquire_raises_when_daily_limit_reached(self):
        limiter = RateLimiter(max_daily_requests=2, max_window_requests=5, window_seconds=60)
        limiter.acquire()
        limiter.acquire()
        with pytest.raises(RuntimeError, match="daily limit reached"):
            limiter.acquire()

    def test_acquire_raises_when_window_limit_reached(self):
        limiter = RateLimiter(max_daily_requests=1000, max_window_requests=2, window_seconds=60)
        limiter.acquire()
        limiter.acquire()
        with pytest.raises(RuntimeError, match="short-term limit reached"):
            limiter.acquire()

    def test_clean_window_removes_old_timestamps(self):
        limiter = RateLimiter(max_daily_requests=1000, max_window_requests=2, window_seconds=60)
        times = [1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 2500.0, 2500.0, 2500.0, 2500.0, 2500.0, 2500.0]
        with patch.object(time, "time", side_effect=times):
            limiter.acquire()
            limiter.acquire()
            limiter.acquire()
            status = limiter.status()
        assert status["window_used"] == 1

    def test_rotate_day_resets_daily_count(self):
        limiter = RateLimiter(max_daily_requests=2, max_window_requests=5, window_seconds=60)
        limiter.acquire()
        limiter.acquire()
        assert limiter.status()["daily_used"] == 2
        with patch.object(time, "time", return_value=limiter.daily_reset + 1):
            limiter.acquire()
        assert limiter.status()["daily_used"] == 1


# ---------------------------------------------------------------------------
# BrsApiClient tests
# ---------------------------------------------------------------------------


class TestBrsApiClientInitialization:
    def test_default_service_name(self):
        client = BrsApiClient()
        assert client.service_name == "BrsApiClient"

    async def test_initialize_creates_session(self):
        client = BrsApiClient()
        await client.initialize()
        assert client.session is not None
        assert not client.session.closed
        await client.shutdown()

    async def test_shutdown_closes_session(self):
        client = BrsApiClient()
        await client.initialize()
        await client.shutdown()
        assert client.session.closed


class TestBrsApiClientRequest:
    async def test_request_raises_when_not_initialized(self):
        client = BrsApiClient()
        with pytest.raises(RuntimeError, match="not initialized"):
            await client._request("/Tsetmc/Symbol.php")

    async def test_request_injects_api_key(self):
        client = BrsApiClient(api_key="ABC123")
        session_mock = MagicMock()
        response_mock = AsyncMock()
        response_mock.status = 200
        response_mock.json = AsyncMock(return_value={"ok": True})
        cm = AsyncMock()
        cm.__aenter__.return_value = response_mock
        cm.__aexit__.return_value = False
        session_mock.get.return_value = cm
        client.session = session_mock

        result = await client._request("/Tsetmc/Symbol.php", {"l18": "فملی"})
        assert result == {"ok": True}
        called_params = session_mock.get.call_args[1]["params"]
        assert called_params["key"] == "ABC123"
        assert called_params["l18"] == "فملی"

    async def test_request_sets_browser_user_agent(self):
        client = BrsApiClient()
        session_mock = MagicMock()
        response_mock = AsyncMock()
        response_mock.status = 200
        response_mock.json = AsyncMock(return_value={"ok": True})
        cm = AsyncMock()
        cm.__aenter__.return_value = response_mock
        cm.__aexit__.return_value = False
        session_mock.get.return_value = cm
        client.session = session_mock

        await client._request("/Tsetmc/Symbol.php", {})
        headers = session_mock.get.call_args[1]["headers"]
        assert "Mozilla/5.0" in headers["User-Agent"]

    async def test_request_returns_data_on_200(self):
        client = BrsApiClient()
        session_mock = MagicMock()
        response_mock = AsyncMock()
        response_mock.status = 200
        response_mock.json = AsyncMock(return_value={"data": 1})
        cm = AsyncMock()
        cm.__aenter__.return_value = response_mock
        cm.__aexit__.return_value = False
        session_mock.get.return_value = cm
        client.session = session_mock

        result = await client._request("/Tsetmc/Symbol.php")
        assert result == {"data": 1}

    async def test_request_raises_on_api_error(self):
        client = BrsApiClient()
        session_mock = MagicMock()
        response_mock = AsyncMock()
        response_mock.status = 500
        response_mock.json = AsyncMock(return_value={"error": "server"})
        cm = AsyncMock()
        cm.__aenter__.return_value = response_mock
        cm.__aexit__.return_value = False
        session_mock.get.return_value = cm
        client.session = session_mock

        with pytest.raises(RuntimeError, match="BrsApi error 500"):
            await client._request("/Tsetmc/Symbol.php")

    async def test_request_retries_on_client_error(self):
        from aiohttp import ClientError

        client = BrsApiClient(max_retries=2)
        session_mock = MagicMock()
        client.session = session_mock

        class _FailingCM:
            async def __aenter__(self):
                raise ClientError("network")

            async def __aexit__(self, *args):
                return False

        session_mock.get.return_value = _FailingCM()

        with pytest.raises(ClientError, match="network"):
            await client._request("/Tsetmc/Symbol.php")

        assert session_mock.get.call_count == 2


class TestBrsApiClientEndpoints:
    async def test_get_all_symbols(self):
        client = BrsApiClient()
        with patch.object(client, "_request", new_callable=AsyncMock, return_value={"symbols": [{"s": 1}]}) as mock_req:
            result = await client.get_all_symbols(market_type=1)
            assert result == [{"s": 1}]
            mock_req.assert_awaited_once_with("/Tsetmc/AllSymbols.php", {"type": 1})

    async def test_get_symbol(self):
        client = BrsApiClient()
        with patch.object(client, "_request", new_callable=AsyncMock, return_value={"symbol": "فملی"}) as mock_req:
            result = await client.get_symbol("فملی")
            assert result == {"symbol": "فملی"}
            mock_req.assert_awaited_once_with("/Tsetmc/Symbol.php", {"l18": "فملی"})

    async def test_get_candlestick(self):
        client = BrsApiClient()
        with patch.object(client, "_request", new_callable=AsyncMock, return_value={"candles": []}) as mock_req:
            result = await client.get_candlestick("فملی", candle_type=2)
            assert result == {"candles": []}
            mock_req.assert_awaited_once_with("/Tsetmc/Candlestick.php", {"type": 2, "l18": "فملی"})

    async def test_get_history(self):
        client = BrsApiClient()
        with patch.object(client, "_request", new_callable=AsyncMock, return_value=[{"date": "2025-01-01"}]) as mock_req:
            result = await client.get_history("فملی", history_type=0)
            assert result == [{"date": "2025-01-01"}]
            mock_req.assert_awaited_once_with("/Tsetmc/History.php", {"type": 0, "l18": "فملی"})

    async def test_get_codal(self):
        client = BrsApiClient()
        with patch.object(client, "_request", new_callable=AsyncMock, return_value={"announcements": []}) as mock_req:
            result = await client.get_codal(l18="فملی", category=1, date_start="2025-01-01", date_end="2025-01-31", page=2)
            assert result == {"announcements": []}
            mock_req.assert_awaited_once_with(
                "/Codal/Announcement.php",
                {"page": 2, "l18": "فملی", "category": 1, "date_start": "2025-01-01", "date_end": "2025-01-31"},
            )

    async def test_get_ime_physical(self):
        client = BrsApiClient()
        with patch.object(client, "_request", new_callable=AsyncMock, return_value={"physical": []}) as mock_req:
            result = await client.get_ime_physical()
            assert result == []
            mock_req.assert_awaited_once_with("/IME/Physical.php")