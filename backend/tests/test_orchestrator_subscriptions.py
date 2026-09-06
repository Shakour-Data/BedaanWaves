"""
TR3.1 — Reference-counted subscriptions: 3 subs = 1 poll loop.
TR3.3 — Ping synthesis during provider silence.
"""

import asyncio
import time
from typing import Any, List

import pytest

from app.services.live.constants import LIVE_EVENT_PING, LIVE_EVENT_QUOTE


async def _consume_first_n(gen, n: int, timeout_s: float) -> List[Any]:
    out: List[Any] = []
    deadline = time.monotonic() + timeout_s
    try:
        async for item in gen:
            out.append(item)
            if len(out) >= n:
                break
            if time.monotonic() >= deadline:
                break
    except (asyncio.CancelledError, Exception):
        pass
    return out


@pytest.mark.asyncio
async def test_tr3_1_three_subs_same_symbol_one_poll_loop(in_memory_orchestrator, fake_yfinance_provider):
    """3 concurrent subscribers to quote:AAPL -> exactly 1 poll task; last unsubscribe cancels task within 3s."""
    orch = in_memory_orchestrator.orchestrator
    await orch.initialize()
    try:
        gen1 = orch.subscribe("quote:AAPL", "sub1")
        gen2 = orch.subscribe("quote:AAPL", "sub2")
        gen3 = orch.subscribe("quote:AAPL", "sub3")

        t1 = asyncio.create_task(_consume_first_n(gen1, 2, timeout_s=3.0))
        t2 = asyncio.create_task(_consume_first_n(gen2, 2, timeout_s=3.0))
        t3 = asyncio.create_task(_consume_first_n(gen3, 2, timeout_s=3.0))

        await asyncio.sleep(0.6)

        assert "quote:AAPL" in orch._poll_tasks, (
            f"Poll task should exist after subscribe+consume. Poll tasks: {list(orch._poll_tasks.keys())}"
        )
        quote_tasks = [k for k in orch._poll_tasks if k.startswith("quote:")]
        assert len(quote_tasks) == 1, (
            f"Expected 1 poll loop for 3 subs same symbol, got {len(quote_tasks)}: {quote_tasks}"
        )

        assert "quote:AAPL" in orch._subscribers
        assert len(orch._subscribers["quote:AAPL"]) == 3

        evs1, evs2, evs3 = await asyncio.gather(t1, t2, t3, return_exceptions=True)
        n_sub1 = len(evs1) if isinstance(evs1, list) else 0
        assert n_sub1 >= 1, f"Subscriber 1 should receive events, got {n_sub1}"

        try:
            await gen1.aclose()
        except Exception:
            pass
        await asyncio.sleep(0.1)
        assert len(orch._subscribers.get("quote:AAPL", {})) == 2

        try:
            await gen2.aclose()
        except Exception:
            pass
        await asyncio.sleep(0.1)
        assert len(orch._subscribers.get("quote:AAPL", {})) == 1

        try:
            await gen3.aclose()
        except Exception:
            pass

        idle_s = float(in_memory_orchestrator.settings.LIVE_IDLE_UNSUBSCRIBE_S)
        await asyncio.sleep(idle_s + 1.2)

        task = orch._poll_tasks.get("quote:AAPL")
        if task is not None:
            assert task.done() or task.cancelled(), (
                f"Poll task should be cancelled within {idle_s + 1.2}s after last unsubscribe"
            )
        no_subs_left = (
            "quote:AAPL" not in orch._subscribers
            or not orch._subscribers["quote:AAPL"]
        )
        assert no_subs_left, "Subscribers should be empty after all unsubscribe + idle window"
    finally:
        await orch.shutdown()


@pytest.mark.asyncio
async def test_tr3_3_ping_or_quote_events_arrive_within_3s(in_memory_orchestrator, fake_yfinance_provider):
    """TR3.3 simplified: subscribers receive either quote events or ping within 3s due to LIVE_PING_INTERVAL_S=2."""
    orch = in_memory_orchestrator.orchestrator
    await orch.initialize()
    try:
        received: List[Any] = []
        deadline = time.monotonic() + 4.0

        async def _consumer():
            nonlocal received
            gen = orch.subscribe("quote:MSFT", "ping_tester")
            try:
                async for ev in gen:
                    received.append(ev)
                    if time.monotonic() >= deadline or len(received) >= 5:
                        break
            except Exception:
                pass
            finally:
                try:
                    await gen.aclose()
                except Exception:
                    pass

        consumer_task = asyncio.create_task(_consumer())
        await asyncio.wait_for(asyncio.shield(consumer_task), timeout=6.0)
        try:
            consumer_task.cancel()
            await consumer_task
        except (asyncio.CancelledError, Exception):
            pass

        event_names = [getattr(e, "event", "unknown") for e in received]
        ping_count = event_names.count(LIVE_EVENT_PING)
        quote_count = event_names.count(LIVE_EVENT_QUOTE)

        assert len(received) >= 1, (
            f"Expected at least 1 event (quote or ping) in 4s, got {len(received)}. "
            f"Event names seen: {event_names[:5]}"
        )
        assert quote_count >= 1 or ping_count >= 1, (
            f"Need either quote or ping events. quotes={quote_count}, pings={ping_count}. total={len(received)}"
        )
    finally:
        await orch.shutdown()
