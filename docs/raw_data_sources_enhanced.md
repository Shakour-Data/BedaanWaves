# BedaanWaves Raw Data Sources Documentation

This document outlines all data sources integrated into the unified BedaanWaves platform, including both traditional markets and cryptocurrency.

## 1. Tehran Stock Exchange (BrsApiClient)
- **Source Type**: Iranian Equity Market
- **Data Types**:
  - Real-time price feeds
  - Trading volumes
  - Market depth
  - Order book data
- **Access**: Real-time API integration
- **Diagram**:
  ```
  [BrsApiClient] → [Currency Converter] → [Analysis]
  ```

## 2. Nasdaq Stock Market
- **Source Type**: US Equity Market
- **Data Types**:
  - Real-time stock prices
  - Market indices (^IXIC, ^NDX)
  - Trading volumes
  - Market depth
- **Access**: yfinance API integration
- **Diagram**:
  ```
  [yfinance API] → [Currency Converter] → [Analysis]
  ```

## 3. Cryptocurrency Market (CryptoApiClient)
- **Sources**:
  - CoinGecko
  - Binance
  - Crypto.com
- **Data Types**:
  - Price data
  - Market cap
  - Trading volumes
- **Diagram**:
  ```
  [Exchange APIs] → [Blockchain Explorer] → [Analysis]
  ```

## 4. Global Financial Data
- **Sources**:
  - Yahoo Finance
  - Alpha Vantage
  - Bloomberg
- **Data Types**:
  - Income statements
  - Balance sheets
  - FX rates
- **Diagram**:
  ```
  [Global APIs] → [Data Normalizer] → [Analysis]
  ```

## 5. News & Events
- **Sources**:
  - Yahoo News API
  - Reuters API
  - Iranian news platforms
- **Data Types**:
  - Market news
  - Regulatory updates
  - Sentiment indicators
- **Diagram**:
  ```
  [News APIs] → [NLP Processing] → [Correlation Analysis]
  ```

## 6. SEC Filings (In Development)
- **Current Status**: Under development (TODO-H2)
- **Expected Features**:
  - 10-K/10-Q/8-K filing retrieval
  - Document parsing pipeline
- **Access Model**:
  - SEC EDGAR database publicly accessible
  - API implementation pending

## Data Normalization Layer
- **Functions**:
  - Currency conversion with confidence intervals
  - Taxonomic normalization for cross-asset comparison
  - Temporal alignment for analysis

## Future Expansion Architecture
```
  [New Market API] → [Currency Converter] → [Analysis Layer]
```