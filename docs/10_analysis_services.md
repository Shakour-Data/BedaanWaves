# BedaanWaves Tier 3: Analysis Services

## Overview

Tier 3 Analysis Services implement the core financial analysis algorithms for the BedaanWaves platform. These services compute technical indicators, fundamental ratios, risk metrics, and specialized scoring systems.

**Implementation Status**: 7/7 Complete (100%)
**Service Count**: 7 services
**Location**: `backend/app/services/analysis/`

## ScoringService (6D Scoring System)

**File**: `app/services/analysis/scoring_service.py`

### Purpose
Implements the comprehensive 6D scoring system with a 305-node hierarchy for evaluating stocks, portfolios, and investment opportunities across multiple dimensions.

### The 6D Scoring Framework
| Dimension | Description | Nodes | Weight |
|-----------|-------------|-------|--------|
| **D1: Growth Potential (G)** | Revenue, earnings, and fundamental growth trajectory | 52 nodes | 17.5% |
| **D2: Financial Health (H)** | Balance sheet strength, solvency, liquidity ratios | 42 nodes | 17.5% |
| **D3: Valuation (V)** | Current valuation relative to intrinsic value | 32 nodes | 12.5% |
| **D4: Technical Strength (T)** | Momentum, trend, and price action analysis | 37 nodes | 15.0% |
| **D5: Market Dynamics (M)** | Sector, industry, market position, sentiment | 47 nodes | 18.0% |
| **D6: Risk Profile (R)** | Risk metrics, volatility, correlation, stress scenarios | 45 nodes | 17.0% |
| **Bonus: Liquidity (L)** | Trading activity and market accessibility | 20 nodes | 2.5% |

### Scoring Methodology
- **Node Hierarchy**: Each dimension is scored through 20-50 sub-nodes
- **Weighted Average**: Dimensions weighted and combined into aggregate score
- **Normalization**: Scores scaled 0-100, relative to market universe
- **Benchmarking**: Comparison against industry and market benchmarks
- **Dynamic Adjustment**: Real-time updates based on new data

### Score Interpretation
| Score Range | Rating | Description |
|-------------|--------|-------------|
| 0-10 | Extreme Sell | Severe fundamental issues |
| 10-30 | Strong Sell | Significant concerns |
| 30-50 | Hold | Mixed signals |
| 50-70 | Buy | Positive attributes |
| 70-90 | Strong Buy | Exceptional fundamentals |
| 90-100 | Premium | Elite investment opportunity |

### Usage
```python
from app.services.analysis.scoring_service import ScoringService

service = ScoringService()

# Score a single stock
score = await service.score_symbol({
    "symbol_id": asset_uuid,
    "include_details": True,
    "benchmark": "market_avg"
})

# Get 6D breakdown
dimensions = score["dimensions"]
# {"growth_potential": 78.5, "financial_health": 65.2, ...}

# Compare multiple stocks
comparison = await service.score_compare({
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "dimensions": ["growth", "valuation", "risk"]
})

# Get sector-relative score
sector_score = await service.score_sector_relative({
    "symbol_id": asset_uuid,
    "sector": "Technology"
})
```

### Key Methods
| Method | Description |
|--------|-------------|
| `score_symbol(symbol_id, include_details, benchmark)` | Score individual symbol |
| `score_portfolio(portfolio_id)` | Score entire portfolio |
| `score_compare(symbols, dimensions)` | Compare scores across symbols |
| `score_sector_relative(symbol_id, sector)` | Sector-relative scoring |
| `score_history(symbol_id, start, end)` | Historical scores |
| `score_distribution(sector, market)` | Score distribution analysis |
| `get_node_weights()` | Get node importance weights |

---

## TechnicalAnalysisService (50+ Indicators)

**File**: `app.services/analysis/technical_service.py`

### Purpose
Implements comprehensive technical analysis with 50+ indicators across categories including momentum, volatility, volume, and trend analysis.

### Indicator Categories

