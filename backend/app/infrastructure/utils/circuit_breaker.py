import time
import asyncio
from typing import Callable, Any, Type, Optional
from ...application.interfaces.i_logger import ILogger

class CircuitBreaker:
    """
    Infrastructure implementation of Circuit Breaker pattern.
    Protects against cascading failures in external API calls.
    """
    
    def __init__(
        self, 
        logger: ILogger,
        failure_threshold: int = 5, 
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        self._logger = logger
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._expected_exception = expected_exception
        
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = "CLOSED" # CLOSED, OPEN, HALF_OPEN

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        self._check_state()
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self._expected_exception as e:
            self._on_failure(e)
            raise e

    def _check_state(self):
        if self._state == "OPEN":
            if time.time() - self._last_failure_time > self._recovery_timeout:
                self._state = "HALF_OPEN"
                self._logger.info("Circuit breaker state changed to HALF_OPEN")
            else:
                raise RuntimeError("Circuit breaker is OPEN")

    def _on_success(self):
        if self._state != "CLOSED":
            self._logger.info("Circuit breaker state changed to CLOSED")
        self._failure_count = 0
        self._state = "CLOSED"

    def _on_failure(self, error: Exception):
        self._failure_count += 1
        self._last_failure_time = time.time()
        self._logger.warning(f"Circuit breaker recorded failure: {str(error)}")
        
        if self._failure_count >= self._failure_threshold:
            self._state = "OPEN"
            self._logger.error("Circuit breaker state changed to OPEN")
