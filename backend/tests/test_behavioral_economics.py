import pytest
import numpy as np
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.analysis.behavioral_economics_service import BehavioralEconomicsService


class TestBehavioralEconomicsService:
    """Test cases for BehavioralEconomicsService."""

    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        service = BehavioralEconomicsService()
        service.logger = MagicMock()
        return service

    @pytest.mark.asyncio
    async def test_initialize(self, service):
        """Test service initialization creates HTTP session."""
        await service.initialize()
        service.logger.info.assert_called_with("BehavioralEconomicsService initialized")
        assert service.session is not None

    @pytest.mark.asyncio
    async def test_shutdown(self, service):
        """Test service shutdown closes HTTP session."""
        service.session = AsyncMock()
        await service.shutdown()
        service.logger.info.assert_called_with("BehavioralEconomicsService shutdown")

    @pytest.mark.asyncio
    async def test_behavioral_inconsistency_index(self, service):
        """Test Behavioral Inconsistency Index calculation."""
        market_data = {"sentiment": 0.8}
        survey_data = {"expectation": 0.3}
        result = await service.behavioral_inconsistency_index(market_data, survey_data)

        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0
        assert result > 0.0

    @pytest.mark.asyncio
    async def test_noise_trader_risk_low(self, service):
        """Test noise trader risk with stable data."""
        market_data = {
            "volatility": [0.01] * 20,
            "volume": [100] * 20,
        }
        result = await service._noise_trader_risk(market_data)

        assert "noise_risk" in result
        assert "volatility_clustering" in result
        assert "volume_spike_ratio" in result
        assert "confidence" in result
        assert result["noise_risk"] >= 0.0

    @pytest.mark.asyncio
    async def test_noise_trader_risk_high(self, service):
        """Test noise trader risk with volatile data."""
        market_data = {
            "volatility": [0.01, 0.05, 0.02, 0.08, 0.01, 0.06, 0.03, 0.09, 0.02, 0.07],
            "volume": [100, 500, 120, 600, 110, 550, 130, 700, 100, 600],
        }
        result = await service._noise_trader_risk(market_data)

        assert result["noise_risk"] > 0.0
        assert result["volume_spike_ratio"] > 1.0

    @pytest.mark.asyncio
    async def test_prospect_theory_weighting(self, service):
        """Test Prospect Theory value function asymmetry."""
        market_data = {
            "returns": [0.05, -0.02, 0.03, -0.05, 0.01, -0.03, 0.02, -0.01],
        }
        result = await service._prospect_theory_weighting(market_data)

        assert "value_function_asymmetry" in result
        assert "loss_aversion_ratio" in result
        assert "gain_count" in result
        assert "loss_count" in result
        assert result["gain_count"] > 0
        assert result["loss_count"] > 0

    @pytest.mark.asyncio
    async def test_prospect_theory_no_gains(self, service):
        """Test Prospect Theory with only losses."""
        market_data = {"returns": [-0.01, -0.02, -0.03, -0.01, -0.02]}
        result = await service._prospect_theory_weighting(market_data)

        assert result["value_function_asymmetry"] == 0.0

    @pytest.mark.asyncio
    async def test_behavioral_regime_classifier(self, service):
        """Test behavioral regime classification."""
        market_data = {
            "sentiment": 0.8,
            "noise_risk": {"noise_risk": 0.7},
            "volatility": [0.01] * 10,
        }
        result = await service._behavioral_regime_classifier(market_data)

        assert "regime" in result
        assert "confidence" in result
        assert "components" in result
        assert result["regime"] in [
            "irrational_exuberance",
            "panic_selling",
            "noise_dominated",
            "high_volatility",
            "normal",
        ]

    @pytest.mark.asyncio
    async def test_fetch_survey_data_invalid_source(self, service):
        """Test fetching survey data with invalid source."""
        result = await service.fetch_survey_data("invalid_source")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_analyze_full(self, service):
        """Test full behavioral economics analysis."""
        market_data = {
            "sentiment": 0.5,
            "volatility": [0.01] * 20,
            "volume": [100] * 20,
            "returns": [0.01, -0.01, 0.02, -0.02, 0.01],
        }
        survey_data = {"expectation": 0.4}
        result = await service.analyze({"market_data": market_data, "survey_data": survey_data})

        assert "behavioral_index" in result
        assert "noise_trader_risk" in result
        assert "prospect_theory" in result
        assert "regime_classifier" in result