# BedaanWaves API Documentation

## Overview

BedaanWaves provides a comprehensive set of RESTful API endpoints across 16+ routers, covering authentication, market data, analysis, ML predictions, portfolio management, and more. All endpoints are documented via automatic OpenAPI/Swagger generation.

## Base URL
- **Production**: Configured via `API_HOST` and `API_PORT` environment variables
- **Development**: `http://localhost:3000`
- **API Prefix**: `/api/v1/` (configurable via `API_V1_STR`)

## Authentication

All endpoints require JWT authentication unless otherwise specified.

### Authentication Flow
1. POST `/api/v1/auth/register` - Create new account
2. POST `/api/v1/auth/login` - Get access token
3. All subsequent requests include: `Authorization: Bearer <access_token>`
4. POST `/api/v1/auth/refresh` - Refresh access token (using refresh token)

### Access Token
- **Algorithm**: HS256 (configurable)
- **Expiration**: 24 hours (configurable via `JWT_EXPIRATION_HOURS`)
- **Format**: JWT token string

## API Routers (16 Total)

### 1. Auth Router (`/api/v1/auth`)
Endpoints for authentication and authorization management.

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/register` | Register new user | No |
| POST | `/login` | Authenticate and get token | No |
| POST | `/refresh` | Refresh access token | No |
| GET | `/verify` | Verify token validity | Yes |
| PUT | `/password` | Change password | Yes |
| DELETE | `/logout` | Invalidate token | Yes |

**Response Format (Success)**:
```json
{
  "status": "success",
  "data": {...},
  "timestamp": "ISO8601"
}
```

**Response Format (Error)**:
```json
{
  "status": "error",
  "detail": "Human-readable error message",
  "code": "ERROR_CODE"
}
```

### 2. Stocks Router (`/api/v1/stocks`)
Endpoints for stock data, details, history, and analysis.

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/list` | List all stocks with pagination | Yes |
| GET | `/{symbol}` | Get stock details | Yes |
| GET | `/{symbol}/history` | Historical price data | Yes |
| GET | `/{symbol}/analysis` | Technical & fundamental analysis | Yes |
| GET | `/{symbol}/fundamental` | Fundamental data details | Yes |
| GET | `/{symbol}/peers` | Peer companies | Yes |
| GET | `/sectors` | Available sectors | No |
| GET | `/exchanges` | Available exchanges | No |

**Query Parameters**:
- `symbol`: Stock ticker symbol
- `from_date`, `to_date`: Date range for history
- `interval`: Time interval (1d, 1h, 15m, 5m, 1m)
- `limit`, `offset`: Pagination

### 3. Market Router (`/api/v1/market`)
Endpoints for market-wide data, indices, and sector performance.

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/overview` | Market overview summary | Yes |
| GET | `/indices` | Market indices data | Yes |
| GET | `/sectors` | Sector performance ranking | Yes |
| GET | `/gainers` | Top gaining stocks | Yes |
| GET | `/losers` | Top losing stocks | Yes |
| GET | `/active` | Most active stocks | Yes |
| GET | `/calendar` | Market calendar events | No |
| GET | `/sentiment` | Market sentiment indicators | Yes |

**Path Parameters**:
- `index_type`: 1 (NASDAQ), 2 (International)
- `exchange`: Exchange code (NASDAQ, OTC, etc.)

### 4. Analysis Router (`/api/v1/analysis`)
Endpoints for scoring, signals, predictions, and backtesting.

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/{symbol}/scores` | Get 6D scores | Yes |
| GET | `/{symbol}/signals` | Trading signals | Yes |
| GET | `/{symbol}/predict` | Price predictions | Yes |
| POST | `/{symbol}/backtest` | Run backtest strategy | Yes |
| POST | `/batch` | Batch analysis | Yes |
| GET | `/rankings` | Symbol rankings | Yes |
| GET | `/heatmap` | Sector performance heat map | Yes |

**Request Body (Backtest)**:
```json
{
  "strategy": {
    "type": "moving_average_crossover",
    "params": {
      "short_window": 20,
      "long_window": 50
    }
  },
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 100000000
}
```

