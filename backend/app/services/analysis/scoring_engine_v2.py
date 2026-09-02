"""
scoring_engine_v2 — Cross-sectional percentile-rank z-score scoring.

Why a new engine
----------------
The legacy `scoring_service` uses absolute thresholds (e.g. P/E < 10 = 90,
P/E < 18 = 75) that don't reflect today's market. It also only writes the
top-level 6D dimension scores to `score_history`; L2/L3/L4 sub-dimension,
aspect, and sub-aspect scores are never persisted, so the dashboard has to
fall back to a regex-based rollup.

This engine:
  * Transforms every raw metric with a **percentile-rank → z-score** over
    the same market (NASDAQ) on the same day. Calibrated to ~N(50, 15).
  * Aggregates L4 → L3 → L2 → L1 → overall using **coverage-weighted**
    means, where missing data is neutral (50), not zero.
  * Returns the full hierarchy so the caller can persist all four levels
    to `raw_performance_scores` + `score_history` in one transaction.

The transform is direction-aware (lower-is-better for P/E, volatility,
drawdown, etc.) and is stable for any market size ≥ 30 assets.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

try:
    from scipy.stats import norm, rankdata
    _HAS_SCIPY = True
except ImportError:  # pragma: no cover
    _HAS_SCIPY = False


# ---------------------------------------------------------------------------
# Metric universe — single source of truth for the hierarchy
# ---------------------------------------------------------------------------
# Each entry: (dim, sub_dim, aspect, sub_aspect, db_field, lower_is_better)
METRIC_UNIVERSE: List[Tuple[str, str, str, str, str, bool]] = [
    # fundamental
    ("fundamental", "valuation",       "pe_band",        "pe_ratio",     "pe_ratio",     True),
    ("fundamental", "valuation",       "pe_band",        "pb_ratio",     "pb_ratio",     True),
    ("fundamental", "valuation",       "pe_band",        "ev_ebitda",    "ev_ebitda",    True),
    ("fundamental", "profitability",   "roe_block",      "roe",          "roe",          False),
    ("fundamental", "profitability",   "roe_block",      "roa",          "roa",          False),
    ("fundamental", "profitability",   "roe_block",      "profit_margin","profit_margin",False),
    ("fundamental", "growth",          "growth_block",   "revenue_growth","revenue_growth",False),
    ("fundamental", "growth",          "growth_block",   "eps_growth",   "eps_growth",   False),
    ("fundamental", "liquidity",       "liquidity_block","current_ratio","current_ratio",False),
    ("fundamental", "liquidity",       "liquidity_block","quick_ratio",  "quick_ratio",  False),
    # technical
    ("technical",   "trend",           "trend_block",    "macd_histogram","macd_histogram",False),
    ("technical",   "trend",           "trend_block",    "bb_width",     "bb_width",     False),
    ("technical",   "momentum",        "momentum_block", "rsi_14",       "rsi_14",       False),
    ("technical",   "volatility",      "volatility_block","realized_vol_30d","realized_vol_30d", True),
    ("technical",   "volatility",      "volatility_block","atr_value",   "atr_value",    True),
    ("technical",   "volume",          "volume_block",   "volume_ratio", "volume_ratio", False),
    # sentiment
    ("sentiment",   "news",            "news_block",     "news_sentiment_avg","news_sentiment_avg", False),
    ("sentiment",   "news",            "news_block",     "news_volume",  "news_volume",  False),
    # risk
    ("risk",        "market_risk",     "risk_block",     "volatility_z", "volatility_z", True),
    ("risk",        "market_risk",     "risk_block",     "max_drawdown", "max_drawdown", True),
    # macro
    ("macro",       "rates",           "rates_block",    "treasury_yield_10y","treasury_yield_10y", True),
    ("macro",       "rates",           "rates_block",    "dollar_index", "dollar_index", True),
    ("macro",       "commodity",       "commodity_block","oil_price",    "oil_price",    True),
    ("macro",       "commodity",       "commodity_block","gold_price",   "gold_price",   True),
    # ai
    ("ai",          "ml_signal",       "ml_block",       "expected_return","expected_return", False),
    ("ai",          "ml_signal",       "ml_block",       "confidence",   "confidence",   False),
]


DIMENSION_WEIGHTS: Dict[str, float] = {
    "fundamental": 0.25,
    "technical":   0.20,
    "sentiment":   0.15,
    "risk":        0.20,
    "macro":       0.10,
    "ai":          0.10,
}


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------
@dataclass
class HierarchicalScore:
    sub_aspect_scores: Dict[str, float] = field(default_factory=dict)
    aspect_scores:     Dict[str, float] = field(default_factory=dict)
    sub_dimension_scores: Dict[str, float] = field(default_factory=dict)
    dimension_scores:  Dict[str, float] = field(default_factory=dict)
    overall_score:     float = 50.0
    coverage:          float = 0.0  # fraction of L4 metrics present


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------
def _percentile_to_score(values: List[Optional[float]],
                          lower_is_better: bool) -> List[Optional[float]]:
    """Cross-sectional percentile → z-score → rescale to [0, 100].

    Missing inputs (None) are passed through as None so they don't
    influence ranks but can still be skipped at aggregation time.
    """
    present = [(i, v) for i, v in enumerate(values) if v is not None and not (isinstance(v, float) and math.isnan(v))]
    n = len(present)
    if n < 2:
        return [None] * len(values)

    sorted_vals = sorted(v for _, v in present)
    # Map each value → its rank (1..n) for ties use the average rank
    rank_of: Dict[int, float] = {}
    i = 0
    while i < n:
        j = i
        while j + 1 < n and sorted_vals[j + 1] == sorted_vals[i]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0  # midrank, 1-based
        for k in range(i, j + 1):
            rank_of[sorted_vals[k]] = avg_rank
        i = j + 1

    out: List[Optional[float]] = [None] * len(values)
    for idx, v in present:
        p = (rank_of[v] - 0.5) / n  # (0, 1)
        if lower_is_better:
            p = 1.0 - p
        # Clip to avoid inf at exact 0 / 1
        p = min(max(p, 1e-6), 1.0 - 1e-6)
        if _HAS_SCIPY:
            z = float(norm.ppf(p))
        else:
            # Rational approximation of the inverse normal CDF
            # (Abramowitz & Stegun 26.2.23) — good to ~4.5 decimals
            t = math.sqrt(-2.0 * math.log(min(p, 1.0 - p)))
            c0, c1, c2 = 2.515517, 0.802853, 0.010328
            d1, d2, d3 = 1.432788, 0.189269, 0.001308
            z = t - (c0 + c1 * t + c2 * t * t) / (1.0 + d1 * t + d2 * t * t + d3 * t * t * t)
            if p < 0.5:
                z = -z
        out[idx] = max(0.0, min(100.0, 50.0 + 15.0 * z))
    return out


def _weighted_mean(values: Dict[str, Optional[float]],
                   weights: Optional[Dict[str, float]] = None) -> float:
    """Coverage-weighted mean. Missing entries are skipped, not zero-filled."""
    items = [(k, v) for k, v in values.items() if v is not None]
    if not items:
        return 50.0  # neutral default — never 0
    if weights is None:
        return sum(v for _, v in items) / len(items)
    w = [weights.get(k, 1.0) for k, _ in items]
    s = sum(w)
    if s <= 0:
        return sum(v for _, v in items) / len(items)
    return sum(v * wi for (_, v), wi in zip(items, w)) / s


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def score_market(asset_metrics: Dict[str, Dict[str, Optional[float]]]
                 ) -> Dict[str, HierarchicalScore]:
    """Score every asset in a market using cross-sectional ranks.

    Args:
        asset_metrics: {asset_id: {db_field: value or None, ...}, ...}

    Returns:
        {asset_id: HierarchicalScore}
    """
    if not asset_metrics:
        return {}

    # Group every (db_field → list of values across assets)
    by_field: Dict[str, List[Optional[float]]] = {db: [] for *_, db, _ in METRIC_UNIVERSE}
    asset_ids = list(asset_metrics.keys())
    for aid in asset_ids:
        m = asset_metrics[aid]
        for *_, db_field, _ in METRIC_UNIVERSE:
            by_field[db_field].append(m.get(db_field))

    # Per-field rank transform
    transformed: Dict[str, List[Optional[float]]] = {}
    for *_, db_field, lower_better in METRIC_UNIVERSE:
        transformed[db_field] = _percentile_to_score(by_field[db_field], lower_better)

    # Build per-asset L4 scores
    results: Dict[str, HierarchicalScore] = {}
    for idx, aid in enumerate(asset_ids):
        hs = HierarchicalScore()
        for dim, sub, asp, sa, db_field, _ in METRIC_UNIVERSE:
            v = transformed[db_field][idx]
            hs.sub_aspect_scores[sa] = v if v is not None else 50.0
        # Coverage = fraction of metrics that had a real value
        real = sum(1 for v in asset_metrics[aid].values() if v is not None)
        hs.coverage = real / max(1, len(by_field))

        # L3: aggregate over the L4s in each aspect
        aspect_groups: Dict[str, List[float]] = {}
        for *_, asp, sa, _, _ in METRIC_UNIVERSE:
            aspect_groups.setdefault(asp, []).append(hs.sub_aspect_scores[sa])
        for asp, vals in aspect_groups.items():
            hs.aspect_scores[asp] = round(sum(vals) / len(vals), 2)

        # L2: aggregate aspects in each sub-dim, weighted by aspect count
        sub_groups: Dict[str, Dict[str, float]] = {}
        for dim, sub, asp, sa, _, _ in METRIC_UNIVERSE:
            sub_groups.setdefault(sub, {})[asp] = hs.aspect_scores[asp]
        for sub, asp_map in sub_groups.items():
            hs.sub_dimension_scores[sub] = round(_weighted_mean(asp_map), 2)

        # L1: aggregate sub-dims in each dimension
        dim_groups: Dict[str, Dict[str, float]] = {}
        for dim, sub, *_ in METRIC_UNIVERSE:
            dim_groups.setdefault(dim, {})[sub] = hs.sub_dimension_scores[sub]
        for dim, sub_map in dim_groups.items():
            hs.dimension_scores[dim] = round(_weighted_mean(sub_map), 2)

        # Overall: 6D weighted mean
        overall = sum(hs.dimension_scores[d] * w for d, w in DIMENSION_WEIGHTS.items())
        hs.overall_score = round(max(0.0, min(100.0, overall)), 2)

        results[aid] = hs

    return results


def grade(score: float) -> str:
    """Map 0-100 overall to a buy/hold/sell grade."""
    if score >= 80:
        return "A_STRONG_BUY"
    if score >= 65:
        return "B_BUY"
    if score >= 50:
        return "C_HOLD"
    if score >= 35:
        return "D_SELL"
    return "E_STRONG_SELL"
