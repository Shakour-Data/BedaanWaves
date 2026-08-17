# BedaanWaves Raw Data Sources Documentation

## Overview
This document outlines all data sources integrated into the unified BedaanWaves platform, including both traditional markets and cryptocurrency.

## 1. Tehran Stock Exchange (BrsApiClient)
- **Source Type**: Iranian Equity Market
- **Data Types**:
  - Real-time price feeds
  - Trading volumes
  - Market depth
  - Order book data
- **Access**: Real-time API integration via BrsApi.ir

## 2. Nasdaq Stock Market (NasdaqApiClient)
- **Source Type**: US Equity Market
- **Data Types**:
  - Real-time stock prices
  - Market indices (^IXIC, ^NDX, ^GSPC, ^DJI, ^RUT)
  - Trading volumes
  - Historical data
- **Access**: yfinance API integration

## 3. Cryptocurrency Feeds (CryptoApiClient)
- **Sources**:
  - CoinGecko
  - Binance
  - Crypto.com
- **Data Types**:
  - Price data
  - Trading volumes
  - Market cap
- **Access**: Exchange APIs integration

## 4. Financial Data Pipeline
- **Sources**:
  - CODAL (Iranian Stock Exchange)
  - Yahoo Finance
  - Alpha Vantage
- **Data Types**:
  - Income statements
  - Balance sheets
  - Cash flow statements

## 5. Global Financial Data
- **Sources**:
  - Bloomberg API
  - Yahoo Finance
  - Alpha Vantage
- **Data Types**:
  - International stock data
  - FX rates
  - Global indices

## 6. News & Events
- **Sources**:
  - Yahoo News API
  - Reuters API
- **Data Types**:
  - Market news
  - Regulatory updates

## 7. SEC Filings (SECRestAPIClient - In Development)
- **Current Status**: Under development (TODO-H2)
- **Expected Features**:
  - 10-K/10-Q/8-K filing retrieval
  - Document parsing pipeline
- **Access Model**:
  - SEC EDGAR database is publicly accessible
  - API implementation pending
  - Rate limiting considerations

## Data Normalization & Currency Conversion
- **Currency Conversion Service**:
  - Multi-currency support (USD, IRR, EUR, etc.)
  - Confidence intervals (±2σ) for conversions
  - PPP-adjusted inflation framework
- **Cross-Asset Normalization**:
  - Unified metric taxonomy
  - Semantic annotations (flow/stocks, nominal/real)
  - Temporal alignment for analysis

## Multi-Market Data Flow Architecture
```
[Global Sources] ──→ [Data Normalization Layer] ──→ [Analysis Engine]
       │                    │
       ├── Tehran Stock Exchange
       ├── Nasdaq Stock Market
       ├── Cryptocurrencies
       └── Global Financial Data
```

## Supported Markets

| Market Type | Status | Primary Source | Tickers Supported |
|-------------|--------|----------------|-------------------|
| Tehran Stock Exchange | Active | BRS API | Iranian tickers (فملی, خودرو, etc.) |
| Nasdaq | Active | yfinance | AAPL, MSFT, GOOGL, etc. |
| Cryptocurrency | Active | CoinGecko/Binance | BTC, ETH, etc. |
| Global Stocks | Active | Yahoo/Alpha Vantage | International symbols |
| SEC Filings | In Development | EDGAR API | US public companies |

## Future Integrations
- Forex markets
- Bond markets
- Commodity exchanges
- Emerging markets

---

**Last Updated**: August 2026  
**Status**: Complete - All major data sources integrated