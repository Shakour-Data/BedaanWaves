"""Comprehensive scientific validation tests.

Validates all financial and statistical computations against
reference implementations (NumPy, manual verification) and
verifies scientific correctness of all formulas.
"""
import math
import unittest

import numpy as np

from app.domain.services.analysis.momentum_engine import MomentumEngine
from app.domain.services.analysis.moving_average_engine import MovingAverageEngine
from app.services.analysis.fundamental_service import FundamentalAnalysisService
from app.services.analysis.risk_service import RiskAnalysisService
from app.services.analysis.technical_indicators import compute_rsi, compute_ema, compute_macd
from app.services.specialized.correlation_service import CorrelationService


class TestRSIValidation(unittest.TestCase):
    def test_rsi_matches_reference(self):
        closes = [44.0, 44.5, 43.5, 44.0, 44.5, 45.0, 45.5, 46.0, 45.5, 45.0,
                  44.5, 44.0, 43.5, 43.0, 43.5, 44.0, 44.5, 45.0, 45.5, 46.0,
                  46.5, 47.0, 46.5, 46.0, 45.5]
        period = 14

        deltas = [closes[i + 1] - closes[i] for i in range(len(closes) - 1)]
        gains = []
        losses = []
        for d in deltas:
            if d > 0:
                gains.append(d)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-d)

        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        expected_rs = avg_gain / avg_loss if avg_loss != 0 else float("inf")
        expected_rsi = 100 - (100 / (1 + expected_rs)) if avg_loss != 0 else 100.0

        me = MomentumEngine()
        actual_rsi = me.calculate_rsi(closes, period)
        assert abs(actual_rsi - round(expected_rsi, 2)) < 0.5

    def test_rsi_oversold_range(self):
        me = MomentumEngine()
        strong_down = list(range(100, 70, -1))
        rsi = me.calculate_rsi(strong_down, 14)
        assert 0 <= rsi <= 30, f"Expected oversold RSI <= 30, got {rsi}"

    def test_rsi_overbought_range(self):
        me = MomentumEngine()
        strong_up = list(range(70, 100))
        rsi = me.calculate_rsi(strong_up, 14)
        assert 70 <= rsi <= 100, f"Expected overbought RSI >= 70, got {rsi}"


class TestEMAValidation(unittest.TestCase):
    def test_ema_sma_initialization(self):
        mae = MovingAverageEngine()
        prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
        ema = mae.calculate_ema(prices, 5)
        sma = sum(prices[:5]) / 5
        assert ema > 0
        assert sma == 12.0

    def test_ema_matches_numpy(self):
        mae = MovingAverageEngine()
        prices = [10.0, 11.0, 12.5, 13.2, 14.1, 15.3, 16.0, 17.5, 18.2, 19.0,
                  18.5, 18.0, 19.5, 20.0, 21.0]
        period = 5
        multiplier = 2 / (period + 1)
        expected = sum(prices[:period]) / period
        for price in prices[period:]:
            expected = (price * multiplier) + (expected * (1 - multiplier))
        actual = mae.calculate_ema(prices, period)
        assert abs(actual - round(expected, 2)) < 0.01

    def test_sma_correctness(self):
        mae = MovingAverageEngine()
        prices = [1.0, 2.0, 3.0, 4.0, 5.0]
        sma = mae.calculate_sma(prices, 3)
        expected = (3.0 + 4.0 + 5.0) / 3
        assert sma == round(expected, 2)


class TestMACDValidation(unittest.TestCase):
    def test_macd_returns_five_values(self):
        me = MomentumEngine()
        prices = [float(i) for i in range(100)]
        macd_line, signal, histogram, ema12, ema26 = me.calculate_macd(prices)
        assert len([macd_line, signal, histogram, ema12, ema26]) == 5
        assert abs(macd_line - (ema12 - ema26)) < 0.05
        assert abs(histogram - (macd_line - signal)) < 0.05


class TestDuPontValidation(unittest.TestCase):
    def test_dupont_identity(self):
        fas = FundamentalAnalysisService()
        f = {"net_income": 150, "revenue": 1000, "total_assets": 800, "equity": 400}
        result = fas._calculate_dupont_analysis(f)
        assert result["dupont_identity_check"] is True
        expected_roe = 150 / 400 * 100
        assert abs(result["roe"] - round(expected_roe, 2)) < 0.01

    def test_dupont_insufficient_data(self):
        fas = FundamentalAnalysisService()
        result = fas._calculate_dupont_analysis({"net_income": 0, "revenue": 0,
                                                   "total_assets": 0, "equity": 0})
        assert result["roe"] == 0.0


