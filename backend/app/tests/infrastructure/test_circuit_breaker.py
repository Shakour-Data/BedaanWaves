import asyncio

import pytest

from app.infrastructure.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)


class FakeService:
    def __init__(self, fail_count: int = 0):
        self.calls = 0
        self.fail_count = fail_count
        self._failures = 0

    async def call(self):
        self.calls += 1
        if self._failures < self.fail_count:
            self._failures += 1
            raise RuntimeError("boom")
        return "ok"


class TestCircuitBreaker:
    @pytest.fixture
    def breaker(self):
        return CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=1.0)

    async def test_closed_state_success(self, breaker):
        svc = FakeService(fail_count=0)
        result = await breaker.call(svc.call)
        assert result == "ok"
        assert breaker.state == CircuitState.CLOSED

    async def test_opens_after_threshold(self, breaker):
        svc = FakeService(fail_count=5)
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await breaker.call(svc.call)
        assert breaker.state == CircuitState.OPEN

    async def test_open_blocks_calls(self, breaker):
        svc = FakeService(fail_count=5)
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await breaker.call(svc.call)
        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(svc.call)

    async def test_half_open_recovery(self, breaker):
        svc = FakeService(fail_count=3)
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await breaker.call(svc.call)
        await asyncio.sleep(1.1)
        result = await breaker.call(svc.call)
        assert result == "ok"
        assert breaker.state == CircuitState.CLOSED
