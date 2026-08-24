from typing import Any, Dict, Optional
from datetime import datetime, timedelta, timezone
from ..cache.i_cache_backend import ICacheBackend # Wait, path is wrong.

# Correcting path based on new structure:
# backend/app/infrastructure/cache/memory_cache_backend.py
# backend/app/application/interfaces/i_cache_backend.py

from ...application.interfaces.i_cache_backend import ICacheBackend

class MemoryCacheBackend(ICacheBackend):
    """In-memory implementation of cache backend."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if self._is_expired(entry):
            del self._cache[key]
            return None
        
        return entry['value']
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        expiry = None
        if ttl:
            expiry = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        
        self._cache[key] = {
            'value': value,
            'expiry': expiry,
            'created_at': datetime.now(timezone.utc)
        }
    
    async def delete(self, key: str) -> None:
        self._cache.pop(key, None)
    
    async def clear(self) -> None:
        self._cache.clear()
    
    async def exists(self, key: str) -> bool:
        if key not in self._cache:
            return False
        
        entry = self._cache[key]
        if self._is_expired(entry):
            del self._cache[key]
            return False
        
        return True
    
    def size(self) -> int:
        return len(self._cache)
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        if not entry['expiry']:
            return False
        return datetime.now(timezone.utc) > entry['expiry']
