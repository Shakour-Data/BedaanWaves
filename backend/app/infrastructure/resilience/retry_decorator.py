import asyncio
import functools
import logging
import random
import time
from collections.abc import Callable
from typing import TypeVar

F = TypeVar("F")
T = TypeVar("T")


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    retry_on: type[Exception] | tuple[type[Exception], ...] = (Exception,),
    logger: logging.Logger | None = None,
) -> Callable[[F], F]:
    """Decorator that retries a function with exponential backoff and optional jitter.

    Args:
        max_retries: Maximum number of retry attempts after the initial call.
        base_delay: Initial delay in seconds before the first retry.
        max_delay: Upper bound for the delay between retries.
        jitter: If True, add a random jitter factor to each delay.
        retry_on: Exception type(s) that trigger a retry.
        logger: Optional logger instance. Defaults to a module-level logger.
    """
    _logger = logger or logging.getLogger(__name__)

    def decorator(func: F) -> F:
        is_async = asyncio.iscoroutinefunction(func)

        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args: object, **kwargs: object) -> T:
                attempt = 0
                last_exception: BaseException | None = None
                while attempt <= max_retries:
                    try:
                        return await func(*args, **kwargs)
                    except retry_on as exc:
                        last_exception = exc
                        if attempt >= max_retries:
                            _logger.error(
                                "Max retries exceeded for %s after %s attempts",
                                func.__qualname__,
                                attempt + 1,
                                exc_info=True,
                            )
                            raise
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        if jitter:
                            delay = delay * (0.5 + random.random())
                        _logger.warning(
                            "Retry %s/%s for %s after %s: %s",
                            attempt + 1,
                            max_retries,
                            func.__qualname__,
                            f"{delay:.2f}s",
                            exc,
                        )
                        await asyncio.sleep(delay)
                        attempt += 1
                raise last_exception  # type: ignore[misc]
            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(func)
        def sync_wrapper(*args: object, **kwargs: object) -> T:
            attempt = 0
            last_exception: BaseException | None = None
            while attempt <= max_retries:
                try:
                    return func(*args, **kwargs)
                except retry_on as exc:
                    last_exception = exc
                    if attempt >= max_retries:
                        _logger.error(
                            "Max retries exceeded for %s after %s attempts",
                            func.__qualname__,
                            attempt + 1,
                            exc_info=True,
                        )
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    _logger.warning(
                        "Retry %s/%s for %s after %s: %s",
                        attempt + 1,
                        max_retries,
                        func.__qualname__,
                        f"{delay:.2f}s",
                        exc,
                    )
                    time.sleep(delay)
                    attempt += 1
            raise last_exception  # type: ignore[misc]
        return sync_wrapper  # type: ignore[return-value]

    return decorator
