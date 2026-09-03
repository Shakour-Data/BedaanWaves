import { describe, it, expect } from "vitest";
import { isNasdaqEquityLike } from "@/lib/dashboard-data";

describe("isNasdaqEquityLike", () => {
  it("accepts plain Nasdaq tickers", () => {
    expect(isNasdaqEquityLike({ market: "NASDAQ", symbol: "AAPL" })).toBe(true);
    expect(isNasdaqEquityLike({ market: "NASDAQ", symbol: "MSFT" })).toBe(true);
  });

  it("accepts Nasdaq-listed ETFs", () => {
    expect(isNasdaqEquityLike({ market: "NASDAQ", symbol: "QQQ" })).toBe(true);
    expect(isNasdaqEquityLike({ market: "NASDAQ", symbol: "TQQQ" })).toBe(true);
  });

  it("rejects explicit non-NASDAQ markets", () => {
    expect(isNasdaqEquityLike({ market: "NYSE", symbol: "JPM" })).toBe(false);
    expect(isNasdaqEquityLike({ market: "BINANCE", symbol: "BTCUSDT" })).toBe(false);
    expect(isNasdaqEquityLike({ market: "TSE", symbol: "7203" })).toBe(false);
  });

  it("rejects crypto-style suffixes even if market is missing", () => {
    expect(isNasdaqEquityLike({ symbol: "BTC-USD" })).toBe(false);
    expect(isNasdaqEquityLike({ symbol: "ETH-USD" })).toBe(false);
    expect(isNasdaqEquityLike({ symbol: "BTCUSD" })).toBe(false);
    expect(isNasdaqEquityLike({ symbol: "ETHUSDT" })).toBe(false);
  });

  it("rejects empty or missing symbol", () => {
    expect(isNasdaqEquityLike({})).toBe(false);
    expect(isNasdaqEquityLike({ symbol: "" })).toBe(false);
  });
});
