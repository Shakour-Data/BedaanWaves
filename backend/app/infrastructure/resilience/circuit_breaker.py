import logging
import time
from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any, TypeVar

T = TypeVar("T")


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: float = 0.0
        self.half_open_calls = 0
        self.logger = logging.getLogger(f"circuit_breaker.{name}")

    async def call(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        if self.state == CircuitState.OPEN:
            if time.monotonic() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                self.logger.info("Circuit breaker %s moved to HALF_OPEN", self.name)
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN")

        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is HALF_OPEN and saturated")
            self.half_open_calls += 1

        try:
            result = await func(*args, **kwargs)
        except Exception:
            self._on_failure()
            raise
        else:
            self._on_success()
            return result

    def _on_success(self) -> None:
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.logger.info("Circuit breaker %s recovered, moving to CLOSED", self.name)
        self.state = CircuitState.CLOSED

    def _on_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                self.logger.error(
                    "Circuit breaker %s tripped to OPEN after %s failures", self.name, self.failure_count
                )
            self.state = CircuitState.OPEN

    def reset(self) -> None:
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.half_open_calls = 0
        self.logger.info("Circuit breaker %s manually reset", self.name)

    def get_state(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
        }