### 5. Portfolio Router (`/api/v1/portfolio`)
Endpoints for portfolio management operations.

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/` | Create new portfolio | Yes |
| GET | `/list` | List user portfolios | Yes |
| GET | `/{id}` | Get portfolio details | Yes |
| PUT | `/{id}` | Update portfolio | Yes |
| DELETE | `/{id}` | Delete portfolio | Yes |
| POST | `/{id}/holdings` | Add holding | Yes |
| PUT | `/{id}/holdings/{symbol}` | Update holding | Yes |
| DELETE | `/{id}/holdings/{symbol}` | Remove holding | Yes |
| GET | `/{id}/performance` | Portfolio performance | Yes |
| GET | `/{id}/allocation` | Asset allocation breakdown | Yes |
| POST | `/{id}/analyze` | Portfolio analysis | Yes |

**Portfolio Model**:
```json
{
  "name": "My Portfolio",
  "description": "Conservative allocation",
  "strategy": "balanced",
  "is_public": false
}
```

### 6. History Router (`/api/v1/history`)
Endpoints for historical data retrieval.

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/price-history` | Historical price data | Yes |
| GET | `/fundamental-history` | Historical fundamental data | Yes |
| GET | `/score-history` | Historical scores | Yes |
| GET | `/signal-history` | Historical signals | Yes |
| GET | `/prediction-history` | Historical predictions | Yes |

### 7. News Router (`/api/v1/news`)
Endpoints for news search, sentiment, and summarization.

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/search` | Search news by query | Yes |
| GET | `/{symbol}` | News for specific symbol | Yes |
| GET | `/sentiment/{symbol}` | Sentiment analysis | Yes |
| POST | `/summarize` | Summarize news articles | Yes |
| GET | `/sources` | Available news sources | No |
| GET | `/top-headlines` | Top news headlines | Yes |

### 8. ML Router (`/api/v1/ml`)
Endpoints for machine learning model predictions and analysis.

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/models` | Available models | Yes |
| POST | `/predict/{symbol}` | Generate prediction | Yes |
| GET | `/recommendations` | Personalized recommendations | Yes |
| GET | `/anomalies` | Detect anomalies | Yes |
| POST | `/patterns` | Detect chart patterns | Yes |
| GET | `/forecast/{symbol}` | Time series forecast | Yes |
| POST | `/optimize` | Portfolio optimization | Yes |

**ML Model Endpoints**:
- `/models/list` - List available trained models
- `/models/{model_id}/metrics` - Get model performance metrics
- `/models/{model_id}/version` - Get model version info

### 9. Users Router (`/api/v1/users`)
Endpoints for user profile and management.

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/profile` | Get current user profile | Yes |
| PUT | `/profile` | Update user profile | Yes |
| GET | `/settings` | Get user settings | Yes |
| PUT | `/settings` | Update user settings | Yes |
| POST | `/kyc` | Submit KYC information | Yes |

### 10. Watchlists Router (`/api/v1/watchlists`)
Endpoints for watchlist management.

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/` | Create watchlist | Yes |
| GET | `/list` | List all watchlists | Yes |
| GET | `/{id}` | Get watchlist details | Yes |
| PUT | `/{id}` | Update watchlist | Yes |
| DELETE | `/{id}` | Delete watchlist | Yes |
| POST | `/{id}/symbols` | Add symbol to watchlist | Yes |
| DELETE | `/{id}/symbols/{symbol}` | Remove symbol | Yes |

### 11. Notifications Router (`/api/v1/notifications`)
Endpoints for notification management.

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/list` | List recent notifications | Yes |
| POST | `/mark-read` | Mark notifications as read | Yes |
| POST | `/settings` | Configure notification settings | Yes |
| DELETE | `/{id}` | Delete notification | Yes |

### 12. Specialized Router (`/api/v1/specialized`)
Endpoints for specialized analysis and filters.

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/macro-regime` | Macro regime analysis | Yes |
| GET | `/exchange-rates` | Exchange rate information | Yes |
| GET | `/currency-conversion` | Currency conversion | Yes |
| POST | `/cross-asset-comparison` | Cross-asset comparison | Yes |

### 13. System Router (`/api/v1/system`)
Endpoints for system monitoring and administration.

