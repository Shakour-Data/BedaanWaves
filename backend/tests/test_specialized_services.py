"""Unit tests for Tier 7 Specialized Services."""

import pytest
from datetime import date

from app.services.specialized.sector_analysis_service import SectorAnalysisService
from app.services.specialized.screening_service import ScreeningService
from app.services.specialized.comparison_service import ComparisonService
from app.services.specialized.correlation_service import CorrelationService
from app.services.specialized.calendar_service import CalendarService

pytestmark = pytest.mark.unit


# --------------------------------------------------------------------------
# SectorAnalysisService
# --------------------------------------------------------------------------

class TestSectorAnalysisService:
    async def test_initialize_and_shutdown_log(self, caplog):
        svc = SectorAnalysisService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await svc.initialize()
            await svc.shutdown()
        assert "SectorAnalysisService initialized" in caplog.text
        assert "SectorAnalysisService shutdown" in caplog.text

    async def test_empty_sector(self):
        svc = SectorAnalysisService()
        await svc.initialize()
        result = await svc.analyze_sector("TECH", [])
        assert result["count"] == 0
        assert result["average_score"] is None
        assert result["top_mover"] is None

    async def test_sector_summary_aggregates(self):
        svc = SectorAnalysisService()
        await svc.initialize()
        stocks = [
            {"symbol": "A", "sector": "TECH", "score": 80, "change_pct": 3.0},
            {"symbol": "B", "sector": "TECH", "score": 20, "change_pct": -1.0},
            {"symbol": "C", "sector": "TECH", "score": 50, "change_pct": 0.5},
        ]
        result = await svc.analyze_sector("TECH", stocks)
        assert result["count"] == 3
        assert result["scored_count"] == 3
        assert result["average_score"] == pytest.approx(50.0)
        assert result["average_change_pct"] == pytest.approx(0.83, abs=1e-6)
        assert result["top_mover"]["symbol"] == "A"
        assert result["bottom_mover"]["symbol"] == "B"
        assert result["score_distribution"]["strong"] == 1

    async def test_analyze_all_groups_and_ranks(self):
        svc = SectorAnalysisService()
        await svc.initialize()
        stocks = [
            {"symbol": "A", "sector": "TECH", "score": 90, "change_pct": 2.0},
            {"symbol": "B", "symbol": "B", "sector": "BANK", "score": 40, "change_pct": -1.0},
            {"symbol": "C", "sector": "TECH", "score": 60, "change_pct": 0.0},
        ]
        result = await svc.analyze_all(stocks)
        assert result["market_overview"]["total_stocks"] == 3
        assert result["market_overview"]["total_sectors"] == 2
        # TECH has higher composite (higher avg score, positive change)
        assert result["market_overview"]["strongest_sector"] == "TECH"
        assert result["market_overview"]["weakest_sector"] == "BANK"
        sector_names = {s["sector"] for s in result["sectors"]}
        assert sector_names == {"TECH", "BANK"}


# --------------------------------------------------------------------------
# ScreeningService
# --------------------------------------------------------------------------

class TestScreeningService:
    async def test_passes_min_score(self):
        svc = ScreeningService()
        await svc.initialize()
        universe = [
            {"symbol": "A", "score": 80, "change_pct": 1.0},
            {"symbol": "B", "score": 20, "change_pct": 5.0},
        ]
        result = await svc.screen(universe, {"min_score": 50})
        assert result["matched"] == 1
        assert result["results"][0]["symbol"] == "A"

    async def test_sector_filter(self):
        svc = ScreeningService()
        await svc.initialize()
        universe = [
            {"symbol": "A", "sector": "TECH", "score": 70},
            {"symbol": "B", "sector": "BANK", "score": 70},
        ]
        result = await svc.screen(universe, {"sectors": ["TECH"]})
        assert [r["symbol"] for r in result["results"]] == ["A"]

    async def test_no_criteria_matches_all(self):
        svc = ScreeningService()
        await svc.initialize()
        universe = [{"symbol": "A"}, {"symbol": "B"}]
        result = await svc.screen(universe, {})
        assert result["matched"] == 2

    async def test_results_sorted_by_match_score(self):
        svc = ScreeningService()
        await svc.initialize()
        universe = [
            {"symbol": "LOW", "score": 10, "change_pct": 0.0},
            {"symbol": "HIGH", "score": 95, "change_pct": 4.0},
        ]
        result = await svc.screen(universe, {})
        assert result["results"][0]["symbol"] == "HIGH"
        assert result["results"][0]["match_score"] > result["results"][1]["match_score"]

    async def test_price_and_volume_bounds(self):
        svc = ScreeningService()
        await svc.initialize()
        universe = [
            {"symbol": "A", "price": 100, "volume": 5000, "score": 50},
            {"symbol": "B", "price": 5000, "volume": 100, "score": 50},
        ]
        result = await svc.screen(universe, {"min_price": 50, "max_price": 200, "min_volume": 1000})
        assert [r["symbol"] for r in result["results"]] == ["A"]


# --------------------------------------------------------------------------
# ComparisonService
# --------------------------------------------------------------------------

