"""
Logging Service - Tier 9 System Service

Centralized log management and aggregation service for BedaanWaves platform.
Provides log collection, storage, querying, and analysis capabilities.
"""

import asyncio
import json
import logging
import re
from collections import deque, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field

from ..core import BaseService


@dataclass
class LogEntry:
    """Represents a single log entry."""
    timestamp: datetime
    level: str
    logger: str
    message: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "logger": self.logger,
            "message": self.message,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "source": self.source,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            level=data["level"],
            logger=data["logger"],
            message=data["message"],
            trace_id=data.get("trace_id"),
            span_id=data.get("span_id"),
            source=data.get("source"),
            metadata=data.get("metadata", {}),
        )


class LoggingService(BaseService):
    """
    Centralized logging service for BedaanWaves platform.
    
    Provides:
    - Log ingestion from services
    - Persistent storage with rotation
    - Query and search capabilities
    - Log analysis and aggregation
    """
    
    def __init__(
        self,
        service_name: str = "LoggingService",
        log_dir: Optional[str] = None,
        max_entries: int = 10000,
        retention_hours: int = 168,  # 7 days default
        buffer_size: int = 1000,
        log_level: str = "INFO",
    ):
        super().__init__(service_name)
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.max_entries = max_entries
        self.retention_hours = retention_hours
        self.buffer_size = buffer_size
        self.log_level = getattr(logging, log_level.upper())
        
        # Thread-safe storage
        self._log_buffer: deque = deque(maxlen=buffer_size)
        self._log_store: deque = deque(maxlen=max_entries)
        self._lock = asyncio.Lock()
        self._running = False
        self._logger_task: Optional[asyncio.Task] = None
        self._level_counts = defaultdict(int)
        self._logger_counts = defaultdict(int)
        
    async def initialize(self) -> None:
        """Initialize logging service."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._running = True
        self._logger_task = asyncio.create_task(self._persistence_loop())
        self.logger.info(f"LoggingService initialized - dir: {self.log_dir}, retention: {self.retention_hours}h")
        
    async def shutdown(self) -> None:
        """Shutdown logging service."""
        self._running = False
        if self._logger_task:
            self._logger_task.cancel()
            try:
                await self._logger_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining logs to disk
        await self._flush_buffer()
        self.logger.info("LoggingService shutdown")
        
    async def log_entry(
        self,
        level: str,
        logger_name: str,
        message: str,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a log entry to the system.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            logger_name: Name of logger generating the entry
            message: Log message
            trace_id: Optional trace identifier
            span_id: Optional span identifier
            source: Optional source identifier
            metadata: Optional additional metadata
        """
        if not self._running:
            return
            
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc),
            level=level.upper(),
            logger=logger_name,
            message=message,
            trace_id=trace_id,
            span_id=span_id,
            source=source,
            metadata=metadata or {},
        )
        
        async with self._lock:
            self._log_buffer.append(entry)
            self._level_counts[level.upper()] += 1
            self._logger_counts[logger_name] += 1
            
    async def query_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        levels: Optional[List[str]] = None,
        logger_names: Optional[List[str]] = None,
        message_pattern: Optional[str] = None,
        trace_id: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Query logs with filtering options.
        
        Args:
            start_time: Filter logs after this time
            end_time: Filter logs before this time
            levels: Filter by log levels
            logger_names: Filter by logger names
            message_pattern: Regex pattern to match in message
            trace_id: Filter by trace ID
            limit: Maximum results to return
            offset: Number of results to skip
            
        Returns:
            List of matching log entries as dictionaries
        """
        async with self._lock:
            # Filter logs
            filtered_logs = []
            pattern_re = re.compile(message_pattern) if message_pattern else None
            
            for entry in self._log_store:
                if not self._running and not self._log_buffer and not self._log_store:
                    break
                    
                # Time range filter
                if start_time and entry.timestamp < start_time:
                    continue
                if end_time and entry.timestamp > end_time:
                    continue
                
                # Level filter
                if levels and entry.level not in [l.upper() for l in levels]:
                    continue
                
                # Logger filter
                if logger_names and entry.logger not in logger_names:
                    continue
                
                # Message pattern filter
                if pattern_re and not pattern_re.search(entry.message):
                    continue
                
                # Trace ID filter
                if trace_id and entry.trace_id != trace_id:
                    continue
                
                filtered_logs.append(entry.to_dict())
            
            # Apply pagination
            start_idx = offset
            end_idx = min(offset + limit, len(filtered_logs))
            return filtered_logs[start_idx:end_idx]
    
    async def get_log_statistics(self) -> Dict[str, Any]:
        """Get logging statistics."""
        async with self._lock:
            return {
                "total_logs": len(self._log_store),
                "buffered_logs": len(self._log_buffer),
                "level_counts": dict(self._level_counts),
                "logger_counts": dict(self._logger_counts),
                "unique_loggers": len(self._logger_counts),
                "time_range": {
                    "oldest": self._log_store[0].timestamp.isoformat() if self._log_store else None,
                    "newest": self._log_store[-1].timestamp.isoformat() if self._log_store else None,
                },
                "retention_hours": self.retention_hours,
                "max_entries": self.max_entries,
                "buffer_size": self.buffer_size,
            }
            
    async def _persistence_loop(self) -> None:
        """Background task to persist logs to disk."""
        while self._running:
            try:
                # Flush buffer periodically
                if len(self._log_buffer) >= self.buffer_size // 2:
                    await self._flush_buffer()
                    
                # Check for old logs to purge
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.retention_hours)
                async with self._lock:
                    # Find index of first log after cutoff
                    cutoff_index = 0
                    for i, entry in enumerate(self._log_store):
                        if entry.timestamp >= cutoff_time:
                            cutoff_index = i
                            break
                    
                    # Remove old logs if any
                    if cutoff_index > 0:
                        removed_count = len(self._log_store) - cutoff_index
                        self._log_store = self._log_store[cutoff_index:]
                        # Update counts for removed logs (simplified)
                        self.logger.debug(f"Purged {removed_count} old log entries")
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.logger.error(f"Error in persistence loop: {exc}", exc_info=True)
                await asyncio.sleep(5)
                
    async def _flush_buffer(self) -> None:
        """Flush buffered logs to persistent storage and disk."""
        if not self._log_buffer:
            return
            
        # Move from buffer to store
        async with self._lock:
            if self._log_buffer:
                # Add to permanent store
                while self._log_buffer and len(self._log_store) < self.max_entries:
                    self._log_store.append(self._log_buffer.popleft())
                # If store is full, remove oldest to make room
                while self._log_buffer and len(self._log_store) >= self.max_entries:
                    # Remove oldest from store
                    if self._log_store:
                        removed = self._log_store.popleft()
                        # Update counts (simplified)
                        self._level_counts[removed.level] = max(0, self._level_counts[removed.level] - 1)
                        self._logger_counts[removed.logger] = max(0, self._logger_counts[removed.logger] - 1)
                    # Add from buffer
                    self._log_store.append(self._log_buffer.popleft())
        
        # Write to disk
        try:
            log_file = self.log_dir / f"app_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"
            async with self._lock:
                with open(log_file, "a", encoding="utf-8") as f:
                    for entry in list(self._log_store)[-len(self._log_buffer):] if self._log_buffer else []:
                        f.write(json.dumps(entry.to_dict()) + "\n")
        except Exception as exc:
            self.logger.error(f"Failed to write log file: {exc}", exc_info=True)
            
    def get_recent_logs(self, count: int = 100) -> List[Dict[str, Any]]:
        """Get recent log entries synchronously (for quick access)."""
        # Synchronous version for simple access
        recent = list(self._log_store)[-count:] if self._log_store else []
        return [entry.to_dict() for entry in recent]
        
    async def health_check(self) -> Dict[str, Any]:
        """Check logging service health."""
        return {
            "service": self.service_name,
            "status": "healthy" if self._running else "stopped",
            "total_logs": len(self._log_store),
            "buffered_logs": len(self._log_buffer),
            "log_dir": str(self.log_dir),
            "retention_hours": self.retention_hours,
            "max_entries": self.max_entries,
            "uptime_seconds": (datetime.now(timezone.utc) - self.created_at).total_seconds(),
        }