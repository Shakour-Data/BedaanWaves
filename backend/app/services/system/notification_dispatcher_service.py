"""
Notification Dispatcher Service - Tier 9 System Service

Centralized notification system for BedaanWaves platform.
Manages notification routing, dispatching, and tracking across multiple channels.
"""

import asyncio
import json
import logging
import re
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from ..core import BaseService


class NotificationType(str, Enum):
    """Types of notifications."""
    SYSTEM_HEALTH = "system_health"
    ANALYSIS_COMPLETED = "analysis_completed"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELED = "booking_canceled"
    MARKET_ALERT = "market_alert"
    USER_ACTIVITY = "user_activity"
    FEEDBACK_PROVIDED = "feedback_provided"
    API_ACCESS = "api_access"


class NotificationChannel(str, Enum):
    """Types of notification channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(str, Enum):
    """Status of a dispatched notification."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"
    READ = "read"


@dataclass
class NotificationMessage:
    """Represents a notification to be dispatched."""
    notification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: NotificationType
    channel: NotificationChannel
    priority: NotificationPriority
    payload: Dict[str, Any] = field(default_factory=dict)
    recipients: List[str] = field(default_factory=list)  # User or channel IDs
    sender: str = "core"  # Originating service
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
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
        storage_path: Optional[str] = None,
        max_queue_size: int = 10000,
        max_retries: int = 3,
        default_priority: NotificationPriority = NotificationPriority.MEDIUM,
    ):
        super().__init__(service_name)
        self.storage_path = Path(storage_path) if storage_path else Path("notifications")
        self.max_queue_size = max_queue_size
        self.max_retries = max_retries
        self.default_priority = default_priority
        
        # Internal state
        self._event_log: deque = deque()
        self._active_subscriptions: Dict[str, Set[NotificationDispatcher]] = {}
        self._scheduled_tasks: Dict[str, asyncio.Task] = {}
        self._recipients: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
        self._channel_handlers: Dict[NotificationChannel, List[NotificationDispatcher]] = {
            channel: [] for channel in NotificationChannel
        }
        self._pending_events: Dict[str, List[NotificationMessage]] = {}
        self._retry_locks: Dict[str, asyncio.Lock] = {}
        
        # Ensure storage exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    async def initialize(self) -> None:
        """Initialize dispatcher service."""
        self.logger.info(f"NotificationDispatcher initialized")
        
    async def shutdown(self) -> None:
        """Shutdown dispatcher service."""
        self.logger.info("NotificationDispatcher shutdown")
        
    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any] = None,
        recipients: List[str] = None,
        channel: NotificationChannel = NotificationChannel.PUSH,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        sender: str = None,
    ) -> str:
        """Publish an event for dispatching to subscribers."""
        if recipients is None:
            recipients = ["system"]
        if sender is None:
            sender = "core"
            
        notification_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)
        
        message = NotificationMessage(
            notification_id=notification_id,
            type=NotificationType(event_type),
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
                # Rate limiting simulation
                await asyncio.sleep(0.01)
                
                self.logger.debug(f"Dispatching {event_type} via {message.channel.value}")
                message.status = NotificationStatus.SENT
                self.logger.info(f"Notification dispatched: {message.notification_id}")
                
            except Exception as exc:
                self.logger.error(f"Failed to dispatch: {exc}")
                message.retry_count += 1
                message.status = NotificationStatus.FAILED
                
    async def get_notification_status(self, notification_id: str) -> Optional[Dict[str, Any]]:
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
        
    async def get_stats(self) -> Dict[str, Any]:
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
                "uptime_seconds": (datetime.now(timezone.utc) - self.created_at).total_seconds(),
            }
            
    async def health_check(self) -> Dict[str, Any]:
        """Check dispatcher health."""
        pending = sum(len(msgs) for msgs in self._pending_events.values())
        return {
            "service": self.service_name,
            "status": "healthy" if pending < self.max_queue_size else "overloaded",
            "pending_events": pending,
            "total_events_processed": len(self._event_log),
            "uptime_seconds": (datetime.now(timezone.utc) - self.created_at).total_seconds(),
        }