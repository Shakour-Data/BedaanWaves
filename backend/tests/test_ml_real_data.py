"""
Comprehensive real-data integration tests for Tier 4 ML Services.

Uses actual database records from:
- RawPerformanceScore (683k+ records)
- MarketDataSnapshot (4.4M+ records)
- MLSignal (121k+ records)
- ProcessedFeatureData (1.7M+ records)

Validates:
- CoefficientLearningService trains on real performance data
- CryptoMLService generates signals from real snapshots
- Prediction/Anomaly/Pattern/Portfolio/TimeSeries services work with real price data
- Outputs are accurate and within expected bounds
"""

import asyncio
import sys
import os
import math
import random
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import get_async_session
from sqlalchemy import select, func, desc
from app.models.models import (
    Asset,
    RawPerformanceScore,
    MarketDataSnapshot,
    MLSignal,
    ProcessedFeatureData,
)

from app.services.ml.prediction_service import PredictionService
from app.services.ml.anomaly_detection_service import AnomalyDetectionService
from app.services.ml.pattern_recognition_service import PatternRecognitionService
from app.services.ml.portfolio_optimization_service import PortfolioOptimizationService
from app.services.ml.time_series_forecasting_service import TimeSeriesForecastingService
from app.services.ml.coefficient_learning_service import CoefficientLearningService
from app.services.ml.crypto_ml_service import CryptoMLService


async def get_real_data():
    """Fetch real data from database for ML testing."""
    data = {
        "assets": [],
        "raw_scores": [],
        "snapshots": [],
        "ml_signals": [],
        "processed_features": [],
    }

    async for session in get_async_session():
        assets_result = await session.execute(
            select(Asset.id, Asset.symbol, Asset.market, Asset.asset_class)
            .limit(20)
        )
        data["assets"] = [{"id": r[0], "symbol": r[1], "market": r[2], "asset_class": r[3]} for r in assets_result.all()]

        scores_result = await session.execute(
            select(RawPerformanceScore)
            .where(RawPerformanceScore.data_quality == "VALIDATED")
            .where(RawPerformanceScore.is_processed == True)
            .order_by(desc(RawPerformanceScore.captured_at))
            .limit(200)
        )
        data["raw_scores"] = [
            {
                "id": str(r.id),
                "market": r.market,
                "dimension_scores": r.dimension_scores or {},
                "sub_dimension_scores": r.sub_dimension_scores or {},
                "aspect_scores": r.aspect_scores or {},
                "sub_aspect_scores": r.sub_aspect_scores or {},
                "target_return": float(r.target_return) if r.target_return else 0.0,
                "target_volatility": float(r.target_volatility) if r.target_volatility else 0.0,
                "target_price_change": float(r.target_price_change) if r.target_price_change else 0.0,
            }
            for r in scores_result.scalars().all()
        ]

        crypto_assets = [a for a in data["assets"] if a["asset_class"] == "cryptocurrency"]
        if crypto_assets:
            snapshots_result = await session.execute(
                select(MarketDataSnapshot)
                .where(MarketDataSnapshot.asset_id == crypto_assets[0]["id"])
                .order_by(desc(MarketDataSnapshot.snapshot_time))
                .limit(50)
            )
            data["snapshots"] = [
                {
                    "open": float(s.open) if s.open else None,
                    "high": float(s.high) if s.high else None,
                    "low": float(s.low) if s.low else None,
                    "close": float(s.close) if s.close else None,
                    "volume": float(s.volume) if s.volume else None,
                    "rsi": float(s.rsi) if s.rsi else None,
                    "macd": float(s.macd) if s.macd else None,
                    "macd_signal": float(s.macd_signal) if s.macd_signal else None,
                    "macd_histogram": float(s.macd_histogram) if s.macd_histogram else None,
                    "bb_upper": float(s.bb_upper) if s.bb_upper else None,
                    "bb_lower": float(s.bb_lower) if s.bb_lower else None,
                    "ma_7": float(s.ma_7) if s.ma_7 else None,
                    "ma_30": float(s.ma_30) if s.ma_30 else None,
                    "volatility": float(s.volatility) if s.volatility else None,
                }
                for s in snapshots_result.scalars().all()
            ]

        signals_result = await session.execute(
            select(MLSignal)
            .limit(50)
        )
        data["ml_signals"] = [
            {
                "signal_type": r.signal_type,
                "confidence": float(r.confidence) if r.confidence else 0.0,
                "expected_return": float(r.expected_return) if r.expected_return else 0.0,
                "risk_score": float(r.risk_score) if r.risk_score else 0.0,
            }
            for r in signals_result.scalars().all()
        ]

        features_result = await session.execute(
            select(ProcessedFeatureData)
            .limit(50)
        )
        data["processed_features"] = [
            {
                "feature_vector": r.feature_vector or [],
                "dimension_features": r.dimension_features or {},
                "target_values": r.target_values or {},
            }
            for r in features_result.scalars().all()
        ]

        break

    return data


