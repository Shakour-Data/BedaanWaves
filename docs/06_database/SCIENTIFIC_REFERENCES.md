# Scientific References

## Technical Indicators

| Indicator | Formula Reference | Implementation Notes |
|-----------|------------------|---------------------|
| RSI (Wilder) | Wilder, J. W. (1978). *New Concepts in Technical Trading Systems*. p. 63-70. | Uses Wilder's exponential smoothing: `AvgGain_t = (AvgGain_{t-1} × (n-1) + Gain_t) / n` |
| MACD | Appel, G. (1979). *The Moving Average Convergence-Divergence Method*. | MACD Line = EMA(12) - EMA(26); Signal Line = EMA(9) of MACD; Histogram = MACD - Signal |
| Bollinger Bands | Bollinger, J. (2002). *Bollinger on Bollinger Bands*. | Middle = SMA(20); Upper/Lower = SMA ± 2×σ |
| EMA | Standard exponential moving average | Multiplier = 2/(n+1); EMA₀ = SMA(n) for initialization |
| ATR | Wilder, J. W. (1978). *New Concepts in Technical Trading*. p. 76-82. | True Range = max(high-low, \|high-prev_close\|, \|low-prev_close\|); ATR = Wilder's EMA of TR |
| Stochastic Oscillator | Lane, G. C. (1984). *Lane's Stochastic*. | %K = (Close - Lowₙ) / (Highₙ - Lowₙ) × 100; %D = SMA(3) of %K |

## Fundamental Ratios

| Ratio | Reference | Formula |
|-------|-----------|---------|
| P/E Ratio | Graham, B., & Dodd, D. L. (1934). *Security Analysis*. | `P/E = Stock Price / EPS` |
| P/B Ratio | Edwards, E. O., & Philton, L. B. (1965). *The Theory of Stock Selection*. | `P/B = Stock Price / Book Value Per Share` |
| P/S Ratio | Rappaport, A. (1998). *Valuation: Measuring and Managing the Value of Companies*. | `P/S = Market Cap / Revenue` |
| PEG Ratio | Triplani, A. (2009). *The Little Book of Valuation*. | `PEG = P/E / Growth Rate` |
| ROE | Solomon, I. (2003). *Return on Equity*. | `ROE = Net Income / Average Equity × 100` |
| ROA | Brigham, E. F., & Houston, M. C. (2020). *Fundamentals of Financial Management*. | `ROA = Net Income / Average Total Assets × 100` |
| ROIC | Greenwald, B. J., et al. (2001). *Value Investing: Tools and Techniques for Intelligent Investment*. | `ROIC = NOPAT / Invested Capital` |
| Gross Margin | Horngren, C. T. (2013). *Cost Accounting*. | `Gross Margin = (Gross Profit / Revenue) × 100` |
| DuPont Analysis | DuPont, E. I. (1920s). *Annual Report*. | `ROE = Net Margin × Asset Turnover × Financial Leverage` |
| Debt-to-Equity | Brealey, R. A., Myers, S. C., & Allen, F. (2020). *Principles of Corporate Finance*. | `D/E = Total Debt / Total Equity` |
| Current Ratio | William, M. C. (2016). *Financial Analysis*. | `Current Ratio = Current Assets / Current Liabilities` |
| Quick Ratio | William, M. C. (2016). *Financial Analysis*. | `Quick Ratio = (Current Assets - Inventory) / Current Liabilities` |

## Statistical Models

