# BPMN Level 3 — Market Ingest Process (Symbols/History/Live Proxy)

This level shows the process for accessing/fetching market data.

## Scope
- `GET /market/symbols` (from DB)
- `GET /market/price-history` (from DB)
- `GET /market/latest-prices` (from DB)
- `GET /market/live/*` (proxy to Yahoo Finance API)

## Diagram (Mermaid)
```mermaid
flowchart TD
  FE[Frontend / Client] --> R1[GET /api/v1/market/symbols]
  FE --> R2[GET /api/v1/market/price-history]
  FE --> R3[GET /api/v1/market/latest-prices]
  FE --> R4[GET /api/v1/market/live/history/{l18}]

  subgraph DBFlow[DB-backed Market Flow]
    R1 --> MKT1[market router
/market/symbols]
    R2 --> MKT2[market router
/price-history]
    R3 --> MKT3[market router
/latest-prices]

    MKT1 --> DB[(PostgreSQL Asset)]
    MKT2 --> DB
    MKT3 --> DB

    DB --> MKT1
    DB --> MKT2
    DB --> MKT3
  end

  subgraph LiveFlow[Live Proxy Flow]
    R4 --> LIVE1[market/live router
/history/{l18}]
    LIVE1 --> YF[Yahoo Finance API
    YF --> LIVE1
   end

  MKT1 --> RESP1[200 Response]
  MKT2 --> RESP2[200 Response]
  MKT3 --> RESP3[200 Response]
  LIVE1 --> RESP4[200 Upstream JSON]
```

## Data / Events
- **Request**: filter parameters (asset_class, market, sector, timeframe, start/end)
- **DB Entities**:
  - Asset
  - PriceCandle
- **Upstream Entities** (Live): JSON output of Yahoo Finance API