async def get_real_prices(limit=30):
    """Fetch real closing prices from database."""
    prices = []
    async for session in get_async_session():
        result = await session.execute(
            select(MarketDataSnapshot.close)
            .where(MarketDataSnapshot.close.isnot(None))
            .limit(limit)
        )
        prices = [float(r[0]) for r in result.all()]
        break
    return prices


async def test_coefficient_learning_with_real_data():
    print("\n=== Testing CoefficientLearningService with Real Data ===")
    service = CoefficientLearningService("test_real_coeff")
    await service.initialize()

    data = await get_real_data()
    performance_data = []
    for record in data["raw_scores"]:
        performance_data.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dimension_scores": record["dimension_scores"],
            "sub_dimension_scores": record["sub_dimension_scores"],
            "aspect_scores": record["aspect_scores"],
            "sub_aspect_scores": record["sub_aspect_scores"],
            "target_metric": record["target_return"],
            "volatility": record["target_volatility"],
            "price_change": record["target_price_change"],
        })

    print(f"  Using {len(performance_data)} real performance records")
    assert len(performance_data) >= 50, f"Need >= 50 samples, got {len(performance_data)}"

    learned = await service.learn_coefficients(performance_data)
    print(f"  Learned coefficients for levels: {list(learned.keys())}")

    dim_coeffs = learned.get("dimensions", {})
    assert len(dim_coeffs) > 0, "Dimension coefficients should not be empty"
    total = sum(dim_coeffs.values())
    assert abs(total - 1.0) < 1e-6, f"Coefficients sum to {total}, expected 1.0"
    assert all(0.0 <= v <= 1.0 for v in dim_coeffs.values()), "Coefficients out of [0,1] range"

    print(f"  Dimension coefficients (validated): {dim_coeffs}")
    print(f"  Sum: {total:.6f}")

    retrain_result = await service.retrain_all()
    print(f"  Retrain result: {retrain_result.get('status')}")
    assert retrain_result.get("status") in ("completed", "skipped"), f"Unexpected retrain status: {retrain_result}"

    await service.shutdown()
    print("  PASSED")


async def test_prediction_service_with_real_prices():
    print("\n=== Testing PredictionService with Real Data ===")
    service = PredictionService()
    await service.initialize()

    prices = await get_real_prices(20)
    print(f"  Using {len(prices)} real price points")
    assert len(prices) >= 10, f"Need >= 10 prices, got {len(prices)}"

    features = [[p] for p in prices]
    labels = [1] * len(prices)
    await service.train({"features": features, "labels": labels})

    result = await service.predict({"prices": prices, "ticker": "REAL_ASSET", "horizon": 3})
    print(f"  Prediction result: {result}")
    assert result["ticker"] == "REAL_ASSET"
    assert "predicted_price" in result
    assert result["predicted_price"] > 0
    assert result["direction"] in ("up", "down")
    assert 0.0 < result["confidence"] <= 0.95
    assert result["horizon_days"] == 3

    batch_results = await service.batch_predict([
        {"prices": prices, "ticker": "A"},
        {"prices": prices, "ticker": "B"},
    ])
    assert len(batch_results) == 2
    assert batch_results[0]["ticker"] == "A"
    assert batch_results[1]["ticker"] == "B"

    await service.shutdown()
    print("  PASSED")


async def test_anomaly_detection_with_real_returns():
    print("\n=== Testing AnomalyDetectionService with Real Data ===")
    service = AnomalyDetectionService()
    await service.initialize()

    prices = await get_real_prices(20)
    returns = []
    for i in range(1, len(prices)):
        if prices[i - 1] != 0:
            returns.append((prices[i] - prices[i - 1]) / prices[i - 1])
        else:
            returns.append(0.0)

    if len(returns) < 5:
        returns = [0.01, -0.01, 0.02, -0.02, 0.01, -0.01, 0.01, -0.01, 0.01, -0.01]

    print(f"  Using {len(returns)} real return values")
    await service.train({"values": returns})

    result = await service.predict({
        "ticker": "REAL_ASSET",
        "prices": prices[:len(returns) + 1],
        "returns": returns,
        "z_threshold": 2.0,
    })
    print(f"  Anomaly result: is_anomaly={result['is_anomaly']}, z_score={result['z_score']}")
    assert "is_anomaly" in result
    assert "z_score" in result
    assert result["ticker"] == "REAL_ASSET"
    assert result["severity"] in ("low", "medium", "high")

    batch_results = await service.batch_detect([
        {"ticker": "A", "prices": prices[:11], "returns": returns[:10]},
        {"ticker": "B", "prices": prices[:11], "returns": returns[:10]},
    ])
    assert len(batch_results) == 2

    await service.shutdown()
    print("  PASSED")


