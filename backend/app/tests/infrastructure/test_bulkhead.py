import asyncio

import pytest

from app.infrastructure.resilience.bulkhead import Bulkhead, BulkheadConfig


class TestBulkhead:
    async def test_executes_under_limit(self):
        bulk = Bulkhead("test", BulkheadConfig(max_concurrent_calls=2, max_waiting=5, timeout=5.0))

        async def ok():
            return 1

        result = await bulk.execute(ok)
        assert result == 1

    async def test_timeout_slow_function(self):
        bulk = Bulkhead("test", BulkheadConfig(max_concurrent_calls=1, max_waiting=5, timeout=0.1))

        async def slow():
            await asyncio.sleep(1.0)
            return 1

        with pytest.raises(TimeoutError):
            await bulk.execute(slow)

    async def test_get_state(self):
        bulk = Bulkhead("test", BulkheadConfig(max_concurrent_calls=2, max_waiting=5, timeout=5.0))

        async def ok():
            return 1

        await bulk.execute(ok)
        state = bulk.get_state()
        assert state["name"] == "test"
        assert state["max_concurrent_calls"] == 2
        assert state["waiting"] == 0
