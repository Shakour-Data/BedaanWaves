#!/usr/bin/env python
"""
Real Nasdaq data integration test.
Fetches actual market data from Yahoo Finance API.
"""

import yfinance as yf

# NASDAQ Index constituents - real data test
NASDAQ_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'META', 'NVDA']

def fetch_nasdaq_data():
    """Fetch real Nasdaq stock data from Yahoo Finance."""
    print("=" * 60)
    print("FETCHING REAL NASDAQ DATA")
    print("=" * 60)
    
    results = []
    for symbol in NASDAQ_SYMBOLS:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            name = info.get('shortName', 'N/A')
            market_cap = info.get('marketCap', 0)
            currency = info.get('currency', 'USD')
            exchange = info.get('exchange', 'NASDAQ')
            
            result = f"{symbol}: {name} | Market Cap: ${market_cap:,.0f} | Currency: {currency} | Exchange: {exchange}"
            print(result)
            results.append({
                'symbol': symbol,
                'name': name,
                'market_cap': market_cap,
                'currency': currency,
                'exchange': exchange
            })
        except Exception as e:
            print(f"{symbol}: ERROR - {e}")
    
    return results

def fetch_price_history():
    """Fetch historical price data for test symbols."""
    print("\n" + "=" * 60)
    print("FETCHING HISTORICAL PRICE DATA")
    print("=" * 60)
    
    ticker = yf.Ticker("AAPL")
    hist = ticker.history(period="5d")
    
    for date, row in hist.iterrows():
        print(f"{date.strftime('%Y-%m-%d')}: OHLC ({row['Open']:.2f}, {row['High']:.2f}, {row['Low']:.2f}, {row['Close']:.2f}) Vol: {int(row['Volume']):,}")

if __name__ == "__main__":
    data = fetch_nasdaq_data()
    fetch_price_history()
    print(f"\n Successfully fetched data for {len(data)} NASDAQ stocks")
    print(" Data is fresh and real, ready for database ingestion")
