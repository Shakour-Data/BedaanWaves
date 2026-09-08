"""
Health Check Service - Tier 9 System Service

Provides comprehensive health checking for all BedaanWaves services.
Implements liveness, readiness, and health probes for Kubernetes-style orchestration.
"""

from datetime import UTC, datetime
from typing import Any

from ..core import BaseService


class HealthStatus:
    """Health status constants."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckService(BaseService):
    """
    Comprehensive health checking service.

    Provides:
    - Liveness probes (is the service alive?)
    - Readiness probes (is the service ready to serve traffic?)
    - Health probes (is the service functioning correctly?)
    - Dependency health checks (database, cache, external APIs)
    - Self-healing triggers for unhealthy services
    """

    def __init__(self, service_name: str = "HealthCheckService"):
        super().__init__(service_name)
        self._dependencies: dict[str, dict[str, Any]] = {}
        self._health_checks: dict[str, Any] = {}
        self._check_interval: int = 30  # seconds
        self._unhealthy_threshold: int = 3  # consecutive failures before marking unhealthy

    async def initialize(self) -> None:
        """Initialize health check service."""
        self.logger.info("HealthCheckService initialized")

    async def shutdown(self) -> None:
        """Shutdown health check service."""
        self._dependencies.clear()
        self._health_checks.clear()
        self.logger.info("HealthCheckService shutdown")

    def register_dependency(self, name: str, check_func: Any, critical: bool = True) -> None:
        """
        Register a dependency health check.

        Args:
            name: Dependency name (e.g., 'database', 'redis')
            check_func: Async function that returns dict with 'status' key
            critical: If True, failure marks service as unhealthy
        """
        self._dependencies[name] = {
            "check_func": check_func,
            "critical": critical,
            "consecutive_failures": 0,
            "last_check": None,
            "last_status": HealthStatus.UNKNOWN,
        }
        self.logger.debug(f"Registered health check dependency: {name} (critical={critical})")

    def unregister_dependency(self, name: str) -> bool:
        """Remove a dependency health check."""
        if name in self._dependencies:
            del self._dependencies[name]
            return True
        return False

    async def check_liveness(self) -> dict[str, Any]:
        """
        Liveness probe - is the service alive?

        Returns:
            Dict with liveness status
        """
        return {
            "status": HealthStatus.HEALTHY,
            "timestamp": datetime.now(UTC).isoformat(),
            "service": self.service_name,
            "message": "Service is alive",
        }

    async def check_readiness(self) -> dict[str, Any]:
        """
        Readiness probe - is the service ready to serve traffic?

        Returns:
            Dict with readiness status
        """
        # Check if all critical dependencies are ready
        critical_deps = [
            name for name, dep in self._dependencies.items() if dep["critical"]
        ]

        if not critical_deps:
            return {
                "status": HealthStatus.HEALTHY,
                "timestamp": datetime.now(UTC).isoformat(),
                "service": self.service_name,
                "message": "Service is ready",
            }

        # Check critical dependencies
        dep_statuses = {}
        all_ready = True
        for name in critical_deps:
            try:
                dep = self._dependencies[name]
                result = await dep["check_func"]()
                dep_statuses[name] = result.get("status", HealthStatus.UNKNOWN)
                if result.get("status") != HealthStatus.HEALTHY:
                    all_ready = False
            except Exception as exc:
                dep_statuses[name] = HealthStatus.UNHEALTHY
                all_ready = False

        return {
            "status": HealthStatus.HEALTHY if all_ready else HealthStatus.UNHEALTHY,
            "timestamp": datetime.now(UTC).isoformat(),
            "service": self.service_name,
            "dependencies": dep_statuses,
            "message": "Service is ready" if all_ready else "Service is not ready",
        }

    async def check_health(self) -> dict[str, Any]:
        """
        Comprehensive health check - is the service functioning correctly?

        Returns:
            Dict with detailed health status
        """
        dep_results = {}
        overall_status = HealthStatus.HEALTHY
        critical_failures = 0

        for name, dep in self._dependencies.items():
            try:
                result = await dep["check_func"]()
                status = result.get("status", HealthStatus.UNKNOWN)
                dep_results[name] = {
                    "status": status,
                    "critical": dep["critical"],
                    "details": result.get("details", {}),
                    "timestamp": datetime.now(UTC).isoformat(),
                }

                if status == HealthStatus.UNHEALTHY:
                    dep["consecutive_failures"] += 1
                    if dep["critical"]:
                        critical_failures += 1
                        overall_status = HealthStatus.UNHEALTHY
                elif status == HealthStatus.DEGRADED:
                    if overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.DEGRADED
                else:
                    dep["consecutive_failures"] = 0

                dep["last_check"] = datetime.now(UTC)
                dep["last_status"] = status

            except Exception as exc:
                dep_results[name] = {
                    "status": HealthStatus.UNHEALTHY,
                    "critical": dep["critical"],
                    "error": str(exc),
                    "timestamp": datetime.now(UTC).isoformat(),
                }
                dep["consecutive_failures"] += 1
                if dep["critical"]:
                    critical_failures += 1
                    overall_status = HealthStatus.UNHEALTHY

        return {
            "status": overall_status,
            "timestamp": datetime.now(UTC).isoformat(),
            "service": self.service_name,
            "dependencies": dep_results,
            "critical_failures": critical_failures,
            "total_dependencies": len(self._dependencies),
            "message": f"Service is {overall_status}",
        }

    async def get_health_summary(self) -> dict[str, Any]:
        """Get a summary of all health checks."""
        health = await self.check_health()
        return {
            "status": health["status"],
            "timestamp": health["timestamp"],
            "service": self.service_name,
            "dependencies_checked": len(health.get("dependencies", {})),
            "critical_failures": health.get("critical_failures", 0),
        }

    async def is_healthy(self) -> bool:
        """Check if service is healthy."""
        health = await self.check_health()
        return health["status"] == HealthStatus.HEALTHY

    async def is_ready(self) -> bool:
        """Check if service is ready."""
        readiness = await self.check_readiness()
        return readiness["status"] == HealthStatus.HEALTHY

    async def health_check(self) -> dict[str, Any]:
        """Standard health check interface."""
        return await self.check_health()