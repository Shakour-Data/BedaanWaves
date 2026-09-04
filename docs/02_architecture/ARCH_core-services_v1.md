# BedaanWaves Tier 1: Core Services

## Overview

Tier 1 Core Services provide the foundational infrastructure for the entire BedaanWaves platform. These singleton services are initialized first during application startup and provide essential capabilities including dependency injection, configuration, logging, caching, database access, and health monitoring.

**Implementation Status**: 100% Complete
**Service Count**: 6 services
**Location**: `backend/app/services/core/`

## Base Service Classes

All services extend base classes defined in `base_service.py`:

### BaseService
Abstract base class (ABC) providing:
- Dependency injection framework
- Structured logging (`self.logger`)
- In-memory caching (`cache_get`, `cache_set`, `cache_clear`)
- Metrics tracking (`_metrics` dict with calls, errors, cache hits/misses)
- Health check support (`health_check()`)
- Lifecycle methods (`initialize()`, `shutdown()`)

### CachedService
Extends BaseService with:
- TTL-aware caching (`get_cached`, `set_cached`)
- Cache validity checking (`_is_cache_valid`)

### DataService
Extends BaseService with:
- Database operation patterns (`get_by_id`, `list_all`, `create`, `update`, `delete`)

### AnalysisService
Extends BaseService with:
- Analysis computation patterns
- Batch analysis support (`batch_analyze` using `asyncio.gather`)

### MLService
Extends BaseService with:
- ML model management
- Training, prediction, and evaluation interface methods

### ExternalAPIService
Extends BaseService with:
- External API communication patterns
- Rate limiting handling (`_handle_rate_limit` with exponential backoff)

---

## 1. DependencyContainer (IoC/DI Management)

**File**: `app/services/core/dependency_container.py`

### Purpose
Central dependency injection container managing all service instances and their lifecycle. Implements the service locator pattern for dependency injection.

### Key Features
- Service registration with factory functions
- Singleton instance caching
- Default keyword argument passing
- Async lifecycle management (initialize/shutdown)

### Initialization
```python
container = DependencyContainer()
await container.initialize()
```

### Service Registration
```python
container.register(
    service_name="ConfigService",
    factory=lambda: ConfigService(service_name="ConfigService"),
    singleton=True
)
```

### Service Retrieval
```python
config_service = container.get("ConfigService")
db_service = container.get("DatabaseService", database_url="postgresql://...")
```

### Container Statistics
```python
stats = container.get_stats()
# Returns: registered_services, singleton_instances, uptime_seconds
```

### Shutdown
```python
await container.shutdown_all()
```

### Key Methods
| Method | Description |
|--------|-------------|
| `register(name, factory, singleton, **kwargs)` | Register service factory |
| `get(name, **kwargs)` | Get service instance |
| `register_instance(name, instance)` | Register pre-created instance |
| `has(name)` | Check if service is registered |
| `remove(name)` | Remove service registration |
| `initialize()` | Initialize all registered services |
| `shutdown_all()` | Shutdown all services |
| `get_stats()` | Get container statistics |

---

## 2. ConfigService (Centralized Configuration)

**File**: `app/services/core/config_service.py`

### Purpose
Manages all configuration for BedaanWaves application. Handles environment variables, settings, and feature flags with 100+ settings across 15+ categories.

### Key Features
- Environment variable loading with `.env` file support
- Type conversion helpers (`get_int`, `get_bool`, `get_float`, `get_list`, `get_json`)
- Configuration sections: api, database, cache, ml, security, services
- Validation on startup
- Runtime configuration updates
- Environment detection (production/development)

### Configuration Categories
1. **Application**: `ENVIRONMENT`, `DEBUG`, `LOG_LEVEL`
2. **API**: `API_HOST`, `API_PORT`, `API_V1_STR`, CORS settings, rate limits
3. **Database**: `DB_*`, `DATABASE_URL`, pool settings
4. **Cache**: `CACHE_BACKEND`, `REDIS_URL`, `CACHE_TTL`
5. **ML**: `ML_MODELS_DIR`, batch size, learning rate, epochs
6. **Security**: `JWT_SECRET`, `JWT_ALGORITHM`, password policy
7. **Services**: API keys, endpoints, rate limits for external services

### Access Methods
```python
config = ConfigService()

# String value
config.get('DB_NAME', 'bedaanwaves')

# Typed values
config.get_int('API_PORT', 8000)
config.get_bool('DEBUG', False)
config.get_float('ML_LEARNING_RATE', 0.001)
config.get_list('CORS_ORIGINS', ['*'])

# Section access
db_config = config.get_config('database')
api_config = config.get_config('api')

# Environment checks
config.is_production()
config.is_development()
config.is_debug()
```

