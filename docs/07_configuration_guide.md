# BedaanWaves Configuration Guide

## Overview

BedaanWaves configuration is centralized through the `ConfigService` with 100+ environment variables organized into 15+ categories. All configuration is loaded from environment variables with `.env` file support.

## Environment Setup

### Required Files
- `.env` - Development configuration (not committed to git)
- `.env.production` - Production configuration template
- `config.py` - Default settings and validation

### Environment Variable Loading Order
1. System environment variables
2. `.env` file (if exists)
3. Configuration file path from `CONFIG_FILE` env var
4. Default values defined in code

## Configuration Categories

### 1. Application Settings
```env
# Application Environment
ENVIRONMENT=development|production|staging|testing

# Main Configuration
APP_NAME=BedaanWaves
APP_VERSION=1.0.0
APP_DESCRIPTION=Unified Capital Market Analysis Platform
DEBUG=false
LOG_LEVEL=INFO
```

### 2. API Configuration
```env
API_HOST=0.0.0.0
API_PORT=8000
API_TITLE=BedaanWaves API
API_VERSION=1.0.0
API_V1_STR=/api/v1
API_BASE_PATH=/api/v1
API_TIMEOUT=30
API_MAX_CONNECTIONS=100
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,PATCH
CORS_ALLOW_HEADERS=*
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_REQUESTS=1000
RATE_LIMIT_WINDOW_SECONDS=300
```

### 3. Database Configuration
```env
DB_DRIVER=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bedaanwaves
DB_USER=postgres
DB_PASSWORD=your_secure_password
DATABASE_URL=postgresql://postgres:password@localhost:5432/bedaanwaves
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
DATABASE_ECHO=false
```

### 4. Cache Configuration
```env
CACHE_BACKEND=memory|redis
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600
CACHE_MAX_SIZE=1000
CACHE_DEFAULT_TTL=3600
```

### 5. Security Configuration
```env
JWT_SECRET=your-secure-jwt-secret-key-at-least-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
JWT_REFRESH_EXPIRATION_HOURS=168
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL=true
ENABLE_HTTPS=true
CORS_ORIGINS=http://localhost:3000
```

### 6. ML Configuration
```env
ML_MODELS_DIR=/app/models
ML_BATCH_SIZE=32
ML_LEARNING_RATE=0.001
ML_EPOCHS=100
ML_ENSEMBLE_ENABLED=true
ML_PREDICTION_HORIZON=30
ML_CONFIDENCE_THRESHOLD=0.7
ML_MODEL_RETRAIN_INTERVAL=86400
```

### 7. Data Ingestion Configuration
```env
INTERNATIONAL_API_KEY=your-alpha-vantage-key
NEWS_API_KEY=your-news-api-key
```

### 8. News & NLP Configuration
```env
NLP_MODEL=parsbert-base-uncased
NLP_MODEL_PATH=/app/models/parsbert
SENTIMENT_THRESHOLD_POSITIVE=0.55
SENTIMENT_THRESHOLD_NEGATIVE=0.45
NEWS_SUMMARY_LENGTH=100
NEWS_MAX_ARTICLES=50
```

### 9. Risk & Analysis Configuration
```env
RISK_CONFIDENCE_LEVEL=0.95
RISK_HISTORICAL_DAYS=252
VOLATILITY_SHORT_WINDOW=20
VOLATILITY_LONG_WINDOW=50
CORRELATION_WINDOW=252
CORRELATION_THRESHOLD=0.7
```

### 10. Portfolio Configuration
```env
PORTFOLIO_DEFAULT_RISK=moderate
PORTFOLIO_REBALANCE_FREQUENCY=monthly
PORTFOLIO_MIN_INVESTMENT=1000000
PORTFOLIO_MAX_POSITIONS=50
```

### 11. Trading & Signals Configuration
```env
SIGNAL_CONFIDENCE_MIN=0.6
SIGNAL_MOMENTUM_PERIOD=20
SIGNAL_RELATIVE_STRENGTH_DAYS=14
SIGNAL_VOLUME_THRESHOLD=1.5
ARBITRAGE_SPREAD_THRESHOLD=0.5
```

### 12. Notification Configuration
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@bedaanwaves.com
SMS_PROVIDER=twilio
SMS_FROM_NUMBER=+1234567890
```

### 13. Scheduler Configuration
```env
SCHEDULER_ENABLED=true
SCHEDULER_JOB_INTERVAL=3600
SCHEDULER_DATA_INGEST_CRON=0 */2 * * *
SCHEDULER_MODEL_TRAIN_CRON=0 2 * * 0
SCHEDULER_SIGNAL_UPDATE_CRON=*/15 * * * *
```

### 14. Logging Configuration
```env
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_DIR=/var/log/bedaanwaves
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5
LOG_DATE_FORMAT=%Y-%m-%d %H:%M:%S
```

### 15. Monitoring Configuration
```env
METRICS_ENABLED=true
METRICS_PATH=/metrics
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=5
TRACE_SLOW_QUERIES=true
SLOW_QUERY_THRESHOLD=1.0
```

## Configuration Access in Code

### Getting Configuration Values
```python
from app.core.config import get_settings
from app.services.core.config_service import ConfigService

# Standard settings
settings = get_settings()
api_port = settings.API_PORT
db_url = settings.DATABASE_URL