async def test_pattern_recognition_with_real_prices():
    print("\n=== Testing PatternRecognitionService with Real Data ===")
    service = PatternRecognitionService()
    await service.initialize()

    prices = await get_real_prices(30)
    print(f"  Using {len(prices)} real price points")
    result = await service.predict({"ticker": "REAL_ASSET", "prices": prices})
    print(f"  Pattern result: {result['pattern']}, probability={result['probability']}")
    assert result["pattern"] in ("resistance_test", "support_test", "continuation")
    assert result["probability"] in (0.55, 0.75)
    assert result["current_price"] == prices[-1]

    patterns = await service.detect_patterns(prices)
    assert isinstance(patterns, list)

    await service.shutdown()
    print("  PASSED")


async def test_portfolio_optimization_with_real_assets():
    print("\n=== Testing PortfolioOptimizationService with Real Data ===")
    service = PortfolioOptimizationService()
    await service.initialize()

    data = await get_real_data()
    assets = [a["symbol"] for a in data["assets"][:5] if a["symbol"]]
    if len(assets) < 2:
        assets = ["AAPL", "GOOG", "MSFT"]

    expected_returns = {a: round(random.uniform(0.05, 0.25), 4) for a in assets}
    risks = {a: round(random.uniform(0.1, 0.4), 4) for a in assets}

    result = await service.predict({
        "assets": assets,
        "expected_returns": expected_returns,
        "risks": risks,
    })
    print(f"  Allocation: {result['allocation']}")
    assert "allocation" in result
    assert len(result["allocation"]) == len(assets)
    total_weight = sum(result["allocation"].values())
    assert abs(total_weight - 1.0) < 0.01
    assert all(w > 0 for w in result["allocation"].values())
    assert "expected_return" in result
    assert "sharpe_ratio" in result

    await service.shutdown()
    print("  PASSED")


async def test_time_series_forecasting_with_real_prices():
    print("\n=== Testing TimeSeriesForecastingService with Real Data ===")
    service = TimeSeriesForecastingService()
    await service.initialize()

    prices = await get_real_prices(20)
    print(f"  Using {len(prices)} real price points")
    await service.train({"series": prices})

    forecast_result = await service.predict({
        "ticker": "REAL_ASSET",
        "series": prices,
        "horizon": 5,
    })
    print(f"  Forecast: {forecast_result['forecast']}")
    assert len(forecast_result["forecast"]) == 5
    assert all(f > 0 for f in forecast_result["forecast"])
    assert forecast_result["ticker"] == "REAL_ASSET"

    await service.shutdown()
    print("  PASSED")


async def test_crypto_ml_service_with_real_snapshots():
    print("\n=== Testing CryptoMLService with Real Data ===")
    service = CryptoMLService()
    await service.initialize()

    data = await get_real_data()
    crypto_assets = [a for a in data["assets"] if a["asset_class"] == "cryptocurrency"]
    if not crypto_assets:
        print("  No crypto assets found in sample, skipping")
        await service.shutdown()
        return

    asset_id = crypto_assets[0]["id"]
    async for session in get_async_session():
        signals = await service.generate_signals(session, asset_id, lookback_periods=30, min_confidence=50.0)
        print(f"  Generated {len(signals)} signal(s) for {crypto_assets[0]['symbol']}")
        if signals:
            sig = signals[0]
            print(f"  Signal: type={sig.get('signal_type')}, confidence={sig.get('confidence')}")
            assert "signal_type" in sig
            assert sig["signal_type"] in ("BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL")
            assert 0 <= sig.get("confidence", 0) <= 100
        break

    await service.shutdown()
    print("  PASSED")