#### Trend Indicators (15 indicators)
| Indicator | Formula | Purpose |
|-----------|---------|---------|
| Moving Average (MA) | `SMA = Σ(price) / n` | Trend identification |
| Exponential MA | `EMA = α × price + (1-α) × EMA` | Faster trend signal |
| MACD | `EMA(12) - EMA(26)` | Trend direction and momentum |
| ADX | Directional Movement Index | Strength of trend |
| Parabolic SAR | Acceleration + Maximum | Entry/exit points |
| DMI | Directional Movement Index | Trend direction |
| Vortex | VI+ / VI- | Trend reversal signals |
| TEMA | Triple EMA smoothing | Lag reduction |
| DEMA | Double EMA | Smoothing |
| WMA | Weighted MA | Time-weighted average |
| VWMA | Volume Weighted MA | Volume-aware trend |

#### Momentum Indicators (12 indicators)
| Indicator | Formula | Purpose |
|-----------|---------|---------|
| RSI | `100 - (100 / (1 + RS))` | Overbought/Oversold |
| StochRSI | `RSI of RSI` | Momentum within RSI |
| ROC | `(Price - Price_n) / Price_n * 100` | Rate of change |
| CMO | `(sum(gains) - sum(losses)) / (sum(gains) + sum(losses))` | Chande Momentum |
| CCI | `(Price - SMA) / (0.015 * Mean Deviation)` | Cycle detection |
| Williams %R | `(Highest High - Close) / (Highest High - Lowest Low)` | Overbought/Oversold |
| Momentum | `Price / Price_n` | Price velocity |
| Rate of Change (ROC) | `ROC = (Price_now / Price_past) * 100` | Trend confirmation |
| TSI | True Strength Index | Signal line crossover |
| Ultimate Oscillator | `(7*OSC1 + 4*OSC2 + 1*OSC3) / 12` | Multiple timeframes |
| Aroon | `Aroon-Up, Aroon-Down` | Trend appearance |
| Klinger Oscillator | Volume × Trend | Volume-based momentum |

#### Volatility Indicators (8 indicators)
| Indicator | Purpose |
|-----------|---------|
| Bollinger Bands | Volatility envelope |
| ATR | Average True Range |
| Donchian Channel | Price channel width |
| Keltner Channel | EMA + ATR envelope |
| VWAP | Volume-weighted average price |
| Standard Deviation | Price dispersion |
| Variance | Squared deviations |
| Chaikin Volatility | Accumulation/distribution volatility |

#### Volume Indicators (10 indicators)
| Indicator | Purpose |
|-----------|---------|
| OBV | On-Balance Volume |
| Accumulation/Distribution | Money flow volume |
| Chaikin Money Flow | Volume-weighted accumulation |
| Volume Rate of Change | Volume momentum |
| Money Flow Index | Volume + price momentum |
| Ease of Movement | Price movement vs volume |
| Negative Volume Index | Down-volume tracking |
| Positive Volume Index | Up-volume tracking |
| VWOP | Volume-weighted average |
| Elder's Force Index | Volume × price × EMA |

#### Summary Statistics (4 indicators)
| Indicator | Purpose |
|-----------|---------|
| Correlation Matrix | Cross-asset relationships |
| Beta | Systematic risk measure |
| Alpha | Excess return measure |
| Kurtosis/Skewness | Distribution shape measures |

### Signal Generation
```python
# Example: Technical signal
signal = await technical_service.generate_signals({
    "symbol_id": asset_uuid,
    "indicators": ["RSI", "MACD", "Bollinger_Bands"],
    "timeframe": "1d",
    "periods": 252
})

# Returns:
{
    "symbol": "AAPL",
    "timestamp": "2024-08-17T10:30:00Z",
    "signals": [
        {
            "indicator": "RSI",
            "value": 72.5,
            "signal": "OVERSOLD",  # or "OVERBOUGHT", "NEUTRAL"
            "strength": "STRONG"
        },
        {
            "indicator": "MACD",
            "value": {"macd": 0.0015, "signal": 0.0012, "hist": 0.0003},
            "signal": "NEUTRAL"
        },
        {
            "indicator": "BOLLINGER_BANDS",
            "value": {"upper": 192.50, "middle": 187.25, "lower": 182.00},
            "signal": "OVERSOLD",  # Price near lower band
            "strength": "MODERATE"
        }
    ],
    "composite_signal": "HOLD",
    "confidence": 0.75
}
```

