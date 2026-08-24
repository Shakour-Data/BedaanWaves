from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List
from ...domain.shared.result import Result

class ICacheService(ABC):
    """Application-level interface for caching operations."""
    
    @abstractmethod
    async def get(self, key: str, namespace: str = "default") -> Result[Any]:
        """Get a value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, namespace: str = "default", ttl: Optional[int] = None) -> Result[bool]:
        """Set a value in cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str, namespace: str = "default") -> Result[bool]:
        """Delete a cache entry."""
        pass
    
    @abstractmethod
    async def clear(self, namespace: Optional[str] = None) -> Result[bool]:
        """Clear cache entries."""
        pass
    
    @abstractmethod
    async def exists(self, key: str, namespace: str = "default") -> Result[bool]:
        """Check if a key exists in cache."""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        pass