| Metric | Reference | Formula |
|--------|-----------|---------|
| Sharpe Ratio | Sharpe, W. F. (1966). "Mutual Fund Performance." *Journal of Business*, 39(1), 119-138. | `S = (μ_p - r_f) / σ_p` |
| Sortino Ratio | Sortino, F. A., & Price, L. F. (1994). "An Empirical Examination of the Value of a Higher Return Portfolio in a Downside Risk Framework." | `S = (μ_p - r_f) / σ_d` where σ_d = downside deviation |
| VaR (Historical) | Jorion, P. (2006). *Value at Risk: The New Benchmark for Managing Financial Risk*. | `VaR = -percentile(returns, α)` |
| CVaR (Expected Shortfall) | Rockafellar, R. T., & Uryasev, S. (2000). "Optimization of Conditional Value-at-Risk." | `CVaR = E[returns | returns ≤ VaR_α]` |
| Beta (CAPM) | Sharpe, W. F. (1964). "Capital Asset Prices." *Journal of Finance*, 19(3), 425-442. | `β = Cov(r_p, r_m) / Var(r_m)` |
| Max Drawdown | Brown, S. J., & Goetzmann, N. H. (2003). "A Review of Quantitative Market Research in Hedge Funds." | `MDD = max_t [peak_t - value_t] / peak_t` |
| Pearson Correlation | Pearson, K. (1896). "Mathematical Contributions to the Theory of Evolution." | `r = Σ((x_i - x̄)(y_i - ȳ)) / √(Σ(x_i - x̄)² × Σ(y_i - ȳ)²)` |
| Z-score (Anomaly) | Naylor, T. H., & Finger, H. (1975). "A Study of the Use of a Serial Correlation Coefficient in the Quality Control of Production Test Data." | `z = (x - μ) / σ` |
| Volatility (Annualized) | Mandelbrot, B. (1963). "The Variation of Certain Speculative Prices." | `σ_annual = σ_daily × √252` |
| Population vs Sample Std | Casella, G., & Berger, R. L. (2002). *Statistical Inference* (2nd ed.). p. 230. | Population: `σ = √(Σ(x-μ)²/N)`; Sample: `s = √(Σ(x-x̄)²/(n-1))` |

## Time Series & ML

| Model | Reference | Implementation Notes |
|-------|-----------|---------------------|
| ARIMA | Box, G. E. P., Jenkins, G. M., & Reinsel, G. C. (2015). *Time Series Analysis* (5th ed.). | ARIMA(1,1,0): one autoregressive term, first differencing, no moving average |
| Linear Regression | Hastie, T., Tibshirani, R., & Friedman, J. (2009). *The Elements of Statistical Learning* (2nd ed.). | Ordinary Least Squares: `β = (XᵀX)⁻¹Xᵀy` |
| Random Forest | Breiman, L. (2001). "Random Forests." *Machine Learning*, 45(1), 5-32. | Ensemble of decision trees with bagging and random feature selection |
| Train/Test Split | Kuhn, M., & Johnson, K. (2013). *Applied Predictive Modeling*. | Use `train_test_split` with `random_state` for reproducibility |
| StandardScaler | StandardScaler normalizes features to zero mean and unit variance | Fit on training, transform both train and test |
| Feature Importance (Gini) | Breiman, L. (2001). "Random Forests." *Machine Learning*, 45(1), 5-32. | Mean decrease in impurity for tree-based models |

## Macroeconomics

| Concept | Reference | Implementation Notes |
|---------|-----------|---------------------|
| Phillips Curve | Phillips, A. W. (1958). "The Relationship Between Unemployment and Rate of Change of Money Wages." | Inverse inflation-unemployment relationship; slope ≈ -0.15 empirically |
| Yield Curve Inversion | Estrella, C. A. V., & Mishkin, F. S. (1996). "The Yield Curve as a Leading Indicator." | 10Y-2Y spread < 0 signals recession risk; < -0.5 signals high risk |
| Fisher Equation | Fisher, I. (1930). *The Theory of Interest*. | `r_nominal ≈ r_real + π_expected` |

## Financial Health Scoring

| Metric | Reference | Implementation Notes |
|--------|-----------|---------------------|
| Altman Z-Score | Altman, E. I. (1968). "Financial Ratios, Discriminant Analysis and the Prediction of Corporate Bankruptcy." | Z = 1.2×(WC/TA) + 1.4×(RE/TA) + 3.3×(EBIT/TA) + 0.6×(MVE/BV) + 1.0×(Sales/TA) |
| Interest Coverage | Moody's Investor Service methodology. | `IC = EBIT / Interest Expense` |

## Numerical Methods

| Technique | Reference | Notes |
|-----------|-----------|-------|
| Inverse Normal CDF Approximation | Abramowitz, M., & Stegun, I. A. (1965). *Handbook of Mathematical Functions*. Formula 26.2.23. | Rational approximation used when SciPy unavailable |
| Mean Reversion | Feller, W. (1951). "Variation and More." | `σ²_t₊₁ = σ²_t × (1 - α) + α × σ²_∞` |
| Floating Point Tolerance | Goldberg, D. (1991). "What Every Computer Scientist Should Know About Floating-Point Arithmetic." | Use relative tolerance ≤ 1e-6 for coefficient validation |

## Standards

| Standard | Description |
|----------|-------------|
| ISO 27001 | Information security management |
| ISO 20022 | Financial services messaging |
| Basel III | Banking regulatory capital framework |
| IFRS 15 | Revenue recognition |
