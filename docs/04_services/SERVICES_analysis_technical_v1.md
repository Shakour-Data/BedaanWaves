# Technical Analysis in BedaanWaves Scoring System

## Overview
Technical analysis evaluates securities based on historical price and volume patterns. This dimension contributes 20% to the overall 6D score and focuses on market behavior and momentum indicators.

**Important**: The coefficient/weight of each dimension, sub-dimension, aspect, and sub-aspect is dynamically determined through machine learning models and is **not static**. The CoefficientLearningService continuously optimizes these weights based on backtest performance, regime changes, and evolving market conditions.

## Hierarchical Structure
| Level | Description |
|-------|-------------|
| **Level 1** | Technical (20% weight) |
| **Level 2** | Moving Averages, Momentum Indicators, Volatility Metrics, Volume Patterns, Trend Analysis |
| **Level 3** | RSI/MACD (Momentum), Bollinger Bands/ATR (Volatility), OBV/CMF (Volume) |
| **Level 4** | Cross-timeframe validation, indicator divergences, signal confluence scoring |

---

## Detailed Sub-Dimensions, Aspects & Sub-Aspects

### Level 2: Moving Averages
**Aspect 1: Simple Moving Averages (SMA)**
- Sub-Aspect: SMA-20 (short-term trend)
- Sub-Aspect: SMA-50 (medium-term trend)
- Sub-Aspect: SMA-200 (long-term trend)

**Aspect 2: Exponential Moving Averages (EMA)**
- Sub-Aspect: EMA-12 (fast)
- Sub-Aspect: EMA-26 (slow)
- Sub-Aspect: EMA-50 (medium-term)

**Aspect 3: Weighted Moving Averages (WMA)**
- Sub-Aspect: Linear WMA
- Sub-Aspect: Volume-Weighted WMA

### Level 2: Momentum Indicators
**Aspect 1: Relative Strength Index (RSI)**
- Sub-Aspect: RSI-14 (overbought/oversold)
- Sub-Aspect: RSI-25 (short-term momentum)
- Sub-Aspect: RSI D divergence (signal confirmation)

**Aspect 2: Moving Average Convergence Divergence (MACD)**
- Sub-Aspect: MACD Line
- Sub-Aspect: Signal Line
- Sub-Aspect: MACD Histogram

**Aspect 3: Stochastic Oscillator**
- Sub-Aspect: %K Line
- Sub-Aspect: %D Line
- Sub-Aspect: Stochastic RSI (for overbought/oversold confirmation)

**Aspect 4: Commodity Channel Index (CCI)**
- Sub-Aspect: CCI-20 (primary)
- Sub-Aspect: CCI-10 (short-term)

### Level 2: Volatility Metrics
**Aspect 1: Bollinger Bands**
- Sub-Aspect: Upper Band (2σ)
- Sub-Aspect: Middle Band (SMA-20)
- Sub-Aspect: Lower Band (2σ)
- Sub-Aspect: BB Width (volatility indicator)

**Aspect 2: Average True Range (ATR)**
- Sub-Aspect: ATR-14 (volatility measure)
- Sub-Aspect: ATR-50 (long-term volatility)
- Sub-Aspect: Normalized ATR (ATR/price)

**Aspect 3: Keltner Channels**
- Sub-Aspect: Upper Channel (ATR×2)
- Sub-Aspect: Lower Channel (ATR×2)
- Sub-Aspect: Channel Width

### Level 2: Volume Patterns
**Aspect 1: On-Balance Volume (OBV)**
- Sub-Aspect: Cumulative Volume Flow
- Sub-Aspect: OBV Trend Confirmation

**Aspect 2: Accumulation/Distribution Line (A/D)**
- Sub-Aspect: Money Flow Multiplier
- Sub-Aspect: Volume-Weighted Money Flow

**Aspect 3: Chaikin Money Flow (CMF)**
- Sub-Aspect: CMF-20 (volume-weighted money flow)
- Sub-Aspect: CMF-50 (longer-term volume trend)

### Level 2: Trend Analysis
**Aspect 1: ADX (Average Directional Index)**
- Sub-Aspect: ADX-14 (trend strength)
- Sub-Aspect: +DI / -DI (trend direction)
- Sub-Aspect: ADX>25 (strong trend confirmation)

**Aspect 2: Parabolic SAR**
- Sub-Aspect: SAR Reversal Points
- Sub-Aspect: SAR Acceleration Factor (AF)