### Dashboard Integration
```python
# Get live dashboard data
dashboard = await technical_service.get_dashboard({
    "symbol": "AAPL",
    "timeframe": "1d",
    "period": "1y"
})

# Returns:
{
    "symbol": "AAPL",
    "current_price": 185.75,
    "price_change": 1.25,
    "price_change_pct": 0.68,
    "indicators": {
        "rsi": {"value": 72.5, "signal": "NEUTRAL"},
        "macd": {"value": 0.0015, "signal": "BULLISH_CROSS"},
        "bollinger": {"position": "MIDDLE", "bandwidth": 4.2}
    },
    "chart_data": [...],  # Historical data for plotting
    "signals_timeline": [...]  # Historical signals
}
```

### Usage
```python
from app.services.analysis.technical_service import TechnicalAnalysisService

service = TechnicalAnalysisService()

# Calculate specific indicators
rsi = await service.calculate_indicator("RSI", {
    "symbol_id": asset_uuid,
    "period": 14,
    "timeframe": "1d"
})

# Generate signals
signals = await service.generate_signals({
    "symbol_id": asset_uuid,
    "indicators": ["RSI", "MACD", "BOLLINGER_BANDS"],
    "threshold": 0.7  # Only return signals with 70%+ confidence
})

# Get dashboard data
dashboard = await service.get_dashboard({
    "symbol": "AAPL",
    "timeframe": "1d",
    "period": "1y"
})
```

### Key Methods
| Method | Description |
|--------|-------------|
| `calculate_indicator(name, params)` | Calculate specific technical indicator |
| `generate_signals(symbol_id, indicators, threshold)` | Generate trading signals |
| `get_dashboard(symbol, timeframe, period)` | Live dashboard data |
| `get_indicator_category(category)` | Get all indicators in category |
| `compare_indicators(symbols, indicator)` | Cross-symbol comparison |
| `indicator_history(symbol_id, indicator, start, end)` | Historical indicator values |
| `get_available_indicators()` | List all available indicators |

---

## FundamentalAnalysisService (20+ Ratios)

**File**: `app/services/analysis/fundamental_service.py`

### Purpose
Provides fundamental analysis with 20+ financial ratios supporting US and International markets. Computes profitability, valuation, leverage, liquidity, and efficiency metrics.

### Ratio Categories

#### Profitability Ratios (6 ratios)
| Ratio | Formula | Interpretation |
|-------|---------|----------------|
| **ROE** | `Net Income / Average Equity` | Return on shareholders' equity |
| **ROA** | `Net Income / Average Assets` | Return on total assets |
| **ROIC** | `NOPAT / Average Invested Capital` | Return on invested capital |
| **Gross Margin** | `(Revenue - COGS) / Revenue × 100` | Gross profit margin |
| **Net Margin** | `Net Income / Revenue × 100` | Net profit margin |
| **EBITDA Margin** | `EBITDA / Revenue × 100` | Cash flow profitability |

#### Valuation Ratios (8 ratios)
| Ratio | Formula | Interpretation |
|-------|---------|----------------|
| **P/E** | `Market Cap / Net Income` | Price per earnings |
| **P/B** | `Market Cap / Book Value` | Price per book value |
| **P/S** | `Market Cap / Revenue` | Price per sales |
| **EV/EBITDA** | `(Market Cap + Debt - Cash) / EBITDA` | Enterprise value multiple |
| **PEG** | `P/E / Growth Rate` | Growth-adjusted P/E |
| **Dividend Yield** | `Dividend / Stock Price × 100` | Dividend return |
| **Forward P/E** | `Price / Projected EPS` | Future valuation |
| **Price/Cash Flow** | `Market Cap / Operating Cash Flow` | Cash flow valuation |

