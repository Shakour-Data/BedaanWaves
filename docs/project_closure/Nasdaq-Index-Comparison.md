# Nasdaq Composite vs Nasdaq-100: Authoritative Comparison

## Side-by-Side Comparison Table

| Dimension | Nasdaq Composite | Nasdaq-100 |
|-----------|-----------------|------------|
| **Number of Constituents** | ~3,000+ companies (variable, ~3,000 to 3,700 as of 2025) | Exact 100 companies (fixed) |
| **Full Name** | NASDAQ Composite Index (Symbol: IXIC) | NASDAQ-100 Index (Symbol: NDX) |
| **Selection Criteria** | Includes ALL domestic and international common stocks listed on the NASDAQ stock exchange. No market-cap minimum for inclusion beyond basic listing standards. | Includes 100 of the LARGEST non-financial domestic and international companies listed on NASDAQ. Selected by modified market capitalization. Annual reconstitution in December; quarterly re-ranking. |
| **Sectors EXCLUDED** | **None.** All sectors are included: Technology, Financial, Healthcare, Consumer Discretionary, Industrials, Energy, Utilities, Real Estate, Materials, Telecommunications. | **Financial Services firms are explicitly excluded.** No investment companies, no banks, no insurance companies, no broker-dealers. Tech (~60%), Healthcare (~12%), Consumer (~15%), Communications (~8%), Industrials (~5%). |
| **Weighting Methodology** | Market Capitalization Weighted (float-adjusted) | Modified Capitalization Weighted (with special weighting formula to limit single-stock concentration to ~24%; 1% rebalance threshold) |
| **Trading Symbol (Spot/CFD)** | IXIC (rarely traded as CFD) | **NAS100, NDX, US100 — this is what you trade on MetaTrader, cTrader, TradingView CFD accounts** |
| **Tick Value (Futures)** | NQ Futures: $5 per 0.25 index point = $20 per 1.00 point | MNQ Micro-NQ: $0.50 per 0.25 point = $2 per 1.00 point. Contract symbols: NQ (full), MNQ (micro). **NOTE: Both NAS100 CFDs and NQ futures reference the Nasdaq-100, NOT the Composite.** |
| **Dividend Treatment** | Ex-dividend price adjustment; price return only | Ex-dividend price adjustment; price return only (separate Total Return indices exist) |
| **Top 5 Holdings (2025)** | Apple, Microsoft, NVIDIA, Amazon, Alphabet (but diluted across 3,000+ names) | Apple (~13-15%), Microsoft (~11-13%), NVIDIA (~8-10%), Amazon (~6-8%), Meta Platforms (~5-7%). Top 10 = ~65% of the index. |
| **Correlation Between Indices** | 0.95 - 0.98 (highly correlated directionally, but magnitude differs) | Reference series |
| **Volatility Profile** | Lower beta (~0.95-1.05) due to broader diversification across sectors including utilities and financials | Higher beta (~1.10-1.25) due to mega-cap tech concentration. Sharp tech sell-offs hit NDX harder. |

## Simple Analogy: The Relationship

Think of the **NASDAQ Composite** as the **entire student body of a large university** (~3,000 students) — every single enrolled student counts, from the arts department to the business school to the computer science labs. The GPA of the whole student body is the Composite index value.

Think of the **NASDAQ-100** as the **honor society of the top 100 highest-achieving STEM students** from that same university — but you explicitly EXCLUDE all students from the Business/Finance department. Their collective GPA is the NDX value.

They come from the same campus (same exchange), they move in the same general direction, but the honor society (NDX) is far more concentrated, far more volatile, and heavily skewed toward one type of excellence.

## Critical Trading Note: NAS100 = NASDAQ-100, NOT NASDAQ COMPOSITE

**FACT:** When you see the ticker `NAS100` on MetaTrader 4/5, cTrader, TradingView, or any retail CFD/Futures platform — you are trading the **NASDAQ-100 (NDX)**. You are never trading the NASDAQ Composite (IXIC) unless the broker explicitly labels it `NASDAQ_COMPOSITE` or `IXIC`, which almost none do.

**Why this matters:**
- The NAS100 (NDX) has NO financial stocks. During a banking crisis, NAS100 may outperform the Composite.
- The NAS100 is ~60% weighted in technology. During a tech rally, NAS100 will outperform the Composite.
- Entry points, stop-losses, and take-profit levels calibrated to IXIC charts will fail on NAS100 positions.
- Economic data favoring financials (e.g., Fed rate hikes helping net-interest-margin) will benefit the Composite more, not the NAS100.

**Platform Symbol Cross-Reference:**
| Platform | Symbol | Underlying Index |
|----------|--------|------------------|
| MetaTrader 4/5 (most brokers) | NAS100, US100, NASDAQ | Nasdaq-100 (NDX) |
| TradingView CFD | NAS100, NDX1!, NQ1! | Nasdaq-100 (NDX) |
| CME Globex Futures | NQ (full), MNQ (micro) | Nasdaq-100 (NDX) |
| Yahoo Finance | ^IXIC | Nasdaq Composite |
| Yahoo Finance | ^NDX | Nasdaq-100 |

---
*Document ID: BW-FINANCE-REF-001 | Version: 1.0 | Classification: Trader Education*
