# BPMN Level 4 — Analysis / Scoring / Signal Generation Process

This level shows the signal generation process based on the analysis routes:
- `/analysis/technical/{symbol}`
- `/analysis/momentum/{symbol}`
- `/analysis/volatility/{symbol}`
- `/analysis/risk/{symbol}`
- `/analysis/scoring` (6D scoring)
- `/analysis/signals/{symbol}` (reads the latest active MLSignal from the DB)

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

## Data / Events
- Inputs: list of prices/returns from `PriceCandle` (timeframe='1d')
- Outputs:
  - indicators/momentum/volatility/risk dict
  - scoring results + hierarchy
  - `MLSignal` from the `ml_signals` table (active + valid_until)