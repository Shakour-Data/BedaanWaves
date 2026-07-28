# BPMN Level 4 — Analysis / Scoring / Signal Generation Process

این سطح فرآیند تولید سیگنال‌ها را با توجه به routeهای تحلیل نشان می‌دهد:
- `/analysis/technical/{symbol}`
- `/analysis/momentum/{symbol}`
- `/analysis/volatility/{symbol}`
- `/analysis/risk/{symbol}`
- `/analysis/scoring` (6D scoring)
- `/analysis/signals/{symbol}` (خواندن latest active MLSignal از DB)

## Diagram (Mermaid)
```mermaid
flowchart TD
  FE[Frontend / Client] --> T1[GET /analysis/technical/{symbol}]
  FE --> M1[GET /analysis/momentum/{symbol}]
  FE --> V1[GET /analysis/volatility/{symbol}]
  FE --> R1[GET /analysis/risk/{symbol}]
  FE --> S1[POST /analysis/scoring]

  subgraph Indicators[Indicator Computation]
    T1 --> TECH[TechnicalAnalysisService]
    M1 --> MOM[MomentumService]
    V1 --> VOL[VolatilityService]
    R1 --> RISK[RiskAnalysisService]
  end

  TECH --> DB[(PostgreSQL
PriceCandles/Indicators input)]
  MOM --> DB
  VOL --> DB
  RISK --> DB

  S1 --> SCORE[ScoringService (6D weights)]
  SCORE --> DB
  SCORE --> SCOREH[Hierarchy info]

  FE --> SIGRD[GET /analysis/signals/{symbol}]
  SIGRD --> DBSIG[(PostgreSQL MLSignals)]
  DBSIG --> SIGRD

  SIGRD --> FE

  %% Conceptual
  SCOREH --> FE
```

## داده‌ها/ایونت‌ها
- ورودی‌ها: لیست قیمت‌ها/بازده‌ها از `PriceCandle` (timeframe='1d')
- خروجی‌ها:
  - indicators/momentum/volatility/risk dict
  - scoring results + hierarchy
  - `MLSignal` از جدول `ml_signals` (active + valid_until)