class TestComparisonService:
    async def test_compare_empty(self):
        svc = ComparisonService()
        await svc.initialize()
        result = await svc.compare([])
        assert result["symbols"] == []
        assert result["rankings"] == {}

    async def test_compare_rankings(self):
        svc = ComparisonService()
        await svc.initialize()
        data = [
            {"symbol": "A", "score": 90, "change_pct": 2.0, "volatility": 0.3},
            {"symbol": "B", "score": 40, "change_pct": -1.0, "volatility": 0.8},
        ]
        result = await svc.compare(data)
        assert result["best"]["score"] == "A"
        assert result["worst"]["score"] == "B"
        # For volatility lower is better -> A is best
        assert result["best"]["volatility"] == "A"
        assert result["worst"]["volatility"] == "B"
        assert len(result["symbols"]) == 2

    async def test_handles_missing_metrics(self):
        svc = ComparisonService()
        await svc.initialize()
        data = [{"symbol": "A", "score": 50}, {"symbol": "B"}]
        result = await svc.compare(data)
        assert result["rankings"]["score"]["available"] is True
        assert result["rankings"]["volatility"]["available"] is False


# --------------------------------------------------------------------------
# CorrelationService
# --------------------------------------------------------------------------

class TestCorrelationService:
    async def test_identical_series_correlate_one(self):
        svc = CorrelationService()
        await svc.initialize()
        rm = {"A": [0.01, 0.02, 0.03, 0.04], "B": [0.01, 0.02, 0.03, 0.04]}
        result = await svc.compute_correlation(rm)
        assert result["matrix"]["A"]["B"] == pytest.approx(1.0)

    async def test_inverse_series_detected(self):
        svc = CorrelationService()
        await svc.initialize()
        rm = {"A": [0.01, 0.02, 0.03, 0.04], "B": [-0.01, -0.02, -0.03, -0.04]}
        result = await svc.compute_correlation(rm, high_threshold=0.7, low_threshold=-0.7)
        assert len(result["pairs"]["inverse"]) == 1
        assert len(result["pairs"]["high"]) == 0

    async def test_high_correlation_pair(self):
        svc = CorrelationService()
        await svc.initialize()
        rm = {"A": [1.0, 2.0, 3.0, 4.0, 5.0], "B": [2.0, 4.0, 6.0, 8.0, 10.0]}
        result = await svc.compute_correlation(rm, high_threshold=0.7)
        assert len(result["pairs"]["high"]) == 1

    async def test_empty_input(self):
        svc = CorrelationService()
        await svc.initialize()
        result = await svc.compute_correlation({})
        assert result["status"] == "empty"

    async def test_alignment_to_shortest(self):
        svc = CorrelationService()
        await svc.initialize()
        rm = {"A": [0.1, 0.2, 0.3], "B": [0.1, 0.2, 0.3, 0.4, 0.5]}
        result = await svc.compute_correlation(rm, min_observations=2)
        assert result["observations"] == 3
        assert result["matrix"]["A"]["B"] == pytest.approx(1.0)


# --------------------------------------------------------------------------
# CalendarService
# --------------------------------------------------------------------------

class TestCalendarService:
    async def test_initialize_shutdown(self, caplog):
        svc = CalendarService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await svc.initialize()
            await svc.shutdown()
        assert "CalendarService initialized" in caplog.text

    async def test_friday_is_weekend(self):
        svc = CalendarService()
        await svc.initialize()
        # 2026-07-10 is a Friday
        friday = date(2026, 7, 10)
        assert svc.is_trading_day(friday) is False
        # Saturday 2026-07-11 is a trading day
        assert svc.is_trading_day(date(2026, 7, 11)) is True

    async def test_next_trading_day_skips_weekend(self):
        svc = CalendarService()
        await svc.initialize()
        # Friday -> Saturday (next trading day)
        assert svc.next_trading_day(date(2026, 7, 10)) == date(2026, 7, 11)
        # Thursday -> Saturday (skip Friday)
        assert svc.next_trading_day(date(2026, 7, 9)) == date(2026, 7, 11)

    async def test_month_calendar_counts(self):
        svc = CalendarService()
        await svc.initialize()
        result = svc.get_month_calendar(2026, 7)
        assert result["trading_day_count"] == len(result["trading_days"])
        # July 2026 has 31 days, 5 Fridays -> 26 trading days
        assert result["trading_day_count"] == 26

    async def test_add_and_get_events(self):
        svc = CalendarService()
        await svc.initialize()
        svc.add_event({"date": "2026-07-15", "type": "DIVIDEND", "title": "Pay day", "symbol": "فملی"})
        events = svc.get_events(day=date(2026, 7, 15))
        assert len(events) == 1
        assert events[0]["type"] == "DIVIDEND"
        assert len(svc.get_events(symbol="فملی")) == 1

    async def test_events_in_range(self):
        svc = CalendarService()
        await svc.initialize()
        svc.add_event({"date": "2026-07-01", "type": "G", "title": "g1"})
        svc.add_event({"date": "2026-07-10", "type": "G", "title": "g2"})
        svc.add_event({"date": "2026-08-01", "type": "G", "title": "g3"})
        events = svc.events_in_range(date(2026, 7, 1), date(2026, 7, 31))
        assert len(events) == 2

    async def test_custom_weekend(self):
        svc = CalendarService(weekend_days=[6])  # Sunday weekend
        await svc.initialize()
        assert svc.is_trading_day(date(2026, 7, 12)) is False  # Sunday
        assert svc.is_trading_day(date(2026, 7, 10)) is True   # Friday trading