**Aspect 3: Ichimoku Cloud**
- Sub-Aspect: Tenkan-sen (conversion line)
- Sub-Aspect: Kijun-sen (base line)
- Sub-Aspect: Chikou Span (lagging line)
- Sub-Aspect: Kumo (cloud support/resistance)

## Data Sources
- Historical price data (OHLC - Open, High, Low, Close)
- Volume data (trading volume, institutional activity)
- Market breadth Indicators
- Technical indicator calculations
- Pattern recognition signals
- Market sentiment Indicators

## Key Metrics Analyzed

### Momentum Indicators
- **RSI (Relative Strength Index)**: Measures relative overbought/oversold conditions
- **MACD (Moving Average Convergence Divergence)**: Trend momentum and strength
- **Stochastic Oscillator**: Momentum relative to recent range
- **Williams %R**: Overbought/oversold indicator similar to RSI
- **Awesome Oscillator**: Bullish/bearish momentum visual

### Trend Indicators
- **Moving Averages**:
  - Simple Moving Average (SMA)
  - Exponential Moving Average (EMA)
  - Weighted Moving Average (WMA)
- **Trend Lines**: Support and resistance trend identification
- **Moving Average Ribbons**: Multiple moving averages for trend strength

### Volatility Indicators
- **Bollinger Bands**: Price volatility bands
- **ATR (Average True Range)**: Market volatility measurement
- **Keltner Channels**: Volatility-based price channels
- **Volatility Cone**: Statistical volatility analysis

### Volume Analysis
- **Volume Confirmation**: Price movements validated by volume
- **Accumulation/Distribution Line**: Institutional buying/selling pressure
- **Volume Profile**: Price levels with highest trading volume
- **On-Balance Volume (OBV)**: Cumulative volume flow

### Pattern Recognition
- **Candlestick Patterns**: Doji, Hammer, Engulfing, Shooting Star
- **Chart Patterns**: Head & Shoulders, Double Top/Bottom, Triangles
- **Continuation Patterns**: Flags, Pennants, Rectangles
- **Breakout Patterns**: Cup & Handle, Rounding Bottom

### Market Breadth Indicators
- **Advance/Decline Line**: Market participation metrics
- **TRIN (Trading Index)**: Market breadth measure
- **New Highs/Lows**: Market momentum breadth
- **McClellan Oscillator**: Market sentiment measurement

## Analysis Process
1. **Price Data Collection**: Gather high-quality OHLCV data
2. **Indicator Computation**: Calculate all technical indicators
3. **Pattern Detection**: Identify chart patterns and formations
4. **Signal Generation**: Generate buy/sell/hold signals from indicators
5. **Cross-Timeframe Validation**: Confirm signals across daily, weekly, monthly
6. **Score Normalization**: Convert signals to 0-100 scale
7. **Weight Application**: Apply ML-optimized weights
8. **Aggregation**: Combine with other technical sub-dimensions

## Machine Learning Integration
- Pattern recognition through convolutional neural networks
- Time series forecasting with LSTM for trend prediction
- Ensemble methods combining multiple technical strategies
- Real-time market regime detection
- Adaptive indicator weighting based on market conditions

## Output Interpretation
Technical analysis generates signals based on market momentum and patterns:
- **85-100**: Strong bullish momentum with high confidence
- **70-84**: Positive momentum with confirming indicators
- **55-69**: Mixed signals requiring careful monitoring
- **40-54**: Bearish momentum with weakening trends
- **0-39**: Strong bearish signals with high probability reversals

## BPMN Workflow Diagram

```mermaid
graph TD
    subgraph Data_Ingestion
        A1[OHLCV Market Data Feed] --> A2[Data Normalization Engine]
        A2 --> A3[Data Quality Assurance]
        A3 --> A4[Cleaned Price Data Repository]
    end

    subgraph Indicator_Computation
        A4 --> B1[SMA/EMA Calculation Engine]
        B1 --> B2[Momentum Indicator Engine (RSI/MACD/CCI)]
        B2 --> B3[Volatility Calculation Engine (Bollinger/ATR)]
        B3 --> B4[Volume Analysis Engine (OBV/CMF)]
        B4 --> B5[Pattern Recognition Engine]
        B5 --> B6[Computed Indicators Database]
    end

    subgraph Pattern_Recognition
        B6 --> C1[CNN-Based Pattern Detector]
        C1 --> C2[Candlestick Pattern Classifier]
        C2 --> C3[Chart Pattern Detector (Head & Shoulders, Triangles)]
        C3 --> C4[Pattern Signals Database]
        C4 --> C5[Signal Scoring Engine]
    end

    subgraph ML_Integration
        C5 --> D1[Signal Scoring Engine]
        D1 --> D2[CoefficientLearningService (Dynamic Weights)]
        D2 --> D3[Score Normalization (0-100)]
    end

    subgraph Output_Generation
        D3 --> E1[Technical Score (20% weight)]
        D3 --> E2[Sub-Dimension Scores]
        D3 --> E3[Aspect-Level Scores]
        E1 --> F[6D Composite Score Aggregation]
        E2 --> F
        E3 --> F
    end

    subgraph Monitoring_Feedback
        F --> G[Backtest Performance Tracker]
        G --> H[Model Drift Monitor]
        H --> I[Retraining Trigger]
        I --> C1
    end

    style A1 fill:#e1f5fe
    style B5 fill:#e8f5e9
    style C1 fill:#fff3e0
    style D2 fill:#fce4ec
    style F fill:#e0f2f1
    style G fill:#f3e5f5
```

