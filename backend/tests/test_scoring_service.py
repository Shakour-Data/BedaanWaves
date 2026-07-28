"""Unit tests for Tier 3 ScoringService."""

import pytest

from app.services.analysis.scoring_service import ScoringService

pytestmark = pytest.mark.unit


class TestScoringServiceInitialization:
    def test_default_service_name(self):
        service = ScoringService()
        assert service.service_name == "ScoringService"

    async def test_initialize_builds_hierarchy(self, caplog):
        service = ScoringService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.initialize()
        assert "ScoringService initialized" in caplog.text
        assert len(service._hierarchy) > 0

    async def test_hierarchy_node_count(self):
        service = ScoringService()
        await service.initialize()
        assert len(service._hierarchy) == 320

    async def test_shutdown_clears_cache(self, caplog):
        service = ScoringService()
        service._scores_cache["TEST"] = {"a": 1.0}
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.shutdown()
        assert "ScoringService shutdown" in caplog.text
        assert len(service._scores_cache) == 0


class TestAnalyze:
    async def test_empty_data_returns_zero_scores(self):
        service = ScoringService()
        await service.initialize()
        result = await service.analyze({"ticker": "TEST"})
        assert result["ticker"] == "TEST"
        assert result["overall_score"] == 0.0
        assert result["grade"] == "E_STRONG_SELL"
        assert all(v == 0.0 for v in result["dimension_scores"].values())

    async def test_full_scoring_returns_grade(self):
        service = ScoringService()
        await service.initialize()
        data = {
            "ticker": "فملی",
            "market": "TSE",
            "fundamental": {"pe_ratio": 12, "roe": 0.18},
            "technical": {"rsi": 55, "macd": 0.5},
            "sentiment": {"score": 70},
            "risk": {"volatility": 0.2},
            "macro": {"gdp_growth": 3.0},
            "ai": {"prediction": 0.75},
        }
        result = await service.analyze(data)
        assert 0 <= result["overall_score"] <= 100
        assert result["grade"] in (
            "A_STRONG_BUY", "B_BUY", "C_HOLD", "D_SELL", "E_STRONG_SELL"
        )

    async def test_caches_dimension_scores(self):
        service = ScoringService()
        await service.initialize()
        data = {"ticker": "TEST", "technical": {"rsi": 50}}
        await service.analyze(data)
        assert "TEST" in service._scores_cache


class TestScoreDimension:
    async def test_empty_dimension_returns_zero(self):
        service = ScoringService()
        score = await service._score_dimension("technical", {}, "TSE")
        assert score == 0.0

    async def test_numeric_values_are_normalized(self):
        service = ScoringService()
        score = await service._score_dimension("technical", {"rsi": 50}, "TSE")
        assert 0 <= score <= 100


class TestNormalizeScore:
    async def test_tse_rsi_scoring(self):
        service = ScoringService()
        assert service._score_rsi_tse(50) == 50.0
        assert service._score_rsi_tse(80) == 80.0
        assert service._score_rsi_tse(20) == 80.0

    async def test_global_rsi_scoring(self):
        service = ScoringService()
        assert service._score_rsi_global(50) == 50.0
        assert service._score_rsi_global(80) == 87.5
        assert service._score_rsi_global(20) == 87.5

    async def test_crypto_rsi_scoring(self):
        service = ScoringService()
        assert service._score_rsi_crypto(50) == 50.0
        assert service._score_rsi_crypto(85) == 85.0
        assert service._score_rsi_crypto(15) == 85.0

    async def test_pe_tse_scoring(self):
        service = ScoringService()
        assert service._score_pe_tse(10) == 75.0
        assert service._score_pe_tse(20) == 60.0
        assert service._score_pe_tse(100) == 0.0
        assert service._score_pe_tse(-5) == 0.0

    async def test_pe_global_scoring(self):
        service = ScoringService()
        assert service._score_pe_global(15) == 75.0
        assert service._score_pe_global(40) == 40.0
        assert service._score_pe_global(-10) == 0.0

    async def test_roe_scoring(self):
        service = ScoringService()
        assert service._score_roe_tse(0.15) == 0.3
        assert service._score_roe_global(0.20) == 0.4

    async def test_crypto_volatility_scoring(self):
        service = ScoringService()
        assert service._score_volatility_crypto(0.1) == 80.0
        assert service._score_volatility_crypto(0.6) == 40.0
        assert service._score_volatility_crypto(0.9) == 20.0

    async def test_crypto_risk_scoring(self):
        service = ScoringService()
        assert service._score_risk_crypto(0.2) == 70.0
        assert service._score_risk_crypto(0.8) == 30.0

    async def test_default_generic_normalization(self):
        service = ScoringService()
        result = service._normalize_score(75.0, "generic_metric", "technical", "NYSE")
        assert result == 75.0
        assert result == max(0.0, min(100.0, 75.0))


