# Analysis Page

## Overview
The Analysis page provides technical and fundamental analysis tools, custom screening, and comparative analysis for research and decision-making.

## Key Features
- **Technical Analysis**: 50+ technical indicators with live calculations
- **Fundamental Analysis**: Financial ratios, valuation metrics, industry comparisons
- **Screening Tool**: Custom filters for stock selection based on user criteria
- **Comparative Analysis**: Peer benchmarking across multiple dimensions
- **Sector Analysis**: Industry performance and trend analysis
- **Correlation Matrix**: Cross-asset correlation visualization
- **Export Tools**: Export charts, reports, and data to PDF/PNG/CSV

## Tool Categories
1. **Indicators**: RSI, MACD, Bollinger Bands, Moving Averages, ATR, OBV
2. **Patterns**: Chart pattern recognition (head and shoulders, double tops)
3. **Risk Metrics**: Volatility, VaR, Sharpe ratio, maximum drawdown
4. **Fundamentals**: P/E, P/B, Debt/Equity, ROE, ROIC, dividend yield

## Navigation
- Access via: `/analysis` (protected route)
- Left sidebar: Category navigation
- Toolbar: Date range, timeframe selection
- Results grid: Sortable and filterable data table

## Technical Details
- Real-time indicator calculations
- Support for custom indicator formulas
- Historical backtesting mode
- Multi-chart comparison capability
- WebSocket updates for live market data

## API Integration
- `/api/v1/analysis/technical` - Technical indicator data
- `/api/v1/analysis/fundamental` - Fundamental metrics
- `/api/v1/analysis/screener` - Screening results
- `/api/v1/analysis/comparison` - Comparative analysis

## Custom Analysis
Users can save custom analysis templates, set watchlist-specific analysis, and create alert conditions based on indicator thresholds.