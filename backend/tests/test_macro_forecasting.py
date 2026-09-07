"""Offline unit tests for MacroForecastingService (no DB, network mocked)."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.ml.macro_forecasting_service import (
    MacroForecastingService,
    _add_periods,
    _fit_forecast,
)


class _FakeCtx:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, *exc):
        return False


def test_add_periods_monthly_quarterly_daily():
    assert _add_periods(date(2024, 1, 1), 3, "monthly") == date(2024, 4, 1)
    assert _add_periods(date(2024, 1, 1), 1, "quarterly") == date(2024, 4, 1)
    assert _add_periods(date(2024, 1, 1), 3, "daily") == date(2024, 1, 4)


def test_fit_forecast_arima_path_returns_three_steps():
    values = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0]
    fc, lo, hi, model, conf = _fit_forecast(values, horizon=3, freq="monthly")
    assert len(fc) == 3 and len(lo) == 3 and len(hi) == 3
    assert model in {"ARIMA(1,1,0)", "naive_drift"}
    for f, l, h in zip(fc, lo, hi):
        assert l <= f <= h
    assert 0 < conf <= 1


def test_fit_forecast_naive_drift_for_short_series():
    # last=20, drift=(20-10)/1=10 -> [30, 40, 50]; residual std=0 -> zero-width band
    fc, lo, hi, model, conf = _fit_forecast([10.0, 20.0], horizon=3, freq="monthly")
    assert fc == [30.0, 40.0, 50.0]
    assert model == "naive_drift"
    assert lo == fc and hi == fc


def test_fit_forecast_too_few_points_returns_zeros():
    fc, lo, hi, model, _ = _fit_forecast([5.0], horizon=2, freq="monthly")
    assert fc == [0.0, 0.0]
    assert model == "naive_zero"


def test_fit_forecast_handles_constant_series():
    fc, lo, hi, model, _ = _fit_forecast([5.0, 5.0, 5.0, 5.0, 5.0], horizon=3, freq="monthly")
    assert fc == [5.0, 5.0, 5.0]
    assert model in {"ARIMA(1,1,0)", "naive_drift"}


def test_forecast_and_persist_persists_horizon_steps(monkeypatch):
    import asyncio

    import app.services.ml.macro_forecasting_service as mod

    svc = MacroForecastingService()
    monkeypatch.setattr(svc, "get_history", AsyncMock(return_value=[1.0, 2.0, 3.0, 4.0, 5.0]))
    monkeypatch.setattr(svc, "_latest_as_of", AsyncMock(return_value=date(2024, 6, 30)))

    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    monkeypatch.setattr(mod, "async_session_maker", lambda: _FakeCtx(session))

    result = asyncio.new_event_loop().run_until_complete(svc.forecast_and_persist("INFLATION"))

    assert result is True
    assert session.execute.await_count == 3
    assert session.commit.await_count == 1


def test_get_latest_forecasts_reads_db(monkeypatch):
    import app.services.ml.macro_forecasting_service as mod

    fake_fc = SimpleNamespace(
        indicator_code="INFLATION",
        model_name="ARIMA(1,1,0)",
        horizon=1,
        frequency="monthly",
        forecast_date=date(2026, 9, 30),
        forecast_value=3.4,
        lower_ci=2.9,
        upper_ci=3.9,
        confidence=0.85,
        created_at=date(2026, 9, 7),
    )

    session = MagicMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [fake_fc]
    session.execute = AsyncMock(return_value=result_mock)
    monkeypatch.setattr(mod, "async_session_maker", lambda: _FakeCtx(session))

    svc = MacroForecastingService()
    import asyncio

    out = asyncio.new_event_loop().run_until_complete(svc.get_latest_forecasts())
    assert isinstance(out, list)
    assert out[0]["indicator_code"] == "INFLATION"
    assert out[0]["forecast_value"] == pytest.approx(3.4)
    assert out[0]["model_name"] == "ARIMA(1,1,0)"
