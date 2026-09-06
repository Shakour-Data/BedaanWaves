import logging
from collections.abc import Callable
from typing import Any, TypeVar

from ...application.interfaces.i_dependency_container import IDependencyContainer
from ...domain.shared.result import Result

T = TypeVar('T')

class DependencyContainer(IDependencyContainer):
    """
    Concrete implementation of IDependencyContainer.
    Manages service lifecycles and provides type-safe resolution.
    """

    def __init__(self, logger: logging.Logger):
        self._logger = logger
        self._factories: dict[type, Callable] = {}
        self._singletons: dict[type, Any] = {}
        self._is_singleton: dict[type, bool] = {}

    def register(
        self,
        service_type: type[T],
        factory: Callable[..., T],
        is_singleton: bool = True
    ) -> None:
        self._factories[service_type] = factory
        self._is_singleton[service_type] = is_singleton
        self._logger.info(f"Registered service: {service_type.__name__}")

    def resolve(self, service_type: type[T]) -> Result[T]:
        if service_type in self._singletons:
            return Result.success(self._singletons[service_type])

        if service_type not in self._factories:
            return Result.failure(
                f"Service {service_type.__name__} not registered",
                "SERVICE_NOT_FOUND"
            )

        try:
            instance = self._factories[service_type]()
            if self._is_singleton.get(service_type, False):
                self._singletons[service_type] = instance
            return Result.success(instance)
        except Exception as e:
            self._logger.error(f"Failed to resolve {service_type.__name__}: {e!s}")
            return Result.failure(str(e), "RESOLUTION_FAILED")

    async def initialize_all(self) -> Result[bool]:
        """Initializes all singleton services that have an initialize method."""
        for service_type, instance in self._singletons.items():
            if hasattr(instance, "initialize") and callable(instance.initialize):
                try:
                    await instance.initialize()
                except Exception as e:
                    self._logger.error(f"Initialization failed for {service_type.__name__}: {e!s}")
                    return Result.failure(str(e), "INITIALIZATION_FAILED")
        return Result.success(True)

    async def shutdown_all(self) -> None:
        for service_type, instance in self._singletons.items():
            if hasattr(instance, "shutdown") and callable(instance.shutdown):
                await instance.shutdown()
        self._singletons.clear()
        self._logger.info("All services shut down.")
