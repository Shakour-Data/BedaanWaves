import asyncio

import pytest

from app.infrastructure.events.event_bus import Event, InMemoryEventBus


class TestInMemoryEventBus:
    @pytest.fixture
    async def bus(self):
        bus = InMemoryEventBus()
        await bus.start()
        yield bus
        await bus.stop()

    async def test_publish_subscribe(self, bus):
        received = []

        async def handler(event: Event):
            received.append(event)

        await bus.subscribe("test", handler)
        await bus.publish(Event(event_type="test", data={"key": "value"}))

        await asyncio.sleep(0.1)
        assert len(received) == 1
        assert received[0].data == {"key": "value"}

    async def test_multiple_handlers(self, bus):
        received = []

        async def handler1(event: Event):
            received.append("h1")

        async def handler2(event: Event):
            received.append("h2")

        await bus.subscribe("test", handler1)
        await bus.subscribe("test", handler2)
        await bus.publish(Event(event_type="test", data={}))

        await asyncio.sleep(0.1)
        assert received == ["h1", "h2"]

    async def test_no_handler_does_not_raise(self, bus):
        await bus.publish(Event(event_type="no-handler", data={}))
        await asyncio.sleep(0.1)
