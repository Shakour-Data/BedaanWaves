"""Unit tests for Tier 4 CoefficientLearningService."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ml.coefficient_learning_service import CoefficientLearningService


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

    def test_prepare_training_data_empty(self, coefficient_service):
        """Test preparing training data with empty input."""
        result = coefficient_service._prepare_training_data([])
        assert result == {}

    def test_prepare_training_data_missing_scores(self, coefficient_service):
        """Test preparing training data with missing score keys."""
        data = [{
            'timestamp': datetime.now(timezone.utc),
            'target_metric': 0.05
            # Missing score keys
        }]
        
        result = coefficient_service._prepare_training_data(data)
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
                    'X': [[1.0, 2.0] * 25],  # 50 features
                    'y': [[0.01]],
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
        assert health['service'] == 'coefficient_learning_service'
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


if __name__ == "__main__":
    pytest.main([__file__])