import asyncio
import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Event:
    event_type: str
    data: dict[str, Any]
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    source: str = "unknown"
    correlation_id: str | None = None


EventHandler = Callable[[Event], Awaitable[None]]


class EventBus(ABC):
    @abstractmethod
    async def publish(self, event: Event) -> None:
        raise NotImplementedError

    @abstractmethod
    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        raise NotImplementedError

    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError


class InMemoryEventBus(EventBus):
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}
        self._queue: asyncio.Queue[Event] | None = None
        self._running = False
        self._logger = logging.getLogger("event_bus.memory")

    async def start(self) -> None:
        self._queue = asyncio.Queue()
        self._running = True
        asyncio.create_task(self._consume())

    async def stop(self) -> None:
        self._running = False

    async def publish(self, event: Event) -> None:
        if not self._queue:
            raise RuntimeError("EventBus not started")
        await self._queue.put(event)

    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def _consume(self) -> None:
        while self._running:
            queue = self._queue
            if not queue:
                break
            event = await queue.get()
            for handler in self._handlers.get(event.event_type, []):
                try:
                    await handler(event)
                except Exception as exc:
                    self._logger.error("Event handler failed for %s: %s", event.event_type, exc)


class KafkaEventBus(EventBus):
    def __init__(self, bootstrap_servers: str, client_id: str = "bedaanwaves") -> None:
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self._producer: Any = None
        self._consumer: Any = None
        self._running = False
        self._logger = logging.getLogger("event_bus.kafka")

    async def start(self) -> None:
        try:
            from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

            self._producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers, client_id=self.client_id)
            self._consumer = AIOKafkaConsumer(bootstrap_servers=self.bootstrap_servers, client_id=self.client_id)
            await self._producer.start()
            await self._consumer.start()
            self._running = True
        except ImportError:
            self._logger.warning("aiokafka not installed; KafkaEventBus falling back to no-op")
            self._running = False

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
        if self._consumer is not None:
            await self._consumer.stop()
        self._running = False

    async def publish(self, event: Event) -> None:
        if not self._producer:
            return
        topic = event.event_type
        payload = json.dumps({
            "event_type": event.event_type,
            "data": event.data,
            "occurred_at": event.occurred_at.isoformat(),
            "source": event.source,
            "correlation_id": event.correlation_id,
        }).encode("utf-8")
        await self._producer.send_and_wait(topic, payload)

    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if not self._consumer:
            return
        self._consumer.subscribe([event_type])
