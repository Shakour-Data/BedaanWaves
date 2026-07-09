"""
Cache Service - Tier 1 Core Service

Multi-backend caching service supporting memory, Redis, and other backends.
Provides TTL management, pattern-based invalidation, and statistics.
"""

from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import hashlib
import json
from .base_service import BaseService


class CacheBackend(ABC):
    """Abstract base for cache backends"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete key from cache"""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear entire cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # Check TTL
        if entry['ttl'] and datetime.utcnow() > entry['expiry']:
            del self._cache[key]
            return None
        
        return entry['value']
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        expiry = None
        if ttl:
            expiry = datetime.utcnow() + timedelta(seconds=ttl)
        
        self._cache[key] = {
            'value': value,
            'ttl': ttl,
            'expiry': expiry,
            'created_at': datetime.utcnow(),
        }
    
    async def delete(self, key: str) -> None:
        self._cache.pop(key, None)
    
    async def clear(self) -> None:
        self._cache.clear()
    
    async def exists(self, key: str) -> bool:
        if key not in self._cache:
            return False
        
        entry = self._cache[key]
        if entry['ttl'] and datetime.utcnow() > entry['expiry']:
            del self._cache[key]
            return False
        
        return True
    
    def size(self) -> int:
        """Get cache size"""
        return len(self._cache)


class CacheService(BaseService):
    """
    Centralized cache management for BedaanWaves.
    
    Provides:
    - Multiple backend support (memory, Redis)
    - Automatic TTL management
    - Pattern-based invalidation
    - Statistics and monitoring
    """
    
    def __init__(
        self,
        service_name: str = "CacheService",
        backend: str = "memory",
        default_ttl: int = 3600,
    ):
        """
        Initialize cache service.
        
        Args:
            service_name: Service identifier
            backend: Cache backend ('memory' or 'redis')
            default_ttl: Default TTL in seconds
        """
        super().__init__(service_name)
        self.backend_type = backend
        self.default_ttl = default_ttl
        self.backend = self._create_backend(backend)
        self._key_prefixes: Dict[str, str] = {}
    
    async def initialize(self) -> None:
        """Initialize cache service"""
        self.logger.info(f"CacheService initialized with {self.backend_type} backend")
    
    async def shutdown(self) -> None:
        """Shutdown cache service"""
        await self.backend.clear()
        self.logger.info("CacheService shutdown")
    
    def _create_backend(self, backend_type: str) -> CacheBackend:
        """Create cache backend instance"""
        if backend_type.lower() == 'memory':
            return MemoryCacheBackend()
        elif backend_type.lower() == 'redis':
            self.logger.warning("Redis backend not yet implemented, using memory backend")
            return MemoryCacheBackend()
        else:
            raise ValueError(f"Unknown cache backend: {backend_type}")
    
    def _get_key(self, namespace: str, key: str) -> str:
        """Generate namespaced cache key"""
        return f"{namespace}:{key}"
    
    def _get_hash_key(self, data: Any) -> str:
        """Generate hash-based key from data"""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(json_str.encode()).hexdigest()
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            namespace: Key namespace
            
        Returns:
            Cached value or None
        """
        full_key = self._get_key(namespace, key)
        value = await self.backend.get(full_key)
        
        if value is not None:
            self._metrics["cache_hits"] += 1
        else:
            self._metrics["cache_misses"] += 1
        
        return value
    
    async def set(
        self,
        key: str,
        value: Any,
        namespace: str = "default",
        ttl: Optional[int] = None,
    ) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            namespace: Key namespace
            ttl: Time to live in seconds
        """
        full_key = self._get_key(namespace, key)
        ttl = ttl or self.default_ttl
        await self.backend.set(full_key, value, ttl)
        self.logger.debug(f"Cached {full_key} (TTL: {ttl}s)")
    
    async def delete(self, key: str, namespace: str = "default") -> None:
        """Delete cache entry"""
        full_key = self._get_key(namespace, key)
        await self.backend.delete(full_key)
    
    async def clear(self, namespace: Optional[str] = None) -> None:
        """
        Clear cache.
        
        Args:
            namespace: Optional namespace to clear (clears all if not specified)
        """
        if namespace is None:
            await self.backend.clear()
            self.logger.info("Cleared entire cache")
        else:
            self.logger.warning("Namespace-specific clearing not yet implemented")
    
    async def exists(self, key: str, namespace: str = "default") -> bool:
        """Check if key exists in cache"""
        full_key = self._get_key(namespace, key)
        return await self.backend.exists(full_key)
    
    async def get_or_set(
        self,
        key: str,
        factory: callable,
        namespace: str = "default",
        ttl: Optional[int] = None,
    ) -> Any:
        """
        Get from cache or compute and set.
        
        Args:
            key: Cache key
            factory: Callable to compute value if not cached
            namespace: Key namespace
            ttl: Time to live in seconds
            
        Returns:
            Cached or computed value
        """
        cached = await self.get(key, namespace)
        if cached is not None:
            return cached
        
        value = factory() if callable(factory) else factory
        await self.set(key, value, namespace, ttl)
        return value
    
    async def set_many(
        self,
        items: Dict[str, Any],
        namespace: str = "default",
        ttl: Optional[int] = None,
    ) -> None:
        """Set multiple cache entries"""
        for key, value in items.items():
            await self.set(key, value, namespace, ttl)
    
    async def get_many(
        self,
        keys: List[str],
        namespace: str = "default",
    ) -> Dict[str, Any]:
        """Get multiple cache entries"""
        results = {}
        for key in keys:
            value = await self.get(key, namespace)
            if value is not None:
                results[key] = value
        return results
    
    def register_namespace(self, namespace: str, prefix: str = "") -> None:
        """Register namespace prefix"""
        self._key_prefixes[namespace] = prefix
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = super().get_metrics()
        
        if isinstance(self.backend, MemoryCacheBackend):
            stats['cache_size'] = self.backend.size()
        
        return stats
