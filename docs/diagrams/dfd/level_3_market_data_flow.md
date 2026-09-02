# DFD Level 3 — Market Data Flow (DB-backed & Live Proxy)

This level shows the market data flows across two paths:
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
- `Asset` is read with:
  - filters: `asset_class`, `market`, `sector`, `industry`, `active`
- `PriceCandle` is read with:
  - `timeframe` and a `timestamp` range
  - sorting and limit

## Data Flows (Live Proxy)
- `BrsApiClient` calls BRS API for:
  - AllSymbols / Symbol / Candlestick / History / Transaction / Shareholder / Index / Codal ...
- The output is returned to the client with minimal processing (almost pass-through).