"""Tier 4: ML Services

Services for machine learning and predictions:
- MLService: Ensemble model training and prediction
- PricePredictionService: Stock price predictions
- AnomalyDetectionService: Anomaly detection
- ClusteringService: Data clustering
- EnsembleService: Ensemble model management
- FeatureEngineeringService: Feature engineering
- CoefficientLearningService: ML-driven coefficient learning for 6D scoring
"""

from .coefficient_learning_service import CoefficientLearningService

__all__ = [
    "MLService",
    "PricePredictionService", 
    "AnomalyDetectionService",
    "ClusteringService",
    "EnsembleService",
    "FeatureEngineeringService",
    "CoefficientLearningService"
]

# Lazy imports to avoid circular dependencies
def __getattr__(name: str):
    if name == "MLService":
        from .prediction_service import MLService
        return MLService
    elif name == "PricePredictionService":
        from .prediction_service import PredictionService as PricePredictionService
        return PricePredictionService
    elif name == "AnomalyDetectionService":
        from .anomaly_detection_service import AnomalyDetectionService
        return AnomalyDetectionService
    elif name == "ClusteringService":
        from .pattern_recognition_service import ClusteringService
        return ClusteringService
    elif name == "EnsembleService":
        from .recommendation_service import EnsembleService
        return EnsembleService
    elif name == "FeatureEngineeringService":
        from .time_series_forecasting_service import FeatureEngineeringService
        return FeatureEngineeringService
    elif name == "CoefficientLearningService":
        from .coefficient_learning_service import CoefficientLearningService
        return CoefficientLearningService
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")