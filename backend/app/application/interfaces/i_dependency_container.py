from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Type, TypeVar
from ...domain.shared.result import Result

T = TypeVar('T')

class IDependencyContainer(ABC):
    """Interface for dependency injection and service management."""
    
    @abstractmethod
    def register(
        self, 
        service_type: Type[T], 
        factory: Callable[..., T], 
        is_singleton: bool = True
    ) -> None:
        """Register a service factory."""
        pass
    
    @abstractmethod
    def resolve(self, service_type: Type[T]) -> Result[T]:
        """Resolve a service instance by its type."""
        pass
    
    @abstractmethod
    async def initialize_all(self) -> Result[bool]:
        """Initialize all registered services."""
        pass
    
    @abstractmethod
    async def shutdown_all(self) -> None:
        """Shutdown and cleanup all services."""
        pass
