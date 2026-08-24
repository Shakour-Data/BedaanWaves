from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List
from ...domain.shared.result import Result

class ICacheBackend(ABC):
    """Interface for cache storage backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the backend."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value in the backend."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove a value from the backend."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all values from the backend."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in the backend."""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """Get the number of items in the backend."""
        pass
