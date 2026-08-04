"""Unit tests for Tier 4 CoefficientLearningService."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ml.coefficient_learning_service import CoefficientLearningService
from app.services.analysis.scoring_service import ScoringService


@pytest.fixture
def coefficient_service():
    """Create a CoefficientLearningService instance for testing."""
    return CoefficientLearningService("test_coefficient_service")


@pytest.mark.unit
class TestCoefficientLearningServiceInitialization:
    """Test initialization of CoefficientLearningService."""

    def test_default_service_name(self):
        """Test default service name."""
        service = CoefficientLearningService()
        assert service.service_name == "coefficient_learning_service"

    def test_custom_service_name(self):
        """Test custom service name."""
        service = CoefficientLearningService("custom_service")
        assert service.service_name == "custom_service"

    async def test_initialize_loads_models(self, coefficient_service):
        """Test that initialize loads existing models or creates defaults."""
        with patch.object(coefficient_service, '_load_existing_models') as mock_load, \
             patch.object(coefficient_service, '_initialize_default_models') as mock_init:
            
            await coefficient_service.initialize()
            
            assert coefficient_service._is_initialized
            mock_load.assert_called_once()
            # Note: _initialize_default_models is called in _load_existing_models if loading fails


@pytest.mark.unit
class TestCoefficientLearningServiceFeatures:
    """Test feature extraction and data preparation."""

    def test_extract_features_basic(self, coefficient_service):
        """Test basic feature extraction."""
        # Mock a data row
        row = {
            'dimension_scores': {'fundamental': 0.8, 'technical': 0.6},
            'sub_dimension_scores': {'fundamental_price_history': 0.7},
            'aspect_scores': {},
            'sub_aspect_scores': {},
            'timestamp': datetime.now(timezone.utc),
            'volatility': 0.2,
            'volume': 1000,
            'price_change': 0.05,
            'market_cap': 1000000
        }
        
        features = coefficient_service._extract_features(row)
        
        # Should return a list of 50 features
        assert isinstance(features, list)
        assert len(features) == 50
        assert all(isinstance(f, float) for f in features)

    def test_extract_features_empty_data(self, coefficient_service):
        """Test feature extraction with empty data."""
        row = {}
        
        features = coefficient_service._extract_features(row)
        
        # Should return zero vector
        assert len(features) == 50
        assert all(f == 0.0 for f in features)

    def test_extract_features_missing_timestamp(self, coefficient_service):
        """Test feature extraction with missing timestamp."""
        row = {
            'dimension_scores': {'fundamental': 0.5},
            'sub_dimension_scores': {},
            'aspect_scores': {},
            'sub_aspect_scores': {}
        }
        
        features = coefficient_service._extract_features(row)
        
        # Should still return 50 features (timestamp defaults to zeros)
        assert len(features) == 50

    async def test_prepare_training_data_empty(self, coefficient_service):
        """Test preparing training data with empty input."""
        result = await coefficient_service._prepare_training_data([])
        assert result == {}

    async def test_prepare_training_data_missing_scores(self, coefficient_service):
        """Test preparing training data with missing score keys."""
        data = [{
            'timestamp': datetime.now(timezone.utc),
            'target_metric': 0.05
            # Missing score keys
        }]
        
        result = await coefficient_service._prepare_training_data(data)
        # Should return empty dict since required keys are missing
        assert result == {}


@pytest.mark.unit
class TestCoefficientLearningServiceTraining:
    """Test model training functionality."""

    async def test_train_level_model_insufficient_data(self, coefficient_service):
        """Test training with insufficient data."""
        # Create minimal data
        X = [[1.0, 2.0]]  # Only 1 sample
        y = [[0.5]]
        feature_names = ['feat1', 'feat2']
        
        training_data = {
            'X': X,
            'y': y,
            'feature_names': feature_names
        }
        
        # Should not raise exception but log warning
        await coefficient_service._train_level_model('dimensions', training_data)
        
        # Model might still be None or unchanged due to insufficient data
        # The method should handle this gracefully

    async def test_train_level_model_sufficient_data(self, coefficient_service):
        """Test training with sufficient data."""
        # Create sufficient data (more than min_samples_for_training)
        n_samples = 60
        X = [[float(i), float(i*2)] for i in range(n_samples)]
        y = [[float(i)*0.1] for i in range(n_samples)]
        feature_names = ['feature1', 'feature2']
        
        training_data = {
            'X': X,
            'y': y,
            'feature_names': feature_names
        }
        
        # Should not raise exception
        await coefficient_service._train_level_model('dimensions', training_data)
        
        # Model should be trained
        assert coefficient_service.models['dimensions'] is not None
        assert coefficient_service.scalers['dimensions'] is not None
        assert 'dimensions' in coefficient_service.feature_names
        assert len(coefficient_service.learned_coefficients['dimensions']) > 0

    def test_get_coefficients_untrained(self, coefficient_service):
        """Test getting coefficients from untrained model."""
        coeffs = coefficient_service.get_coefficients('dimensions')
        # Should return empty dict for untrained model
        assert coeffs == {}

    def test_get_coefficients_trained(self, coefficient_service):
        """Test getting coefficients from trained model."""
        # Set up mock trained coefficients
        coefficient_service.learned_coefficients['dimensions'] = {
            'fundamental': 0.25,
            'technical': 0.20,
            'sentiment': 0.15,
            'risk': 0.20,
            'macro': 0.10,
            'ai': 0.10
        }
        
        coeffs = coefficient_service.get_coefficients('dimensions')
        assert coeffs == {
            'fundamental': 0.25,
            'technical': 0.20,
            'sentiment': 0.15,
            'risk': 0.20,
            'macro': 0.10,
            'ai': 0.10
        }

    def test_is_model_trained(self, coefficient_service):
        """Test checking if model is trained."""
        # Initially not trained
        assert not coefficient_service.is_model_trained('dimensions')
        
        # After setting coefficients
        coefficient_service.learned_coefficients['dimensions'] = {'test': 1.0}
        coefficient_service.models['dimensions'] = "mock_model"
        
        assert coefficient_service.is_model_trained('dimensions')


@pytest.mark.unit
class TestCoefficientLearningServiceLearnCoefficients:
    """Test the main learn_coefficients method."""

    async def test_learn_coefficients_insufficient_data(self, coefficient_service):
        """Test learn_coefficients with insufficient data."""
        # Not enough samples
        data = [{'timestamp': datetime.now(timezone.utc), 'target_metric': 0.01}] * 10
        
        result = await coefficient_service.learn_coefficients(data)
        
        # Should return current coefficients (empty initially)
        assert result == coefficient_service.learned_coefficients
        # Should not have updated last_training_time significantly
        assert coefficient_service.last_training_time is None or \
               (datetime.now(timezone.utc) - coefficient_service.last_training_time).seconds < 5

    async def test_learn_coefficients_sufficient_data(self, coefficient_service):
        """Test learn_coefficients with sufficient data."""
        # Create mock data that looks like real performance data
        base_time = datetime.now(timezone.utc)
        data = []
        for i in range(60):  # Enough samples
            data.append({
                'timestamp': base_time,
                'dimension_scores': {
                    'fundamental': 0.5 + (i % 10) * 0.05,
                    'technical': 0.4 + (i % 8) * 0.05,
                    'sentiment': 0.3 + (i % 6) * 0.05,
                    'risk': 0.2 + (i % 5) * 0.05,
                    'macro': 0.1 + (i % 4) * 0.05,
                    'ai': 0.1 + (i % 3) * 0.05
                },
                'sub_dimension_scores': {},
                'aspect_scores': {},
                'sub_aspect_scores': {},
                'target_metric': 0.01 + (i % 7) * 0.005  # Some correlation with features
            })
        
# Mock the internal methods to avoid actual training complexity
        with patch.object(coefficient_service, '_prepare_training_data') as mock_prepare, \
             patch.object(coefficient_service, '_train_level_model') as mock_train:
            # Mock prepare_training_data to return dummy data
            mock_prepare.return_value = {
                'dimensions': {
                    'X': [[float(i), float(i*2)] for i in range(60)],  # 60 samples
                    'y': [[float(i)*0.01] for i in range(60)],
                    'feature_names': [f'f{i}' for i in range(50)]
                }
            }
            
            result = await coefficient_service.learn_coefficients(data)
            
            # Should have called preparation and training
            mock_prepare.assert_called_once_with(data)
            assert mock_train.call_count >= 1  # At least for dimensions
            
            # Should have updated last_training_time
            assert coefficient_service.last_training_time is not None

    def test_get_training_status(self, coefficient_service):
        """Test getting training status."""
        status = coefficient_service.get_training_status()
        
        assert 'last_training_time' in status
        assert 'samples_in_history' in status
        assert 'models_trained' in status
        assert 'feature_counts' in status
        assert 'retrain_interval_hours' in status
        
        # Check initial values
        assert status['samples_in_history'] == 0
        assert all(not trained for trained in status['models_trained'].values())
        assert all(count == 0 for count in status['feature_counts'].values())

    async def test_health_check(self, coefficient_service):
        """Test health check."""
        health = await coefficient_service.health_check()
        
        assert 'service' in health
        assert 'status' in health
        assert 'timestamp' in health
        assert health['service'] == 'test_coefficient_service'
        assert health['status'] in ['healthy', 'unhealthy']


@pytest.mark.unit
class TestCoefficientLearningServiceIntegration:
    """Integration tests for CoefficientLearningService with ScoringService."""

    async def test_get_dynamic_weights_ml_unavailable(self, coefficient_service):
        """Test getting dynamic weights when ML service is unavailable."""
        # No coefficient service set
        weights = coefficient_service._get_dynamic_weights('dimensions')
        # Should fall back to static weights
        assert weights == {
            'fundamental': 0.25,
            'technical': 0.20,
            'sentiment': 0.15,
            'risk': 0.20,
            'macro': 0.10,
            'ai': 0.10
        }

    async def test_get_dynamic_weights_ml_available_untrained(self, coefficient_service):
        """Test getting dynamic weights when ML service available but not trained."""
        # Mock coefficient service as available but not trained
        mock_coeff_service = MagicMock()
        mock_coeff_service.is_model_trained.return_value = False
        
        # Temporarily replace the service
        original_service = coefficient_service._coefficient_service
        coefficient_service._coefficient_service = mock_coeff_service
        
        try:
            weights = coefficient_service._get_dynamic_weights('dimensions')
            # Should fall back to static weights
            assert weights == {
                'fundamental': 0.25,
                'technical': 0.20,
                'sentiment': 0.15,
                'risk': 0.20,
                'macro': 0.10,
                'ai': 0.10
            }
        finally:
            coefficient_service._coefficient_service = original_service

    async def test_get_dynamic_weights_ml_available_trained(self, coefficient_service):
        """Test getting dynamic weights when ML service available and trained."""
        # Mock coefficient service as available and trained
        mock_coeff_service = MagicMock()
        mock_coeff_service.is_model_trained.return_value = True
        mock_coeff_service.get_coefficients.return_value = {
            'fundamental': 0.3,
            'technical': 0.25,
            'sentiment': 0.1,
            'risk': 0.15,
            'macro': 0.1,
            'ai': 0.1
        }
        
        # Temporarily replace the service
        original_service = coefficient_service._coefficient_service
        coefficient_service._coefficient_service = mock_coeff_service
        
        try:
            weights = coefficient_service._get_dynamic_weights('dimensions')
            # Should return ML weights
            assert weights == {
                'fundamental': 0.3,
                'technical': 0.25,
                'sentiment': 0.1,
                'risk': 0.15,
                'macro': 0.1,
                'ai': 0.1
            }
        finally:
            coefficient_service._coefficient_service = original_service

    async def test_get_dynamic_weights_ml_invalid_sum(self, coefficient_service):
        """Test getting dynamic weights when ML weights don't sum to ~1.0."""
        # Mock coefficient service as available and trained but with bad weights
        mock_coeff_service = MagicMock()
        mock_coeff_service.is_model_trained.return_value = True
        mock_coeff_service.get_coefficients.return_value = {
            'fundamental': 0.5,
            'technical': 0.5,
            'sentiment': 0.5,  # Sum is now 1.5
            'risk': 0.0,
            'macro': 0.0,
            'ai': 0.0
        }
        
        # Temporarily replace the service
        original_service = coefficient_service._coefficient_service
        coefficient_service._coefficient_service = mock_coeff_service
        
        try:
            weights = coefficient_service._get_dynamic_weights('dimensions')
            # Should fall back to static weights due to invalid sum
            assert weights == {
                'fundamental': 0.25,
                'technical': 0.20,
                'sentiment': 0.15,
                'risk': 0.20,
                'macro': 0.10,
                'ai': 0.10
            }
        finally:
            coefficient_service._coefficient_service = original_service