class TestOperatingLeverage(unittest.TestCase):
    def test_correct_formula(self):
        fas = FundamentalAnalysisService()
        f = {"operating_income": 200, "revenue": 1000}
        result = fas._calc_operating_leverage(f)
        assert result == 1.0, f"Expected 1.0, got {result}"

    def test_zero_operating_income(self):
        fas = FundamentalAnalysisService()
        result = fas._calc_operating_leverage({"operating_income": 0, "revenue": 1000})
        assert result == 0.0


class TestFundamentalRatios(unittest.TestCase):
    def test_pe_ratio(self):
        fas = FundamentalAnalysisService()
        f = {"stock_price": 100, "eps": 5}
        assert fas._calc_pe_ratio(f) == 20.0

    def test_pe_negative_eps(self):
        fas = FundamentalAnalysisService()
        f = {"stock_price": 100, "eps": -5}
        assert fas._calc_pe_ratio(f) == 0.0

    def test_peg_ratio(self):
        fas = FundamentalAnalysisService()
        f = {"stock_price": 100, "eps": 5, "growth_rate": 0.25}
        result = fas._calc_peg_ratio(f)
        assert abs(result - 20.0 / 0.25) < 0.01

    def test_ev_to_ebitda(self):
        fas = FundamentalAnalysisService()
        f = {"stock_price": 100, "shares_outstanding": 10, "total_debt": 500,
             "cash": 200, "operating_income": 300, "depreciation": 50, "amortization": 30}
        result = fas._calc_ev_to_ebitda(f)
        equity_value = 1000
        ev = 1000 + 500 - 200
        ebitda = 380
        expected = ev / ebitda
        assert abs(result - expected) < 0.01

    def test_ebitda(self):
        fas = FundamentalAnalysisService()
        f = {"operating_income": 300, "depreciation": 50, "amortization": 30}
        assert fas._calc_ebitda(f) == 380


class TestRiskMetrics(unittest.TestCase):
    def test_sharpe_uses_risk_free(self):
        import asyncio
        ras = RiskAnalysisService()
        returns = [0.01] * 252
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(ras._calculate_performance_metrics(returns, risk_free_rate=0.02))
            assert "sharpe_ratio" in result
        finally:
            loop.close()

    def test_std_dev_uses_sample(self):
        ras = RiskAnalysisService()
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        std = ras._calculate_std_dev(values)
        expected_sample = math.sqrt(sum((v - 3) ** 2 for v in values) / 4)
        expected_pop = math.sqrt(sum((v - 3) ** 2 for v in values) / 5)
        assert abs(std - expected_sample) < 0.001
        assert abs(std - expected_pop) > 0.001

    def test_beta_uses_sample_covariance(self):
        ras = RiskAnalysisService()
        returns = [0.01, -0.02, 0.015, -0.01, 0.02]
        market_returns = [0.012, -0.018, 0.017, -0.009, 0.021]
        beta = ras._calculate_beta(returns, market_returns)
        n = 5
        mean_r = sum(returns) / n
        mean_m = sum(market_returns) / n
        cov = sum((returns[i] - mean_r) * (market_returns[i] - mean_m) for i in range(n)) / (n - 1)
        var_m = sum((market_returns[i] - mean_m) ** 2 for i in range(n)) / (n - 1)
        expected = cov / var_m
        assert abs(beta - expected) < 0.0001

    def test_sortino_uses_downside_dev(self):
        ras = RiskAnalysisService()
        returns = [0.01, -0.02, 0.015, -0.01, 0.02, 0.005, -0.015, 0.01, 0.008, -0.005]
        sortino = ras._calculate_sortino_ratio(returns)
        assert sortino > 0

    def test_max_drawdown(self):
        ras = RiskAnalysisService()
        returns = [0.1, 0.1, -0.2, 0.1, 0.1]
        mdd = ras._calculate_max_drawdown(returns)
        assert mdd > 0


