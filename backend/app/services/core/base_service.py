"""
Base Service Class - Foundation for all 50+ BedaanWaves Services

This abstract base class provides:
- Dependency injection
- Logging
- Caching
- Error handling
- Performance monitoring
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar
import logging
from datetime import datetime, timezone
from functools import wraps

T = TypeVar('T')


class BaseService(ABC):
    """Abstract base class for all BedaanWaves services"""
    
    def __init__(self, service_name: str, logger: Optional[logging.Logger] = None):
        """
        Initialize base service.
        
        Args:
            service_name: Unique identifier for this service
            logger: Optional logger instance
        """
        self.service_name = service_name
        self.logger = logger or logging.getLogger(service_name)
        self.created_at = datetime.now(timezone.utc)
        self._cache: Dict[str, Any] = {}
        self._metrics = {
            "calls": 0,
            "errors": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_time_ms": 0.0,
        }
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize service - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown service - must be implemented by subclasses"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        return {
            "service": self.service_name,
            "status": "healthy",
            "uptime_seconds": (datetime.now(timezone.utc) - self.created_at).total_seconds(),
            "metrics": self._metrics.copy(),
        }
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get value from service cache"""
        if key in self._cache:
            self._metrics["cache_hits"] += 1
            return self._cache[key]
        self._metrics["cache_misses"] += 1
        return None
    
    def cache_set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in service cache"""
        self._cache[key] = {
            "value": value,
            "timestamp": datetime.now(timezone.utc),
            "ttl": ttl_seconds,
        }
    
    def cache_clear(self, key: Optional[str] = None) -> None:
        """Clear cache entry or entire cache"""
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()
    
    def _track_metric(self, success: bool, duration_ms: float) -> None:
        """Track service metrics"""
        self._metrics["calls"] += 1
        if not success:
            self._metrics["errors"] += 1
        self._metrics["total_time_ms"] += duration_ms
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        return {
            "service": self.service_name,
            "uptime_seconds": (datetime.now(timezone.utc) - self.created_at).total_seconds(),
            "calls": self._metrics["calls"],
            "errors": self._metrics["errors"],
            "error_rate": (
                self._metrics["errors"] / self._metrics["calls"]
                if self._metrics["calls"] > 0
                else 0
            ),
            "cache_hit_rate": (
                self._metrics["cache_hits"]
                / (self._metrics["cache_hits"] + self._metrics["cache_misses"])
                if (self._metrics["cache_hits"] + self._metrics["cache_misses"]) > 0
                else 0
            ),
            "avg_response_time_ms": (
                self._metrics["total_time_ms"] / self._metrics["calls"]
                if self._metrics["calls"] > 0
                else 0
            ),
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.service_name}>"


class CachedService(BaseService):
    """
    Service with built-in caching support
    
    Useful for services that frequently access same data
    """
    
    def __init__(self, service_name: str, logger: Optional[logging.Logger] = None, cache_ttl_seconds: int = 3600):
        super().__init__(service_name, logger)
        self.cache_ttl_seconds = cache_ttl_seconds
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid"""
        if key not in self._cache:
            return False
        
        entry = self._cache[key]
        if entry["ttl"] is None:
            return True
        
        age_seconds = (datetime.now(timezone.utc) - entry["timestamp"]).total_seconds()
        return age_seconds < entry["ttl"]
    
    def get_cached(self, key: str) -> Optional[Any]:
        """Get cached value if valid"""
        if self._is_cache_valid(key):
            self._metrics["cache_hits"] += 1
            return self._cache[key]["value"]
        
        self._metrics["cache_misses"] += 1
        self._cache.pop(key, None)
        return None
    
    def set_cached(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value with optional TTL"""
        ttl = ttl_seconds or self.cache_ttl_seconds
        self.cache_set(key, value, ttl)


class DataService(BaseService):
    """
    Base class for data access services
    
    Provides database interaction patterns
    """
    
    def __init__(self, service_name: str, logger: Optional[logging.Logger] = None):
        super().__init__(service_name, logger)
        self.db_connection = None
    
    async def get_by_id(self, entity_id: int) -> Optional[Dict[str, Any]]:
        """Fetch entity by ID - must be implemented by subclass"""
        raise NotImplementedError
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> list:
        """List all entities - must be implemented by subclass"""
        raise NotImplementedError
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new entity - must be implemented by subclass"""
        raise NotImplementedError
    
    async def update(self, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update entity - must be implemented by subclass"""
        raise NotImplementedError
    
    async def delete(self, entity_id: int) -> bool:
        """Delete entity - must be implemented by subclass"""
        raise NotImplementedError


class AnalysisService(BaseService):
    """
    Base class for analysis services
    
    Provides analysis computation patterns
    """
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform analysis - must be implemented by subclass"""
        raise NotImplementedError
    
    async def batch_analyze(self, data_list: list) -> list:
        """Perform batch analysis using asyncio.gather"""
        import asyncio
        tasks = [self.analyze(item) for item in data_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed = []
        for item, result in zip(data_list, results):
            if isinstance(result, Exception):
                self.logger.error(f"Batch analysis error for {item}: {result}")
                processed.append({"error": str(result)})
            else:
                processed.append(result)
        
        return processed


class MLService(BaseService):
    """
    Base class for machine learning services
    
    Provides model training and prediction patterns
    """
    
    def __init__(self, service_name: str, logger: Optional[logging.Logger] = None):
        super().__init__(service_name, logger)
        self.model = None
        self.features = None
    
    async def train(self, training_data: Dict[str, Any]) -> Dict[str, Any]:
        """Train model - must be implemented by subclass"""
        raise NotImplementedError
    
    async def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction - must be implemented by subclass"""
        raise NotImplementedError
    
    async def evaluate(self, test_data: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate model performance"""
        raise NotImplementedError


class ExternalAPIService(BaseService):
    """
    Base class for external API integration services
    
    Provides API communication patterns with retry logic
    """
    
    def __init__(
        self,
        service_name: str,
        base_url: str,
        logger: Optional[logging.Logger] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        super().__init__(service_name, logger)
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None
    
    async def fetch(self, endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        """Fetch from external API - must be implemented by subclass"""
        raise NotImplementedError
    
    async def _handle_rate_limit(self, retry_count: int) -> None:
        """Handle API rate limiting with exponential backoff"""
        import asyncio
        wait_time = min(2 ** retry_count, 60)  # Max 60 seconds
        self.logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
        await asyncio.sleep(wait_time)