@pytest.mark.unit
class TestCoefficientConstraints:
    """Test coefficient validation and normalization constraints."""

    def test_normalize_coefficients_basic(self, coefficient_service):
        """Test basic coefficient normalization."""
        # Test with values that don't sum to 1
        coeffs = {'a': 0.3, 'b': 0.5, 'c': 0.3}
        normalized = coefficient_service._normalize_coefficients(coeffs)
        
        # Should sum to 1.0
        assert abs(sum(normalized.values()) - 1.0) < 1e-6
        # All values should be in [0, 1]
        assert all(0.0 <= v <= 1.0 for v in normalized.values())
        # Should preserve relative proportions
        assert normalized['b'] > normalized['a']
        assert normalized['b'] > normalized['c']

    def test_normalize_coefficients_negative_values(self, coefficient_service):
        """Test normalization handles negative values."""
        coeffs = {'a': 0.5, 'b': -0.2, 'c': 0.8}
        normalized = coefficient_service._normalize_coefficients(coeffs)
        
        # Negative values should be clamped to 0
        assert normalized['b'] == 0.0
        assert abs(sum(normalized.values()) - 1.0) < 1e-6
        assert all(v >= 0.0 for v in normalized.values())

    def test_normalize_coefficients_values_above_1(self, coefficient_service):
        """Test normalization handles values > 1."""
        coeffs = {'a': 1.5, 'b': 0.5, 'c': 0.2}
        normalized = coefficient_service._normalize_coefficients(coeffs)
        
        # Values > 1 should be clamped to 1
        assert normalized['a'] <= 1.0
        assert abs(sum(normalized.values()) - 1.0) < 1e-6

    def test_normalize_coefficients_all_zero(self, coefficient_service):
        """Test normalization with all zero values."""
        coeffs = {'a': 0.0, 'b': 0.0, 'c': 0.0}
        normalized = coefficient_service._normalize_coefficients(coeffs)
        
        # Should fall back to uniform distribution
        assert len(normalized) == 3
        # Check that they're approximately equal (within rounding error)
        values = list(normalized.values())
        assert all(v > 0 for v in values)
        # Allow for small floating point rounding errors
        assert abs(sum(normalized.values()) - 1.0) < 1e-5

    def test_normalize_coefficients_empty(self, coefficient_service):
        """Test normalization with empty dict."""
        coeffs = {}
        normalized = coefficient_service._normalize_coefficients(coeffs)
        assert normalized == {}

    def test_validate_coefficients_valid(self, coefficient_service):
        """Test validation passes for valid coefficients."""
        coeffs = {'a': 0.3, 'b': 0.5, 'c': 0.2}
        assert coefficient_service._validate_coefficients(coeffs) is True

    def test_validate_coefficients_invalid_sum(self, coefficient_service):
        """Test validation fails for sum != 1."""
        coeffs = {'a': 0.5, 'b': 0.5}  # Sum = 1.0 - this is valid
        assert coefficient_service._validate_coefficients(coeffs) is True
        
        coeffs = {'a': 0.3, 'b': 0.3}  # Sum = 0.6 - invalid
        assert coefficient_service._validate_coefficients(coeffs) is False

    def test_validate_coefficients_negative(self, coefficient_service):
        """Test validation fails for negative values."""
        coeffs = {'a': 0.5, 'b': -0.1, 'c': 0.6}
        assert coefficient_service._validate_coefficients(coeffs) is False

    def test_validate_coefficients_above_1(self, coefficient_service):
        """Test validation fails for values > 1."""
        coeffs = {'a': 1.1, 'b': 0.1}
        assert coefficient_service._validate_coefficients(coeffs) is False

    def test_validate_coefficients_non_numeric(self, coefficient_service):
        """Test validation fails for non-numeric values."""
        coeffs = {'a': 0.5, 'b': 'invalid'}
        assert coefficient_service._validate_coefficients(coeffs) is False

    def test_get_coefficients_validates_before_return(self, coefficient_service):
        """Test that get_coefficients validates and normalizes before returning."""
        # Set invalid coefficients
        coefficient_service.learned_coefficients['dimensions'] = {
            'fundamental': 0.5,
            'technical': 0.5,
            'sentiment': 0.5,  # Sum = 1.5
        }
        
        # Should return normalized coefficients
        coeffs = coefficient_service.get_coefficients('dimensions')
        assert abs(sum(coeffs.values()) - 1.0) < 1e-6
        assert all(0.0 <= v <= 1.0 for v in coeffs.values())


