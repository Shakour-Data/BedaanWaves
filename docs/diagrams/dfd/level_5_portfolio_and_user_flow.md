# DFD Level 5 — Portfolio, Positions & Notifications Flow

این سطح جریان داده‌ها برای:
- Portfolio CRUD
- Position (holding) مدیریت
- Notification نمایش و تغییر وضعیت

را نشان می‌دهد.

## Diagram (Mermaid)
```mermaid
flowchart TD
  FE[Frontend] --> P1[POST /portfolios]
  FE --> P2[GET /portfolios]
  FE --> P3[PUT /portfolios/{id}]
  FE --> P4[POST /portfolios/{id}/holdings]
  FE --> P5[GET /portfolios/{id}/holdings]
  FE --> P6[DELETE /portfolios/{id}/holdings/{holding_id}]

  FE --> N1[GET /notifications]
  FE --> N2[POST /notifications/{id}/read]
  FE --> N3[POST /notifications/read-all]
  FE --> N4[DELETE /notifications/{id}]

  subgraph Auth[Auth & User Context]
    FE --> G[AuthGuardMiddleware]
    G --> UID[get_route_user_id]
  end

  P1 --> UID
  P2 --> UID
  P3 --> UID
  P4 --> UID
  P5 --> UID
  P6 --> UID

  N1 --> UID
  N2 --> UID
  N3 --> UID
  N4 --> UID

  subgraph DB[(PostgreSQL)]
    DBP[portfolios]
    DBS[positions]
    DBA[assets]
    DBN[notifications]
    DBU[users]
  end

  UID --> DBU
  P1 --> DBP
  P4 --> DBS
  P4 --> DBA
  P5 --> DBS
  N1 --> DBN
  N2 --> DBN
  N3 --> DBN
  N4 --> DBN
```

## Data Flows
- Portfolio ops: داده‌های `Portfolio`
- Holdings: داده‌های `Position` و ارجاع به `Asset`
- Notifications: داده‌های `Notification` با scope بر اساس `user_id`

