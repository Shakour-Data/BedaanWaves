"""
Notification Dispatcher Service - Tier 9 System Service

Centralized notification system for BedaanWaves platform.
Manages notification routing, dispatching, and tracking across multiple channels.
"""

import asyncio
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from ..core import BaseService


class NotificationType(StrEnum):
    """Types of notifications."""
    SYSTEM_HEALTH = "system_health"
    ANALYSIS_COMPLETED = "analysis_completed"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELED = "booking_canceled"
    MARKET_ALERT = "market_alert"
    USER_ACTIVITY = "user_activity"
    FEEDBACK_PROVIDED = "feedback_provided"
    API_ACCESS = "api_access"


class NotificationChannel(StrEnum):
    """Types of notification channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NotificationPriority(StrEnum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(StrEnum):
    """Status of a dispatched notification."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"
    READ = "read"


@dataclass
class NotificationMessage:
    """Represents a notification to be dispatched."""
    type: NotificationType
    channel: NotificationChannel
    priority: NotificationPriority
    notification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    payload: dict[str, Any] = field(default_factory=dict)
    recipients: list[str] = field(default_factory=list)
    sender: str = "core"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: NotificationStatus = NotificationStatus.PENDING
    retry_count: int = 0


class NotificationDispatcher(BaseService):
    """
    Centralized notification dispatcher for BedaanWaves platform.

    Provides:
    - Notification dispatching across multiple channels
    - Queueing and retry logic
    - Status tracking and callbacks
    - Channel-specific dispatching
    - Analytics and monitoring
    """

    def __init__(
        self,
        service_name: str = "NotificationDispatcher",
        storage_path: str | None = None,
        max_queue_size: int = 10000,
        max_retries: int = 3,
        default_priority: NotificationPriority = NotificationPriority.MEDIUM,
    ):
        super().__init__(service_name)
        self.storage_path = Path(storage_path) if storage_path else Path("notifications")
        self.max_queue_size = max_queue_size
        self.max_retries = max_retries
        self.default_priority = default_priority
        self._lock = asyncio.Lock()

        # Internal state
        self._event_log: deque = deque()
        self._active_subscriptions: dict[str, set[NotificationDispatcher]] = {}
        self._scheduled_tasks: dict[str, asyncio.Task] = {}
        self._recipients: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
        self._channel_handlers: dict[NotificationChannel, list[Callable[[NotificationMessage], None]]] = {
            NotificationChannel.EMAIL: [self._send_email],
            NotificationChannel.SMS: [self._send_sms],
            NotificationChannel.PUSH: [self._send_push],
            NotificationChannel.IN_APP: [self._send_in_app],
            NotificationChannel.WEBHOOK: [self._send_webhook],
        }
        self._pending_events: dict[str, list[NotificationMessage]] = {}
        self._retry_locks: dict[str, asyncio.Lock] = {}

        # Ensure storage exists
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> None:
        """Initialize dispatcher service."""
        self.logger.info("NotificationDispatcher initialized")

    async def shutdown(self) -> None:
        """Shutdown dispatcher service."""
        self.logger.info("NotificationDispatcher shutdown")

    async def publish_event(
        self,
        event_type: str,
        payload: dict[str, Any] = None,
        recipients: list[str] = None,
        channel: NotificationChannel = NotificationChannel.PUSH,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        sender: str = None,
    ) -> str:
        """Publish an event for dispatching to subscribers."""
        if recipients is None:
            recipients = ["system"]
        if sender is None:
            sender = "core"

        try:
            notification_type = NotificationType(event_type)
        except ValueError:
            raise ValueError(f"Invalid event_type: {event_type!r}. Allowed: {[e.value for e in NotificationType]}")

        notification_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC)

        message = NotificationMessage(
            notification_id=notification_id,
            type=notification_type,
            channel=channel,
            priority=priority,
            payload=payload or {},
            recipients=recipients,
            sender=sender,
            created_at=timestamp,
        )

        async with self._lock:
            if self._pending_events.get(event_type):
                self._pending_events[event_type].append(message)
            else:
                self._pending_events[event_type] = [message]

            self._event_log.append(message)

        self.logger.info(f"Event published: {event_type} to {len(recipients)} recipients")
        asyncio.create_task(self._dispatch_events(event_type))
        return notification_id

    async def _dispatch_events(self, event_type: str) -> None:
        """Dispatch events to appropriate subscribers."""
        async with self._lock:
            if event_type not in self._pending_events or not self._pending_events[event_type]:
                return
            messages = self._pending_events[event_type]
            self._pending_events[event_type] = []

        for message in messages:
            try:
                await asyncio.sleep(0.01)
                handlers = self._channel_handlers.get(message.channel, [])
                for handler in handlers:
                    handler(message)
                message.status = NotificationStatus.SENT
                self.logger.info(f"Notification dispatched: {message.notification_id} via {message.channel.value}")
            except Exception as exc:
                self.logger.error(f"Failed to dispatch: {exc}")
                message.retry_count += 1
                message.status = NotificationStatus.FAILED

    async def get_notification_status(self, notification_id: str) -> dict[str, Any] | None:
        """Get status of a notification by ID."""
        async with self._lock:
            for entry in self._event_log:
                if hasattr(entry, 'notification_id') and entry.notification_id == notification_id:
                    return {
                        "notification_id": notification_id,
                        "status": entry.status.value,
                        "created_at": entry.created_at.isoformat(),
                        "channel": entry.channel.value,
                    }
        return None

    async def get_stats(self) -> dict[str, Any]:
        """Get detailed service statistics."""
        async with self._lock:
            status_counts = defaultdict(int)
            channel_counts = defaultdict(int)

            for entry in self._event_log:
                if hasattr(entry, 'status'):
                    status_counts[entry.status.value] += 1
                if hasattr(entry, 'channel'):
                    channel_counts[entry.channel.value] += 1

            return {
                "total_events": len(self._event_log),
                "pending_events": sum(len(msgs) for msgs in self._pending_events.values()),
                "status_breakdown": dict(status_counts),
                "channel_breakdown": dict(channel_counts),
                "uptime_seconds": (datetime.now(UTC) - self.created_at).total_seconds(),
            }

    def _send_email(self, message: NotificationMessage) -> None:
        self.logger.debug(f"Email sender stub for {message.notification_id}: {message.payload}")

    def _send_sms(self, message: NotificationMessage) -> None:
        self.logger.debug(f"SMS sender stub for {message.notification_id}: {message.payload}")

    def _send_push(self, message: NotificationMessage) -> None:
        self.logger.debug(f"Push sender stub for {message.notification_id}: {message.payload}")

    def _send_in_app(self, message: NotificationMessage) -> None:
        self.logger.debug(f"In-app sender stub for {message.notification_id}: {message.payload}")

    def _send_webhook(self, message: NotificationMessage) -> None:
        self.logger.debug(f"Webhook sender stub for {message.notification_id}: {message.payload}")

    async def health_check(self) -> dict[str, Any]:
        """Check dispatcher health."""
        pending = sum(len(msgs) for msgs in self._pending_events.values())
        return {
            "service": self.service_name,
            "status": "healthy" if pending < self.max_queue_size else "overloaded",
            "pending_events": pending,
            "total_events_processed": len(self._event_log),
            "uptime_seconds": (datetime.now(UTC) - self.created_at).total_seconds(),
        }