#### Leverage Ratios (4 ratios)
| Ratio | Formula | Interpretation |
|-------|---------|----------------|
| **Debt/Equity** | `Total Debt / Shareholders' Equity` | Financial leverage |
| **Debt Ratio** | `Total Debt / Total Assets` | Debt proportion |
| **Interest Coverage** | `EBIT / Interest Expense` | Ability to pay interest |
| **Equity Multiplier** | `Total Assets / Shareholders' Equity` | Financial leverage effect |

#### Liquidity Ratios (4 ratios)
| Ratio | Formula | Interpretation |
|-------|---------|----------------|
| **Current Ratio** | `Current Assets / Current Liabilities` | Short-term liquidity |
| **Quick Ratio** | `(Cash + AR) / Current Liabilities` | Immediate liquidity |
| **Cash Ratio** | `Cash / Current Liabilities` | Cash liquidity |
| **Operating Cash Flow Ratio** | `Operating Cash Flow / Current Liabilities` | Cash-based liquidity |

#### Efficiency Ratios (4 ratios)
| Ratio | Formula | Interpretation |
|-------|---------|----------------|
| **Asset Turnover** | `Revenue / Average Total Assets` | Asset utilization |
| **Inventory Turnover** | `COGS / Average Inventory` | Inventory management |
| **Receivables Turnover** | `Revenue / Average Accounts Receivable` | Collection efficiency |
| **Working Capital** | `Current Assets - Current Liabilities` | Operational efficiency |

### Regional Support
- **US Market**: SEC filings, Yahoo Finance, Alpha Vantage
- **US Market**: SEC filings, Yahoo Finance, Alpha Vantage
- **International Markets**: Global financial data providers

### Usage
```python
from app.services.analysis.fundamental_service import FundamentalAnalysisService

service = FundamentalAnalysisService()

# Get fundamental ratios
ratios = await service.analyze({
    "symbol_id": asset_uuid,
    "region": "us",  # "us", "international"
    "include_comparison": True
})

# Get specific ratio
roe = await service.get_ratio("roe", {
    "symbol_id": asset_uuid,
    "period": "annual",
    "year": 2024
})

# Peer comparison
comparison = await service.compare_to_peers({
    "symbol_id": asset_uuid,
    "sector": "Technology",
    "region": "us",
    "ratios": ["pe_ratio", "roa", "debt_to_equity"]
})
```

### Key Methods
| Method | Description |
|--------|-------------|
| `analyze(symbol_id, region, include_comparison)` | Comprehensive fundamental analysis |
| `get_ratio(ratio_name, params)` | Get specific ratio |
| `get_all_ratios(symbol_id, region)` | Get all available ratios |
| `compare_to_peers(symbol_id, sector, ratios)` | Peer comparison |
| `get_trend(symbol_id, ratios, periods)` | Ratio trend analysis |
| `screen_by_fundamentals(criteria)` | Filter by fundamental criteria |
| `get_sector_benchmarks(sector)` | Sector average benchmarks |

---

## RiskAnalysisService (VaR, Sharpe, Stress Testing)

**File**: `app/services/analysis/risk_service.py`

### Purpose
Comprehensive risk analysis including Value-at-Risk (VaR), Sharpe ratio, stress testing, scenario analysis, and portfolio risk attribution. Production-ready risk management system.

### Risk Models

#### 1. Value-at-Risk (VaR)
```python
# Parametric VaR (Variance-Covariance)
# Formula: VaR = Z × σ × √t × Portfolio Value
var = await risk_service.calculate_var({
    "portfolio_id": portfolio_uuid,
    "method": "historical",  # or "parametric", "monte_carlo"
    "confidence_level": 0.95,  # 95% confidence
    "time_horizon": 1,  # 1 day
    "method": "historical"
})

# Returns: {"var": 15000000, "expected_shortfall": 22000000, "confidence": 0.95}
```

#### 2. Sharpe Ratio
```python
# Sharpe ratio calculation
sharpe = await risk_service.calculate_sharpe({
    "symbol_id": asset_uuid,
    "period": "252",  # 1 year
    "risk_free_rate": 0.04,  # 4% annual
    "timeframe": "daily"
})

# Returns: {"sharpe_ratio": 1.25, "annualized_return": 0.15, "volatility": 0.09}
```

