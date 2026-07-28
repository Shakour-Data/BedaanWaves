# BPMN Level 1 — Processes Overview

این سطح نمای کلی فرآیندهای اصلی سیستم را نشان می‌دهد.

## فرآیندها
- **Authentication**: Register / Login / Refresh (Public)
- **Market Data Access**: Symbols / Price History / Latest Prices
- **Live Data Proxy**: Proxy endpoints به BRS API
- **Analysis Pipeline**: Technical / Momentum / Volatility / Risk / Scoring / Signals
- **ML Inference**: Predict / Patterns / Anomaly / Recommendation / Forecast / Optimize
- **Portfolio Management**: Create portfolio / Manage holdings
- **Notifications**: List / Mark read / Mark all read / Delete
- **System Operations**: Scheduler / Queue / Metrics

## Diagram (Mermaid flowchart-style)
```mermaid
flowchart TD
  U[User / Frontend] -->|Auth| AUTH[API /auth]
  U -->|Market| MK[API /market]
  U -->|Live| LIVE[API /market/live]
  U -->|Analysis| AN[API /analysis]
  U -->|ML| ML[API /ml]
  U -->|Portfolio| PO[API /portfolios]
  U -->|Notifications| NOTIF[API /notifications]
  U -->|System| SYS[API /system]

  AUTH --> DB[(PostgreSQL users)]
  MK --> DB
  LIVE --> BRS[BRS API brsapi.ir]
  AN --> DB
  ML --> DB
  PO --> DB
  NOTIF --> DB
  SYS --> QUEUE[Queue/Scheduler]
  SYS --> METR[Metrics]

  QUEUE --> DB
  METR --> DB
  %% Business processes summarized
```

## داده‌ها/ایونت‌های کلیدی
- JWT Access/Refresh
- Asset / PriceCandle / MLSignal
- Portfolio / Position
- Notification
- Job (queue)

