# DFD Level 4 — Analysis & ML Flow

Data flow between PriceCandle/Asset and the analysis/ML services, then MLSignal.

## Diagram (Mermaid)
```mermaid
flowchart TD
  FE[Frontend] --> A1[GET /analysis/technical/{symbol}]
  FE --> A2[GET /analysis/volatility/{symbol}]
  FE --> A3[GET /analysis/momentum/{symbol}]
  FE --> A4[GET /analysis/risk/{symbol}]
  FE --> A5[POST /analysis/scoring]
  FE --> A6[GET /analysis/signals/{symbol}]

  subgraph DB[(PostgreSQL)]
    AS[Asset]
    PC[PriceCandle (daily)]
    SIG[MLSignal]
  end

  A1 --> AS
  A1 --> PC
  A2 --> AS
  A2 --> PC
  A3 --> AS
  A3 --> PC
  A4 --> AS
  A4 --> PC

  A5 --> TECH[ScoringService (6D)]
  TECH --> AS
  TECH --> PC
  TECH --> SIG

  A6 --> AS
  A6 --> SIG

  TECH --> RESP1[Indicators/Scoring output]
  A1 --> RESP1
  A2 --> RESP1
  A3 --> RESP1
  A4 --> RESP1

  SIG --> A6
  A6 --> FE
```

## Data Flows
- Analysis inputs:
  - `Asset` by `symbol`
  - `PriceCandle` with timeframe `1d` and a specified time range
- Outputs:
  - dict/metrics for technical/momentum/volatility/risk
  - scoring + hierarchy info
  - active and valid `MLSignal` (valid_until >= now)