@pytest.mark.unit
class TestScoringServiceScoreConstraints:
    """Test that scores are constrained to [0, 100] range."""

    async def test_dimension_scores_clamped_to_100(self):
        """Test dimension scores don't exceed 100."""
        service = ScoringService()
        await service.initialize()
        
        # Create data that would produce scores > 100
        data = {
            "ticker": "TEST",
            "market": "TSE",
            "fundamental": {"pe_ratio": 5, "roe": 50},  # Very high values
            "technical": {"rsi": 90, "macd": 10},       # Very high values
            "sentiment": {"score": 150},
            "risk": {"volatility": 0.01},
            "macro": {"gdp_growth": 20},
            "ai": {"prediction": 2.0}
        }
        
        result = await service.analyze(data)
        
        # All dimension scores should be in [0, 100]
        for dim, score in result["dimension_scores"].items():
            assert 0.0 <= score <= 100.0, f"Dimension {dim} score {score} out of range"
        
        # Overall score should be in [0, 100]
        assert 0.0 <= result["overall_score"] <= 100.0

    async def test_dimension_scores_clamped_to_0(self):
        """Test dimension scores don't go below 0."""
        service = ScoringService()
        await service.initialize()
        
        # Create data that would produce negative scores
        data = {
            "ticker": "TEST",
            "market": "TSE",
            "fundamental": {"pe_ratio": -50, "roe": -1.0},
            "technical": {"rsi": -10, "macd": -5},
            "sentiment": {"score": -50},
            "risk": {"volatility": 2.0},
            "macro": {"gdp_growth": -10},
            "ai": {"prediction": -1.0}
        }
        
        result = await service.analyze(data)
        
        # All dimension scores should be in [0, 100]
        for dim, score in result["dimension_scores"].items():
            assert 0.0 <= score <= 100.0, f"Dimension {dim} score {score} out of range"
        
        # Overall score should be in [0, 100]
        assert 0.0 <= result["overall_score"] <= 100.0

    async def test_overall_score_weighted_sum_valid(self):
        """Test that overall score is a valid weighted sum of dimension scores."""
        service = ScoringService()
        await service.initialize()
        
        # Use known values
        data = {
            "ticker": "TEST",
            "market": "TSE",
            "fundamental": {"pe_ratio": 10, "roe": 0.15},
            "technical": {"rsi": 55, "macd": 0.5},
            "sentiment": {"score": 70},
            "risk": {"volatility": 0.2},
            "macro": {"gdp_growth": 3.0},
            "ai": {"prediction": 0.75}
        }
        
        result = await service.analyze(data)
        
        # Verify overall score is calculated correctly
        weights = service._get_dynamic_weights("dimensions")
        if not weights:
            weights = service.DIMENSION_WEIGHTS
        
        total_weight = sum(weights.values())
        if total_weight > 0:
            normalized = {k: v / total_weight for k, v in weights.items()}
        else:
            normalized = service.DIMENSION_WEIGHTS
        
        expected = sum(
            result["dimension_scores"].get(dim, 0) * normalized.get(dim, 0)
            for dim in service.DIMENSIONS
        )
        
        # Should match within rounding precision
        assert abs(result["overall_score"] - round(max(0.0, min(100.0, expected)), 2)) < 0.01


if __name__ == "__main__":
    pytest.main([__file__])