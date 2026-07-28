# DFD Level 3 — Market Data Flow (DB-backed & Live Proxy)

این سطح جریان داده‌های بازار را در دو مسیر نشان می‌دهد:
1) DB-backed endpoints (`/market/*`)
2) Live proxy endpoints (`/market/live/*`)

## Diagram (Mermaid)
```mermaid
flowchart TD
  FE[Frontend] -->|GET /market/symbols
(GET /market/price-history)
(GET /market/latest-prices)
| MK[Market Router]

  MK -->|SQL queries| DB[(PostgreSQL)]
  DB -->|Asset + PriceCandle| MK
  MK --> FE

  FE -->|GET /market/live/*| L[Market Live Router]
  L -->|HTTP upstream calls| BRS[BRS API]
  BRS -->|upstream JSON| L
  L --> FE

  %% Internal normalization notes
  MK --> N1[Response normalization]
  L --> N2[pass-through upstream payload]
```

## Data Flows (DB-backed)
- `Asset` خوانده می‌شود:
  - فیلترها: `asset_class`, `market`, `sector`, `industry`, `active`
- `PriceCandle` خوانده می‌شود:
  - `timeframe` و بازه `timestamp`
  - مرتب‌سازی و limit

## Data Flows (Live Proxy)
- `BrsApiClient` به BRS API درخواست می‌زند:
  - AllSymbols / Symbol / Candlestick / History / Transaction / Shareholder / Index / Codal ...
- خروجی بدون پردازش سنگین (تقریباً pass-through) به کلاینت برمی‌گردد.