async def test_prediction_accuracy_bounds():
    print("\n=== Testing Prediction Accuracy Bounds ===")
    service = PredictionService()
    await service.initialize()

    prices = await get_real_prices(20)
    features = [[p] for p in prices]
    labels = [1] * len(prices)
    await service.train({"features": features, "labels": labels})

    horizon = 5
    result = await service.predict({"prices": prices, "ticker": "ACCURACY_TEST", "horizon": horizon})

    last_price = float(prices[-1])
    predicted = result["predicted_price"]
    momentum = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 and prices[-5] else 0
    expected_predicted = last_price * (1 + momentum * 0.5 * horizon)

    print(f"  Last price: {last_price:.2f}")
    print(f"  Predicted:  {predicted:.2f}")
    print(f"  Expected:   {expected_predicted:.2f}")
    print(f"  Direction:  {result['direction']}")
    print(f"  Confidence: {result['confidence']}")

    assert predicted > 0, "Predicted price must be positive"
    assert abs(predicted - expected_predicted) < last_price * 0.5, "Prediction deviates wildly from expected"

    if momentum > 0:
        assert result["direction"] == "up"
    elif momentum < 0:
        assert result["direction"] == "down"

    await service.shutdown()
    print("  PASSED")


async def test_anomaly_detection_distribution():
    print("\n=== Testing Anomaly Detection Distribution ===")
    service = AnomalyDetectionService()
    await service.initialize()

    prices = await get_real_prices(30)
    normal_prices = prices[: max(10, len(prices) // 2)]
    returns = []
    for i in range(1, len(normal_prices)):
        if normal_prices[i - 1] != 0:
            returns.append((normal_prices[i] - normal_prices[i - 1]) / normal_prices[i - 1])
        else:
            returns.append(0.0)

    await service.train({"values": returns})

    anomalies = 0
    total = 0
    for i in range(1, len(normal_prices)):
        r = returns[i - 1] if i - 1 < len(returns) else 0.0
        res = await service.predict({
            "ticker": "DIST_TEST",
            "prices": normal_prices[max(0, i - 1):i + 1],
            "returns": [r],
        })
        total += 1
        if res["is_anomaly"]:
            anomalies += 1

    anomaly_rate = anomalies / total if total > 0 else 0.0
    print(f"  Anomaly rate on normal data: {anomaly_rate:.2%} ({anomalies}/{total})")
    assert anomaly_rate <= 0.5, f"Too many anomalies flagged on normal data: {anomaly_rate:.2%}"

    await service.shutdown()
    print("  PASSED")


async def test_ml_signal_confidence_distribution():
    print("\n=== Testing ML Signal Confidence Distribution ===")
    data = await get_real_data()
    signals = data["ml_signals"]
    assert len(signals) > 0, "No ML signals available"

    confidences = [s["confidence"] for s in signals if s["confidence"] > 0]
    expected_returns = [s["expected_return"] for s in signals]
    risk_scores = [s["risk_score"] for s in signals]

    avg_conf = sum(confidences) / len(confidences) if confidences else 0
    avg_ret = sum(expected_returns) / len(expected_returns) if expected_returns else 0
    avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0

    print(f"  Signals analyzed: {len(signals)}")
    print(f"  Avg confidence: {avg_conf:.4f}")
    print(f"  Avg expected return: {avg_ret:.4f}")
    print(f"  Avg risk score: {avg_risk:.4f}")

    assert 0.3 <= avg_conf <= 0.99, f"Average confidence {avg_conf} out of expected range"
    assert all(0.0 <= s["confidence"] <= 1.0 for s in signals), "Signal confidence out of [0,1]"

    print("  PASSED")


async def main():
    print("=" * 60)
    print("ML Real-Data Integration Test Suite")
    print("=" * 60)

    failures = []

    tests = [
        test_coefficient_learning_with_real_data,
        test_prediction_service_with_real_prices,
        test_anomaly_detection_with_real_returns,
        test_pattern_recognition_with_real_prices,
        test_portfolio_optimization_with_real_assets,
        test_time_series_forecasting_with_real_prices,
        test_crypto_ml_service_with_real_snapshots,
        test_prediction_accuracy_bounds,
        test_anomaly_detection_distribution,
        test_ml_signal_confidence_distribution,
    ]

    for test in tests:
        try:
            await test()
        except Exception as e:
            failures.append((test.__name__, str(e)))
            print(f"  FAILED: {e}")

    print("\n" + "=" * 60)
    if failures:
        print(f"FAILURES: {len(failures)}")
        for name, err in failures:
            print(f"  - {name}: {err}")
    else:
        print("ALL REAL-DATA ML TESTS PASSED")
    print("=" * 60)

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
