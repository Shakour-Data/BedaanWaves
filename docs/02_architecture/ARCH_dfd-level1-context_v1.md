# DFD Level 1 — Context Diagram

Overview of Data Flows at the Context level.

## Diagram (Mermaid)
```mermaid
flowchart LR
  U[User / Frontend] -->|HTTP/WebSocket requests| BE[Backend API (FastAPI)]
  BE -->|Responses / JSON| U

  BE -->|Read/Write SQL| DB[(PostgreSQL)]
  DB -->|Query Results| BE

  BE -->|Upstream data fetch| YF[Yahoo Finance API]
  YF -->|Upstream JSON payload| BE
```

## Data Flows
- Client → Backend: request path `/api/v1/*`, query params, JWT header
- Backend → PostgreSQL: SQL queries for Asset/PriceCandle/MLSignal/Portfolio/Position/Notification
- Backend → Yahoo Finance API: live proxy calls
- Backend → Client: response objects (symbols, candles, indicators, signals, holdings, notifications)