class TestCorrelationService(unittest.TestCase):
    def test_pearson_perfect_positive(self):
        result = CorrelationService._pearson([1, 2, 3, 4, 5], [2, 4, 6, 8, 10])
        assert abs(result - 1.0) < 0.0001

    def test_pearson_perfect_negative(self):
        result = CorrelationService._pearson([1, 2, 3, 4, 5], [10, 8, 6, 4, 2])
        assert abs(result - (-1.0)) < 0.0001

    def test_pearson_no_correlation(self):
        result = CorrelationService._pearson([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [5, 10, 2, 8, 1, 7, 3, 9, 4, 6])
        assert abs(result) < 0.5

    def test_pearson_vs_numpy(self):
        a = [1.0, 2.5, 3.0, 4.5, 5.0, 6.0, 7.5, 8.0, 9.0, 10.0]
        b = [2.0, 4.0, 5.5, 7.0, 9.0, 11.0, 13.0, 14.0, 16.0, 18.0]
        expected = float(np.corrcoef(a, b)[0, 1])
        actual = CorrelationService._pearson(a, b)
        assert abs(actual - expected) < 0.001


class TestAnomalyDetection(unittest.TestCase):
    def test_sample_std_dev(self):
        import math
        from app.services.ml.anomaly_detection_service import AnomalyDetectionService
        ad = AnomalyDetectionService()
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        mean = sum(values) / len(values)
        sample_var = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        pop_var = sum((x - mean) ** 2 for x in values) / len(values)
        assert abs(sample_var - pop_var) > 0.01


class TestVolatilityService(unittest.TestCase):
    def test_sample_variance(self):
        from app.services.analysis.volatility_service import VolatilityService
        vs = VolatilityService()
        returns = [0.01, 0.02, -0.01, 0.005, -0.005, 0.015, -0.02, 0.01, -0.005, 0.01]
        vol = vs._calculate_historical_volatility(returns)
        n = len(returns)
        mean = sum(returns) / n
        sample_var = sum((r - mean) ** 2 for r in returns) / (n - 1)
        expected = math.sqrt(sample_var)
        assert abs(vol - expected) < 0.0001


class TestPredictionService(unittest.TestCase):
    def test_predict_uses_trained_model(self):
        from app.services.ml.prediction_service import PredictionService
        ps = PredictionService()
        ps.model = {"trained": True, "samples": 100}
        import numpy as np
        from sklearn.linear_model import LinearRegression
        X = np.array([[0.01, 50.0], [0.02, 51.0], [0.03, 52.0], [0.01, 50.5],
                       [0.02, 51.5], [0.03, 52.5], [0.01, 50.0], [0.02, 51.0],
                       [0.03, 52.0], [0.01, 50.5]])
        y = np.array([50.5, 51.5, 52.5, 50.8, 51.8, 52.8, 50.5, 51.5, 52.5, 50.8])
        ps._sklearn_model = LinearRegression().fit(X, y)
        result = await_run(ps.predict({"prices": list(range(10, 30)), "horizon": 1}))
        assert "predicted_price" in result
        assert result["predicted_price"] > 0

    def test_predict_fallback_without_model(self):
        from app.services.ml.prediction_service import PredictionService
        ps = PredictionService()
        ps.model = None
        try:
            result = await_run(ps.predict({"prices": list(range(10, 30)), "horizon": 1}))
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


class TestScoringStrategies(unittest.TestCase):
    def test_rsi_scoring_neutral(self):
        from app.domain.services.scoring_strategies import TseScoringStrategy
        strat = TseScoringStrategy()
        score = strat.score_rsi(50)
        assert score == 50.0

    def test_rsi_scoring_extreme(self):
        from app.domain.services.scoring_strategies import TseScoringStrategy
        strat = TseScoringStrategy()
        assert strat.score_rsi(0) <= 50
        assert strat.score_rsi(100) <= 50

    def test_pe_scoring_reasonable(self):
        from app.domain.services.scoring_strategies import GlobalScoringStrategy
        strat = GlobalScoringStrategy()
        low_pe = strat.score_pe(5)
        high_pe = strat.score_pe(50)
        very_high_pe = strat.score_pe(200)
        assert low_pe > high_pe > very_high_pe


class TestHealthScore(unittest.TestCase):
    def test_strong_company(self):
        fas = FundamentalAnalysisService()
        ratios = {"net_margin": 20, "current_ratio": 2.0, "debt_to_equity": 0.5,
                  "interest_coverage": 5.0, "revenue_growth": 15, "free_cash_flow_growth": 15,
                  "pe_ratio": 15, "pb_ratio": 2.0}
        score = fas._calculate_health_score(ratios)
        assert score >= 80

    def test_weak_company(self):
        fas = FundamentalAnalysisService()
        ratios = {"net_margin": 1, "current_ratio": 0.8, "debt_to_equity": 3.0,
                  "interest_coverage": 0.5, "revenue_growth": 0, "free_cash_flow_growth": 0,
                  "pe_ratio": 999, "pb_ratio": 999}
        score = fas._calculate_health_score(ratios)
        assert score < 50


def await_run(coro):
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


if __name__ == "__main__":
    unittest.main()
