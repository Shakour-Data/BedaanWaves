# BedaanWaves - ML Services Documentation

## Overview
BedaanWaves Machine Learning Services provide advanced analytics, price prediction, pattern recognition, and anomaly detection across multiple asset classes including stocks and traditional markets.

## ML Service Tiers

### 1. PredictionService
- **Purpose**: Price prediction models using ARIMA, LSTM, and Prophet
- **Features**: Multi-horizon forecasting (1min to 30d)
- **Models**: Time-series forecasting with confidence intervals
- **Endpoints**: `/api/v1/ml/predictions`

### 2. PatternRecognitionService
- **Purpose**: Chart pattern detection (head-shoulders, double tops/bottoms, triangles)
- **Patterns**: 30+ candlestick patterns with success rates
- **Features**: Real-time pattern scanning across all timeframes
- **Endpoints**: `/api/v1/ml/patterns`

### 3. AnomalyDetectionService
- **Purpose**: Outlier detection in market data and trading signals
- **Algorithms**: Isolation Forest, Local Outlier Factor, DBSCAN
- **Features**: Real-time anomaly scoring and alerting
- **Endpoints**: `/api/v1/ml/anomalies`

### 4. RecommendationService
- **Purpose**: Stock recommendations based on multi-factor scoring
- **Scoring**: 6D scoring system (fundamental, technical, sentiment, risk, macro, AI)
- **Features**: User-preference filtering and risk adjustment
- **Endpoints**: `/api/v1/ml/recommendations`

### 5. PortfolioOptimizationService
- **Purpose**: Efficient frontier optimization and portfolio rebalancing
- **Assets**: Multi-asset support (stocks, ETFs)
- **Constraints**: Risk limits, sector caps, concentration limits
- **Endpoints**: `/api/v1/portfolio/optimization`

### 6. TimeSeriesForecastingService
- **Purpose**: ARIMA, LSTM, and Prophet models for various forecasting horizons
- **Features**: Automated model selection and backtesting
- **Endpoints**: `/api/v1/ml/forecasting`

### 7. CoefficientLearningService
- **Purpose**: Dynamic coefficient learning and model weight optimization
- **Features**: Adaptive weighting based on market regimes
- **Endpoints**: `/api/v1/ml/coefficients`

### 8. TimeSeriesForecastingService
- **Probabilistic**: Bayesian ensembles, Quantile regression

## Configuration
- Model retraining intervals (default: 7 days)
- Lookback periods (default: 252 trading days)
- Confidence thresholds (default: 0.65)
- Feature normalization (default: zscore)

## Integration Points
- Connected to DataIngestionService for real-time data
- Consumes signals from ScoringService
- Outputs to NotificationService for alerts
- Metrics published to MonitoringService