# ConfigService for dynamic access
config = ConfigService()
value = config.get('SOME_VARIABLE')
int_value = config.get_int('PORT', 8000)
bool_value = config.get_bool('DEBUG', False)
list_value = config.get_list('CORS_ORIGINS', ['*'])
```

### Configuration Sections
```python
# Get all configuration
all_config = config.get_config()

# Get specific section
api_config = config.get_config('api')
db_config = config.get_config('database')
ml_config = config.get_config('ml')

# Check environment
if config.is_production():
    # Production-specific logic
    pass

if config.is_debug():
    # Debug-mode specific logic
    pass
```

## Environment-Specific Configuration

### Development (.env)
```env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://postgres:password@localhost:5432/bedaanwaves_dev
CORS_ORIGINS=*
```

### Staging (.env.staging)
```env
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://postgres:password@staging-db:5432/bedaanwaves
CORS_ORIGINS=https://staging.bedaanwaves.com
```

### Production (.env.production)
```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://postgres:secure-password@prod-db:5432/bedaanwaves
CORS_ORIGINS=https://bedaanwaves.com,https://api.bedaanwaves.com
```

## Configuration Validation

### Startup Validation
ConfigService validates critical settings on initialization:

```python
# Required validations
assert settings.DATABASE_URL is not None
assert settings.JWT_SECRET is not None and len(settings.JWT_SECRET) >= 32
assert settings.DEBUG is False when ENVIRONMENT=production

# Value range validations
assert 0 <= settings.RATE_LIMIT_MAX_REQUESTS <= 100000
assert 0 <= settings.JWT_EXPIRATION_HOURS <= 168
```

### Custom Validation
```python
from pydantic import field_validator

class Settings(BaseSettings):
    @field_validator('JWT_SECRET')
    @classmethod
    def jwt_secret_length(cls, v):
        if len(v) < 32:
            raise ValueError('JWT_SECRET must be at least 32 characters')
        return v
```

## Security Best Practices

### Secrets Management
1. **Never commit `.env` files** - Add to `.gitignore`
2. **Use environment variables** in production deployments
3. **Rotate secrets regularly** - Especially JWT_SECRET and API keys
4. **Use different secrets per environment**
5. **Consider HashiCorp Vault** for production secrets

### Example `.gitignore`
```
.env
.env.*
!.env.example
config/secrets/
*.secret
```

### Example `.env.example`
```env
# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bedaanwaves
DB_USER=postgres
DB_PASSWORD=change_me_in_production

# Security (CHANGE THESE)
JWT_SECRET=your-secure-jwt-secret-key-min-32-chars
SECRET_KEY=your-django-secret-key-here

# API
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# Cache (optional)
REDIS_URL=redis://localhost:6379/0
```

## Configuration Override

### Runtime Override
```python
config = ConfigService()
config.set_config('custom_value', 'test')

# Override database URL temporarily
config.set_config('database', {
    **config.get_config('database'),
    'test_mode': True
})
```

### Environment Variable Precedence
```
Code Default < .env < Environment Variable
```

## Feature Flags

Feature flags are configured via environment variables:

```env
# Feature flags
FEATURE_NEW_DASHBOARD=true
FEATURE_ADVANCED_ANALYTICS=false
FEATURE_CV_SCANNER=true
FEATURE_ML_PREDICTIONS=true
FEATURE_RISK_SIMULATOR=false
```

Access in code:
```python
def is_feature_enabled(feature_name: str, default: bool = False) -> bool:
    return config.get_bool(f'FEATURE_{feature_name}', default)

if is_feature_enabled('NEW_DASHBOARD'):
    # Enable new dashboard feature
    pass
```

## Configuration Hot Reload (Development Only)

```python
# Enable hot reload in development
if settings.ENVIRONMENT == 'development':
    import os
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    
    class ConfigReloader(FileSystemEventHandler):
        def on_modified(self, event):
            if event.src_path.endswith('.env'):
                config.reload()
```

## Common Configuration Issues

### Database Connection Issues
```bash
# Error: could not connect to server
# Check: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD are correct
# Verify: PostgreSQL is running on the specified port

# Error: database does not exist
# Fix: Create the database
createdb bedaanwaves
```

### CORS Issues
```bash
# Error: CORS preflight failed
# Fix: Ensure CORS_ORIGINS includes your frontend URL
CORS_ORIGINS=https://your-frontend.com,http://localhost:3000
```

### JWT Issues
```bash
# Error: token is expired
# Fix: Check JWT_EXPIRATION_HOURS and system time
# Fix: Ensure client is using correct token refresh mechanism

# Error: token is invalid
# Fix: Verify JWT_SECRET is the same for encoding and decoding
```

## Configuration Logging

At startup, BedaanWaves logs all non-sensitive configuration:

```
[2026-08-17 10:00:00] [INFO] Loaded 100+ configuration settings
[2026-08-17 10:00:00] [INFO] Database configured: postgresql://postgres:***@localhost:5432/bedaanwaves
[2026-08-17 10:00:00] [INFO] API configured: http://0.0.0.0:8000
[2026-08-17 10:00:00] [INFO] Cache backend: memory
[2026-08-17 10:00:00] [INFO] Environment: development
```

---
*Last Updated: 2026-08-17*
*Status: Production Ready - Full Configuration Documentation*