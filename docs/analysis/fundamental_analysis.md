# Fundamental Analysis in BedaanWaves Scoring System

## Overview
Fundamental analysis evaluates the intrinsic value of securities by examining related economic, financial, and other qualitative and quantitative factors. This dimension contributes 25% to the overall 6D score.

**Important**: The coefficient/weight of each dimension, sub-dimension, aspect, and sub-aspect is dynamically determined through machine learning models and is **not static**. The CoefficientLearningService continuously optimizes these weights based on backtest performance, regime changes, and evolving market conditions.

## Hierarchical Structure
- **Level 1**: Fundamental (25% weight)
- **Level 2**: Price history, OHLCV data, Corporate actions
- **Level 3**: Financial ratios, Earnings quality, Growth metrics, Asset quality, Management quality
- **Level 4**: 50+ specific financial metrics and indicators

## Data Sources
- Financial statements (Income Statement, Balance Sheet, Cash Flow)
- Regulatory filings (CODAL for Iranian companies, SEC filings for international)
- Economic indicators from IMF, World Bank, central banks
- Analyst estimates and consensus forecasts
- Corporate actions data (dividends, splits, buybacks)

## Key Metrics Analyzed

### Profitability Metrics
- **ROE (Return on Equity)**: Measures return generated on shareholders' equity
- **ROA (Return on Assets)**: Indicates efficiency of asset utilization
- **Net Profit Margin**: Percentage of revenue converted to profit
- **Operating Margin**: Operational efficiency before interest and taxes
- **Gross Margin**: Production efficiency and pricing power

### Valuation Metrics
- **P/E Ratio (Price-to-Earnings)**: Market price relative to earnings per share
- **P/B Ratio (Price-to-Book)**: Market value relative to book value
- **EV/EBITDA**: Enterprise value relative to EBITDA (capital structure neutral)
- **PEG Ratio**: P/E ratio adjusted for earnings growth
- **Dividend Yield**: Annual dividend per share divided by price per share

### Financial Health Metrics
- **Debt-to-Equity Ratio**: Financial leverage measurement
- **Current Ratio**: Short-term liquidity position
- **Quick Ratio**: Immediate liquidity without inventory
- **Interest Coverage Ratio**: Ability to meet interest obligations
- **Cash Conversion Cycle**: Working capital efficiency

### Growth Metrics
- **Revenue Growth (YoY)**: Top-line expansion rate
- **EPS Growth (YoY)**: Earnings per share growth rate
- **Book Value Growth**: Shareholder equity growth
- **Dividend Growth Rate**: Dividend payout increase over time
- **Asset Growth**: Total asset expansion rate

### Quality Metrics
- **Earnings Quality**: Sustainability and predictability of earnings
- **Accounting Quality**: Transparency and conservatism in reporting
- **Management Effectiveness**: Capital allocation and operational efficiency
- **Corporate Governance**: Board structure and shareholder rights
- **Business Model Sustainability**: Competitive advantages and moats

## Analysis Process
1. **Data Collection**: Gather latest financial statements and key metrics
2. **Normalization**: Adjust for accounting differences and one-time events
3. **Benchmarking**: Compare against industry peers and historical averages
4. **Trend Analysis**: Identify improving or deteriorating trends over 3-5 years
5. **Scoring**: Convert normalized metrics to 0-100 scale using sector-specific curves
6. **Weight Application**: Apply learned weights from ML coefficient service
7. **Aggregation**: Combine sub-dimension scores into final fundamental score

## Machine Learning Integration
- Feature importance analysis identifies most predictive metrics
- Non-linear relationships captured through ensemble methods
- Sector-specific models account for industry variations
- Temporal weighting emphasizes recent performance while maintaining historical context
- Outlier detection prevents extreme values from skewing results

## Output
Fundamental analysis produces a normalized score between 0-100 where:
- 85-100: Exceptional fundamentals (Strong Buy signal)
- 70-84: Solid fundamentals (Buy signal)
- 55-69: Adequate fundamentals (Hold signal)
- 40-54: Concerning fundamentals (Sell signal)
- 0-39: Poor fundamentals (Strong Sell signal)

This score contributes 25% to the final 6D composite score, making it the single largest weighted component in the BedaanWaves scoring system.