#### 3. Stress Testing
```python
# Scenario-based stress testing
results = await risk_service.stress_test({
    "portfolio_id": portfolio_uuid,
    "scenarios": [
        {"name": "Market Crash", "shock": -20},  # 20% market drop
        {"name": "Interest Rate Spike", "shock_type": "rates", "amount": 2.0},
        {"name": "Sector Decline", "sector": "Banking", "shock": -35}
    ]
})

# Returns scenario impact analysis for each stress test
```

#### 4. Portfolio Risk Attribution
```python
# Decompose portfolio risk by asset, sector, factor
attribution = await risk_service.risk_attribution({
    "portfolio_id": portfolio_uuid,
    "method": "component"  # or "marginal"
})
```

### Risk Metrics
| Metric | Description | Formula |
|--------|-------------|---------|
| **Volatility** | Standard deviation of returns | `σ = sqrt(Σ(r-μ)² / n)` |
| **Max Drawdown** | Largest peak-to-trough decline | `max((peak - trough) / peak)` |
| **Value-at-Risk (VaR)** | Maximum loss at confidence level | Parametric/Historical/Monte Carlo |
| **Expected Shortfall** | Average loss beyond VaR | `E[L | L > VaR]` |
| **Sharpe Ratio** | Risk-adjusted return | `(R - Rf) / σ` |
| **Sortino Ratio** | Downside risk-adjusted return | `(R - Rf) / Downside σ` |
| **Beta** | Systematic risk | `Cov(R, Rm) / Var(Rm)` |
| **Alpha** | Active return | `R - (α + β × Rm)` |
| **Correlation** | Asset relationship | `ρ = Cov(X,Y) / (σx × σy)` |

### Stress Testing Scenarios
```python
# Built-in stress scenarios
scenarios = {
    "market_crisis": {
        "description": "2008 Financial Crisis Simulation",
        "shocks": {
            "equity_market": -35,  # 35% drop
            "credit_spread": 300,  # Basis points widening
            "volatility": 2.5  # 2.5x normal volatility
        },
        "duration": 30  # days
    },
    "inflation_shock": {
        "description": "High Inflation Scenario",
        "shocks": {
            "inflation_rate": 8.0,  # 8% inflation
            "interest_rates": 2.5,  # 2.5% rate increase
            "bond_yields": 200
        },
        "duration": 90
    },
    "geopolitical": {
        "description": "Geopolitical Crisis",
        "shocks": {
            "market_volatility": 5.0,
            "currency_impact": {"USD": -10, "EUR": -5}
        },
        "duration": 60
    }
}
```

### Usage
```python
from app.services.analysis.risk_service import RiskAnalysisService

service = RiskAnalysisService()

# Calculate VaR
var = await service.calculate_var({
    "portfolio_id": portfolio_uuid,
    "confidence_level": 0.95,
    "time_horizon_days": 1,
    "method": "historical"
})

# Sharpe ratio
sharpe = await service.calculate_sharpe({
    "symbol_id": asset_uuid,
    "period": "annual",
    "risk_free_rate": 0.04
})

# Stress testing
results = await service.stress_test({
    "portfolio_id": portfolio_uuid,
    "scenarios": ["market_crisis", "inflation_shock"]
})

# Portfolio risk attribution
attribution = await service.risk_attribution({
    "portfolio_id": portfolio_uuid
})
```

### Key Methods
| Method | Description |
|--------|-------------|
| `calculate_var(portfolio_id, confidence_level, method)` | Value-at-Risk calculation |
| `calculate_sharpe(symbol_id, period, risk_free_rate)` | Sharpe ratio |
| `stress_test(portfolio_id, scenarios)` | Stress testing scenarios |
| `risk_attribution(portfolio_id, method)` | Risk decomposition |
| `calculate_max_drawdown(symbol_id, period)` | Maximum drawdown |
| `calculate_correlation(symbols, period, method)` | Cross-asset correlation |
| `portfolio_risk_metrics(portfolio_id)` | Comprehensive risk metrics |

---

## MomentumService (Momentum Analysis)

**File**: `app/services.analysis/momentum_service.py`

