"""
TR3.2 — LiveDataOrchestrator uses only fetch_*_no_cache methods.
CacheService.get/set must NEVER be called for quote:AAPL or intraday:AAPL:* keys.
"""

import asyncio
import time
from typing import Any, Dict, List

import pytest

from app.services.core.cache_service import CacheService, MemoryCacheBackend


class _SpyingMemoryBackend(MemoryCacheBackend):
    def __init__(self):
        super().__init__()
        self.get_calls: List[str] = []
        self.set_calls: List[str] = []
        self.delete_calls: List[str] = []

    async def get(self, key: str):
        self.get_calls.append(key)
        return await super().get(key)

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        self.set_calls.append(key)
        await super().set(key, value, ttl)

    async def delete(self, key: str) -> None:
        self.delete_calls.append(key)
        await super().delete(key)


@pytest.mark.asyncio
async def test_tr3_2_no_cache_get_set_calls_for_quote_keys(in_memory_orchestrator, fake_yfinance_provider):
    """Run orchestrator.subscribe quote:AAPL for 5 ticks -> assert spying CacheService backend.get/.set called zero times for quote: or intraday:AAPL keys."""
    orch = in_memory_orchestrator.orchestrator
    rt_service = in_memory_orchestrator.market_data_service

    spying_backend = _SpyingMemoryBackend()
    spying_cache = CacheService(backend="memory", default_ttl=60)
    spying_cache._backend = spying_backend

    rt_service._cache_service = spying_cache

    await orch.initialize()
    try:
        received: List[Any] = []
        gen = orch.subscribe("quote:AAPL", "no_cache_inspector")

        deadline = time.monotonic() + 4.0
        min_ticks = 3
        try:
            async for ev in gen:
                received.append(ev)
                if len(received) >= min_ticks or time.monotonic() >= deadline:
                    break
        except Exception:
            pass
        finally:
            try:
                await gen.aclose()
            except Exception:
                pass

        assert len(received) >= 1, f"Expected at least 1 tick, got {len(received)}"

        quote_get = [k for k in spying_backend.get_calls if k.startswith("quote:AAPL") or k.startswith("quote:")]
        quote_set = [k for k in spying_backend.set_calls if k.startswith("quote:AAPL") or k.startswith("quote:")]
        intraday_get = [k for k in spying_backend.get_calls if k.startswith("intraday:AAPL:") or k.startswith("intraday:")]
        intraday_set = [k for k in spying_backend.set_calls if k.startswith("intraday:AAPL:") or k.startswith("intraday:")]

        assert len(quote_get) == 0, f"quote:* get calls should be 0, got {quote_get}"
        assert len(quote_set) == 0, f"quote:* set calls should be 0, got {quote_set}"
        assert len(intraday_get) == 0, f"intraday:AAPL:* get calls should be 0, got {intraday_get}"
        assert len(intraday_set) == 0, f"intraday:AAPL:* set calls should be 0, got {intraday_set}"
    finally:
        await orch.shutdown()
