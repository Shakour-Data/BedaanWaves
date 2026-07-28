"""Unit tests for Tier 3 RiskAnalysisService."""

import math

import pytest

from app.services.analysis.risk_service import RiskAnalysisService

pytestmark = pytest.mark.unit


class TestRiskAnalysisServiceInitialization:
    def test_default_service_name(self):
        service = RiskAnalysisService()
        assert service.service_name == "RiskAnalysisService"

    async def test_initialize_logs(self, caplog):
        service = RiskAnalysisService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.initialize()
        assert "RiskAnalysisService initialized" in caplog.text

    async def test_shutdown_logs(self, caplog):
        service = RiskAnalysisService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.shutdown()
        assert "RiskAnalysisService shutdown" in caplog.text


class TestAnalyze:
    async def test_insufficient_data_returns_error(self):
        service = RiskAnalysisService()
        result = await service.analyze({"returns": [0.01, -0.02]})
        assert "error" in result
        assert result["error"] == "Insufficient return data"

    async def test_valid_data_returns_metrics(self):
        service = RiskAnalysisService()
        returns = [0.01, -0.02, 0.015, -0.005, 0.02] * 5
        result = await service.analyze({
            "returns": returns,
            "ticker": "TEST",
        })
        assert result["ticker"] == "TEST"
        assert "metrics" in result
        assert "volatility" in result["metrics"]
        assert "annual_volatility" in result["metrics"]
        assert "beta" in result["metrics"]
        assert "var_95" in result["metrics"]
        assert "var_99" in result["metrics"]
        assert "cvar_95" in result["metrics"]
        assert "mean_return" in result["metrics"]
        assert "sharpe_ratio" in result["metrics"]
        assert "max_drawdown" in result["metrics"]
        assert "sortino_ratio" in result["metrics"]


class TestVolatilityMetrics:
    async def test_std_dev_basic(self):
        service = RiskAnalysisService()
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        std = service._calculate_std_dev(values)
        assert std > 0

    async def test_std_dev_empty(self):
        service = RiskAnalysisService()
        assert service._calculate_std_dev([]) == 0.0

    async def test_std_dev_single_value(self):
        service = RiskAnalysisService()
        assert service._calculate_std_dev([5.0]) == 0.0


class TestValueAtRisk:
    async def test_var_calculation(self):
        service = RiskAnalysisService()
        returns = [-0.05, -0.03, -0.01, 0.0, 0.01, 0.02, 0.03, 0.04] * 3
        result = await service._calculate_value_at_risk(returns)
        assert "var_95" in result
        assert "var_99" in result
        assert "cvar_95" in result
        assert result["var_95"] <= 0
        assert result["var_99"] <= result["var_95"]

    async def test_var_empty_returns(self):
        service = RiskAnalysisService()
        result = await service._calculate_value_at_risk([])
        assert "var_95" in result
        assert "var_99" in result


class TestPerformanceMetrics:
    async def test_sharpe_ratio_positive(self):
        service = RiskAnalysisService()
        returns = [0.01] * 20 + [0.02] * 5 + [-0.01] * 5
        result = await service._calculate_performance_metrics(returns)
        assert "mean_return" in result
        assert "sharpe_ratio" in result
        assert isinstance(result["sharpe_ratio"], float)

    async def test_max_drawdown(self):
        service = RiskAnalysisService()
        returns = [0.1, -0.2, 0.05, -0.1, 0.02]
        dd = service._calculate_max_drawdown(returns)
        assert dd > 0
        assert dd <= 100

    async def test_max_drawdown_empty(self):
        service = RiskAnalysisService()
        assert service._calculate_max_drawdown([]) == 0.0

    async def test_sortino_ratio(self):
        service = RiskAnalysisService()
        returns = [0.01, 0.02, -0.01, 0.015, -0.005, 0.01]
        sortino = service._calculate_sortino_ratio(returns)
        assert isinstance(sortino, float)


class TestPortfolioRisk:
    async def test_equal_weight_portfolio(self):
        service = RiskAnalysisService()
        weights = {"A": 0.5, "B": 0.5}
        correlations = {"A_A": 1.0, "A_B": 0.3, "B_A": 0.3, "B_B": 1.0}
        volatilities = {"A": 0.2, "B": 0.3}
        result = await service.calculate_portfolio_risk(weights, correlations, volatilities)
        assert "portfolio_volatility" in result
        assert "portfolio_var_95" in result
        assert "portfolio_var_99" in result
        assert result["portfolio_volatility"] >= 0

    async def test_single_asset_portfolio(self):
        service = RiskAnalysisService()
        weights = {"A": 1.0}
        correlations = {"A_A": 1.0}
        volatilities = {"A": 0.25}
        result = await service.calculate_portfolio_risk(weights, correlations, volatilities)
        assert result["portfolio_volatility"] == pytest.approx(0.25, rel=1e-6)

    async def test_zero_volatility_assets(self):
        service = RiskAnalysisService()
        weights = {"A": 1.0, "B": 0.0}
        correlations = {"A_A": 1.0, "A_B": 0.0, "B_A": 0.0, "B_B": 1.0}
        volatilities = {"A": 0.0, "B": 0.0}
        result = await service.calculate_portfolio_risk(weights, correlations, volatilities)
        assert result["portfolio_volatility"] == 0.0


class TestStressTest:
    async def test_single_scenario(self):
        service = RiskAnalysisService()
        portfolio = {"A": 100000.0, "B": 50000.0}
        scenarios = [{"A": -0.2, "B": 0.1}]
        results = await service.stress_test(portfolio, scenarios)
        assert len(results) == 1
        assert results[0]["loss"] == 15000.0
        assert results[0]["portfolio_value"] == 135000.0

    async def test_multiple_scenarios(self):
        service = RiskAnalysisService()
        portfolio = {"A": 100000.0}
        scenarios = [
            {"A": -0.1},
            {"A": -0.3},
            {"A": 0.1},
        ]
        results = await service.stress_test(portfolio, scenarios)
        assert len(results) == 3
        assert results[0]["loss"] == pytest.approx(10000.0)
        assert results[1]["loss"] == pytest.approx(30000.0)
        assert results[2]["loss"] == pytest.approx(-10000.0)

    async def test_empty_scenarios(self):
        service = RiskAnalysisService()
        portfolio = {"A": 1000.0}
        results = await service.stress_test(portfolio, [])
        assert len(results) == 0
