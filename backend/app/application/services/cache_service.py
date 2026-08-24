from typing import Any, Optional, Dict, List
from ..interfaces.i_cache_service import ICacheService
from ..interfaces.i_cache_backend import ICacheBackend
from ...domain.shared.result import Result

class CacheService(ICacheService):
    """
    Implementation of CacheService using a provided backend.
    Follows Clean OO: Single Responsibility, DI, Result Pattern.
    """
    
    def __init__(
        self, 
        backend: ICacheBackend, 
        default_ttl: int = 3600
    ):
        """Constructor injection for backend dependency."""
        self._backend = backend
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    async def get(self, key: str, namespace: str = "default") -> Result[Any]:
        """Fail fast and return Result."""
        if not key:
            return Result.failure("Key cannot be empty", "INVALID_ARGUMENT")
            
        full_key = self._format_key(namespace, key)
        value = await self._backend.get(full_key)
        
        if value is not None:
            self._hits += 1
            return Result.success(value)
            
        self._misses += 1
        return Result.failure(f"Key '{full_key}' not found in cache", "CACHE_MISS")

    async def set(
        self, 
        key: str, 
        value: Any, 
        namespace: str = "default", 
        ttl: Optional[int] = None
    ) -> Result[bool]:
        if not key:
            return Result.failure("Key cannot be empty", "INVALID_ARGUMENT")
            
        full_key = self._format_key(namespace, key)
        expiration = ttl if ttl is not None else self._default_ttl
        
        await self._backend.set(full_key, value, expiration)
        return Result.success(True)

    async def delete(self, key: str, namespace: str = "default") -> Result[bool]:
        if not key:
            return Result.failure("Key cannot be empty", "INVALID_ARGUMENT")
            
        full_key = self._format_key(namespace, key)
        await self._backend.delete(full_key)
        return Result.success(True)

    async def clear(self, namespace: Optional[str] = None) -> Result[bool]:
        if namespace:
            # Logic for namespace-specific clearing could be added here
            pass
        await self._backend.clear()
        return Result.success(True)

    async def exists(self, key: str, namespace: str = "default") -> Result[bool]:
        if not key:
            return Result.failure("Key cannot be empty", "INVALID_ARGUMENT")
            
        full_key = self._format_key(namespace, key)
        exists = await self._backend.exists(full_key)
        return Result.success(exists)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": self._backend.size(),
            "default_ttl": self._default_ttl
        }

    def _format_key(self, namespace: str, key: str) -> str:
        """Private method for key formatting."""
        return f"{namespace}:{key}"
