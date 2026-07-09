"""
Dependency Injection Container - Tier 1 Core Service

Manages all service instances and their lifecycle.
Implements the service locator pattern for dependency injection.
"""

from typing import Any, Dict, Optional, Type, TypeVar, Callable
import logging
from datetime import datetime

T = TypeVar('T')


class DependencyContainer:
    """
    Central dependency injection container for all BedaanWaves services.
    
    Manages:
    - Service registration
    - Service instantiation
    - Lifecycle management
    - Singleton instances
    """
    
    def __init__(self):
        """Initialize the dependency container"""
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self.logger = logging.getLogger("DependencyContainer")
        self.created_at = datetime.utcnow()
        self._is_initialized = False
    
    def register(
        self,
        service_name: str,
        factory: Callable,
        singleton: bool = True,
        **default_kwargs
    ) -> None:
        """
        Register a service factory.
        
        Args:
            service_name: Unique service identifier
            factory: Callable that creates service instance
            singleton: Whether to cache single instance
            **default_kwargs: Default arguments for factory
        """
        self._factories[service_name] = {
            'factory': factory,
            'singleton': singleton,
            'kwargs': default_kwargs,
        }
        self.logger.info(f"Registered service: {service_name} (singleton={singleton})")
    
    def get(self, service_name: str, **kwargs) -> Any:
        """
        Get service instance.
        
        Args:
            service_name: Service identifier
            **kwargs: Additional arguments for factory
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If service not registered
        """
        if service_name not in self._factories:
            raise KeyError(f"Service not registered: {service_name}")
        
        factory_info = self._factories[service_name]
        factory = factory_info['factory']
        is_singleton = factory_info['singleton']
        
        # Return cached singleton if available
        if is_singleton and service_name in self._singletons:
            self.logger.debug(f"Returning singleton: {service_name}")
            return self._singletons[service_name]
        
        # Merge default kwargs with provided kwargs
        merged_kwargs = {**factory_info['kwargs'], **kwargs}
        
        # Create new instance
        try:
            instance = factory(**merged_kwargs)
            
            # Cache if singleton
            if is_singleton:
                self._singletons[service_name] = instance
                self.logger.debug(f"Cached singleton: {service_name}")
            
            self.logger.debug(f"Created service instance: {service_name}")
            return instance
        except Exception as e:
            self.logger.error(f"Failed to create service {service_name}: {e}")
            raise
    
    def register_instance(self, service_name: str, instance: Any) -> None:
        """
        Register a pre-created service instance (useful for testing).
        
        Args:
            service_name: Service identifier
            instance: Service instance
        """
        self._singletons[service_name] = instance
        self.logger.info(f"Registered instance: {service_name}")
    
    def has(self, service_name: str) -> bool:
        """Check if service is registered"""
        return service_name in self._factories or service_name in self._singletons
    
    def remove(self, service_name: str) -> None:
        """Remove service registration"""
        self._factories.pop(service_name, None)
        self._singletons.pop(service_name, None)
        self.logger.info(f"Removed service: {service_name}")
    
    async def shutdown_all(self) -> None:
        """Shutdown all services"""
        self.logger.info("Shutting down all services...")
        
        for service_name, instance in self._singletons.items():
            try:
                if hasattr(instance, 'shutdown'):
                    if callable(instance.shutdown):
                        await instance.shutdown()
                    self.logger.info(f"Shutdown service: {service_name}")
            except Exception as e:
                self.logger.error(f"Error shutting down {service_name}: {e}")
        
        self._singletons.clear()
        self._is_initialized = False
        self.logger.info("All services shutdown complete")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get container statistics"""
        return {
            "registered_services": len(self._factories),
            "singleton_instances": len(self._singletons),
            "uptime_seconds": (datetime.utcnow() - self.created_at).total_seconds(),
        }
    
    def __repr__(self) -> str:
        return (
            f"<DependencyContainer: "
            f"{len(self._factories)} registered, "
            f"{len(self._singletons)} singletons>"
        )


# Global container instance (lazy-loaded)
_global_container: Optional[DependencyContainer] = None


def get_global_container() -> DependencyContainer:
    """Get or create global dependency container"""
    global _global_container
    if _global_container is None:
        _global_container = DependencyContainer()
    return _global_container
