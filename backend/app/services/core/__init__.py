"""
Core Services - Foundation Layer

These core services provide the foundation for all other services:
1. DependencyContainer - IoC/DI for service management
2. ConfigService - Centralized configuration
3. LoggerService - Structured logging
4. CacheService - Redis caching
5. DatabaseService - Database connection pooling
6. HealthChecker - System health monitoring
"""

from .base_service import (
    BaseService,
    CachedService,
    DataService,
    AnalysisService,
    MLService,
    ExternalAPIService,
)
from .dependency_container import DependencyContainer, get_global_container
from .config_service import ConfigService
from .logger_service import LoggerService
from .cache_service import CacheService, MemoryCacheBackend
from .database_service import DatabaseService
from .health_checker import HealthChecker, check_database, check_cache, check_memory, check_disk

__all__ = [
    # Base classes
    "BaseService",
    "CachedService",
    "DataService",
    "AnalysisService",
    "MLService",
    "ExternalAPIService",
    # Tier 1 Core Services
    "DependencyContainer",
    "get_global_container",
    "ConfigService",
    "LoggerService",
    "CacheService",
    "MemoryCacheBackend",
    "DatabaseService",
    "HealthChecker",
    "check_database",
    "check_cache",
    "check_memory",
    "check_disk",
]
