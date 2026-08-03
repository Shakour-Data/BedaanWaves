# BedaanWaves Raw Data Sources Documentation

![Architecture Diagram](https://via.placeholder.com/600x200?text=Raw+Data+Sources+Architecture)

## 1. Tehran Stock Exchange (BrsApiClient)
- **Source Type**: Equity Market Data
- **Data Types**:
  - Real-time price feeds
  - Trading volumes
  - Market depth
  - Order book data
- **Access**: Real-time API integration
- **Diagram**:
  ```
  [BrsApiClient] → [Database]
  ```

## 2. Financial Data Pipeline
- **Sources**:
  - CODAL (Iranian Stock Exchange)
  - Yahoo Finance
  - Alpha Vantage
- **Data Types**:
  - Income statements
  - Balance sheets
  - Cash flow statements
- **Diagram**:
  ```
  [CODAL API] → [Validation] → [Standardized Format]
  [Yahoo API] → [Validation] → [Standardized Format]
  ```

## 3. Cryptocurrency Feeds
- **Sources**:
  - CoinGecko
  - Binance
  - Crypto.com
- **Data Types**:
  - Price data
  - Trading volumes
  - Market cap
- **Diagram**:
  ```
  [Exchange APIs] → [Blockchain Data] → [Analysis]
  ```

## 4. International Markets
- **Sources**:
  - NASDAQ API
  - Bloomberg API
- **Data Types**:
  - FX rates
  - Global indices
- **Diagram**:
  ```
  [NASDAQ] → [FX Conversion] → [Analysis]
  ```

## 5. News & Events
- **Sources**:
  - Yahoo News API
  - Reuters API
- **Data Types**:
  - Market news
  - Regulatory updates
- **Diagram**:
  ```
  [News APIs] → [NLP Processing] → [Correlation Analysis]
  ```

## 6. SEC Filings (SECRestAPIClient - In Development)
- **Current Status**: Under development (TODO-H2)
- **Expected Features**:
  - 10-K/10-Q/8-K filing retrieval
  - Document parsing pipeline
- **Access Model**:
  - SEC EDGAR database is publicly accessible
  - API implementation pending
  - Rate limiting considerations

![SEC Access Diagram](https://via.placeholder.com/400x150?text=SEC+API+Access)

## Data Flow Architecture
```
[Raw Sources] → [Validation] → [Standardized] → [Analysis]
```