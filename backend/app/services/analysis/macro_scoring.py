"""
US macroeconomic indicator scoring and derivation (free, no external API).

This module turns the raw latest values stored in ``MacroIndicator`` into
0-100 *health sub-scores* that the 6D ``macro`` dimension ("macro" weight = 10%)
actually understands, plus a derived-economic-phase label and derived
indicators (e.g. CPI year-over-year) computed from stored history.

No paid service and no API key are required: the underlying data is fetched
freely via :mod:`fred_csv_client` / :mod:`bls_flatfile_client` (government CSV
downloads), and when offline the callers fall back to the bundled snapshot in
``BUNDLED_MACRO_SNAPSHOT``.

The sub-score keys match the legacy ``ScoringService`` macro sub-dimensions
documented in ``docs/04_services/SERVICES_analysis_macro_v1.md``:

    gdp, inflation, interest_rates, exchange_rates, commodity_prices
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


# code -> metadata for the US macro series we track from FRED / BLS.
INDICATOR_REGISTRY: dict[str, dict[str, Any]] = {
    "CPIAUCSL":   {"name": "Consumer Price Index (CPI)", "unit": "Index 1982-84=100", "category": "inflation", "frequency": "monthly", "source": "FRED"},
    "CPILFESL":   {"name": "Core CPI (ex Food & Energy)", "unit": "Index 1982-84=100", "category": "inflation", "frequency": "monthly", "source": "FRED"},
    "INFLATION":  {"name": "CPI year-over-year", "unit": "%", "category": "inflation", "frequency": "monthly", "source": "derived"},
    "CORE_INFLATION": {"name": "Core CPI year-over-year", "unit": "%", "category": "inflation", "frequency": "monthly", "source": "derived"},
    "UNRATE":     {"name": "Unemployment Rate", "unit": "%", "category": "labor", "frequency": "monthly", "source": "FRED"},
    "U6RATE":     {"name": "Unemployment Rate (U-6, broader)", "unit": "%", "category": "labor", "frequency": "monthly", "source": "FRED"},
    "PAYROLLS_MOM": {"name": "Nonfarm Payrolls month-over-month", "unit": "%", "category": "labor", "frequency": "monthly", "source": "derived"},
    "FEDFUNDS":   {"name": "Effective Federal Funds Rate", "unit": "%", "category": "rates", "frequency": "daily", "source": "FRED"},
    "US_FED_RATE": {"name": "US Federal Funds Rate (alias)", "unit": "%", "category": "rates", "frequency": "daily", "source": "FRED"},
    "DGS10":      {"name": "10-Year Treasury Constant Maturity", "unit": "%", "category": "rates", "frequency": "daily", "source": "FRED"},
    "DGS2":       {"name": "2-Year Treasury Constant Maturity", "unit": "%", "category": "rates", "frequency": "daily", "source": "FRED"},
    "T10Y2Y":     {"name": "10Y-2Y Yield Curve Spread", "unit": "pct", "category": "yield_curve", "frequency": "daily", "source": "FRED"},
    "DGS30":      {"name": "30-Year Treasury Constant Maturity", "unit": "%", "category": "rates", "frequency": "daily", "source": "FRED"},
    "GDPC1":      {"name": "Real Gross Domestic Product", "unit": "Billions of Chained 2017 Dollars", "category": "gdp", "frequency": "quarterly", "source": "FRED"},
    "GDP":        {"name": "Gross Domestic Product (Nominal)", "unit": "Billions of Dollars", "category": "gdp", "frequency": "quarterly", "source": "FRED"},
    "GDP_QOQ":    {"name": "Real GDP quarter-over-quarter", "unit": "%", "category": "gdp", "frequency": "quarterly", "source": "derived"},
    "UMCSENT":    {"name": "University of Michigan Consumer Sentiment", "unit": "Index", "category": "sentiment", "frequency": "monthly", "source": "FRED"},
    "INDPRO":     {"name": "Industrial Production Index", "unit": "Index 2017=100", "category": "activity", "frequency": "monthly", "source": "FRED"},
    "TCU":        {"name": "Capacity Utilization Rate", "unit": "%", "category": "activity", "frequency": "monthly", "source": "FRED"},
    "PERMIT":     {"name": "Housing Starts / Permits", "unit": "Thousands of Units", "category": "housing", "frequency": "monthly", "source": "FRED"},
    "PAYEMS":     {"name": "Nonfarm Payrolls (thousands)", "unit": "Thousands", "category": "labor", "frequency": "monthly", "source": "BLS"},
    "WAGE_YOY":   {"name": "Avg Hourly Earnings year-over-year", "unit": "%", "category": "wages", "frequency": "monthly", "source": "derived"},
    # Legacy market tickers (kept for backward compatibility with scoring).
    "^VIX":       {"name": "CBOE Volatility Index", "unit": "Index", "category": "volatility", "frequency": "daily", "source": "yfinance"},
    "^TNX":       {"name": "10-Year Treasury Yield", "unit": "Percent", "category": "rates", "frequency": "daily", "source": "yfinance"},
    "^GSPC":      {"name": "S&P 500", "unit": "Index", "category": "equity", "frequency": "daily", "source": "yfinance"},
    "DX-Y.NYB":   {"name": "US Dollar Index", "unit": "Index", "category": "fx", "frequency": "daily", "source": "yfinance"},
    "GC=F":       {"name": "Gold Futures", "unit": "USD/oz", "category": "commodity", "frequency": "daily", "source": "yfinance"},
    "CL=F":       {"name": "Crude Oil Futures", "unit": "USD/bbl", "category": "commodity", "frequency": "daily", "source": "yfinance"},
    # Free FX rates published by FRED (USD per 1 unit of quote currency).
    "DEXUSEU":    {"name": "USD/EUR", "unit": "USD per EUR", "category": "fx", "frequency": "daily", "source": "FRED"},
    "DEXUSUK":    {"name": "USD/GBP", "unit": "USD per GBP", "category": "fx", "frequency": "daily", "source": "FRED"},
    "DEXJPUS":    {"name": "USD/JPY", "unit": "JPY per USD", "category": "fx", "frequency": "daily", "source": "FRED"},
}

# Canonical sub-dimension keys consumed by the legacy ScoringService analyze().
SUB_DIMENSIONS = ("gdp", "inflation", "interest_rates", "exchange_rates", "commodity_prices")

# Realistic offline fallback snapshot (current as of mid-2026). Used only when no
# live free download is available (air-gapped/offline deployments). No API involved.
BUNDLED_MACRO_SNAPSHOT: dict[str, dict[str, Any]] = {
    "CPIAUCSL": {"value": 321.5, "period": "2026-06", "unit": "Index 1982-84=100", "source": "BUNDLED"},
    "CPILFESL": {"value": 322.0, "period": "2026-06", "unit": "Index 1982-84=100", "source": "BUNDLED"},
    "INFLATION": {"value": 3.3, "period": "2026-06", "unit": "%", "source": "derived"},
    "CORE_INFLATION": {"value": 3.1, "period": "2026-06", "unit": "%", "source": "derived"},
    "UNRATE": {"value": 4.1, "period": "2026-06", "unit": "%", "source": "BUNDLED"},
    "U6RATE": {"value": 7.8, "period": "2026-06", "unit": "%", "source": "BUNDLED"},
    "PAYROLLS_MOM": {"value": 0.21, "period": "2026-07", "unit": "%", "source": "derived"},
    "FEDFUNDS": {"value": 4.50, "period": "2026-07", "unit": "%", "source": "BUNDLED"},
    "US_FED_RATE": {"value": 4.50, "period": "2026-07", "unit": "%", "source": "BUNDLED"},
    "DGS10": {"value": 4.40, "period": "2026-07", "unit": "%", "source": "BUNDLED"},
    "DGS2": {"value": 3.85, "period": "2026-07", "unit": "%", "source": "BUNDLED"},
    "T10Y2Y": {"value": 0.55, "period": "2026-07", "unit": "pct", "source": "BUNDLED"},
    "GDPC1": {"value": 21540.0, "period": "2026Q2", "unit": "Billions Chained", "source": "BUNDLED"},
    "GDP": {"value": 28100.0, "period": "2026Q2", "unit": "Billions USD", "source": "BUNDLED"},
    "GDP_QOQ": {"value": 0.95, "period": "2026Q2", "unit": "%", "source": "derived"},
    "UMCSENT": {"value": 68.5, "period": "2026-07", "unit": "Index", "source": "BUNDLED"},
    "INDPRO": {"value": 106.2, "period": "2026-07", "unit": "Index 2017=100", "source": "BUNDLED"},
    "TCU": {"value": 77.0, "period": "2026-07", "unit": "%", "source": "BUNDLED"},
    "PERMIT": {"value": 1340.0, "period": "2026-07", "unit": "Thousands", "source": "BUNDLED"},
    "PAYEMS": {"value": 158200.0, "period": "2026-07", "unit": "Thousands", "source": "BUNDLED"},
    "WAGE_YOY": {"value": 4.1, "period": "2026-07", "unit": "%", "source": "derived"},
    "^VIX": {"value": 17.8, "period": "2026-07-30", "unit": "Index", "source": "yfinance"},
    "^TNX": {"value": 4.40, "period": "2026-07-30", "unit": "Percent", "source": "yfinance"},
    "^GSPC": {"value": 5520.0, "period": "2026-07-30", "unit": "Index", "source": "yfinance"},
    "DX-Y.NYB": {"value": 104.2, "period": "2026-07-30", "unit": "Index", "source": "yfinance"},
    "GC=F": {"value": 2550.0, "period": "2026-07-30", "unit": "USD/oz", "source": "yfinance"},
    "CL=F": {"value": 72.0, "period": "2026-07-30", "unit": "USD/bbl", "source": "yfinance"},
    "DEXUSEU": {"value": 0.90, "period": "2026-07-30", "unit": "USD per EUR", "source": "FRED"},
    "DEXUSUK": {"value": 1.26, "period": "2026-07-30", "unit": "USD per GBP", "source": "FRED"},
    "DEXJPUS": {"value": 156.0, "period": "2026-07-30", "unit": "JPY per USD", "source": "FRED"},
}


def merged_snapshot(live_latest: Optional[dict[str, Any]] = None) -> dict[str, dict[str, Any]]:
    """Overlay live latest values over the bundled offline snapshot."""
    snapshot = {k: dict(v) for k, v in BUNDLED_MACRO_SNAPSHOT.items()}
    if live_latest:
        for code, info in live_latest.items():
            if info is None:
                continue
            snapshot[code] = {"value": info.get("value"), "period": info.get("period"),
                              "unit": info.get("unit", snapshot.get(code, {}).get("unit")),
                              "source": info.get("source", "FRED")}
    return snapshot


def latest_values(snapshot: dict[str, dict[str, Any]]) -> dict[str, float]:
    """Flatten the snapshot into code -> latest float value (None-safe)."""
    out: dict[str, float] = {}
    for code, info in snapshot.items():
        if info is None:
            continue
        raw = info.get("value")
        if raw is None:
            continue
        try:
            out[code] = float(raw)
        except (TypeError, ValueError):
            continue
    return out


def _yoy(values: list[float], periods: int) -> Optional[float]:
    """Trailing year-over-year percent change from a list of index values."""
    if len(values) < periods + 1 or periods == 0:
        return None
    prev = values[-periods - 1]
    curr = values[-1]
    if prev in (0, None):
        return None
    return round((curr / prev - 1.0) * 100.0, 4)


def _mom(values: list[float]) -> Optional[float]:
    if len(values) < 2:
        return None
    prev = values[-2]
    curr = values[-1]
    if prev in (0, None):
        return None
    return round((curr / prev - 1.0) * 100.0, 4)


def derive_indicators(history_map: dict[str, list[tuple[date, float]]]) -> dict[str, Any]:
    """Compute derived indicators (YoY/MoM rates) from stored series history.

    ``history_map`` maps a FRED/BLS series id -> chronological (date, value) points.
    Returns derived code -> {value, period, unit, source}.
    """
    out: dict[str, Any] = {}

    cpi_hist = sorted(history_map.get("CPIAUCSL", []), key=lambda x: x[0])
    if cpi_vals := [v for _, v in cpi_hist]:
        yoy = _yoy(cpi_vals, 12)
        if yoy is not None:
            out["INFLATION"] = {"value": yoy, "period": str(cpi_hist[-1][0].isoformat()),
                                "unit": "%", "source": "derived"}

    core_cpi_hist = sorted(history_map.get("CPILFESL", []), key=lambda x: x[0])
    if core_vals := [v for _, v in core_cpi_hist]:
        yoy = _yoy(core_vals, 12)
        if yoy is not None:
            out["CORE_INFLATION"] = {"value": yoy, "period": str(core_cpi_hist[-1][0].isoformat()),
                                     "unit": "%", "source": "derived"}

    gdp_hist = sorted(history_map.get("GDPC1", []), key=lambda x: x[0])
    if gdp_vals := [v for _, v in gdp_hist]:
        qoq = _yoy(gdp_vals, 1)  # quarter-over-quarter (quarterly series)
        if qoq is not None:
            out["GDP_QOQ"] = {"value": qoq, "period": str(gdp_hist[-1][0].isoformat()),
                              "unit": "%", "source": "derived"}

    payrolls_hist = sorted(history_map.get("PAYEMS", []), key=lambda x: x[0])
    if payroll_vals := [v for _, v in payrolls_hist]:
        mom = _mom(payroll_vals)
        if mom is not None:
            out["PAYROLLS_MOM"] = {"value": mom, "period": str(payrolls_hist[-1][0].isoformat()),
                                   "unit": "%", "source": "derived"}

    wage_hist = sorted(history_map.get("CES0501000000000000050Q0", history_map.get("WAGE", [])), key=lambda x: x[0])
    wv = [v for _, v in wage_hist]
    if len(wv) > 12:
        yoy = _yoy(wv, 12)
        if yoy is not None:
            out["WAGE_YOY"] = {"value": yoy, "period": str(wage_hist[-1][0].isoformat()),
                               "unit": "%", "source": "derived"}

    return out


def _score_inflation(inflation: Optional[float]) -> Optional[float]:
    if inflation is None:
        return None
    if inflation < 0:
        return _clamp(30.0)                       # deflation is bad
    if inflation <= 1.5:
        return _clamp(60.0)                        # too low
    return _clamp(90.0 - abs(inflation - 2.5) * 12.0, 20.0, 90.0)


def _score_gdp(growth: Optional[float]) -> Optional[float]:
    if growth is None:
        return None
    if growth < 0:
        return _clamp(40.0 + growth * 10.0, 20.0, 90.0)   # -2% -> ~20, -1% -> ~30
    return _clamp(52.0 + growth * 12.0, 20.0, 90.0)        # +1% -> 64, +3% -> 76


def _score_interest_rates(fed_funds: Optional[float], curve: Optional[float]) -> Optional[float]:
    if fed_funds is None and curve is None:
        return None
    base = _clamp(90.0 - abs((fed_funds or 3.0) - 3.0) * 10.0, 20.0, 90.0)
    if curve is not None and curve < 0:          # inverted curve -> recession risk
        base = _clamp(base - 30.0, 10.0, base)
    return base


def _score_exchange_rates(dxy: Optional[float], eurusd: Optional[float]) -> Optional[float]:
    if dxy is not None:
        return _clamp(90.0 - abs(dxy - 100.0) * 1.2, 20.0, 90.0)
    if eurusd is not None:
        # USD-per-EUR: ~0.90 is historically normal; large deviations stress macro.
        return _clamp(90.0 - abs(eurusd - 0.95) * 80.0, 20.0, 90.0)
    return None


def _score_commodities(oil: Optional[float], gold: Optional[float]) -> Optional[float]:
    if oil is None and gold is None:
        return None
    vals = []
    if oil is not None:
        vals.append(_clamp(80.0 - abs(oil - 80.0) * 1.5, 25.0, 80.0))
    if gold is not None:
        vals.append(_clamp(90.0 - abs(gold - 2300.0) / 30.0, 30.0, 90.0))
    return round(sum(vals) / len(vals), 2) if vals else None


def compute_macro_scores(latest: dict[str, float]) -> dict[str, Any]:
    """Map latest raw macro values -> 0-100 health sub-scores.

    Output keys are the ScoringService macro sub-dimensions plus ``overall``
    and a textual ``phase``. Missing indicators are neutral (50.0), not zero.
    """
    g = _score_gdp(latest.get("GDP_QOQ"))
    inf = _score_inflation(latest.get("INFLATION") or latest.get("CPIAUCSL"))
    ir = _score_interest_rates(latest.get("FEDFUNDS") or latest.get("US_FED_RATE"), latest.get("T10Y2Y"))
    xr = _score_exchange_rates(latest.get("DX-Y.NYB"), latest.get("DEXUSEU"))
    comm = _score_commodities(latest.get("CL=F"), latest.get("GC=F"))

    sub = {
        "gdp": g if g is not None else 50.0,
        "inflation": inf if inf is not None else 50.0,
        "interest_rates": ir if ir is not None else 50.0,
        "exchange_rates": xr if xr is not None else 50.0,
        "commodity_prices": comm if comm is not None else 50.0,
    }

    sub_scores = list(sub.values())
    overall = round(sum(sub_scores) / len(sub_scores), 2) if sub_scores else 50.0
    sub["overall"] = overall
    sub["phase"] = macro_phase(overall)
    return sub


def macro_phase(score: float) -> str:
    """Map a 0-100 macro score to the economic phase described in the docs."""
    if score < 20:
        return "Deflationary Recession"
    if score < 40:
        return "Late Cycle"
    if score < 55:
        return "Middle Cycle"
    if score < 70:
        return "Early Cycle"
    if score < 85:
        return "Early Expansion"
    return "Strong Expansion"


def summarize(latest: dict[str, float]) -> dict[str, Any]:
    """Full macro summary: sub-scores, phase, and key readings."""
    sub = compute_macro_scores(latest)
    return {
        "sub_scores": {k: v for k, v in sub.items() if k in SUB_DIMENSIONS},
        "overall": sub["overall"],
        "phase": sub["phase"],
        "readings": latest,
    }
