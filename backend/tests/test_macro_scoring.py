"""Offline unit tests for the macro-scoring helpers (no DB, no network)."""

from datetime import date

import pytest

from app.services.analysis.macro_scoring import (
    BUNDLED_MACRO_SNAPSHOT,
    INDICATOR_REGISTRY,
    SUB_DIMENSIONS,
    compute_macro_scores,
    derive_history_map,
    derive_indicators,
    latest_values,
    macro_phase,
    merged_snapshot,
)


def test_sub_dimensions_match_legacy_scoring_contract():
    assert set(SUB_DIMENSIONS) == {
        "gdp", "inflation", "interest_rates", "exchange_rates", "commodity_prices",
    }


def test_scores_with_real_readings():
    latest = {
        "INFLATION": 3.0,
        "GDP_QOQ": 1.5,
        "FEDFUNDS": 4.0,
        "T10Y2Y": 0.5,
        "DX-Y.NYB": 100.0,
        "CL=F": 72.0,
        "GC=F": 2550.0,
    }
    scores = compute_macro_scores(latest)
    # gdp 1.5% -> 52 + 1.5*12 = 70
    assert scores["gdp"] == pytest.approx(70.0, abs=0.01)
    # inflation 3.0% -> 90 - 0.5*12 = 84
    assert scores["inflation"] == pytest.approx(84.0, abs=0.01)
    # fed funds 4.0 -> 90 - 1.0*10 = 80
    assert scores["interest_rates"] == pytest.approx(80.0, abs=0.01)
    # dxy 100 -> 90
    assert scores["exchange_rates"] == pytest.approx(90.0, abs=0.01)
    # commodity = mean of oil(68) and gold(90 - 250/30 = 81.67)
    assert scores["commodity_prices"] == pytest.approx((68.0 + 90.0 - 250.0 / 30.0) / 2.0, abs=0.05)
    assert "overall" in scores and "phase" in scores
    assert scores["phase"] == "Early Expansion"


def test_scores_missing_indicators_are_neutral():
    scores = compute_macro_scores({})
    for sub in SUB_DIMENSIONS:
        assert scores[sub] == 50.0
    assert scores["overall"] == 50.0
    assert scores["phase"] == "Middle Cycle"


def test_inflation_deflation_and_high_penalty():
    assert compute_macro_scores({"INFLATION": -1.0})["inflation"] == 30.0
    assert compute_macro_scores({"INFLATION": 10.0})["inflation"] < 30.0
    assert compute_macro_scores({"INFLATION": 2.5})["inflation"] == 90.0


def test_inverted_curve_penalizes_interest_rates():
    flat = compute_macro_scores({"FEDFUNDS": 3.0, "T10Y2Y": 0.5})["interest_rates"]
    inverted = compute_macro_scores({"FEDFUNDS": 3.0, "T10Y2Y": -0.8})["interest_rates"]
    assert inverted < flat
    assert inverted == 60.0  # neutral fed funds (90) minus the 30-point inversion penalty


def test_macro_phase_boundaries():
    assert macro_phase(10) == "Deflationary Recession"
    assert macro_phase(25) == "Late Cycle"
    assert macro_phase(50) == "Middle Cycle"
    assert macro_phase(62) == "Early Cycle"
    assert macro_phase(75) == "Early Expansion"
    assert macro_phase(90) == "Strong Expansion"


def test_derive_inflation_yoy_from_history():
    history = []
    for i in range(13):
        y = 2023 + i // 12
        m = 6 + i if 6 + i <= 12 else 6 + i - 12
        if 6 + i > 12:
            y += 1
        history.append((date(y, m, 1), 300.0 + 0.5 * i))
    # 13 monthly CPI points; last=306, value 12 months ago=300 -> 2.0% YoY
    derived = derive_indicators({"CPIAUCSL": history, "CPILFESL": [], "GDPC1": [], "PAYEMS": []})
    assert "INFLATION" in derived
    assert derived["INFLATION"]["value"] == pytest.approx(2.0, abs=0.001)
    assert derived["INFLATION"]["unit"] == "%"


def test_derive_handles_short_history():
    derived = derive_indicators({"CPIAUCSL": [(date(2024, 1, 1), 300.0)], "CPILFESL": []})
    assert "INFLATION" not in derived


def test_merged_snapshot_overlays_live():
    snap = merged_snapshot({"FEDFUNDS": {"value": 5.25, "period": "2026-07", "source": "FRED"}})
    assert snap["FEDFUNDS"]["value"] == 5.25
    # Bundled-only codes remain untouched.
    assert snap["UNRATE"]["value"] == BUNDLED_MACRO_SNAPSHOT["UNRATE"]["value"]


def test_latest_values_flattens_snapshot():
    snapshot = merged_snapshot({"US_FED_RATE": {"value": 5.25, "period": "2026-07"}})
    flat = latest_values(snapshot)
    assert flat["US_FED_RATE"] == 5.25
    assert "INFLATION" in flat


def test_indicator_registry_has_free_sources():
    for code in ("CPIAUCSL", "UNRATE", "FEDFUNDS", "GDPC1", "T10Y2Y", "CPILFESL", "PAYEMS"):
        assert code in INDICATOR_REGISTRY
        assert INDICATOR_REGISTRY[code]["source"] in ("FRED", "BLS")


def test_derive_history_map_computes_yoy_history():
    # 14 monthly CPI points spanning 2023-01 .. 2024-02 (value = 300 + index).
    cpi_history = []
    for i in range(14):
        y = 2023 + (i // 12)
        m = 1 + i
        if m > 12:
            m -= 12
        cpi_history.append((date(y, m, 1), 300.0 + i))

    result = derive_history_map({"CPIAUCSL": cpi_history, "CPILFESL": [], "GDPC1": [], "PAYEMS": []})
    assert "INFLATION" in result
    # 14 points, periods=12 → 2 YoY points (i=12, i=13)
    assert len(result["INFLATION"]) == 2
    # i=12: 312/300 → 4.0 ; i=13: 313/301 → 3.9867
    expected_first = round((312.0 / 300.0 - 1.0) * 100.0, 4)
    expected_last = round((313.0 / 301.0 - 1.0) * 100.0, 4)
    assert result["INFLATION"][0] == (date(2024, 1, 1), expected_first)
    assert result["INFLATION"][-1] == (date(2024, 2, 1), expected_last)


def test_derive_history_map_empty_input():
    assert derive_history_map({}) == {}


def test_derive_history_map_short_history_omitted():
    # Only 10 CPI points (< 12) → no YoY possible → INFLATION omitted.
    short = [(date(2024, 1, 1), 300.0 + i) for i in range(10)]
    result = derive_history_map({"CPIAUCSL": short})
    assert "INFLATION" not in result
