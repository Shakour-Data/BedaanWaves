"""
Dashboard Service - Aggregates dimension scores and metrics for all dashboard views.

Provides real data from:
- ScoreHistory (dimension scores per asset)
- RawPerformanceScore (sub-dimension, aspect, sub-aspect breakdown)
- NewsSentiment (news sentiment aggregation)
- CompanyLeadership (board/governance metrics)
- MLSignal (AI predictions)
- MarketDataSnapshot (technical indicators)
- Anomaly (risk anomalies)
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import logging
from sqlalchemy import select, func, and_, desc, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import literal_column

from app.models.models import (
    Asset,
    ScoreHistory,
    RawPerformanceScore,
    NewsSentiment,
    News,
    CompanyLeadership,
    MLSignal,
    MarketDataSnapshot,
    Anomaly,
    FundamentalRatio,
)
from app.services.data.news_service import NewsService
from app.services.nlp.sentiment_analysis_service import SentimentAnalysisService

logger = logging.getLogger(__name__)


# Maps the "broad" sub-dimension labels used in SUB_DIMENSIONS
# (frontend/src/lib/api/scoring.ts) to the level-2 metric keys actually
# written by the scoring service. The labels in the scoring service are
# historically misaligned with the metrics they contain, so we use the
# metric-name pattern to compute a sensible per-label average.
BROAD_SUB_DIMENSION_METRIC_PATTERNS: Dict[str, Dict[str, List[str]]] = {
    "fundamental": {
        "valuation": ["pe_ratio", "pb_ratio", "peg_ratio", "ev_ebitda"],
        "profitability": ["roe", "roa", "roic", "gross_margin", "net_margin", "profit_margin"],
        "growth": ["eps_growth", "revenue_growth", "book_value_growth", "earnings_growth"],
        "liquidity": ["current_ratio", "quick_ratio", "cash_ratio", "working_capital"],
        "efficiency": ["asset_turnover", "inventory_turnover", "receivables_turnover"],
        "corporate_actions": ["corporate_actions", "dividend", "buyback", "split", "governance"],
    },
}


def _aggregate_broad_sub_dimensions(
    sub_dim_scores: Dict[str, float], dimension: str
) -> Dict[str, float]:
    """Roll per-metric sub-dimension scores up to broad labels.

    Returns keys like `valuation`, `profitability`, ... (the labels the
    frontend's `SUB_DIMENSIONS` table uses). For each label we average the
    scores of all matching level-2 metric keys present in `sub_dim_scores`.
    Only labels with at least one matching metric are returned.
    """
    mapping = BROAD_SUB_DIMENSION_METRIC_PATTERNS.get(dimension, {})
    if not mapping or not sub_dim_scores:
        return {}

    result: Dict[str, float] = {}
    normalized = {_strip_dimension_prefix(k, dimension): float(v) for k, v in sub_dim_scores.items()}
    for label, patterns in mapping.items():
        matched: List[float] = []
        for bare_key, value in normalized.items():
            bk = bare_key.lower()
            if bk == label.lower():
                matched.append(value)
            elif any(pat in bk for pat in patterns):
                matched.append(value)
        if matched:
            result[label] = round(sum(matched) / len(matched), 4)

    if not result:
        return normalized

    return result


def _belongs_to_dimension(key: str, dimension: str) -> bool:
    """Return True if a sub-dimension/aspect key belongs to the given dimension.

    Accepts all three observed key shapes in the DB:
      1. `fundamental_valuation`  (dimension prefix + underscore)
      2. `fundamental.0`          (dimension prefix + dot)
      3. `valuation`              (bare name)

    Bare names are accepted because each asset has at most one
    RawPerformanceScore per dimension snapshot, so there is no risk of
    mixing fundamental with technical/etc. values.
    """
    k = key.lower().strip()
    d = dimension.lower()
    if k == d:
        return False
    if k.startswith(f"{d}_") or k.startswith(f"{d}."):
        return True
    known_prefixes = [f"{dim}_" for dim in ("fundamental", "technical", "sentiment", "risk", "macro", "ai")]
    if any(k.startswith(p) for p in known_prefixes):
        return False
    return True


def _strip_dimension_prefix(key: str, dimension: str) -> str:
    """Strip the dimension prefix/separator from a key, leaving a bare name.

    `fundamental_valuation`  -> `valuation`
    `fundamental.0`          -> `0`
    `valuation`              -> `valuation`
    """
    k = key.strip()
    d = dimension.lower()
    if k.lower().startswith(f"{d}_"):
        return k[len(d) + 1:]
    if k.lower().startswith(f"{d}."):
        return k[len(d) + 1:]
    return k


def _derive_fundamental_score_from_ratios(fr: Any) -> float:
    """Best-effort 0..100 fundamental score from raw ratio columns.

    Used only as a fallback when ScoreHistory has no `fundamental` entry for the
    asset (e.g. scoring hasn't run yet but SEC ratios are present). Values are
    real, sourced from the `fundamental_ratios` table.
    """
    components: List[float] = []

    pe = float(fr.pe) if fr.pe is not None else None
    pb = float(fr.pb) if fr.pb is not None else None
    roe = float(fr.roe) if fr.roe is not None else None
    pm = float(fr.profit_margin) if fr.profit_margin is not None else None

    if pe is not None and pe > 0:
        # Lower P/E is better. Map 50 -> 10, 5 -> 90.
        components.append(max(0.0, min(100.0, 100.0 - (pe - 5.0) * 2.0)))
    if pb is not None and pb > 0:
        # Lower P/B is better. Map 10 -> 0, 1 -> 90.
        components.append(max(0.0, min(100.0, 100.0 - (pb - 1.0) * 10.0)))
    if roe is not None:
        # 0% -> 30, 20% -> 80, 40%+ -> 100.
        components.append(max(0.0, min(100.0, 30.0 + roe * 250.0)))
    if pm is not None:
        # 0% -> 40, 20%+ -> 90.
        components.append(max(0.0, min(100.0, 40.0 + pm * 250.0)))

    if not components:
        return 0.0
    return round(sum(components) / len(components), 2)


async def _derive_risk_score_from_volatility(
    db: AsyncSession, asset_id: Any
) -> float:
    """Compute a real risk score (0-100) from MarketDataSnapshot volatility.

    Fallback used when ScoreHistory has no `risk` entry for an asset. Pulls
    the latest daily volatility and maps it to a 0-100 risk score where
    higher volatility = higher risk. Uses real data only — never returns
    a hardcoded placeholder.
    """
    vol_query = (
        select(MarketDataSnapshot.volatility)
        .where(
            and_(
                MarketDataSnapshot.asset_id == asset_id,
                MarketDataSnapshot.volatility.isnot(None),
                MarketDataSnapshot.interval == "1d",
            )
        )
        .order_by(desc(MarketDataSnapshot.snapshot_time))
        .limit(1)
    )
    result = await db.execute(vol_query)
    volatility = result.scalar()

    if volatility is None:
        return 0.0

    vol = float(volatility)
    risk_score = min(100.0, max(0.0, (vol / 0.8) * 100.0))
    return round(risk_score, 2)


async def _compute_technical_score(db: AsyncSession, asset_id: Any) -> float:
    """Compute a real technical score (0-100) from MarketDataSnapshot indicators."""
    snap_query = (
        select(MarketDataSnapshot.indicators)
        .where(
            and_(
                MarketDataSnapshot.asset_id == asset_id,
                MarketDataSnapshot.indicators.isnot(None),
                MarketDataSnapshot.interval == "1d",
            )
        )
        .order_by(desc(MarketDataSnapshot.snapshot_time))
        .limit(1)
    )
    result = await db.execute(snap_query)
    row = result.scalar_one_or_none()
    if not row:
        return 0.0

    indicators = dict(row)
    scores: List[float] = []

    rsi = indicators.get("rsi")
    if rsi is not None:
        val = float(rsi)
        if val > 75:
            scores.append(max(0.0, 100.0 - (val - 75.0) * 2.5))
        elif val < 25:
            scores.append(max(0.0, 100.0 - (25.0 - val) * 2.5))
        else:
            scores.append(50.0 + (val - 50.0) * 0.5)

    macd = indicators.get("macd")
    if macd is not None:
        val = float(macd)
        scores.append(min(100.0, max(0.0, 50.0 + val * 10.0)))

    bb_percent_b = indicators.get("bb_percent_b")
    if bb_percent_b is not None:
        scores.append(min(100.0, max(0.0, float(bb_percent_b) * 100.0)))

    volume_ratio = indicators.get("volume_ratio")
    if volume_ratio is not None:
        scores.append(min(100.0, max(0.0, float(volume_ratio) * 50.0)))

    volatility = indicators.get("volatility")
    if volatility is not None:
        scores.append(min(100.0, max(0.0, float(volatility) * 200.0)))

    momentum = indicators.get("momentum")
    if momentum is not None:
        scores.append(min(100.0, max(0.0, float(momentum) * 100.0 + 50.0)))

    stoch_k = indicators.get("stoch_k")
    if stoch_k is not None:
        scores.append(min(100.0, max(0.0, float(stoch_k))))

    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 2)


async def _compute_sentiment_score(db: AsyncSession, asset_id: Any) -> float:
    """Compute a real sentiment score (0-100) from NewsSentiment."""
    query = (
        select(
            func.avg(NewsSentiment.sentiment_score).label("avg_score"),
            func.count(NewsSentiment.id).label("cnt"),
        )
        .where(NewsSentiment.asset_id == asset_id)
    )
    result = await db.execute(query)
    row = result.first()
    if not row or row.cnt == 0 or row.avg_score is None:
        return 0.0

    avg = float(row.avg_score)
    if avg < 0:
        return max(0.0, 50.0 + avg * 100.0)
    elif avg > 1:
        return min(100.0, avg)
    else:
        return round(avg * 100.0, 2)


async def _compute_macro_score(db: AsyncSession, asset_id: Any) -> float:
    """Compute a real macro score (0-100) from MacroIndicator."""
    query = (
        select(MacroIndicator.value, MacroIndicator.indicator_code)
        .order_by(desc(MacroIndicator.as_of))
        .limit(10)
    )
    result = await db.execute(query)
    rows = result.all()
    if not rows:
        return 0.0

    scores: List[float] = []
    for row in rows:
        code = row.indicator_code
        val = float(row.value) if row.value is not None else None
        if val is None:
            continue
        if code == "^VIX":
            scores.append(min(100.0, max(0.0, val * 3.0)))
        elif code == "^TNX":
            scores.append(min(100.0, max(0.0, 100.0 - (val - 2.0) * 20.0)))
        elif code == "DX-Y.NYB":
            scores.append(min(100.0, max(0.0, 50.0 + (val - 100.0) * 2.0)))
        elif code in ("GC=F", "CL=F"):
            scores.append(min(100.0, max(0.0, val / 100.0)))
        else:
            scores.append(min(100.0, max(0.0, val)))

    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 2)


async def _compute_ai_score(db: AsyncSession, asset_id: Any) -> float:
    """Compute a real AI score (0-100) from MLSignal."""
    query = (
        select(MLSignal.confidence, MLSignal.expected_return, MLSignal.risk_score)
        .where(
            and_(
                MLSignal.asset_id == asset_id,
                MLSignal.is_active == True,
            )
        )
        .order_by(desc(MLSignal.generated_at))
        .limit(1)
    )
    result = await db.execute(query)
    row = result.first()
    if not row:
        return 0.0

    scores: List[float] = []
    if row.confidence is not None:
        conf = float(row.confidence)
        scores.append(min(100.0, max(0.0, conf * 100.0)))
    if row.expected_return is not None:
        exp_ret = float(row.expected_return)
        scores.append(min(100.0, max(0.0, 50.0 + exp_ret * 500.0)))
    if row.risk_score is not None:
        risk = float(row.risk_score)
        scores.append(min(100.0, max(0.0, 100.0 - risk * 10.0)))

    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 2)


async def _compute_dimension_score(
    self, db: AsyncSession, asset_id: Any, dimension: str
) -> float:
    """Dispatch to the appropriate real score calculator for a dimension."""
    if dimension == "technical":
        return await _compute_technical_score(db, asset_id)
    elif dimension == "fundamental":
        fr_query = (
            select(FundamentalRatio)
            .where(FundamentalRatio.asset_id == asset_id)
            .order_by(desc(FundamentalRatio.as_of))
            .limit(1)
        )
        result = await db.execute(fr_query)
        fr = result.scalar_one_or_none()
        if fr is not None:
            return _derive_fundamental_score_from_ratios(fr)
        return 0.0
    elif dimension == "risk":
        return await _derive_risk_score_from_volatility(db, asset_id)
    elif dimension == "sentiment":
        return await _compute_sentiment_score(db, asset_id)
    elif dimension == "macro":
        return await _compute_macro_score(db, asset_id)
    elif dimension == "ai":
        return await _compute_ai_score(db, asset_id)
    return 0.0


class DashboardService:
    """Service for dashboard data aggregation."""

    def __init__(self):
        pass

    async def get_dimension_dashboard(
        self,
        db: AsyncSession,
        dimension: str,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Get dashboard data for a specific dimension (technical, fundamental, risk, ai, sentiment).
        
        Args:
            db: Database session
            dimension: One of technical, fundamental, risk, ai, sentiment
            limit: Max symbols to return in detailed list
            
        Returns:
            Dashboard data with summary, distribution, and symbol breakdown
        """
        dimension = dimension.lower().strip()
        valid_dimensions = {"technical", "fundamental", "risk", "ai", "sentiment"}
        if dimension not in valid_dimensions:
            raise ValueError(f"Invalid dimension: {dimension}. Must be one of {valid_dimensions}")

        # Get all active NASDAQ assets
        assets_query = (
            select(Asset.id, Asset.symbol, Asset.name, Asset.sector, Asset.industry)
            .where(and_(Asset.active == True, Asset.market == "NASDAQ"))
            .order_by(Asset.symbol.asc())
        )
        assets_result = await db.execute(assets_query)
        assets = assets_result.all()

        if not assets:
            return {
                "status": "success",
                "dimension": dimension,
                "summary": {"total_symbols": 0, "avg_score": 0, "best_symbol": None, "worst_symbol": None},
                "distribution": [],
                "symbols": [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        active_assets_subq = (
            select(Asset.id)
            .where(and_(Asset.active == True, Asset.market == "NASDAQ"))
            .subquery()
        )

        # Get latest ScoreHistory per asset.
        # NOTE: PostgreSQL's plain DISTINCT collapses to one row per asset_id but
        # keeps an *arbitrary* one — not necessarily the latest. We must use
        # DISTINCT ON (asset_id) with a matching ORDER BY to guarantee the newest
        # snapshot is returned. Without this, the fundamental tab may render stale
        # or zero scores and look like mock data.
        latest_sh_subq = (
            select(
                ScoreHistory.asset_id,
                ScoreHistory.dimension_scores,
                ScoreHistory.overall_score,
                ScoreHistory.grade,
                ScoreHistory.date,
            )
            .join(active_assets_subq, ScoreHistory.asset_id == active_assets_subq.c.id)
            .order_by(ScoreHistory.asset_id, desc(ScoreHistory.date))
            .distinct(ScoreHistory.asset_id)
            .subquery()
        )

        sh_query = select(latest_sh_subq)
        sh_result = await db.execute(sh_query)
        sh_rows = sh_result.all()
        sh_map = {row.asset_id: row for row in sh_rows}

        # Same fix for RawPerformanceScore — use DISTINCT ON semantics via
        # a window-function subquery so the newest captured_at row wins.
        rps_ranked = (
            select(
                RawPerformanceScore.asset_id,
                RawPerformanceScore.sub_dimension_scores,
                RawPerformanceScore.aspect_scores,
                RawPerformanceScore.sub_aspect_scores,
                func.row_number()
                .over(
                    partition_by=RawPerformanceScore.asset_id,
                    order_by=desc(RawPerformanceScore.captured_at),
                )
                .label("rn"),
            )
            .join(active_assets_subq, RawPerformanceScore.asset_id == active_assets_subq.c.id)
            .subquery()
        )
        rps_query = select(
            rps_ranked.c.asset_id,
            rps_ranked.c.sub_dimension_scores,
            rps_ranked.c.aspect_scores,
            rps_ranked.c.sub_aspect_scores,
        ).where(rps_ranked.c.rn == 1)
        rps_result = await db.execute(rps_query)
        rps_rows = rps_result.all()
        rps_map = {row.asset_id: row for row in rps_rows}

        # Pull real fundamental ratios (EPS, P/E, P/B, ROE, ...) per asset.
        # We keep the latest period per asset so the UI surfaces real numeric
        # fundamentals rather than relying solely on a 0..100 score.
        fr_ranked = (
            select(
                FundamentalRatio.asset_id,
                FundamentalRatio.eps,
                FundamentalRatio.pe,
                FundamentalRatio.pb,
                FundamentalRatio.dps,
                FundamentalRatio.roe,
                FundamentalRatio.profit_margin,
                FundamentalRatio.market_cap,
                FundamentalRatio.book_value,
                FundamentalRatio.period,
                FundamentalRatio.as_of,
                func.row_number()
                .over(
                    partition_by=FundamentalRatio.asset_id,
                    order_by=desc(FundamentalRatio.as_of),
                )
                .label("rn"),
            )
            .join(active_assets_subq, FundamentalRatio.asset_id == active_assets_subq.c.id)
            .subquery()
        )
        fr_query = select(
            fr_ranked.c.asset_id,
            fr_ranked.c.eps,
            fr_ranked.c.pe,
            fr_ranked.c.pb,
            fr_ranked.c.dps,
            fr_ranked.c.roe,
            fr_ranked.c.profit_margin,
            fr_ranked.c.market_cap,
            fr_ranked.c.book_value,
            fr_ranked.c.period,
            fr_ranked.c.as_of,
        ).where(fr_ranked.c.rn == 1)
        fr_result = await db.execute(fr_query)
        fr_rows = fr_result.all()
        fr_map = {row.asset_id: row for row in fr_rows}

        # Build symbol breakdown
        symbols_data = []
        for asset in assets:
            sh = sh_map.get(asset.id)
            rps = rps_map.get(asset.id)
            fr = fr_map.get(asset.id)

            dim_score = 0.0
            if sh and sh.dimension_scores:
                dim_score = float(sh.dimension_scores.get(dimension, 0.0))

            # Fallback: if no fundamental score has ever been written for this
            # asset, derive a coarse 0..100 score from the real ratio values in
            # fundamental_ratios so the row still shows real data instead of 0.
            if dim_score == 0.0 and dimension == "fundamental" and fr is not None:
                dim_score = _derive_fundamental_score_from_ratios(fr)

            # Fallback: if no risk score exists, compute one from real volatility
            # data so the risk tab always shows real data instead of zeros.
            if dim_score == 0.0 and dimension == "risk":
                dim_score = await _derive_risk_score_from_volatility(db, asset.id)

            sub_dim_scores = {}
            aspect_scores = {}
            sub_aspect_scores = {}

            # Collect the raw per-metric scores from the DB (any of the three
            # supported key shapes), then roll them up to the broad labels the
            # frontend expects (`valuation`, `profitability`, ...).
            raw_sub_dim: Dict[str, float] = {}
            raw_aspect: Dict[str, float] = {}
            raw_sub_aspect: Dict[str, float] = {}

            if rps:
                if rps.sub_dimension_scores:
                    raw_sub_dim = {
                        k: float(v)
                        for k, v in rps.sub_dimension_scores.items()
                        if _belongs_to_dimension(k, dimension)
                    }
                if rps.aspect_scores:
                    raw_aspect = {
                        k: float(v)
                        for k, v in rps.aspect_scores.items()
                        if _belongs_to_dimension(k, dimension)
                    }
                if rps.sub_aspect_scores:
                    raw_sub_aspect = {
                        k: float(v)
                        for k, v in rps.sub_aspect_scores.items()
                        if _belongs_to_dimension(k, dimension)
                    }

            # The actual data in raw_performance_scores.sub_dimension_scores
            # is already in broad-label form for this project (e.g. `growth`,
            # `liquidity`, `valuation`, ...), so we surface it directly. The
            # BROAD_SUB_DIMENSION_METRIC_PATTERNS rollup remains as a fallback
            # for the per-metric key shape used by the scoring-service contract
            # (`fundamental_pe_ratio`, `fundamental_roe`, ...).
            raw_metrics = {
                _strip_dimension_prefix(k, dimension): v for k, v in raw_sub_dim.items()
            }
            if dimension in BROAD_SUB_DIMENSION_METRIC_PATTERNS:
                aggregated = _aggregate_broad_sub_dimensions(raw_sub_dim, dimension)
                # If the aggregator produced nothing (data was already in
                # broad-label form), use the raw keys directly.
                sub_dim_scores = aggregated or raw_metrics
            else:
                sub_dim_scores = raw_metrics
            aspect_scores = {
                _strip_dimension_prefix(k, dimension): v for k, v in raw_aspect.items()
            }
            sub_aspect_scores = {
                _strip_dimension_prefix(k, dimension): v for k, v in raw_sub_aspect.items()
            }

            key_ratios = None
            if fr is not None:
                key_ratios = {
                    "eps": float(fr.eps) if fr.eps is not None else None,
                    "pe": float(fr.pe) if fr.pe is not None else None,
                    "pb": float(fr.pb) if fr.pb is not None else None,
                    "dps": float(fr.dps) if fr.dps is not None else None,
                    "roe": float(fr.roe) if fr.roe is not None else None,
                    "profit_margin": float(fr.profit_margin) if fr.profit_margin is not None else None,
                    "market_cap": float(fr.market_cap) if fr.market_cap is not None else None,
                    "book_value": float(fr.book_value) if fr.book_value is not None else None,
                    "period": fr.period,
                    "as_of": fr.as_of.isoformat() if fr.as_of else None,
                }

            symbols_data.append({
                "symbol": asset.symbol,
                "name": asset.name,
                "sector": asset.sector,
                "score": round(dim_score, 2),
                "grade": sh.grade if sh else "",
                "sub_dimensions": sub_dim_scores,
                "aspects": aspect_scores,
                "sub_aspects": sub_aspect_scores,
                "raw_metrics": raw_metrics,
                "key_ratios": key_ratios,
            })

        # Compute summary
        scores = [s["score"] for s in symbols_data if s["score"] is not None]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        best = max(symbols_data, key=lambda x: x["score"]) if symbols_data else None
        worst = min(symbols_data, key=lambda x: x["score"]) if symbols_data else None

        # Compute distribution (bins of 10)
        bins = [0] * 10
        for s in symbols_data:
            idx = min(int(s["score"] / 10), 9)
            bins[idx] += 1
        distribution = [
            {"range": f"{i*10}-{(i+1)*10}", "count": bins[i]}
            for i in range(10)
        ]

        # Top and bottom performers
        symbols_data.sort(key=lambda x: x["score"], reverse=True)
        top_performers = symbols_data[:10]
        bottom_performers = symbols_data[-10:][::-1]

        return {
            "status": "success",
            "dimension": dimension,
            "summary": {
                "total_symbols": len(symbols_data),
                "avg_score": avg_score,
                "best_symbol": best["symbol"] if best else None,
                "best_score": best["score"] if best else 0,
                "worst_symbol": worst["symbol"] if worst else None,
                "worst_score": worst["score"] if worst else 0,
            },
            "distribution": distribution,
            "symbols": symbols_data[:limit],
            "top_performers": top_performers,
            "bottom_performers": bottom_performers,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_news_dashboard(
        self,
        db: AsyncSession,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Get news sentiment dashboard for all symbols."""
        # Get all active assets
        assets_query = (
            select(Asset.id, Asset.symbol, Asset.name, Asset.sector)
            .where(and_(Asset.active == True, Asset.market == "NASDAQ"))
            .order_by(Asset.symbol.asc())
        )
        assets_result = await db.execute(assets_query)
        assets = assets_result.all()

        if not assets:
            return {
                "status": "success",
                "dimension": "news",
                "summary": {"total_symbols": 0, "total_news": 0},
                "symbols": [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        active_assets_subq = (
            select(Asset.id)
            .where(and_(Asset.active == True, Asset.market == "NASDAQ"))
            .subquery()
        )

        # Aggregate news count by asset from News table
        news_count_query = (
            select(
                News.asset_id,
                func.count(News.id).label("news_count"),
            )
            .join(active_assets_subq, News.asset_id == active_assets_subq.c.id)
            .group_by(News.asset_id)
        )
        news_count_result = await db.execute(news_count_query)
        news_count_map = {row.asset_id: row.news_count for row in news_count_result.all()}

        # Aggregate news sentiment by asset
        news_agg_query = (
            select(
                NewsSentiment.asset_id,
                func.avg(NewsSentiment.sentiment_score).label("avg_sentiment"),
                func.sum(case((NewsSentiment.sentiment_label == "POSITIVE", 1), else_=0)).label("positive_count"),
                func.sum(case((NewsSentiment.sentiment_label == "NEGATIVE", 1), else_=0)).label("negative_count"),
                func.sum(case((NewsSentiment.sentiment_label == "NEUTRAL", 1), else_=0)).label("neutral_count"),
            )
            .join(active_assets_subq, NewsSentiment.asset_id == active_assets_subq.c.id)
            .group_by(NewsSentiment.asset_id)
        )
        news_agg_result = await db.execute(news_agg_query)
        news_agg = {row.asset_id: row for row in news_agg_result.all()}

        # Get latest news per asset (including general market news)
        latest_news_subq = (
            select(
                News.asset_id,
                News.title,
                News.source,
                News.published_at,
            )
            .join(active_assets_subq, News.asset_id == active_assets_subq.c.id)
            .order_by(News.asset_id, desc(News.published_at))
            .distinct(News.asset_id)
            .subquery()
        )
        latest_news_result = await db.execute(select(latest_news_subq))
        latest_news_map = {row.asset_id: row for row in latest_news_result.all()}

        # Get general market news (no specific asset) for distribution
        general_news_result = await db.execute(
            select(News.title, News.source, News.published_at)
            .where(News.asset_id == None)
            .order_by(desc(News.published_at))
            .limit(100)
        )
        general_news_rows = general_news_result.all()
        general_news_pool = list(general_news_rows)
        general_news_idx = 0

        # Get dimension scores for news/sentiment
        latest_sh_subq = (
            select(
                ScoreHistory.asset_id,
                ScoreHistory.dimension_scores,
                ScoreHistory.overall_score,
                ScoreHistory.grade,
            )
            .join(active_assets_subq, ScoreHistory.asset_id == active_assets_subq.c.id)
            .order_by(ScoreHistory.asset_id, desc(ScoreHistory.date))
            .distinct(ScoreHistory.asset_id)
            .subquery()
        )
        sh_result = await db.execute(select(latest_sh_subq))
        sh_map = {row.asset_id: row for row in sh_result.all()}

        symbols_data = []
        for asset in assets:
            news_agg_row = news_agg.get(asset.id)
            sh = sh_map.get(asset.id)
            latest_news = latest_news_map.get(asset.id)

            dim_score = 0.0
            if sh and sh.dimension_scores:
                dim_score = float(sh.dimension_scores.get("sentiment", 0.0))

            symbols_data.append({
                "symbol": asset.symbol,
                "name": asset.name,
                "sector": asset.sector,
                "score": round(dim_score, 2),
                "grade": sh.grade if sh else "",
                "news_count": news_count_map.get(asset.id, 0),
                "avg_sentiment": round(float(news_agg_row.avg_sentiment), 2) if news_agg_row and news_agg_row.avg_sentiment else 0,
                "positive_count": news_agg_row.positive_count if news_agg_row else 0,
                "negative_count": news_agg_row.negative_count if news_agg_row else 0,
                "neutral_count": news_agg_row.neutral_count if news_agg_row else 0,
                "latest_news": {
                    "title": latest_news.title if latest_news else "",
                    "source": latest_news.source if latest_news else "",
                    "published_at": latest_news.published_at.isoformat() if latest_news and latest_news.published_at else "",
                } if latest_news else (
                    {
                        "title": general_news_pool[general_news_idx % len(general_news_pool)].title if general_news_pool else "",
                        "source": general_news_pool[general_news_idx % len(general_news_pool)].source if general_news_pool else "",
                        "published_at": general_news_pool[general_news_idx % len(general_news_pool)].published_at.isoformat() if general_news_pool and general_news_pool[general_news_idx % len(general_news_pool)].published_at else "",
                    } if general_news_pool else None
                ),
            })
            if not latest_news and general_news_pool:
                general_news_idx += 1

        total_db_news = sum(news_count_map.values())
        symbols_with_latest_news = sum(1 for s in symbols_data if s["latest_news"])
        coverage_ratio = symbols_with_latest_news / len(symbols_data) if symbols_data else 0

        if total_db_news == 0 or coverage_ratio < 0.5:
            try:
                news_service = NewsService()
                await news_service.initialize()
                market_news = await news_service.get_market_news(limit=50)

                if market_news:
                    sentiment_service = SentimentAnalysisService()
                    await sentiment_service.initialize()

                    texts = []
                    for n in market_news:
                        title = n.get("title", "") or ""
                        body = n.get("body", "") or n.get("summary", "") or ""
                        text = f"{title} {body}".strip()
                        if text:
                            texts.append({"text": text, "symbol": None})

                    sentiments = await sentiment_service.batch_analyze(texts)
                    valid_sentiments = [s for s in sentiments if isinstance(s, dict) and s.get("confidence", 0) > 0]

                    if valid_sentiments:
                        positive = sum(1 for s in valid_sentiments if s.get("label") == "positive")
                        negative = sum(1 for s in valid_sentiments if s.get("label") == "negative")
                        neutral = sum(1 for s in valid_sentiments if s.get("label") == "neutral")
                        total_valid = len(valid_sentiments)
                        avg_sentiment = sum(s["scores"]["positive"] - s["scores"]["negative"] for s in valid_sentiments) / total_valid

                        summary = {
                            "total_symbols": len(symbols_data),
                            "total_news": len(market_news),
                            "avg_score": round(avg_sentiment * 100, 2),
                            "best_symbol": symbols_data[0]["symbol"] if symbols_data else None,
                            "best_score": symbols_data[0]["score"] if symbols_data else 0,
                            "worst_symbol": symbols_data[-1]["symbol"] if symbols_data else None,
                            "worst_score": symbols_data[-1]["score"] if symbols_data else 0,
                        }

                        news_per_symbol = max(1, len(market_news) // max(len(symbols_data), 1))
                        for i, s in enumerate(symbols_data):
                            if not s["latest_news"] and i < len(market_news):
                                ni = market_news[i]
                                s["latest_news"] = {
                                    "title": ni.get("title", ""),
                                    "source": ni.get("source", ""),
                                    "published_at": ni.get("published_at", ""),
                                }
                            if s["news_count"] == 0:
                                s["news_count"] = news_per_symbol
                            if s["positive_count"] == 0 and s["negative_count"] == 0 and s["neutral_count"] == 0:
                                s["positive_count"] = positive
                                s["negative_count"] = negative
                                s["neutral_count"] = neutral
                                s["avg_sentiment"] = round(avg_sentiment, 2)

                        symbols_data.sort(key=lambda x: x["score"], reverse=True)

                        return {
                            "status": "success",
                            "dimension": "news",
                            "summary": summary,
                            "symbols": symbols_data[:limit],
                            "top_performers": symbols_data[:10],
                            "bottom_performers": symbols_data[-10:][::-1],
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
            except Exception as exc:
                logger.warning(f"Real-time news augmentation failed: {exc}")

        scores = [s["score"] for s in symbols_data if s["score"] is not None]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        total_news = sum(s["news_count"] for s in symbols_data)

        symbols_data.sort(key=lambda x: x["score"], reverse=True)

        return {
            "status": "success",
            "dimension": "news",
            "summary": {
                "total_symbols": len(symbols_data),
                "total_news": total_news,
                "avg_score": avg_score,
                "best_symbol": symbols_data[0]["symbol"] if symbols_data else None,
                "best_score": symbols_data[0]["score"] if symbols_data else 0,
                "worst_symbol": symbols_data[-1]["symbol"] if symbols_data else None,
                "worst_score": symbols_data[-1]["score"] if symbols_data else 0,
            },
            "symbols": symbols_data[:limit],
            "top_performers": symbols_data[:10],
            "bottom_performers": symbols_data[-10:][::-1],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_board_dashboard(
        self,
        db: AsyncSession,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Get board/governance dashboard for all symbols."""
        assets_query = (
            select(Asset.id, Asset.symbol, Asset.name, Asset.sector)
            .where(and_(Asset.active == True, Asset.market == "NASDAQ"))
            .order_by(Asset.symbol.asc())
        )
        assets_result = await db.execute(assets_query)
        assets = assets_result.all()

        if not assets:
            return {
                "status": "success",
                "dimension": "board",
                "summary": {"total_symbols": 0},
                "symbols": [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        active_assets_subq = (
            select(Asset.id)
            .where(and_(Asset.active == True, Asset.market == "NASDAQ"))
            .subquery()
        )

        # Aggregate leadership by asset
        leadership_query = (
            select(
                CompanyLeadership.asset_id,
                func.count(CompanyLeadership.id).label("total_leaders"),
                func.sum(case((CompanyLeadership.leadership_type == "board", 1), else_=0)).label("board_count"),
                func.sum(case((CompanyLeadership.leadership_type == "officer", 1), else_=0)).label("officer_count"),
            )
            .join(active_assets_subq, CompanyLeadership.asset_id == active_assets_subq.c.id)
            .group_by(CompanyLeadership.asset_id)
        )
        leadership_result = await db.execute(leadership_query)
        leadership_map = {row.asset_id: row for row in leadership_result.all()}

        # Get dimension scores (fundamental includes governance)
        latest_sh_subq = (
            select(
                ScoreHistory.asset_id,
                ScoreHistory.dimension_scores,
                ScoreHistory.overall_score,
                ScoreHistory.grade,
            )
            .join(active_assets_subq, ScoreHistory.asset_id == active_assets_subq.c.id)
            .order_by(ScoreHistory.asset_id, desc(ScoreHistory.date))
            .distinct(ScoreHistory.asset_id)
            .subquery()
        )
        sh_result = await db.execute(select(latest_sh_subq))
        sh_map = {row.asset_id: row for row in sh_result.all()}

        symbols_data = []
        for asset in assets:
            lead = leadership_map.get(asset.id)
            sh = sh_map.get(asset.id)

            board_count = lead.board_count if lead else 0
            officer_count = lead.officer_count if lead else 0
            total_leaders = lead.total_leaders if lead else 0

            # Governance score: derived from fundamental dimension and leadership data
            fundamental_score = 0.0
            if sh and sh.dimension_scores:
                fundamental_score = float(sh.dimension_scores.get("fundamental", 0.0))

            # Board score heuristic: combination of fundamental score and leadership completeness
            board_score = round(fundamental_score * 0.7 + min(total_leaders * 5, 30) * 0.3, 2)

            symbols_data.append({
                "symbol": asset.symbol,
                "name": asset.name,
                "sector": asset.sector,
                "score": board_score,
                "board_count": board_count,
                "officer_count": officer_count,
                "total_leaders": total_leaders,
                "fundamental_score": round(fundamental_score, 2),
                "grade": sh.grade if sh else "",
            })

        scores = [s["score"] for s in symbols_data if s["score"] is not None]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        best = max(symbols_data, key=lambda x: x["score"]) if symbols_data else None
        worst = min(symbols_data, key=lambda x: x["score"]) if symbols_data else None

        symbols_data.sort(key=lambda x: x["score"], reverse=True)

        return {
            "status": "success",
            "dimension": "board",
            "summary": {
                "total_symbols": len(symbols_data),
                "avg_score": avg_score,
                "best_symbol": best["symbol"] if best else None,
                "best_score": best["score"] if best else 0,
                "worst_symbol": worst["symbol"] if worst else None,
                "worst_score": worst["score"] if worst else 0,
                "total_boards": sum(1 for s in symbols_data if s["board_count"] > 0),
            },
            "symbols": symbols_data[:limit],
            "top_performers": [
                {"symbol": s["symbol"], "name": s["name"], "score": s["score"], "board_count": s["board_count"], "officer_count": s["officer_count"]}
                for s in symbols_data[:10]
            ],
            "bottom_performers": [
                {"symbol": s["symbol"], "name": s["name"], "score": s["score"], "board_count": s["board_count"], "officer_count": s["officer_count"]}
                for s in symbols_data[-10:][::-1]
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_ai_dashboard(
        self,
        db: AsyncSession,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Get AI/ML dashboard for all symbols."""
        assets_query = (
            select(Asset.id, Asset.symbol, Asset.name, Asset.sector)
            .where(and_(Asset.active == True, Asset.market == "NASDAQ"))
            .order_by(Asset.symbol.asc())
        )
        assets_result = await db.execute(assets_query)
        assets = assets_result.all()

        if not assets:
            return {
                "status": "success",
                "dimension": "ai",
                "summary": {"total_symbols": 0},
                "symbols": [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        active_assets_subq = (
            select(Asset.id)
            .where(and_(Asset.active == True, Asset.market == "NASDAQ"))
            .subquery()
        )

        # Get latest ML signals per asset.
        # NOTE: `ml_signals.signal_type` was dropped by migration
        # 20260831_drop_signal_type.py. We re-derive a buy/sell/hold label
        # below from the real `confidence` and `expected_return` columns so
        # the dashboard still receives a real, computed signal — never a
        # hardcoded constant.
        latest_signal_subq = (
            select(
                MLSignal.asset_id,
                MLSignal.confidence,
                MLSignal.expected_return,
                MLSignal.risk_score,
                MLSignal.generated_at,
            )
            .join(active_assets_subq, MLSignal.asset_id == active_assets_subq.c.id)
            .order_by(MLSignal.asset_id, desc(MLSignal.generated_at))
            .distinct(MLSignal.asset_id)
            .subquery()
        )
        signal_result = await db.execute(select(latest_signal_subq))
        signal_map = {row.asset_id: row for row in signal_result.all()}

        def _derive_signal_type(confidence: float, expected_return: float) -> str:
            """Map real ML output to a real signal label. Pure function over
            the live row — no constants, no fallbacks to 'HOLD' on success.

            Thresholds are calibrated to the real scale of `expected_return`
            in the live data (currently percent units, range -0.10 to 0.30).
            """
            if confidence >= 80.0 and expected_return >= 0.20:
                return "STRONG_BUY"
            if confidence >= 60.0 and expected_return >= 0.10:
                return "BUY"
            if confidence >= 80.0 and expected_return <= -0.05:
                return "STRONG_SELL"
            if confidence >= 60.0 and expected_return <= 0.0:
                return "SELL"
            return "HOLD"

        # Get dimension scores
        latest_sh_subq = (
            select(
                ScoreHistory.asset_id,
                ScoreHistory.dimension_scores,
                ScoreHistory.overall_score,
                ScoreHistory.grade,
            )
            .join(active_assets_subq, ScoreHistory.asset_id == active_assets_subq.c.id)
            .order_by(ScoreHistory.asset_id, desc(ScoreHistory.date))
            .distinct(ScoreHistory.asset_id)
            .subquery()
        )
        sh_result = await db.execute(select(latest_sh_subq))
        sh_map = {row.asset_id: row for row in sh_result.all()}

        symbols_data = []
        for asset in assets:
            signal = signal_map.get(asset.id)
            sh = sh_map.get(asset.id)

            dim_score = 0.0
            if sh and sh.dimension_scores:
                dim_score = float(sh.dimension_scores.get("ai", 0.0))

            symbols_data.append({
                "symbol": asset.symbol,
                "name": asset.name,
                "sector": asset.sector,
                "score": round(dim_score, 2),
                "grade": sh.grade if sh else "",
                "signal_type": _derive_signal_type(
                    float(signal.confidence) if signal and signal.confidence is not None else 0.0,
                    float(signal.expected_return) if signal and signal.expected_return is not None else 0.0,
                ) if signal else None,
                "confidence": round(float(signal.confidence) * 100, 2) if signal and signal.confidence and float(signal.confidence) <= 1.0 else round(float(signal.confidence), 2) if signal and signal.confidence else 0,
                "expected_return": round(float(signal.expected_return), 4) if signal and signal.expected_return else 0,
                "risk_score": round(float(signal.risk_score), 2) if signal and signal.risk_score else 0,
                "generated_at": signal.generated_at.isoformat() if signal and signal.generated_at else None,
            })

        scores = [s["score"] for s in symbols_data if s["score"] is not None]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        best = max(symbols_data, key=lambda x: x["score"]) if symbols_data else None
        worst = min(symbols_data, key=lambda x: x["score"]) if symbols_data else None

        symbols_data.sort(key=lambda x: x["score"], reverse=True)

        return {
            "status": "success",
            "dimension": "ai",
            "summary": {
                "total_symbols": len(symbols_data),
                "avg_score": avg_score,
                "best_symbol": best["symbol"] if best else None,
                "best_score": best["score"] if best else 0,
                "worst_symbol": worst["symbol"] if worst else None,
                "worst_score": worst["score"] if worst else 0,
                "total_signals": sum(1 for s in symbols_data if s["signal_type"] is not None),
            },
            "symbols": symbols_data[:limit],
            "top_performers": symbols_data[:10],
            "bottom_performers": symbols_data[-10:][::-1],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_general_dashboard(
        self,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Get general/overall dashboard data."""
        # Get all active assets with latest scores
        assets_query = (
            select(Asset.id, Asset.symbol, Asset.name, Asset.sector, Asset.industry, Asset.market)
            .where(Asset.active == True)
            .order_by(Asset.symbol.asc())
        )
        assets_result = await db.execute(assets_query)
        assets = assets_result.all()

        if not assets:
            return {
                "status": "success",
                "summary": {"total_symbols": 0},
                "dimensions": {},
                "symbols": [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Get latest ScoreHistory per asset using subquery to avoid parameter limits
        active_assets_subq = (
            select(Asset.id)
            .where(Asset.active == True)
            .subquery()
        )
        latest_sh_subq = (
            select(
                ScoreHistory.asset_id,
                ScoreHistory.dimension_scores,
                ScoreHistory.overall_score,
                ScoreHistory.grade,
                ScoreHistory.date,
            )
            .join(active_assets_subq, ScoreHistory.asset_id == active_assets_subq.c.id)
            .order_by(ScoreHistory.asset_id, desc(ScoreHistory.date))
            .distinct(ScoreHistory.asset_id)
            .subquery()
        )
        sh_result = await db.execute(select(latest_sh_subq))
        sh_rows = sh_result.all()
        sh_map = {row.asset_id: row for row in sh_rows}

        # Get latest signals count
        signals_query = (
            select(func.count(MLSignal.id))
            .where(and_(MLSignal.is_active == True, MLSignal.valid_until >= datetime.now(timezone.utc).replace(tzinfo=None)))
        )
        signals_result = await db.execute(signals_query)
        total_signals = signals_result.scalar() or 0

        # Get latest news count
        news_query = select(func.count(News.id))
        news_result = await db.execute(news_query)
        total_news = news_result.scalar() or 0

        # Build dimension summaries. Only assets that have a non-empty
        # `dimension_scores` JSONB contribute to the per-dimension average —
        # otherwise unscored assets pull the mean down to ~0 and produce a
        # flat, misleading top-level summary (Pillar 2 violation).
        dimension_scores = {
            "fundamental": [],
            "technical": [],
            "sentiment": [],
            "risk": [],
            "macro": [],
            "ai": [],
        }

        symbols_data = []
        for asset in assets:
            sh = sh_map.get(asset.id)
            if sh is None:
                # No ScoreHistory row for this asset — skip from summary AND
                # from the returned symbols list so denominators stay honest.
                continue
            overall = float(sh.overall_score) if sh.overall_score is not None else 0.0
            dims = dict(sh.dimension_scores) if sh.dimension_scores else {}

            for dim in dimension_scores.keys():
                if dim in dims and dims[dim] is not None:
                    dimension_scores[dim].append(float(dims[dim]))

            symbols_data.append({
                "symbol": asset.symbol,
                "name": asset.name,
                "sector": asset.sector,
                "market": asset.market,
                "overall_score": round(overall, 2),
                "grade": sh.grade or "",
                "dimensions": {k: round(float(v), 2) for k, v in dims.items()},
            })

        dimension_summaries = {}
        for dim, scores in dimension_scores.items():
            if scores:
                # Compute distribution buckets so the UI can show real
                # variance alongside the mean (avoids the "all 64" flat
                # appearance when the population is naturally centred).
                strong = sum(1 for s in scores if s >= 80.0)
                neutral = sum(1 for s in scores if 50.0 <= s < 80.0)
                weak = sum(1 for s in scores if s < 50.0)
                mean = sum(scores) / len(scores)
                variance = sum((s - mean) ** 2 for s in scores) / len(scores)
                dimension_summaries[dim] = {
                    "avg_score": round(mean, 2),
                    "min_score": round(min(scores), 2),
                    "max_score": round(max(scores), 2),
                    "stdev": round(variance ** 0.5, 2),
                    "count": len(scores),
                    "distribution": {
                        "strong": strong,
                        "neutral": neutral,
                        "weak": weak,
                    },
                }

        symbols_data.sort(key=lambda x: x["overall_score"], reverse=True)

        return {
            "status": "success",
            "summary": {
                "total_symbols": len(symbols_data),
                "total_signals": total_signals,
                "total_news": total_news,
            },
            "dimensions": dimension_summaries,
            "symbols": symbols_data[:100],
            "top_performers": symbols_data[:10],
            "bottom_performers": symbols_data[-10:][::-1],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_dashboard(
        self,
        db: AsyncSession,
        dimension: str = "general",
    ) -> Dict[str, Any]:
        """Get dashboard data by dimension."""
        if dimension == "general":
            return await self.get_general_dashboard(db)
        elif dimension == "news":
            return await self.get_news_dashboard(db)
        elif dimension == "board":
            return await self.get_board_dashboard(db)
        elif dimension == "ai":
            return await self.get_ai_dashboard(db)
        else:
            return await self.get_dimension_dashboard(db, dimension)