## Data Flow Diagram (DFD)

```mermaid
graph LR
    subgraph External_Sources
        ES1[Market Data Vendors]
        ES2[Real-time Price Feeds]
        ES3[Historical Archives]
        ES4[Trading Volume Data]
    end

    subgraph Data_Ingestion_Layer
        IL1[API Connectors]
        IL2[Data Lake]
        IL3[Real-time Queue (Kafka)]
    end

    subgraph Processing_Layer
        PL1[Indicator Calculation Engine]
        PL2[Pattern Recognition Engine (CNN)]
        PL3[Signal Scoring Engine]
        PL4[Time Series Models (LSTM)]
    end

    subgraph Scoring_Layer
        SL1[Technical Scoring Service]
        SL2[Coefficient Learning Service]
        SL3[Score Aggregation Service]
    end

    subgraph API_Layer
        AL1[FastAPI Endpoints]
        AL2[GraphQL Gateway]
        AL3[WebSocket Real-time Feed]
    end

    subgraph Consumers
        C1[Frontend Dashboard]
        C2[Alerting Engine]
        C3[Trading Signals Interface]
    end

    ES1 --> IL1
    ES2 --> IL1
    ES3 --> IL1
    ES4 --> IL1
    IL1 --> IL2
    IL2 --> IL3
    IL3 --> PL1
    PL1 --> PL2
    PL2 --> PL3
    PL3 --> PL4
    PL4 --> SL1
    SL1 --> SL2
    SL2 --> SL3
    SL3 --> AL1
    SL3 --> AL2
    SL3 --> AL3
    AL1 --> C1
    AL2 --> C2
    AL3 --> C3
```

## UML Class Diagram (Technical Analysis)

```mermaid
classdiagram
    class TechnicalIndicator {
        +String name
        +IndicatorType type
        +Integer period
        +Double[] values
        +Double signalStrength
        +calculate(MarketData): Double[]
        +normalize(): Double
    }

    class PriceHistoryData {
        +Instrument instrument
        +LocalDate date
        +BigDecimal open
        +BigDecimal high
        +BigDecimal low
        +BigDecimal close
        +Long volume
        +normalize(): PriceHistoryData
    }

    class PatternRecognitionEngine {
        +List~Pattern~ detect(PriceHistoryData): List
        +double score(Pattern): Double
        +List~Signal~ generateSignals(List~Pattern~): List
    }

    class TechnicalScorer {
        +CoefficientLearningService coeffService
        +score(TechnicalFeatures): TechnicalScore
        +scoreSubDimensions(TechnicalFeatures): Map~SubDimension, Double~
    }

    class TechnicalScore {
        +Double overallScore
        +Map~SubDimension, Double~ subDimensionScores
        +Map~Aspect, Double~ aspectScores
        +LocalDateTime timestamp
        +ModelVersion version
    }

    class SubDimension {
        <<enumeration>>
        MOVING_AVERAGES
        MOMENTUM_INDICATORS
        VOLATILITY_METRICS
        VOLUME_PATTERNS
        TREND_ANALYSIS
    }

    PriceHistoryData --> TechnicalIndicator
    TechnicalIndicator --> PatternRecognitionEngine
    PatternRecognitionEngine --> TechnicalScorer
    TechnicalScorer --> CoefficientLearningService
    TechnicalScorer --> TechnicalScore
    TechnicalScore --> SubDimension
```

## Integration with Other Dimensions
This dimension helps identify optimal timing for trades, complementing fundamental analysis for comprehensive investment decisions.