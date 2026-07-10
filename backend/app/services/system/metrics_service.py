"""
Metrics Service - Tier 9 System Service

Aggregates metrics from all registered BedaanWaves services.
Provides Prometheus-style counters and health summaries.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..core import BaseService


class MetricsService(BaseService):
    """
    Service metrics aggregator.
    
    Collects metrics from all registered services and exposes
    platform-wide health and performance summaries.
    """
    
    def __init__(self, service_name: str = "MetricsService"):
        super().__init__(service_name)
        self._registered_services: Dict[str, BaseService] = {}
        self._platform_start: datetime = datetime.now(timezone.utc)
    
    async def initialize(self) -> None:
        self.logger.info("MetricsService initialized")
    
    async def shutdown(self) -> None:
        self._registered_services.clear()
        self.logger.info("MetricsService shutdown")
    
    def register_service(self, name: str, service: BaseService) -> None:
        """
        Register a service for metrics collection.
        
        Args:
            name: Service identifier
            service: Service instance implementing get_metrics()
        """
        self._registered_services[name] = service
        self.logger.debug(f"Registered metrics source: {name}")
    
    def unregister_service(self, name: str) -> bool:
        """Unregister a metrics source."""
        if name in self._registered_services:
            del self._registered_services[name]
            return True
        return False
    
    def get_service_metrics(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific registered service."""
        if name not in self._registered_services:
            return None
        return self._registered_services[name].get_metrics()
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for all registered services.
        
        Returns:
            Platform-wide metrics summary
        """
        services_metrics = {}
        total_calls = 0
        total_errors = 0
        total_cache_hits = 0
        total_cache_misses = 0
        
        for name, service in self._registered_services.items():
            try:
                metrics = service.get_metrics()
                services_metrics[name] = metrics
                total_calls += metrics.get("calls", 0)
                total_errors += metrics.get("errors", 0)
                total_cache_hits += metrics.get("cache_hits", 0)
                total_cache_misses += metrics.get("cache_misses", 0)
            except Exception as exc:
                self.logger.warning(f"Failed to collect metrics from {name}: {exc}")
                services_metrics[name] = {"error": str(exc)}
        
        total_cache_requests = total_cache_hits + total_cache_misses
        platform_uptime = (datetime.now(timezone.utc) - self._platform_start).total_seconds()
        
        return {
            "platform": {
                "uptime_seconds": platform_uptime,
                "services_count": len(self._registered_services),
                "total_calls": total_calls,
                "total_errors": total_errors,
                "global_error_rate": total_errors / total_calls if total_calls > 0 else 0,
                "total_cache_hits": total_cache_hits,
                "total_cache_misses": total_cache_misses,
                "global_cache_hit_rate": (
                    total_cache_hits / total_cache_requests if total_cache_requests > 0 else 0
                ),
            },
            "services": services_metrics,
        }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for all registered services."""
        health = {"platform": "healthy", "services": {}}
        for name, service in self._registered_services.items():
            try:
                health["services"][name] = {
                    "status": "healthy",
                    "service": name,
                }
            except Exception as exc:
                health["services"][name] = {"status": "unhealthy", "error": str(exc)}
        return health
    
    async def health_check(self) -> Dict[str, Any]:
        """Check metrics service health."""
        return {
            "service": self.service_name,
            "status": "healthy",
            "registered_services": len(self._registered_services),
            "uptime_seconds": (datetime.now(timezone.utc) - self.created_at).total_seconds(),
        }
