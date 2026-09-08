"""
In-process macro-economic forecasting (free, no external API).

Forecasts US macro indicators from locally-stored ``MacroIndicator`` history
using statsmodels ARIMA when available, falling back to a naive drift model so
the service works even when network/paid feeds are absent. Confidence intervals
are produced analytically for ARIMA and from residual standard deviation for
the naive fallback.

This satisfies the "forecasts and predictions" requirement for the macro
dimension without any paid API or API key.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

import numpy as np

from app.db.base import async_session_maker
from app.models.models import MacroForecast, MacroIndicator
from app.services.analysis.macro_scoring import INDICATOR_REGISTRY

logger = logging.getLogger(__name__)


def _add_periods(d: date, n: int, freq: str) -> date:
    """Advance a date by ``n`` periods given its frequency."""
    if freq == "monthly":
        total = d.month - 1 + n
        return date(d.year + total // 12, total % 12 + 1, 1)
    if freq == "quarterly":
        current_q = (d.month - 1) // 3
        total = current_q + n
        return date(d.year + total // 4, (total % 4) * 3 + 1, 1)
    if freq == "daily":
        return d + timedelta(days=n)
    return d + timedelta(days=n)


def _fit_forecast(
    values: list[float], horizon: int, freq: str
) -> tuple[list[float], list[float], list[float], str, float]:
    """Fit a forecast; returns (forecast, lower_ci, upper_ci, model_name, confidence).

    Uses ARIMA(1,1,0) from statsmodels when enough data is available, otherwise
    falls back to a naive drift model with residual-based bands.
    """
    horizon = max(1, int(horizon))
    arr = np.asarray([v for v in values if v is not None and np.isfinite(v)], dtype=float)
    if arr.size < 2:
        return [0.0] * horizon, [0.0] * horizon, [0.0] * horizon, "naive_zero", 0.3

    forecast: list[float] = []
    ci_low: list[float] = []
    ci_high: list[float] = []
    model_name = "naive_drift"

    if arr.size >= 5:
        try:
            from statsmodels.tsa.arima.model import ARIMA

            fit = ARIMA(arr, order=(1, 1, 0)).fit()
            fc = fit.get_forecast(steps=horizon)
            forecast = [float(x) for x in np.asarray(fc.predicted_mean, dtype=float).tolist()]
            ci = fc.conf_int(alpha=0.20)
            ci_low = [float(x) for x in np.asarray(ci[:, 0], dtype=float).tolist()]
            ci_high = [float(x) for x in np.asarray(ci[:, 1], dtype=float).tolist()]
            model_name = "ARIMA(1,1,0)"
        except Exception as exc:  # noqa: BLE001 - any fit failure falls back to naive
            logger.debug("ARIMA fit failed for %s; using naive drift: %s", len(arr), exc)

    if not forecast:
        last = float(arr[-1])
        drift = (float(arr[-1]) - float(arr[0])) / (arr.size - 1) if arr.size > 1 else 0.0
        resid = np.diff(arr)
        std = float(np.std(resid)) if resid.size > 0 else 0.0
        forecast = [last + drift * (i + 1) for i in range(horizon)]
        ci_low = [f - 1.96 * std for f in forecast]
        ci_high = [f + 1.96 * std for f in forecast]
        model_name = "naive_drift"

    confidence = 0.85 if model_name.startswith("ARIMA") else 0.60
    return forecast, ci_low, ci_high, model_name, confidence


class MacroForecastingService:
    """Generate and persist free, in-process macroeconomic forecasts."""

    DEFAULT_HORIZON = 3

    async def initialize(self) -> None:
        logger.info("MacroForecastingService initialized (free, in-process)")

    async def shutdown(self) -> None:
        logger.info("MacroForecastingService shutdown")

    async def get_history(self, code: str, lookback: int = 24) -> list[float]:
        """Return chronological (oldest-first) float values for an indicator."""
        async with async_session_maker() as session:
            rows = await session.execute(
                select(MacroIndicator.value)
                .where(MacroIndicator.indicator_code == code)
                .order_by(MacroIndicator.as_of.desc())
                .limit(lookback)
            )
        values = [float(r) for (r,) in rows.all() if r is not None]
        return list(reversed(values))

    async def _latest_as_of(self, code: str) -> date | None:
        async with async_session_maker() as session:
            row = await session.execute(
                select(MacroIndicator.as_of)
                .where(MacroIndicator.indicator_code == code)
                .order_by(MacroIndicator.as_of.desc())
                .limit(1)
            )
        res = row.scalar_one_or_none()
        if res is None:
            return None
        return res if isinstance(res, date) else res.date()

    async def forecast_and_persist(self, code: str, horizon: int | None = None) -> bool:
        """Fit a forecast for ``code`` and persist horizon-step MacroForecast rows."""
        horizon = horizon or self.DEFAULT_HORIZON
        freq = INDICATOR_REGISTRY.get(code, {}).get("frequency", "monthly")
        lookback = 60 if freq == "daily" else (8 if freq == "quarterly" else 24)

        values = await self.get_history(code, lookback)
        if len(values) < 3:
            logger.info("Not enough history to forecast %s (%d points)", code, len(values))
            return False

        forecast, ci_low, ci_high, model_name, confidence = _fit_forecast(
            values, horizon, freq
        )
        base = await self._latest_as_of(code) or date.today()

        from sqlalchemy.dialects.postgresql import insert as pg_insert

        count = 0
        async with async_session_maker() as session:
            for i in range(horizon):
                fdate = _add_periods(base, i + 1, freq)
                stmt = pg_insert(MacroForecast).values(
                    {
                        "indicator_code": code,
                        "model_name": model_name,
                        "horizon": i + 1,
                        "frequency": freq,
                        "forecast_date": fdate,
                        "forecast_value": float(forecast[i]),
                        "lower_ci": float(ci_low[i]),
                        "upper_ci": float(ci_high[i]),
                        "confidence": float(confidence),
                    }
                )
                stmt = stmt.on_conflict_do_update(
                    constraint="uix_macro_forecast",
                    set_={
                        "forecast_value": stmt.excluded.forecast_value,
                        "lower_ci": stmt.excluded.lower_ci,
                        "upper_ci": stmt.excluded.upper_ci,
                        "confidence": stmt.excluded.confidence,
                        "model_name": stmt.excluded.model_name,
                        "created_at": _now(),
                    },
                )
                await session.execute(stmt)
                count += 1
            await session.commit()
        logger.info("Forecast %s: %d steps via %s (confidence=%.2f)", code, count, model_name, confidence)
        return count > 0

    async def get_latest_forecasts(
        self, codes: list[str] | None = None, limit_per_code: int = 3
    ) -> list[dict[str, Any]]:
        """Return the most recent forecasts (newest first)."""
        async with async_session_maker() as session:
            query = (
                select(MacroForecast)
                .order_by(
                    MacroForecast.indicator_code,
                    MacroForecast.horizon,
                    MacroForecast.created_at.desc(),
                )
            )
            if codes:
                query = query.where(MacroForecast.indicator_code.in_(codes))
            rows = await session.execute(query)

        # Keep only the newest `limit_per_code` per indicator.
        seen: dict[str, list[dict[str, Any]]] = {}
        out: list[dict[str, Any]] = []
        for fc in rows.scalars().all():
            code = fc.indicator_code
            item = {
                "indicator_code": code,
                "model_name": fc.model_name,
                "horizon": fc.horizon,
                "frequency": fc.frequency,
                "forecast_date": fc.forecast_date.isoformat() if fc.forecast_date else None,
                "forecast_value": float(fc.forecast_value) if fc.forecast_value is not None else None,
                "lower_ci": float(fc.lower_ci) if fc.lower_ci is not None else None,
                "upper_ci": float(fc.upper_ci) if fc.upper_ci is not None else None,
                "confidence": float(fc.confidence) if fc.confidence is not None else 0.0,
                "created_at": fc.created_at.isoformat() if fc.created_at else None,
            }
            seen.setdefault(code, []).append(item)
        for code, items in seen.items():
            items.sort(key=lambda x: (x["created_at"] or "", x["horizon"]), reverse=True)
            out.extend(items[:limit_per_code])
        out.sort(key=lambda x: (x["created_at"] or "", x["indicator_code"]), reverse=True)
        return out


def _now():
    from datetime import datetime
    return datetime.now()


# Need select in module namespace for async DB methods above.
from sqlalchemy import select  # noqa: E402

get_registered = register = None  # placeholders kept for symmetry w/ other services
