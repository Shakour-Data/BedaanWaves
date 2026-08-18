# BedaanWaves - Core Services Documentation

## Overview
This documentation covers the 9 core services that form the foundation of BedaanWaves unified platform. These services provide essential functionality across all aspects of the platform from data access to user management.

## Tier 1 Core Services

### DependencyContainerService
- **Purpose**: Inversion of Control container
- **Features**: Service registration, lifetime management, scope handling
- **Integration**: Used by all other services for dependency resolution
- **Endpoints**: /api/v1/sys/dependency

### ConfigService
- **Purpose**: Centralized configuration management
- **Features**: Environment-aware settings, fallback mechanisms
- **Features**: Supports 100+ configuration parameters
- **Endpoints**: /api/v1/sys/config

### LoggerService
- **Purpose**: Structured logging system
- **Features**: Log levels, correlation IDs, exception tracking
- **Integrations**: Used by all services for audit trails

### CacheService
- **Purpose**: Multi-backend caching layer
- **Features**: Memory and Redis backends
- **TTLs**: Configurable per data type

### DatabaseService
- **Purpose**: Connection pooling and management
- **Features**: PostgreSQL integration
- **Connection Pooling**: Configurable sizes and timeouts

### HealthCheckerService
- **Purpose**: System health monitoring
- **Features**: Service status checks
- **Endpoints**: /api/v1/health

### RateLimiterService
- **Purpose**: API request rate limiting
- **Features**: Configurable limits (per minute/hour)
- **Protection**: Against DDoS attacks

### ErrorHandlerService
- **Purpose**: Centralized error management
- **Features**: Standardized error responses
- **Logging**: Detailed error tracking

## Integration
These services form the foundation that all other components rely on. They provide:
- Basic platform functionality
- Resource management
- Error handling
- Performance monitoring

## Diagrams
```
Core Services Flow:
DatabaseService → CacheService → Service Consumers
← HealthChecker → RateLimiter
```