class TestGradeAssignment:
    async def test_strong_buy_grade(self):
        service = ScoringService()
        assert service._assign_grade(90.0) == "A_STRONG_BUY"
        assert service._assign_grade(85.0) == "A_STRONG_BUY"

    async def test_buy_grade(self):
        service = ScoringService()
        assert service._assign_grade(75.0) == "B_BUY"
        assert service._assign_grade(70.0) == "B_BUY"

    async def test_hold_grade(self):
        service = ScoringService()
        assert service._assign_grade(60.0) == "C_HOLD"
        assert service._assign_grade(55.0) == "C_HOLD"

    async def test_sell_grade(self):
        service = ScoringService()
        assert service._assign_grade(45.0) == "D_SELL"
        assert service._assign_grade(40.0) == "D_SELL"

    async def test_strong_sell_grade(self):
        service = ScoringService()
        assert service._assign_grade(30.0) == "E_STRONG_SELL"
        assert service._assign_grade(0.0) == "E_STRONG_SELL"


class TestSignalGeneration:
    async def test_strong_signals(self):
        service = ScoringService()
        dims = {"fundamental": 85, "technical": 90, "sentiment": 88}
        signals = service._generate_signals(dims)
        assert "strong_fundamental" in signals
        assert "strong_technical" in signals
        assert "strong_sentiment" in signals

    async def test_positive_signals(self):
        service = ScoringService()
        dims = {"fundamental": 65, "technical": 70}
        signals = service._generate_signals(dims)
        assert "positive_fundamental" in signals
        assert "positive_technical" in signals

    async def test_weak_signals(self):
        service = ScoringService()
        dims = {"fundamental": 15, "technical": 10}
        signals = service._generate_signals(dims)
        assert "weak_fundamental" in signals
        assert "weak_technical" in signals

    async def test_neutral_no_signal(self):
        service = ScoringService()
        dims = {"fundamental": 50, "technical": 55}
        signals = service._generate_signals(dims)
        assert len(signals) == 0


class TestBatchOperations:
    async def test_score_multiple(self):
        service = ScoringService()
        await service.initialize()
        stocks = [
            {"ticker": "A", "technical": {"rsi": 50}},
            {"ticker": "B", "technical": {"rsi": 80}},
        ]
        results = await service.score_multiple(stocks)
        assert len(results) == 2
        assert results[0]["ticker"] == "A"

    async def test_rank_stocks_by_overall(self):
        service = ScoringService()
        await service.initialize()
        stocks = [
            {"ticker": "A", "fundamental": {"pe_ratio": 20}, "technical": {"rsi": 50}},
            {"ticker": "B", "fundamental": {"pe_ratio": 10}, "technical": {"rsi": 70}},
        ]
        ranked = await service.rank_stocks(stocks)
        assert len(ranked) == 2
        assert ranked[0]["overall_score"] >= ranked[1]["overall_score"]

    async def test_rank_stocks_by_dimension(self):
        service = ScoringService()
        await service.initialize()
        stocks = [
            {"ticker": "A", "fundamental": {"pe_ratio": 10}},
            {"ticker": "B", "fundamental": {"pe_ratio": 20}},
        ]
        ranked = await service.rank_stocks(stocks, dimension="fundamental")
        assert ranked[0]["dimension_scores"]["fundamental"] >= ranked[1]["dimension_scores"]["fundamental"]


class TestHierarchyInfo:
    async def test_hierarchy_counts(self):
        service = ScoringService()
        await service.initialize()
        info = service.get_hierarchy_info()
        assert info["total_nodes"] == 320
        assert info["level1_dimensions"] == 12
        assert info["level2_subdimensions"] == 45
        assert info["level3_aspects"] == 90
        assert info["level4_subaspects"] == 173
        assert len(info["dimensions_list"]) == 6