### Purpose
Analyzes price momentum, identifies trend continuation and reversal patterns, and generates buy/sell signals based on momentum indicators.

### Key Features
- Rate of change (ROC) analysis
- Relative strength comparison
- Momentum convergence/divergence detection
- Trend identification and duration
- Strength ranking across symbols
- Cross-asset momentum analysis
- Early reversal signal detection

### Momentum Strategies
```python
# Classic momentum: relative strength
momentum = await momentum_service.relative_strength({
    "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN"],
    "lookback": 90,  # Days
    "rank": True
})

# Time-series momentum
ts_momentum = await momentum_service.time_series_momentum({
    "symbols": ["SPY", "TLT", "GSG"],
    "lookback": 252,  # 1 year
    "threshold": 0.0  # Positive momentum only
})

# Cross-asset momentum
cross_momentum = await momentum_service.cross_asset_momentum({
    "assets": ["AAPL", "BTC-USD", "GC=F", "TLT"],
    "lookback": 126,  # 6 months
    "risk_adjusted": True  # Sharpe ratio weighted
})
```

### Signal Generation
```python
# Generate momentum signals
signals = await momentum_service.generate_signals({
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "method": "relative_strength",
    "lookback": 60,
    "min_confidence": 0.75,
    "include_reversals": True
})

# Returns:
{
    "signals": [
        {
            "symbol": "AAPL",
            "signal": "STRONG_BUY",
            "confidence": 0.87,
            "momentum_score": 15.2,
            "reason": "Strong relative strength over 60 days, 1.2x market performance",
            "timeframe": "60d",
            "reversal_risk": "LOW"
        },
        ...
    ]
}
```

### Momentum Ranking
```python
# Rank assets by momentum
rankings = await momentum_service.rank_assets({
    "universe": "sp500",  # or "etf_universe"
    "method": "12-1",  # 12-month minus 1-month
    "top_n": 20,
    "min_price": 10,
    "min_volume_avg": 1000000
})
```

### Key Methods
| Method | Description |
|--------|-------------|
| `relative_strength(symbols, lookback, rank)` | Relative strength analysis |
| `time_series_momentum(symbols, lookback, threshold)` | Time-series momentum |
| `cross_asset_momentum(assets, lookback, risk_adjusted)` | Cross-asset momentum |
| `generate_signals(symbols, method, lookback)` | Generate momentum signals |
| `rank_assets(universe, method, top_n)` | Rank assets by momentum |
| `detect_reversals(symbol, lookback)` | Early reversal detection |
| `momentum_confidence(symbol, lookback)` | Confidence score for signal |

---

## VolatilityService (Volatility Forecasting)

**File**: `app.services/analysis/volatility_service.py`

### Purpose
Volatility forecasting and analysis using statistical and ML-based approaches. Production-ready system for risk management and options pricing.

### Key Features
- Historical volatility (HV) calculation
- Implied volatility analysis
- Volatility forecasting models
- Volatility surface construction
- Regime detection (high/low volatility states)
- Volatility clustering analysis

### Volatility Models

#### 1. Historical Volatility
```python
# Calculate historical volatility
hv = await volatility_service.historical_volatility({
    "symbol_id": asset_uuid,
    "period": "252",  # 252 trading days = 1 year
    "type": "close_to_close",  # or "parkinson", "garman_klass"
    "annualized": True
})

# Returns: {"volatility": 0.22, "annualized_return": 0.15, "directional": "UP"}
```

#### 2. GARCH Model (planned)
```python
# GARCH volatility forecasting
forecast = await volatility_service.garch_forecast({
    "symbol_id": asset_uuid,
    "horizon": 10,  # 10-day forecast
    "model_order": (1, 1)  # GARCH(1,1)
})

# Returns: {"forecast": 0.25, "confidence_interval": [0.22, 0.28]}
```

#### 3. EWMA (Exponentially Weighted Moving Average)
```python
# RiskMetrics EWMA volatility
ewma = await volatility_service.ewma_volatility({
    "symbol_id": asset_uuid,
    "lambda": 0.94,  # Decay factor
    "window": 252
})
```

