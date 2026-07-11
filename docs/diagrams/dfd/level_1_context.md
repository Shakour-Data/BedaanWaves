# DFD Level 1 — Context Diagram

نمای کلی جریان داده‌ها (Data Flows) در سطح Context.

## Diagram (Mermaid)
```mermaid
flowchart LR
  U[User / Frontend] -->|HTTP/WebSocket requests| BE[Backend API (FastAPI)]
  BE -->|Responses / JSON| U

  BE -->|Read/Write SQL| DB[(PostgreSQL)]
  DB -->|Query Results| BE

  BE -->|Upstream data fetch| BRS[BRS API (brsapi.ir)]
  BRS -->|Upstream JSON payload| BE
```

## Data Flows
- Client → Backend: request path `/api/v1/*`, query params, JWT header
- Backend → PostgreSQL: SQL queries for Asset/PriceCandle/MLSignal/Portfolio/Position/Notification
- Backend → BRS API: live proxy calls (AllSymbols/Symbol/Candlestick/History/Transaction/Codal)
- Backend → Client: response objects (symbols, candles, indicators, signals, holdings, notifications)

