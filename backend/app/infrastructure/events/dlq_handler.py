"""
Dead Letter Queue (DLQ) Handler for Kafka

Handles failed messages by routing them to DLQ topics
with retry tracking and manual reprocessing capabilities.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable

logger = logging.getLogger(__name__)


class DLQHandler:
    """
    Manages Dead Letter Queue operations for Kafka consumers.

    Features:
    - Automatic routing to DLQ on max retries exceeded
    - Metadata tracking (failure reason, retry count, timestamps)
    - Manual reprocessing of DLQ messages
    - DLQ monitoring and alerting
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        max_retries: int = 3,
        dlq_topic_prefix: str = "bedaanwaves.dlq",
    ):
        self.bootstrap_servers = bootstrap_servers
        self.max_retries = max_retries
        self.dlq_topic_prefix = dlq_topic_prefix
        self._producer = None
        self._logger = logging.getLogger("dlq.handler")

    async def initialize(self) -> None:
        """Initialize Kafka producer for DLQ."""
        try:
            from aiokafka import AIOKafkaProducer

            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id="bedaanwaves-dlq-handler",
                acks="all",
                enable_idempotence=True,
            )
            await self._producer.start()
            self._logger.info("DLQ handler initialized")
        except ImportError:
            self._logger.warning("aiokafka not available; DLQ handler disabled")

    async def shutdown(self) -> None:
        """Shutdown DLQ producer."""
        if self._producer:
            await self._producer.stop()
            self._logger.info("DLQ handler shutdown")

    async def send_to_dlq(
        self,
        original_topic: str,
        message: Any,
        error: Exception,
        retry_count: int,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Send a failed message to the appropriate DLQ topic.

        Args:
            original_topic: The original Kafka topic
            message: The failed message payload
            error: The exception that caused the failure
            retry_count: Number of retry attempts made
            metadata: Additional context metadata
        """
        if self._producer is None:
            self._logger.error("DLQ producer not initialized")
            return

        dlq_topic = self._get_dlq_topic(original_topic)

        dlq_message = {
            "original_topic": original_topic,
            "original_message": (
                message.decode("utf-8") if isinstance(message, bytes) else str(message)
            ),
            "error": str(error),
            "error_type": type(error).__name__,
            "retry_count": retry_count,
            "max_retries": self.max_retries,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        try:
            await self._producer.send_and_wait(
                dlq_topic,
                json.dumps(dlq_message).encode("utf-8"),
                headers={
                    "original-topic": original_topic.encode("utf-8"),
                    "retry-count": str(retry_count).encode("utf-8"),
                    "error-type": type(error).__name__.encode("utf-8"),
                },
            )
            self._logger.warning(
                f"Message sent to DLQ {dlq_topic} (original: {original_topic}, "
                f"retries: {retry_count})"
            )
        except Exception as exc:
            self._logger.error(f"Failed to send message to DLQ: {exc}", exc_info=True)

    def _get_dlq_topic(self, original_topic: str) -> str:
        """Derive DLQ topic name from original topic."""
        # Remove prefix if present
        base_topic = original_topic
        if base_topic.startswith("bedaanwaves."):
            base_topic = base_topic[len("bedaanwaves."):]
        return f"{self.dlq_topic_prefix}.{base_topic}"

    async def reprocess_dlq_message(
        self,
        dlq_topic: str,
        message: dict[str, Any],
        processor: Callable[[dict[str, Any]], Any],
    ) -> bool:
        """
        Attempt to reprocess a DLQ message.

        Args:
            dlq_topic: The DLQ topic the message came from
            message: The DLQ message payload
            processor: Async callable to process the original message

        Returns:
            True if reprocessing succeeded
        """
        try:
            original_message = message.get("original_message")
            result = await processor(json.loads(original_message))

            self._logger.info(
                f"Successfully reprocessed DLQ message from {dlq_topic}"
            )
            return True
        except Exception as exc:
            self._logger.error(
                f"Reprocessing failed for DLQ message from {dlq_topic}: {exc}",
                exc_info=True,
            )
            return False


class RetryHandler:
    """
    Handles retry logic with exponential backoff for Kafka consumers.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay_ms: int = 1000,
        max_delay_ms: int = 30000,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.base_delay_ms = base_delay_ms
        self.max_delay_ms = max_delay_ms
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff."""
        import random

        delay = min(
            self.base_delay_ms * (2 ** attempt),
            self.max_delay_ms,
        )
        if self.jitter:
            delay = delay * (0.5 + random.random())
        return delay / 1000.0  # Convert to seconds

    async def execute_with_retry(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute a function with retry logic."""
        import asyncio

        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                last_exception = exc
                if attempt >= self.max_retries:
                    raise
                delay = self.get_delay(attempt)
                self._logger.warning(
                    f"Retry {attempt + 1}/{self.max_retries} after {delay:.2f}s: {exc}"
                )
                await asyncio.sleep(delay)
        raise last_exception  # type: ignore[misc]


# --- Integration with EventBus ---

class KafkaDLQEventBus:
    """
    Extended EventBus with DLQ support.
    Wraps KafkaEventBus to add dead-letter handling.
    """

    def __init__(self, bootstrap_servers: str, client_id: str = "bedaanwaves"):
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self._dlq_handler = DLQHandler(bootstrap_servers=bootstrap_servers)
        self._retry_handler = RetryHandler(max_retries=3)
        self._logger = logging.getLogger("event_bus.kafka.dlq")

    async def initialize(self) -> None:
        """Initialize DLQ handler."""
        await self._dlq_handler.initialize()

    async def shutdown(self) -> None:
        """Shutdown DLQ handler."""
        await self._dlq_handler.shutdown()

    async def handle_failure(
        self,
        topic: str,
        message: Any,
        error: Exception,
        retry_count: int,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Handle a message processing failure."""
        if retry_count >= 3:
            await self._dlq_handler.send_to_dlq(
                original_topic=topic,
                message=message,
                error=error,
                retry_count=retry_count,
                metadata=metadata,
            )
        else:
            self._logger.warning(
                f"Message from {topic} will be retried (attempt {retry_count + 1})"
            )