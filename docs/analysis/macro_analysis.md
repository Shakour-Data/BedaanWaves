# Macro Analysis in BedaanWaves Scoring System

## Overview
Macro analysis evaluates securities based on broader economic and market factors. This dimension contributes 10% to the overall 6D score and captures systematic forces affecting all asset classes within specific economies.

**Important**: The coefficient/weight of each dimension, sub-dimension, aspect, and sub-aspect is dynamically determined through machine learning models and is **not static**. The CoefficientLearningService continuously optimizes these weights based on backtest performance, regime changes, and evolving market conditions.

## Hierarchical Structure
- **Level 1**: Macro (10% weight)
- **Level 2**: GDP growth, Inflation rates, Interest rates, Currency exchange rates, Commodity prices
- **Level 3**: Economic indicators, Market conditions, Policy environment, Global factors
- **Level 4**: Leading indicators, Coincident indicators, Lagging indicators, Composite indices

## Data Sources
- National statistics bureaus and central banks
- International organizations (IMF, World Bank, OECD)
- Government economic reports and releases
- Central bank policy communications
- Commodity exchanges and futures markets
- Forex and currency markets
- Global economic databases (FRED, OECD Data)
- Real-time economic indicator feeds

## Key Metrics Analyzed

### GDP and Economic Growth
- **GDP Growth Rate**: Quarterly and annual economic expansion
- **GDP Per Capita**: Economic output per person
- **Industrial Production Index**: Manufacturing and industrial output
- **Capacity Utilization**: Economy operating at what percentage
- **Productivity Growth**: Efficiency improvements
- **Consumer Spending**: Household consumption trends
- **Business Investment**: Capital expenditure trends
- **Export/Import Growth**: Trade balance dynamics

### Inflation Metrics
- **Consumer Price Index (CPI)**: Retail price changes
- **Core CPI**: CPI excluding food and energy
- **Producer Price Index (PPI)**: Wholesale price changes
- **GDP Deflator**: Economy-wide price level
- **Import/Export Prices**: Trade-related inflation
- **Wage Growth**: Labor cost inflation
- **Asset Price Inflation**: Real estate, stocks, commodities
- **Helicopter Money**: Direct monetary transmission

### Interest Rate Environment
- **Policy Interest Rate**: Central bank benchmark rate
- **Yield Curve**: Term structure of interest rates
- **Federal Funds Rate**: US interest rate impact
- **Repo Rate**: Short-term borrowing costs
- **Money Supply Growth**: Monetary expansion rate
- **Banking Sector Lending Rates**: Credit cost transmission
- **Bond Market Yields**: Safe asset returns
- **Term Premium**: Extra return for longer maturities

### Currency Exchange Rates
- **Nominal Exchange Rate**: Price relationship between currencies
- **Real Effective Exchange Rate**: Trade-weighted exchange rate
- **Currency Volatility**: Exchange rate fluctuation intensity
- **Carry Trade Opportunities**: Interest rate differentials
- **Currency Reserves**: Central bank foreign asset holdings
- **Trade Balance Impact**: Export competitiveness
- **Import Price Transmission**: Imported inflation
- **Currency Correlation**: Exchange rate co-movement

### Commodity Prices
- **Energy Prices**: Oil, natural gas, energy sector impact
- **Metal Prices**: Base and precious metals
- **Agricultural Commodities**: Food price trends
- **Soft Commodities**: Non-energy agricultural products
- **Commodity Index**: Broad commodity price measures
- **Commodity Volatility**: Price fluctuation severity
- **Inventory Levels**: Supply glut vs. tight markets
- **Weather Impact**: Agricultural supply disruption risk

## Regional and Geographic Analysis

### Iran-Specific Factors
- **Iran GDP Growth**: Domestic economic expansion
- **Sanctions Impact**: International trade restrictions
- **Currency Devaluation**: Rial exchange rate pressures
- **Inflation Rate**: Domestic price level changes
- **Oil Exports**: Energy revenue flows
- **Subsidy Removal**: Government fiscal policy impact

### Global Market Factors
- **US Dollar Strength**: Currency impact on global markets
- **Federal Reserve Policy**: Global monetary conditions
- **Global Trade Flows**: International commerce trends
- **Geopolitical Tensions**: Conflict impact on markets
- **Supply Chain Disruptions**: Global production challenges
- **Climate Policy**: Environmental regulation impact
- **Demographic Trends**: Population and age structure changes

## Leading Indicators Analysis
- **PMI (Purchasing Managers Index)**: Early economic activity gauge
- **Consumer Confidence**: Future expectations measurement
- **Building Permits**: Future construction activity
- **Stock Market Performance**: Wealth effect on economy
- **Credit Conditions**: Lending availability and terms
- **Money Market Conditions**: Liquidity in short-term markets
- **Commodity Price Trends**: Early supply/demand signals
- **Yield Curve Steepness/Flatness**: Economic cycle prediction

## Analysis Process
1. **Indicator Selection**: Choose relevant macro indicators
2. **Data Collection**: Gather real-time and historical data
3. **Normalization**: Adjust for different scales and units
4. **Trend Analysis**: Identify direction and momentum
5. **Correlation Mapping**: Link economic factors to security performance
6. **Regime Detection**: Identify current economic phase
7. **Impact Assessment**: Estimate sector and security impact
8. **Score Normalization**: Convert to 0-100 scale
9. **Weight Application**: Apply ML-optimized weights
10. **Integration**: Combine with other macro sub-dimensions

## Machine Learning Integration
- **Time Series Forecasting**: ARIMA, LSTM, Prophet models
- **Cointegration Analysis**: Long-term economic relationship modeling
- **Factor Models**: Systematic risk factor identification
- **Causal Inference**: Understanding economic driver relationships
- **Event Detection**: Identifying regime changes and policy shifts
- **Sentiment Analysis**: Central bank communication interpretation
- **Network Analysis**: Economic indicator interdependencies
- **Scenario Generation**: Monte Carlo macroeconomic scenarios

## Output Interpretation
Macro analysis produces economy-cycle positioning:
- **0-19**: Deflationary recession (downward cycle)
- **20-39**: Late cycle (market peak conditions)
- **40-54**: Middle cycle (stable growth)
- **55-69**: Early cycle (expansion beginning)
- **70-84**: Early expansion (recovery underway)
- **85-100**: Strong expansion (peak growth phase)

## Economic Regime Classification
- **Normal Cycle**: Balanced economic conditions
- **Late Cycle**: Approaching recession with tightening monetary
- **Recession**: Economic contraction and weak demand
- **Early Recovery**: Stabilizing economy with improving sentiment
- **Mid-Expansion**: Solid growth with moderate inflation
- **Late Expansion**: Strong growth approaching overheating

## Sector Rotation Implications
Macro scores indicate optimal sector allocations:
- **High Macro Scores**: Cyclical stocks, commodities, financials benefit
- **Low Macro Scores**: Defensive stocks, utilities, bonds outperform
- **Transition Periods**: Mixed signals requiring careful positioning

This dimension provides essential context for understanding the broader economic environment that drives all other dimensions of the 6D scoring system, helping investors position for favorable macro conditions.