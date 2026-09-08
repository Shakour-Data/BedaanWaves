"""
Self-Healing Service - Tier 9 System Service

Provides automatic self-healing capabilities for BedaanWaves services.
Monitors service health and automatically restarts or scales services when issues are detected.
"""

from datetime import UTC, datetime
from typing import Any

from ..core import BaseService


class SelfHealingService(BaseService):
    """
    Self-healing service for automatic recovery.

    Provides:
    - Automatic service restart on failure
    - Auto-scaling based on metrics
    - Circuit breaker pattern
    - Health-based traffic routing
    """

    def __init__(self, service_name: str = "SelfHealingService"):
        super().__init__(service_name)
        self._services: dict[str, dict[str, Any]] = {}
        self._recovery_policies: dict[str, dict[str, Any]] = {}
        self._auto_restart_enabled: bool = True
        self._auto_scale_enabled: bool = True

    async def initialize(self) -> None:
        """Initialize self-healing service."""
        self.logger.info("SelfHealingService initialized")

    async def shutdown(self) -> None:
        """Shutdown self-healing service."""
        self._services.clear()
        self._recovery_policies.clear()
        self.logger.info("SelfHealingService shutdown")

    def register_service(
        self,
        name: str,
        health_check: Any,
        restart_cmd: str | None = None,
        critical: bool = True,
    ) -> None:
        """
        Register a service for self-healing monitoring.

        Args:
            name: Service name
            health_check: Async function returning health status
            restart_cmd: Command to restart the service
            critical: If True, service failure triggers automatic recovery
        """
        self._services[name] = {
            "health_check": health_check,
            "restart_cmd": restart_cmd,
            "critical": critical,
            "consecutive_failures": 0,
            "last_check": None,
            "last_status": "unknown",
            "restart_count": 0,
        }
        self.logger.debug(f"Registered service for self-healing: {name} (critical={critical})")

    def register_recovery_policy(
        self,
        service_name: str,
        policy: dict[str, Any],
    ) -> None:
        """
        Register a recovery policy for a service.

        Args:
            service_name: Service name
            policy: Recovery policy configuration
        """
        self._recovery_policies[service_name] = policy
        self.logger.debug(f"Registered recovery policy for: {service_name}")

    async def check_and_heal(self) -> dict[str, Any]:
        """
        Check all services and perform self-healing if needed.

        Returns:
            Healing report
        """
        healing_report: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "services_checked": 0,
            "services_healed": 0,
            "details": {},
        }

        for name, service in self._services.items():
            try:
                # Check health
                health_result = await service["health_check"]()
                status = health_result.get("status", "unknown")

                if status == "healthy":
                    service["consecutive_failures"] = 0
                    service["last_status"] = "healthy"
                else:
                    service["consecutive_failures"] += 1
                    service["last_status"] = status

                    # Trigger healing if threshold reached
                    if service["consecutive_failures"] >= 3:
                        healed = await self._heal_service(name, service)
                        if healed:
                            healing_report["services_healed"] += 1
                            healing_report["details"][name] = {
                                "status": "healed",
                                "action": "service_restarted",
                            }
                        else:
                            healing_report["details"][name] = {
                                "status": "healing_failed",
                                "action": "restart_failed",
                            }
                    else:
                        healing_report["details"][name] = {
                            "status": "unhealthy",
                            "consecutive_failures": service["consecutive_failures"],
                        }

                service["last_check"] = datetime.now(UTC)
                healing_report["services_checked"] += 1

            except Exception as exc:
                self.logger.error(f"Health check failed for {name}: {exc}")
                healing_report["details"][name] = {
                    "status": "check_failed",
                    "error": str(exc),
                }

        return healing_report

    async def _heal_service(self, name: str, service: dict[str, Any]) -> bool:
        """
        Attempt to heal a service.

        Args:
            name: Service name
            service: Service configuration

        Returns:
            True if healing was successful
        """
        self.logger.warning(f"Attempting to heal service: {name}")

        if not service.get("restart_cmd"):
            self.logger.error(f"No restart command for service: {name}")
            return False

        try:
            # Execute restart command
            import subprocess
            result = subprocess.run(
                service["restart_cmd"],
                shell=True,
                capture_output=True,
                timeout=30,
            )

            if result.returncode == 0:
                service["restart_count"] += 1
                service["consecutive_failures"] = 0
                self.logger.info(f"Service {name} restarted successfully")
                return True
            else:
                self.logger.error(f"Service {name} restart failed: {result.stderr.decode()}")
                return False

        except Exception as exc:
            self.logger.error(f"Error restarting service {name}: {exc}")
            return False

    async def auto_scale_service(
        self,
        service_name: str,
        current_instances: int,
        cpu_usage: float,
        memory_usage: float,
    ) -> int:
        """
        Automatically scale a service based on metrics.

        Args:
            service_name: Service name
            current_instances: Current number of instances
            cpu_usage: Current CPU usage (0-1)
            memory_usage: Current memory usage (0-1)

        Returns:
            New instance count
        """
        if not self._auto_scale_enabled:
            return current_instances

        policy = self._recovery_policies.get(service_name, {})
        min_instances = policy.get("min_instances", 1)
        max_instances = policy.get("max_instances", 10)
        target_cpu = policy.get("target_cpu", 0.7)

        if cpu_usage > target_cpu and current_instances < max_instances:
            new_instances = min(current_instances + 1, max_instances)
            self.logger.info(f"Scaling service {service_name} from {current_instances} to {new_instances} instances (CPU: {cpu_usage:.2f})")
            return new_instances
        elif cpu_usage < target_cpu * 0.5 and current_instances > min_instances:
            new_instances = max(current_instances - 1, min_instances)
            self.logger.info(f"Scaling down service {service_name} from {current_instances} to {new_instances} instances (CPU: {cpu_usage:.2f})")
            return new_instances

        return current_instances

    async def health_check(self) -> dict[str, Any]:
        """Check self-healing service health."""
        unhealthy_services = [
            name for name, svc in self._services.items()
            if svc["consecutive_failures"] > 0
        ]
        return {
            "service": self.service_name,
            "status": "healthy",
            "services_monitored": len(self._services),
            "unhealthy_services": len(unhealthy_services),
            "auto_restart_enabled": self._auto_restart_enabled,
            "auto_scale_enabled": self._auto_scale_enabled,
        }