### Key Methods
| Method | Description |
|--------|-------------|
| `get(key, default)` | Get string value |
| `get_int(key, default)` | Get integer value |
| `get_float(key, default)` | Get float value |
| `get_bool(key, default)` | Get boolean value |
| `get_list(key, default)` | Get list value |
| `get_json(key, default)` | Get JSON value |
| `get_config(section)` | Get configuration section |
| `set_config(key, value)` | Set runtime value |
| `is_production()` | Check if production |
| `is_development()` | Check if development |

---

## 3. LoggerService (Structured Logging)

**File**: `app/services/core/logger_service.py`

### Purpose
Centralized logging service providing structured logging with multiple output formats (console, file). Integrates with Python's logging module and structlog for JSON output.

### Key Features
- Structured logging with JSON support
- Multiple log handlers (console, rotating file)
- Context-aware logging with correlation IDs
- Contextual logging (temporary key-value pairs)
- Performance logging with duration tracking
- Log level management at runtime
- Detailed and summary formatters

### Log Directory
Default: `./logs/` (configurable via `LOG_DIR` env var)
File naming: `bedaanwaves_YYYYMMDD.log`

### Usage
```python
logger_service = LoggerService(log_level="INFO")

# Get logger instance
logger = logger_service.get_logger("MyService")

# Log messages
logger.info("Processing completed")
logger.error("Error occurred")

# Structured logging
logger_service.log_structured(
    "MyService", "info", "User action",
    user_id="123", action="buy"
)

# Error logging with traceback
try:
    risky_operation()
except Exception as e:
    logger_service.log_error("MyService", e, "Failed to process")

# Performance logging
start = time.time()
process_data()
duration = time.time() - start
logger_service.log_performance("MyService", "process_data", duration, True)
```

### Log Format

**Console Format** (non-detailed):
```
[level] module_name - message
```

**File Format** (detailed):
```
[timestamp] [LEVEL] [logger_name:line_number] function() - message
```

**JSON Structured**:
```json
{
  "timestamp": "2026-08-17T10:00:00Z",
  "message": "User action",
  "user_id": "123",
  "action": "buy"
}
```

### Key Methods
| Method | Description |
|--------|-------------|
| `get_logger(name, module)` | Get or create logger instance |
| `set_context(key, value)` | Set contextual information |
| `get_context()` | Get current context |
| `clear_context()` | Clear contextual info |
| `log_structured(name, level, msg, **kwargs)` | Log structured JSON |
| `log_error(name, error, msg, **kwargs)` | Log error with traceback |
| `log_performance(name, op, duration_ms, success)` | Log performance metrics |
| `set_level(level)` | Change log level |
| `get_stats()` | Get logger statistics |

---

## 4. CacheService (Multi-Backend Caching)

**File**: `app/services/core/cache_service.py`

### Purpose
Centralized cache management providing multi-backend caching support (memory, Redis with memory fallback). Features TTL management, pattern-based invalidation, and statistics.

### Key Features
- Pluggable cache backends (Memory, Redis)
- Namespace-based key organization
- Hash-based key generation for complex data
- TTL (Time-To-Live) management with expiry
- Pattern-based invalidation
- Statistics collection and monitoring
- `get_or_set` for cache-aside pattern
- Batch operations (`get_many`, `set_many`)

### Cache Backends

#### MemoryCacheBackend (Default)
- In-process memory cache
- Thread-safe access
- Dictionary-based storage with TTL
- Automatic expiry cleanup

#### RedisCacheBackend (Planned)
- Distributed cache via Redis
- Automatic fallback to memory if Redis unavailable
- Namespace isolation

### Cache Key Patterns
```python
# Namespaced keys
cache.set("price:AAPL", data, namespace="stock")
# Key becomes: "stock:price:AAPL"

# Hash-based keys for complex queries
key = cache._get_hash_key({"symbol": "AAPL", "period": "1y"})
cache.set(key, result, namespace="analysis")
```

### Usage
```python
cache = CacheService(backend="memory", default_ttl=3600)

# Basic operations
await cache.set("user:123:profile", profile_data, ttl=1800)
data = await cache.get("user:123:profile", namespace="user")

# Cache-aside pattern
data = await cache.get_or_set(
    "stock:AAPL:prices",
    factory=lambda: fetch_realtime_prices("AAPL"),
    namespace="stock",
    ttl=300
)

# Check existence
exists = await cache.exists("key", namespace="default")

# Delete
await cache.delete("key", namespace="default")

# Clear namespace
await cache.clear(namespace="stock")
```

### Cache Statistics
```python
stats = cache.get_stats()
# Returns: cache_hits, cache_misses, hit_rate, avg_response_time_ms
```

### Key Methods
| Method | Description |
|--------|-------------|
| `get(key, namespace)` | Get value from cache |
| `set(key, value, namespace, ttl)` | Set value in cache |
| `delete(key, namespace)` | Delete cache entry |
| `clear(namespace)` | Clear entire cache or namespace |
| `exists(key, namespace)` | Check if key exists |
| `get_or_set(key, factory, namespace, ttl)` | Get or compute and set |
| `set_many(items, namespace, ttl)` | Set multiple entries |
| `get_many(keys, namespace)` | Get multiple entries |
| `register_namespace(namespace, prefix)` | Register namespace prefix |
| `get_stats()` | Get cache statistics |

