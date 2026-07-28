# BPMN Level 5 — Portfolio Management Process

این سطح فرآیندهای پورتفولیو/هولدینگ را مطابق routeهای فعلی نشان می‌دهد:
- `POST /portfolios/` (create)
- `GET /portfolios/` / `GET /portfolios/{id}`
- `PUT /portfolios/{id}`
- `DELETE /portfolios/{id}`
- `POST /portfolios/{id}/holdings`
- `GET /portfolios/{id}/holdings`
- `DELETE /portfolios/{id}/holdings/{holding_id}`

## Diagram (Mermaid)
```mermaid
flowchart TD
  FE[Frontend] --> C1[POST /api/v1/portfolios/]
  C1 --> AUTH[AuthGuard + get_route_user_id]
  AUTH --> DBP[(DB: portfolios)]

  DBP --> C1
  C1 --> FE

  FE --> A1[GET /api/v1/portfolios]
  A1 --> AUTH
  A1 --> DBP
  DBP --> A1
  A1 --> FE

  FE --> UPD[PUT /api/v1/portfolios/{portfolio_id}]
  UPD --> DBP
  UPD --> FE

  FE --> ADDH[POST /api/v1/portfolios/{portfolio_id}/holdings]
  ADDH --> AUTH
  ADDH --> DBA[(DB: Asset)]
  ADDH --> DBPos[(DB: positions)]

  DBPos --> ADDH
  %% duplicate check
  subgraph check[Check Duplicate Position]
    ADDH --> CHK[find(Position where portfolio_id & asset_id)]
    CHK -->|exists| E400[400 Holding already exists]
    CHK -->|not exists| INS[insert Position]
  end

  INS --> DBPos
  E400 --> FE

  FE --> LISTH[GET /portfolios/{portfolio_id}/holdings]
  LISTH --> DBPos
  DBPos --> LISTH --> FE

  FE --> DELH[DELETE /holdings/{holding_id}]
  DELH --> DBPos
  DELH --> FE
```

## داده‌ها/ایونت‌ها
- `PortfolioCreate/PortfolioUpdate`
- `PositionCreate/PositionResponse`
- کنترل خطا: پرتاب `404 Portfolio not found` یا `400 Holding already exists`

