# BedaanWaves Raw Data Sources Documentation

![Architecture Diagram](https://via.placeholder.com/600x200?text=Raw+Data+Sources+Architecture)

## 1. Tehran Stock Exchange (BrsApiClient)
- **Source Type**: Iranian Equity Market
- **Data Types**:
  - Real-time price feeds
  - Trading volumes
  - Market depth
  - Order book data
- **Access**: Real-time API integration via BrsApi.ir
- **Diagram**:
  ```
  [BrsApiClient] → [Currency Converter] → [Analysis]
  ```

## 2. Nasdaq Stock Market (NasdaqApiClient)
- **Source Type**: US Equity Market
- **Data Types**:
  - Real-time stock prices
  - Market indices (^IXIC, ^NDX, ^GSPC, ^DJI, ^RUT)
  - Trading volumes
  - Historical data
- **Access**: yfinance API integration
- **Diagram**:
  ```
  [yfinance API] → [Currency Converter] → [Analysis]
  ```

## 3. Financial Data Pipeline
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

## 4. Cryptocurrency Feeds
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

## 5. Global Financial Data
- **Sources**:
  - Bloomberg API
  - Yahoo Finance
  - Alpha Vantage
- **Data Types**:
  - International stock data
  - FX rates
  - Global indices
- **Diagram**:
  ```
  [Global APIs] → [Data Normalizer] → [Analysis]
  ```

## 6. News & Events
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

![SEC Access Diagram](https://via.placeholder.com/400x150?text=SEC+API+Access)