---

## 5. DatabaseService (Connection Pooling)

**File**: `app/services/core/database_service.py`

### Purpose
Manages database connections, session management, and transaction handling. Provides connection pooling via SQLAlchemy with both sync and async support.

### Key Features
- Async PostgreSQL with asyncpg driver
- Connection pooling with configurable sizes
- Session management with automatic cleanup
- Connection health checks
- URL masking for security (password hidden in logs)
- Connection recycling (30min idle timeout)
- Active session tracking

### Engine Configuration
```python
# Async engine
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost:5432/db",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)
```

### Usage
```python
db = DatabaseService(async_mode=True)
await db.initialize()

# Direct query execution
result = await db.execute(query)

# Session management
session = await db.get_session()
try:
    await session.execute(query)
    await session.commit()
finally:
    await session.close()

# Health check
health = await db.health_check()

# Get connection URL (masked)
masked_url = db.get_connection_url()
```

### Session Management
- Sessions are tracked in `_active_sessions` list
- Automatic cleanup on shutdown
- `expire_on_commit=False` for performance
- Connection pool recycling every 3600 seconds

### Key Methods
| Method | Description |
|--------|-------------|
| `initialize()` | Initialize database engine and pool |
| `shutdown()` | Close all sessions and dispose engine |
| `get_session()` | Get a new database session |
| `execute(query)` | Execute raw query |
| `health_check()` | Database connectivity and health |
| `clean_sessions()` | Remove closed sessions |
| `get_connection_url()` | Get masked connection URL |
| `get_stats()` | Get database statistics |

### Health Check Response
```python
{
    "service": "DatabaseService",
    "status": "healthy",  # or "unhealthy"
    "connection_checks": 42,
    "active_sessions": 5,
    "pool_size": 20,
    "max_overflow": 10,
    "async_mode": True
}
```

---

## 6. HealthChecker (System Monitoring)

**File**: `app/services/core/health_checker.py`

### Purpose
System health monitoring service that checks database connectivity, cache functionality, system memory/disk, and service health status. Provides health check endpoints for infrastructure monitoring.

### Key Features
- Database connectivity checks
- Cache functionality verification
- System resource monitoring (memory, disk)
- Service health aggregation
- Detailed health status reporting
- Configurable check timeouts
- Dependency chain health propagation

### Health Check Levels
1. **Basic**: Database and cache connectivity
2. **Detailed**: Resource utilization metrics
3. **Extended**: All services and dependencies

### Usage
```python
health = HealthChecker(
    db_service=db_service,
    cache_service=cache_service
)
await health.initialize()

# Check health
status = await health.check_health()
# Returns: {"status": "healthy", "services": {...}}

# Deep health check
detailed = await health.check_detailed_health()
```

### Health Status Response
```python
{
    "status": "healthy",
    "timestamp": "2026-08-17T10:00:00Z",
    "services": {
        "database": "healthy",
        "cache": "healthy",
        "config": "healthy"
    },
    "system": {
        "cpu_percent": 25.5,
        "memory_percent": 45.2,
        "disk_percent": 60.1
    },
    "version": "1.0.0"
}
```

### Key Methods
| Method | Description |
|--------|-------------|
| `initialize()` | Initialize health checker |
| `shutdown()` | Shutdown health checker |
| `check_health()` | Basic health check |
| `check_detailed_health()` | Comprehensive health check |
| `check_database()` | Check database connectivity |
| `check_cache()` | Check cache functionality |
| `check_system_resources()` | Check system resources |
| `check_service(name, service)` | Check individual service health |
| `get_stats()` | Get health checker statistics |

---

## Tier 1 Service Lifecycle

### Initialization Sequence
```
main.py:
1. Create DependencyContainer
2. await container.initialize()
3. Container initializes all registered services in order
4. Register all API routers
5. Application ready to serve requests

On Shutdown:
1. await container.shutdown_all()
2. All services call shutdown() in reverse order
3. Clean up database connections, close log files
```

### Service Registration Pattern
```python
# In main.py lifespan handler
container = DependencyContainer()
app.state.container = container

# Core services registered as singletons
container.register("ConfigService", lambda: ConfigService(), singleton=True)
container.register("LoggerService", lambda: LoggerService(), singleton=True)
container.register("CacheService", lambda: CacheService(), singleton=True)
container.register("DatabaseService", lambda: DatabaseService(), singleton=True)

# Initialize all services
await container.initialize()
```

### Health Check Endpoint
All Tier 1 services are available at the health endpoint:
```
GET /health
{
  "status": "healthy",
  "service": "BedaanWaves",
  "version": "1.0.0",
  "timestamp": "2026-08-17T10:00:00Z"
}
```

---
*Last Updated: 2026-08-17*
*Status: Production Ready - Tier 1 Services 100% Implemented*