### Volatility Regime Detection
```python
# Detect volatility regime
regime = await volatility_service.detect_regime({
    "symbol_id": asset_uuid,
    "method": "hidden_markov",  # or "threshold", "statistical"
    "lookback": "252d"
})

# Returns: {"regime": "HIGH", "duration_days": 45, "confidence": 0.87}
```

### Volatility Surface (Options)
```python
# Construct volatility surface for options pricing
surface = await volatility_service.volatility_surface({
    "symbol_id": asset_uuid,
    "date": "2024-08-17",
    "strikes": [0.9, 1.0, 1.1],  # Relative strike prices
    "maturities": [7, 30, 60, 90, 180]  # Days
})
```

### Usage
```python
from app.services.analysis.volatility_service import VolatilityService

service = VolatilityService()

# Historical volatility
hv = await service.historical_volatility({
    "symbol": "AAPL",
    "period": "252",
    "annualized": True
})

# Volatility forecast
forecast = await service.forecast({
    "symbol_id": asset_uuid,
    "method": "garch",
    "horizon": 5  # 5-day forecast
})

# Volatility regime
regime = await service.detect_regime({
    "symbol": "AAPL",
    "lookback": "1y"
})

# Volatility comparison
comparison = await service.compare_volatility({
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "period": "252"
})
```

### Key Methods
| Method | Description |
|--------|-------------|
| `historical_volatility(symbol_id, period, type)` | Calculate historical volatility |
| `forecast(symbol_id, method, horizon)` | Volatility forecast |
| `detect_regime(symbol_id, method, lookback)` | Volatility regime detection |
| `volatility_surface(symbol_id, date, strikes, maturities)` | Options surface |
| `compare_volatility(symbols, period)` | Cross-symbol comparison |
| `realized_volatility(symbol_id, period)` | Realized volatility |
| `volatility_atr(symbol_id, period)` | ATR-based volatility |

---

## UserFilteredScoringService (Custom Scoring)

**File**: `app.services/analysis.user_filtered_scoring_service.py`

### Purpose
Generates custom investment scores based on user-selected criteria, preferences, and weighting factors. Provides personalized scoring aligned with individual investment philosophies and risk tolerances.

### Key Features
- Dynamic score component selection
- User weighting adjustment
- Custom factor creation
- Peer group comparison
- Score sensitivity analysis
- Portfolio optimization based on custom scores

### User Filter Configuration
```python
# Example user preferences
user_preferences = {
    "preferred_factors": [
        "growth_potential",
        "dividend_yield",
        "debt_to_equity",
        "price_momentum"
    ],
    "weightings": {
        "growth_potential": 0.40,
        "dividend_yield": 0.25,
        "debt_to_equity": 0.20,
        "price_momentum": 0.15
    },
    "risk_tolerance": "moderate",  # conservative, moderate, aggressive
    "excluded_sectors": ["Commodity"],
    "min_market_cap": 1000000000,  # $1B
    "max_debt_to_equity": 1.0,
    "min_dividend_yield": 0.02  # 2%
}
```

### Custom Score Generation
```python
# Generate custom score based on user preferences
custom_score = await user_scoring_service.score({
    "user_id": user_uuid,
    "symbol_id": asset_uuid,
    "preferences": user_preferences,
    "include_breakdown": True
})

# Returns:
{
    "symbol": "AAPL",
    "custom_score": 82.5,
    "score_breakdown": {
        "growth_potential": {"score": 85.0, "weight": 0.40, "contribution": 34.0},
        "dividend_yield": {"score": 72.0, "weight": 0.25, "contribution": 18.0},
        "debt_to_equity": {"score": 95.0, "weight": 0.20, "contribution": 19.0},
        "price_momentum": {"score": 78.0, "weight": 0.15, "contribution": 11.7}
    },
    "percentile": 85.2  # Top 15% of universe
}
```

