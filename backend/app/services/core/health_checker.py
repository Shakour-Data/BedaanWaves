"""
Health Checker Service - Tier 1 Core Service

Monitors health of all system components and services.
Provides health status endpoints and alerts.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
from .base_service import BaseService


class HealthChecker(BaseService):
    """
    System health monitoring service.
    
    Provides:
    - Component health monitoring
    - Health aggregation
    - Alert triggering
    - Performance tracking
    """
    
    def __init__(
        self,
        service_name: str = "HealthChecker",
        check_interval_seconds: int = 60,
    ):
        """
        Initialize health checker service.
        
        Args:
            service_name: Service identifier
            check_interval_seconds: Interval for health checks
        """
        super().__init__(service_name)
        self.check_interval = check_interval_seconds
        self._checks: Dict[str, callable] = {}
        self._last_results: Dict[str, Dict[str, Any]] = {}
        self._is_monitoring = False
        self._monitor_task = None
    
    async def initialize(self) -> None:
        """Initialize health checker service"""
        self.logger.info("HealthChecker initialized")
        await self.start_monitoring()
    
    async def shutdown(self) -> None:
        """Shutdown health checker service"""
        await self.stop_monitoring()
        self.logger.info("HealthChecker shutdown")
    
    def register_check(self, name: str, check_func: callable) -> None:
        """
        Register a health check function.
        
        Args:
            name: Check identifier
            check_func: Async callable that returns health status dict
        """
        self._checks[name] = check_func
        self.logger.info(f"Registered health check: {name}")
    
    async def run_check(self, name: str) -> Dict[str, Any]:
        """
        Run a single health check.
        
        Args:
            name: Check identifier
            
        Returns:
            Health check result
        """
        if name not in self._checks:
            return {
                "name": name,
                "status": "unknown",
                "error": "Check not registered",
            }
        
        try:
            check_func = self._checks[name]
            result = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()
            
            result['timestamp'] = datetime.utcnow().isoformat()
            self._last_results[name] = result
            return result
        
        except Exception as e:
            result = {
                "name": name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
            self._last_results[name] = result
            self.logger.error(f"Health check failed: {name} - {e}")
            return result
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all registered health checks.
        
        Returns:
            Aggregated health status
        """
        results = {}
        for check_name in self._checks:
            results[check_name] = await self.run_check(check_name)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results,
            "overall_status": self._aggregate_status(results),
        }
    
    def _aggregate_status(self, results: Dict[str, Any]) -> str:
        """
        Aggregate overall health status from check results.
        
        Args:
            results: Check results dictionary
            
        Returns:
            Overall status ('healthy', 'degraded', or 'unhealthy')
        """
        statuses = [r.get('status', 'unknown') for r in results.values()]
        
        if 'error' in statuses or 'unhealthy' in statuses:
            return 'unhealthy'
        elif 'degraded' in statuses or 'warning' in statuses:
            return 'degraded'
        elif all(s == 'healthy' for s in statuses):
            return 'healthy'
        else:
            return 'unknown'
    
    async def start_monitoring(self) -> None:
        """Start continuous health monitoring"""
        if self._is_monitoring:
            return
        
        self._is_monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        self.logger.info("Health monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop continuous health monitoring"""
        self._is_monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Health monitoring stopped")
    
    async def _monitor_loop(self) -> None:
        """Continuous monitoring loop"""
        while self._is_monitoring:
            try:
                await self.run_all_checks()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    def get_last_results(self) -> Dict[str, Any]:
        """Get last health check results"""
        return self._last_results.copy()
    
    def get_check_status(self, name: str) -> Optional[Dict[str, Any]]:
        """Get status of specific health check"""
        return self._last_results.get(name)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get health checker statistics"""
        return {
            "service": self.service_name,
            "registered_checks": len(self._checks),
            "monitoring_active": self._is_monitoring,
            "check_interval_seconds": self.check_interval,
            "last_checks": len(self._last_results),
        }


# Common health check implementations

async def check_database(db_service) -> Dict[str, Any]:
    """Check database health"""
    return await db_service.health_check()


async def check_cache(cache_service) -> Dict[str, Any]:
    """Check cache health"""
    try:
        # Test cache operations
        await cache_service.set("health_check", "ok", namespace="system")
        value = await cache_service.get("health_check", namespace="system")
        
        if value == "ok":
            return {
                "name": "cache",
                "status": "healthy",
            }
        else:
            return {
                "name": "cache",
                "status": "unhealthy",
                "error": "Cache value mismatch",
            }
    except Exception as e:
        return {
            "name": "cache",
            "status": "unhealthy",
            "error": str(e),
        }


async def check_memory() -> Dict[str, Any]:
    """Check system memory"""
    import psutil
    
    try:
        memory = psutil.virtual_memory()
        
        status = "healthy"
        if memory.percent > 90:
            status = "unhealthy"
        elif memory.percent > 80:
            status = "degraded"
        
        return {
            "name": "memory",
            "status": status,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 * 1024),
        }
    except Exception as e:
        return {
            "name": "memory",
            "status": "unknown",
            "error": str(e),
        }


async def check_disk() -> Dict[str, Any]:
    """Check disk usage"""
    import psutil
    
    try:
        disk = psutil.disk_usage('/')
        
        status = "healthy"
        if disk.percent > 90:
            status = "unhealthy"
        elif disk.percent > 80:
            status = "degraded"
        
        return {
            "name": "disk",
            "status": status,
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024 ** 3),
        }
    except Exception as e:
        return {
            "name": "disk",
            "status": "unknown",
            "error": str(e),
        }
