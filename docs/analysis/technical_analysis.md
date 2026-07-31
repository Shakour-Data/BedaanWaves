# Technical Analysis in BedaanWaves Scoring System

## Overview
Technical analysis evaluates securities based on historical price and volume patterns. This dimension contributes 20% to the overall 6D score and focuses on market behavior and momentum indicators.

**Important**: The coefficient/weight of each dimension, sub-dimension, aspect, and sub-aspect is dynamically determined through machine learning models and is **not static**. The CoefficientLearningService continuously optimizes these weights based on backtest performance, regime changes, and evolving market conditions.

## Hierarchical Structure
- **Level 1**: Technical (20% weight)
- **Level 2**: Moving averages, Momentum indicators, Volatility metrics, Volume patterns, Trend analysis
- **Level 3**: 50+ technical indicators including RSI, MACD, SMA, EMA, Bollinger Bands, ADX
- **Level 4**: Specific patterns, candlestick formations, volume analysis, momentum oscillators

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

This dimension helps identify optimal timing for trades, complementing fundamental analysis for comprehensive investment decisions.