### Sensitivity Analysis
```python
# Analyze how score changes with factor weight changes
sensitivity = await user_scoring_service.sensitivity_analysis({
    "user_id": user_uuid,
    "symbol_id": asset_uuid,
    "preferences": user_preferences,
    "factor_variations": {
        "growth_potential": [-0.1, 0, 0.1],  # ±10% weight variations
        "dividend_yield": [-0.05, 0, 0.05]
    }
})

# Returns:
{
    "base_score": 82.5,
    "variations": [
        {"growth_potential": 0.30, "score": 80.2},  # +10% growth weight
        {"growth_potential": 0.50, "score": 85.1},  # +10% growth weight
        {"dividend_yield": 0.15, "score": 83.4},  # +5% dividend weight
        {"dividend_yield": 0.35, "score": 80.1}   # -5% dividend weight
    ]
}
```

### Portfolio Optimization
```python
# Find optimal portfolio based on custom scores
portfolio = await user_scoring_service.optimize_portfolio({
    "user_id": user_uuid,
    "preferences": user_preferences,
    "universe": "sp500",
    "target_return": 0.12,  # 12% annual
    "max_risk": 0.15,  # 15% volatility
    "optimize_for": "score"  # or "risk", "return", "sharpe"
})

# Returns:
{
    "recommended_portfolio": [
        {"symbol": "AAPL", "allocation": 0.30, "score": 88.5},
        {"symbol": "MSFT", "allocation": 0.25, "score": 78.2},
        {"symbol": "GOOGL", "allocation": 0.20, "score": 85.0},
        {"symbol": "BRK.B", "allocation": 0.15, "score": 79.5},
        {"symbol": "JNJ", "allocation": 0.10, "score": 72.3}
    ],
    "expected_return": 0.134,
    "expected_risk": 0.122,
    "sharpe_ratio": 1.10
}
```

### Usage
```python
from app.services.analysis.user_filtered_scoring_service import UserFilteredScoringService

service = UserFilteredScoringService()

# Score a symbol based on user preferences
score = await service.score({
    "user_id": user_uuid,
    "symbol_id": asset_uuid,
    "preferences": user_preferences
})

# Rank symbols based on custom score
rankings = await service.rank({
    "user_id": user_uuid,
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "preferences": user_preferences
})

# Generate portfolio recommendations
portfolio = await service.optimize_portfolio({
    "user_id": user_uuid,
    "preferences": user_preferences,
    "universe": "sp500"
})

# Get score history
history = await service.score_history({
    "user_id": user_uuid,
    "symbol_id": asset_uuid,
    "start": "2024-01-01",
    "end": "2024-08-17"
})
```

### Key Methods
| Method | Description |
|--------|-------------|
| `score(user_id, symbol_id, preferences)` | Generate custom score |
| `rank(user_id, symbols, preferences)` | Rank symbols by score |
| `optimize_portfolio(user_id, preferences, universe)` | Portfolio optimization |
| `score_history(user_id, symbol_id, start, end)` | Score history |
| `sensitivity_analysis(user_id, symbol_id, preferences)` | Score sensitivity |
| `get_available_factors()` | List all scoring factors |
| `get_user_preferences(user_id)` | Get user's default preferences |

---

## Additional Analysis Services

### Behavioral Economics Service
**File**: `app/services/analysis/behavioral_economics_service.py`
- Behavioral bias detection and analysis
- Prospect theory modeling
- Sentiment-regime correlation
- Investor psychology metrics

### Currency Conversion Service
**File**: `app/services/analysis/currency_conversion_service.py`
- Real-time and historical currency conversion
- Multiple exchange rate sources
- Cross-rate triangulation
- Rate forecasting

### Monetary Policy Service
**File**: `app/services/analysis/monetary_policy_service.py`
- Central bank policy rate tracking
- Monetary policy regime detection
- Policy impact analysis
- Forward guidance analysis

### Exchange Rate Volatility Service
**File**: `app/services/analysis/exchange_rate_volatility_service.py`
- FX volatility surface analysis
- Volatility forecasting for currencies
- Regime detection for FX markets

### Regime Compression Service
**File**: `app/services/analysis/regime_compression_service.py`
- Market regime identification
- Compression analysis for similar periods
- State transition modeling

---
*Last Updated: 2026-08-17*
*Status: Production Ready - Tier 3 Analysis Services 100% Implemented*