| Method | Endpoint | Description | Auth Required | Admin Only |
|--------|----------|-------------|---------------|------------|
| GET | `/status` | System status summary | Yes | No |
| GET | `/health` | Detailed health check | No | No |
| GET | `/metrics` | Prometheus metrics | No | No |
| GET | `/logs` | Recent system logs | Yes | Yes |
| POST | `/maintenance` | Toggle maintenance mode | Yes | Yes |
| POST | `/cache/clear` | Clear application cache | Yes | Yes |

### 14. Intl Router (`/api/v1/intl`)
Endpoints for international market data.

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/symbols` | International symbols list | Yes |
| GET | `/{symbol}/history` | Historical data | Yes |
| GET | `/{symbol}/fundamental` | Fundamental data | Yes |
| GET | `/exchanges` | International exchanges | No |
| GET | `/sectors` | International sectors | Yes |

### 16. Live Router (`/api/v1/live`)
Endpoints for real-time/live data streaming.

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/stream` | Live data stream (SSE) | Yes |
| GET | `/index` | Live index data | Yes |
| GET | `/quotes` | Real-time quotes | Yes |
| GET | `/alerts/active` | Active user alerts | Yes |

## Response Schema

### Standard Response Format
All responses follow a consistent format:
```json
{
  "status": "success" | "error",
  "data": {...} | null,   // Present on success
  "error": {...} | null,  // Present on error
  "timestamp": "ISO8601"
}
```

### Pagination Schema
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 1000,
    "total_pages": 50,
    "has_next": true,
    "has_prev": false
  }
}
```

### Error Response Schema
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Detailed error description",
    "details": {...} // Optional additional context
  },
  "timestamp": "ISO8601"
}
```

## HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Success |
| 201 | Created | Resource created successfully |
| 204 | No Content | Success but no content returned |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource does not exist |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 502 | Bad Gateway | Upstream service unavailable |
| 503 | Service Unavailable | Server overloaded or down |
| 504 | Gateway Timeout | Upstream timeout |

## Rate Limiting

### Default Limits
- **Authenticated**: 1000 requests per 5 minutes per user
- **Unauthenticated**: 100 requests per 5 minutes per IP
- **WebSocket**: 1 connection per user, 30 messages per second
- **Bulk Operations**: 10 requests per minute

### Rate Limit Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1692312000
Retry-After: 300
```

## API Documentation Endpoints

- **Swagger UI**: `http://localhost:8000/docs`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`
- **ReDoc**: `http://localhost:8000/redoc`

## API Versioning

The API uses URL-based versioning: `/api/v1/...`
- **Current Version**: v1
- **Deprecation Policy**: 6 months notice for deprecated endpoints
- **Backward Compatibility**: Maintained within same major version

## WebSocket API

### Connection
```
ws://localhost:8000/ws/market/stream
```

### Authentication
Include JWT token as query parameter:
```
ws://localhost:8000/ws/market/stream?token=<jwt_token>
```

### Subscription
```json
{
  "action": "subscribe",
    "symbols": ["AAPL", "GOOGL"],
  "channels": ["price", "signal", "news"]
}
```

### Incoming Messages
```json
{
  "type": "price_update",
  "symbol": "AAPL",
  "data": {
    "price": 185.75,
    "change": 1.25,
    "change_pct": 0.68,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Message Types
- `price_update`: Real-time price data
- `signal_update`: New trading signal generated
- `news_alert`: Breaking news notification
- `portfolio_update`: Portfolio value changes
- `system_announcement`: System maintenance messages

## Client Examples

### Python
```python
import requests

# Authentication
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"username": "user@example.com", "password": "password"}
)
token = response.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get stock analysis
response = requests.get(
    "http://localhost:8000/api/v1/stocks/FSPC/analysis",
    headers=headers
)
print(response.json())
```

### JavaScript (Browser)
```javascript
// Fetch market data
async function getMarketData() {
  const token = localStorage.getItem('access_token');
  const response = await fetch('http://localhost:8000/api/v1/market/overview', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return await response.json();
}
```

## Environment Configuration

API behavior is configured via environment variables:
```env
API_HOST=0.0.0.0
API_PORT=8000
API_V1_STR=/api/v1
API_TITLE=BedaanWaves
API_VERSION=1.0.0
CORS_ORIGINS=http://localhost:3000
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_REQUESTS=1000
```

---
*Last Updated: 2026-08-17*
*Status: Production Ready - API Fully Documented*