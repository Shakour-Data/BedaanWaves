# API Documentation - BedaanWaves v1.0

## Overview

This document describes the REST API endpoints introduced in the latest release. The API is organized into logical groups under `/api/v1/` prefixes.

## Health Checks

### GET /health

General health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "BedaanWaves",
  "version": "1.0.0",
  "timestamp": "2026-08-13T01:51:41Z",
  "endpoints": {
    "health": "GET /health",
    "stocks": "GET /stocks/{ticker}",
    "stocks_search": "GET /stocks/search",
    "stocks_batch": "POST /stocks/batch",
    "stocks_export": "POST /stocks/export",
    "stocks_import": "POST /stocks/import"
  }
}
```

### Health Check Endpoints (API)

### GET /api/v1/health/

General health status.

### GET /api/v1/health/services

Detailed health status for all registered services.

### GET /api/v1/health/services/{service_name}

Health status for a specific service.

**Response:**
```json
{
  "status": "success",
  "service": "stock_service",
  "health": {
    "status": "healthy",
    "timestamp": "2026-08-13T01:51:41Z"
  }
}
```

## Stock Data Routes (v1)

### GET /api/v1/stocks/{ticker}

Retrieve stock information by ticker symbol.

**Parameters:**
- `ticker` (required) - Stock symbol (e.g., "AAPL", "BTC", "XRP")
- `api_version` (optional) - API version (default: "v1")

**Response:**
```json
{
  "status": "success",
  "ticker": "AAPL",
  "data": {
    "symbol": "AAPL",
    "price": 123.45,
    "volume": 1000000,
    "change": 1.23,
    "timestamp": "2026-08-13T01:51:41Z"
  },
  "api_version": "v1"
}
```

### GET /api/v1/stocks/search

Search stocks by query string.

**Query Parameters:**
- `q` (required) - Search query (min 1 character)
- `limit` (optional) - Maximum results (1-100)
- `api_version` (optional) - API version (default: "v1")

**Response:**
```json
{
  "status": "success",
  "query": "AAPL",
  "count": 1,
  "data": [
    {
      "ticker": "AAPL",
      "price": 123.45,
      "volume": 1000000,
      "timestamp": "2026-08-13T01:51:41Z"
    }
  ]
}
```

### POST /api/v1/stocks/batch

Batch export of stock data in JSON or CSV format.

**Request Body:**
```json
{
  "tickers": ["AAPL", "GOOGL", "TSLA"]
}
```

**Response:**
```json
{
  "status": "success",
  "total": 3,
  "successful": 3,
  "failed": 0,
  "data": [...]
}
```

### POST /api/v1/stocks/export

Export portfolio data in JSON or CSV format.

**Request Body:**
```json
{
  "tickers": ["AAPL", "GOOGL"],
  "format": "json",
  "api_version": "v1"
}
```

**Response:**
```json
{
  "status": "success",
  "export_timestamp": "2026-08-13T01:51:41Z",
  "total_records": 2,
  "successful_exports": 2,
  "format": "json",
  "data": [...]
}
```

### POST /api/v1/stocks/import

Import portfolio data from JSON or CSV format.

**Request Body:**
```json
{
  "file": "portfolio_data.json",
  "api_version": "v1"
}
```

**Response:**
```json
{
  "status": "success",
  "imported_count": 5,
  "imported_tickers": ["AAPL", "GOOGL"],
  "errors": []
}
```

## Stock Data Routes (v2)

### POST /api/v1/stocks/v2/batch

Batch export with historical data inclusion.

**Query Parameters:**
- `include_history` (optional) - Include historical data (default: false)

**Request Body:**
```json
{
  "tickers": ["AAPL", "GOOGL"],
  "include_history": true
}
```

**Response:**
```json
{
  "status": "success",
  "total_records": 3,
  "successful_exports": 3,
  "format": "json",
  "data": [...]
}
```

## API Versioning

All endpoints support versioning:
- **v1** - Initial release (default)
- **v2** - Enhanced endpoints with improved features

**Headers:**
- `X-API-Version` - Current API version (default: "v1")
- `X-API-Version-Deprecated` - Indicates if v2 is deprecated (always "false")

## Error Responses

Common error codes:
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (missing/invalid authentication)
- `404` - Resource not found
- `500` - Internal Server Error
- `503` - Service Unavailable (maintenance)

## Rate Limiting

All endpoints are protected by rate limiting:
- **Default:** 100 requests/minute per IP
- **Health checks:** Unlimited
- **Production:** 1000 requests/minute per API key

**Rate Limit Headers:**
- `X-Rate-Limit-Remaining` - Remaining requests in current window
- `X-Rate-Limit-Reset` - Unix timestamp when limit resets
- `X-Rate-Limit-Window` - Current window start time

## Monitoring

Health check endpoints provide:
- Overall service status
- Per-service status
- Timestamp of last check
- Total uptime
- Number of active services

## Performance Optimizations

### Caching
- LRU caching for frequently used calculations
- Cache size limits to prevent memory overflow
- Automatic cache eviction (LRU strategy)

### Batch Processing
- Concurrent data fetching
- Lazy loading of services
- Batch operations for multiple symbols

### Lazy Loading
- Services instantiated only when needed
- Providers registered on-demand

## Support

For API-related issues:
- Open a ticket in the project tracker
- Contact support@bedaanwaves.dev
- Refer to the API documentation at `/docs`
