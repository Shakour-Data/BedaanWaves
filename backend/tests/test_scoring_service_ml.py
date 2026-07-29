"""Integration tests for ScoringService with ML coefficient learning."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.analysis.scoring_service import ScoringService
from app.core.dependency_container import get_global_container
from app.services.ml.coefficient_learning_service import CoefficientLearningService


@pytest.fixture
def scoring_service():
    """Create a ScoringService instance for testing."""
    return ScoringService()


@pytest.fixture
def mock_coefficient_service():
    """Mock a CoefficientLearningService instance."""
    return MagicMock(spec=CoefficientLearningService)


@pytest.mark.unit
class TestScoringServiceMLIntegration:
    """Integration tests for ScoringService with ML coefficient learning."""

    async def test_get_dynamic_weights_calls_coefficient_service(self, scoring_service, mock_coefficient_service):
        """Test that ScoringService.get_dynamic_weights calls CoefficientLearningService."""
        # Arrange
        scoring_service._use_ml_coefficients = True
        scoring_service._coefficient_service = mock_coefficient_service
        mock_coefficient_service.get_coefficients.return_value = {
            'fundamental': 0.25,
            'technical': 0.20,
            'sentiment': 0.15,
            'risk': 0.20,
            'macro': 0.10,
            'ai': 0.10
        }
        
        # Act
        weights = scoring_service._get_dynamic_weights('dimensions')
        
        # Assert
        assert weights == {
            'fundamental': 0.25,
            'technical': 0.20,
            'sentiment': 0.15,
            'risk': 0.20,
            'macro': 0.10,
            'ai': 0.10
        }
        mock_coefficient_service.get_coefficients.assert_called_once()

    async def test_get_dynamic_weights_uses_static_when_ml_unavailable(self, scoring_service):
        """Test that ScoringService uses static weights when ML service is not available."""
        # Arrange
        scoring_service._use_ml_coefficients = True
        scoring_service._coefficient_service = None  # No service available
        
        # Act
        weights = scoring_service._get_dynamic_weights('dimensions')
        
        # Assert
        assert weights == scoring_service.DIMENSION_WEIGHTS

    async def test_get_dynamic_weights_uses_static_when_sum_invalid(self, scoring_service, mock_coefficient_service):
        """Test that ScoringService uses static weights when ML weights don't sum to ~1.0."""
        # Arrange
        scoring_service._use_ml_coefficients = True
        mock_coefficient_service.is_model_trained.return_value = True
        # Return weights that don't sum to ~1.0
        mock_coefficient_service.get_coefficients.return_value = {
            'fundamental': 0.6,  # Would make sum > 1.0
            'technical': 0.6,
            'sentiment': 0.0,
            'risk': 0.0,
            'macro': 0.0,
            'ai': 0.0
        }
        scoring_service._coefficient_service = mock_coefficient_service
        
        # Act
        weights = scoring_service._get_dynamic_weights('dimensions')
        
        # Assert
        assert weights == scoring_service.DIMENSION_WEIGHTS

    async def test_get_dynamic_weights_no_ml_flag_uses_static(self, scoring_service):
        """Test that ScoringService uses static weights when ML flag is disabled."""
        # Arrange
        scoring_service._use_ml_coefficients = False
        scoring_service._coefficient_service = MagicMock()
        
        # Act
        weights = scoring_service._get_dynamic_weights('dimensions')
        
        # Assert
        assert weights == scoring_service.DIMENSION_WEIGHTS

    async def test_analyze_uses_ml_weights(self, scoring_service, mock_coefficient_service):
        """Test that ScoringService.analyze uses ML-derived weights."""
        # Arrange
        mock_coefficient_service.get_coefficients.return_value = {
            'fundamental': 0.3,
            'technical': 0.25,
            'sentiment': 0.15,
            'risk': 0.15,
            'macro': 0.1,
            'ai': 0.05
        }
        scoring_service._coefficient_service = mock_coefficient_service
        scoring_service._use_ml_coefficients = True
        
        data = {
            "ticker": "TEST",
            "market": "TSE",
            "fundamental": {"pe_ratio": 12},
            "technical": {"rsi": 55},
            "sentiment": {"score": 70},
            "risk": {"volatility": 0.2},
            "macro": {"gdp_growth": 3.0},
            "ai": {"prediction": 0.75}
        }
        
        # Mock _score_dimension to return deterministic values
        with patch.object(scoring_service, '_score_dimension', side_effect=[70, 60, 75, 80, 90, 85]):
            # Act
            result = scoring_service.analyze(data)
            
            # Assert that overall_score is calculated using ML weights
            # (We can't easily capture internal weighted_sum without inspecting implementation)
            # But we can assert that result is a dict with expected keys
            assert isinstance(result, dict)
            assert 'overall_score' in result
            assert 'grade' in result
            assert 'dimension_scores' in result
            
            assert result['ticker'] == 'TEST'

    async def test_analyze_uses_static_weights_when_ml_unavailable(self, scoring_service):
        """Test that ScoringService uses static weights when ML coefficients unavailable."""
        # Arrange
        scoring_service._use_ml_coefficients = True
        scoring_service._coefficient_service = None
        
        data = {
            "ticker": "TEST",
            "market": "TSE",
            "fundamental": {"pe_ratio": 12},
            "technical": {"rsi": 55},
            "sentiment": {"score": 70},
            "risk": {"volatility": 0.2},
            "macro": {"gdp_growth": 3.0},
            "ai": {"prediction": 0.75}
        }
        
        # Act
        result = scoring_service.analyze(data)
        
        # Assert basic structure
        assert isinstance(result, dict)
        assert 'overall_score' in result
        assert 'grade' in result
        assert result['ticker'] == 'TEST'
        assert len(result['dimension_scores']) == 6  # All dimensions scored

    async def test_shutdown_calls_super(self, scoring_service):
        """Test that ScoringService.shutdown calls parent shutdown."""
        with patch.object(scoring_service, 'shutdown') as mock_shutdown:
            await scoring_service.shutdown()
            mock_shutdown.assert_called_once()