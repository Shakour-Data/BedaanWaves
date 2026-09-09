import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class BulkheadConfig:
    max_concurrent_calls: int = 10
    max_waiting: int = 50
    timeout: float = 30.0


class Bulkhead:
    def __init__(self, name: str, config: BulkheadConfig | None = None):
        self.name = name
        self.config = config or BulkheadConfig()
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_calls)
        self.waiting = 0
        self._lock = asyncio.Lock()
        self._logger = logging.getLogger(f"bulkhead.{name}")

    async def execute(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        async with self._lock:
            if self.waiting >= self.config.max_waiting:
                raise RuntimeError(f"Bulkhead {self.name} saturated: {self.waiting} waiting")
            self.waiting += 1
        try:
            async with asyncio.timeout(self.config.timeout):
                async with self.semaphore:
                    async with self._lock:
                        self.waiting = max(0, self.waiting - 1)
                    return await func(*args, **kwargs)
        except TimeoutError:
            self._logger.error("Bulkhead %s call timed out after %s seconds", self.name, self.config.timeout)
            raise
        finally:
            async with self._lock:
                self.waiting = max(0, self.waiting - 1)

    def get_state(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "max_concurrent_calls": self.config.max_concurrent_calls,
            "max_waiting": self.config.max_waiting,
            "waiting": self.waiting,
            "available": self.semaphore._value,
        }
