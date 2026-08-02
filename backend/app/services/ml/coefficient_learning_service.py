"""
Coefficient Learning Service - Tier 4 ML Service

Dynamic coefficient learning service for the 6D Scoring System.
Uses hierarchical ML models to learn optimal weights for:
- Dimensions (Level 1: 6 dimensions)
- Sub-Dimensions (Level 2: 40 sub-dimensions)
- Aspects (Level 3: 80 aspects)
- Sub-Aspects (Level 4: 173 sub-aspects)
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import logging
import asyncio
import joblib
import os
from pathlib import Path

from ..core import MLService
from app.core.config import get_settings


class CoefficientLearningService(MLService):
    """
    Machine learning service for learning optimal scoring coefficients
    across the 4-level hierarchy of the 6D scoring system.
    
    Implements hierarchical modeling where:
    - Level 1: 6 dimensions (fundamental, technical, sentiment, risk, macro, AI)
    - Level 2: 40 sub-dimensions (grouped under dimensions)
    - Level 3: 80 aspects (grouped under sub-dimensions)
    - Level 4: 173 sub-aspects (grouped under aspects)
    """
    
    def __init__(self, service_name: str = "coefficient_learning_service"):
        super().__init__(service_name)
        self.settings = get_settings()
        models_dir = getattr(self.settings, 'ML_MODELS_DIR', './models')
        self.models_dir = Path(models_dir) / "coefficients"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Hierarchical models for each level
        self.models: Dict[str, Any] = {
            "dimensions": None,           # Level 1: 6D weights
            "sub_dimensions": None,       # Level 2: 40 sub-dim weights
            "aspects": None,              # Level 3: 80 aspect weights
            "sub_aspects": None           # Level 4: 173 sub-aspect weights
        }
        
        # Scalers for feature normalization
        self.scalers: Dict[str, StandardScaler] = {}
        
        # Feature names for each level (populated during training)
        self.feature_names: Dict[str, List[str]] = {}
        
        # Learned coefficients (weights) - normalized to sum=1.0 per group
        self.learned_coefficients: Dict[str, Dict[str, float]] = {
            "dimensions": {},
            "sub_dimensions": {},
            "aspects": {},
            "sub_aspects": {}
        }
        
        # Performance tracking
        self.performance_history: List[Dict[str, Any]] = []
        self.last_training_time: Optional[datetime] = None
        
        # Configuration
        self.retrain_interval_hours = 24  # Retrain daily
        self.min_samples_for_training = 50
        self.validation_split = 0.2
        
        # Hierarchy mappings (populated from ScoringService)
        self.dimension_names = [
            "fundamental", "technical", "sentiment", 
            "risk", "macro", "ai"
        ]
        self.sub_dimension_map = {
            "fundamental": ["price_history", "ohlcv", "corporate_actions", 
                           "liquidity", "profitability", "efficiency", 
                           "valuation", "growth", "quality"],
            "technical": ["moving_averages", "momentum", "volatility", 
                         "volume", "trend"],
            "sentiment": ["news_sentiment", "social_sentiment", "analyst_sentiment"],
            "risk": ["market_risk", "credit_risk", "operational_risk", 
                   "liquidity_risk"],
            "macro": ["gdp", "inflation", "interest_rates", 
                     "exchange_rates", "commodity_prices"],
            "ai": ["ml_prediction", "pattern_recognition", "anomaly_detection"]
        }
        # Note: aspects and sub-aspects mappings would be generated from ScoringService hierarchy
    
    async def initialize(self) -> None:
        """Initialize the coefficient learning service"""
        try:
            await self._load_existing_models()
            self.logger.info(f"{self.service_name} initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.service_name}: {e}")
            # Initialize with default models if loading fails
            await self._initialize_default_models()
    
    async def shutdown(self) -> None:
        """Shutdown the coefficient learning service"""
        try:
            await self._save_models()
            self.logger.info(f"{self.service_name} shutdown completed")
        except Exception as e:
            self.logger.error(f"Error during {self.service_name} shutdown: {e}")
    
    async def _load_existing_models(self) -> None:
        """Load pre-trained models and scalers from disk"""
        try:
            for level in self.models.keys():
                model_path = self.models_dir / f"{level}_model.joblib"
                scaler_path = self.models_dir / f"{level}_scaler.joblib"
                features_path = self.models_dir / f"{level}_features.joblib"
                coeffs_path = self.models_dir / f"{level}_coefficients.json"
                
                if model_path.exists() and scaler_path.exists():
                    self.models[level] = joblib.load(model_path)
                    self.scalers[level] = joblib.load(scaler_path)
                    if features_path.exists():
                        self.feature_names[level] = joblib.load(features_path)
                    if coeffs_path.exists():
                        import json
                        with open(coeffs_path, 'r') as f:
                            self.learned_coefficients[level] = json.load(f)
                    
                    self.logger.info(f"Loaded {level} model from {model_path}")
                else:
                    self.logger.info(f"No existing model found for {level}, will create new")
                    
        except Exception as e:
            self.logger.warning(f"Could not load existing models: {e}")
            # Continue with empty models - will be initialized on first training
    
    async def _initialize_default_models(self) -> None:
        """Initialize default models with uniform weights"""
        for level in self.models.keys():
            # Create a simple model that returns uniform weights
            self.models[level] = RandomForestRegressor(
                n_estimators=10,
                random_state=42
            )
            self.scalers[level] = StandardScaler()
            
            # Set default uniform coefficients
            if level == "dimensions":
                self.learned_coefficients[level] = {
                    name: 1.0/len(self.dimension_names) 
                    for name in self.dimension_names
                }
            elif level == "sub_dimensions":
                flat_sub_dims = []
                for dim, sub_dims in self.sub_dimension_map.items():
                    for sub_dim in sub_dims:
                        flat_sub_dims.append(f"{dim}_{sub_dim}")
                self.learned_coefficients[level] = {
                    name: 1.0/len(flat_sub_dims) 
                    for name in flat_sub_dims
                }
            # For aspects and sub-aspects, we'll populate during first training
    
    async def learn_coefficients(self, performance_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """
        Learn optimal coefficients from historical performance data.
        
        Args:
            performance_data: List of performance records containing:
                - timestamp: When the measurement was taken
                - dimension_scores: Scores for each dimension
                - sub_dimension_scores: Scores for each sub-dimension
                - aspect_scores: Scores for each aspect
                - sub_aspect_scores: Scores for each sub-aspect
                - target_metric: The performance metric to optimize (e.g., future returns)
                
        Returns:
            Dictionary of learned coefficients for each hierarchy level
        """
        try:
            if not performance_data or len(performance_data) < self.min_samples_for_training:
                self.logger.warning(
                    f"Insufficient data for training: {len(performance_data) if performance_data else 0} samples. "
                    f"Minimum required: {self.min_samples_for_training}"
                )
                return self.learned_coefficients
            
            self.logger.info(f"Starting coefficient learning with {len(performance_data)} samples")
            
            # Prepare data for each level
            training_data = await self._prepare_training_data(performance_data)
            
            # Train models for each level
            for level in self.models.keys():
                if level in training_data and len(training_data[level]["X"]) >= self.min_samples_for_training:
                    await self._train_level_model(level, training_data[level])
            
            # Update last training time
            self.last_training_time = datetime.now(timezone.utc)
            
            # Store performance data for future retraining
            self.performance_history.extend(performance_data)
            # Keep only recent history (last 1000 samples)
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-1000:]
            
            self.logger.info("Coefficient learning completed successfully")
            return self.learned_coefficients
            
        except Exception as e:
            self.logger.error(f"Error during coefficient learning: {e}")
            # Return current coefficients (may be defaults or previously learned)
            return self.learned_coefficients
    
    async def _prepare_training_data(self, 
                                   performance_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Prepare training data for each hierarchy level.
        
        Returns:
            Dictionary with keys for each level containing:
            - X: Feature matrix
            - y: Target vector (normalized performance contributions)
            - feature_names: List of feature names
        """
        training_data = {}
        
        try:
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(performance_data)
            
            # Prepare data for each level
            levels_config = [
                ("dimensions", "dimension_scores", self.dimension_names),
                ("sub_dimensions", "sub_dimension_scores", 
                 [f"{dim}_{sub_dim}" for dim, sub_dims in self.sub_dimension_map.items() 
                  for sub_dim in sub_dims]),
                # For aspects and sub-aspects, we need to derive from hierarchy
                # For now, we'll use placeholder names - in practice these would come from ScoringService
                ("aspects", "aspect_scores", [f"aspect_{i}" for i in range(80)]),
                ("sub_aspects", "sub_aspect_scores", [f"sub_aspect_{i}" for i in range(173)])
            ]
            
            for level_name, score_key, feature_names in levels_config:
                if score_key not in df.columns:
                    self.logger.warning(f"Missing {score_key} in performance data")
                    continue
                
                # Extract features and targets
                features_list = []
                targets_list = []
                
                for _, row in df.iterrows():
                    # Features: historical context and market conditions
                    feature_vector = self._extract_features(row)
                    features_list.append(feature_vector)
                    
                    # Target: normalized contribution to overall performance
                    scores = row.get(score_key, {})
                    target = row.get('target_metric', 0.0)  # Future returns or similar metric
                    
                    # For each item in this level, create a target proportional to its score
                    item_targets = {}
                    total_score = sum(abs(v) for v in scores.values()) or 1.0
                    for item_name in feature_names:
                        score = abs(scores.get(item_name, 0.0))
                        # Normalize contribution: higher score -> higher target weight
                        item_targets[item_name] = (score / total_score) * target if target != 0 else 0.0
                    
                    targets_list.append(list(item_targets.values()))
                
                if features_list and targets_list:
                    X = np.array(features_list)
                    y = np.array(targets_list)
                    
                    # Store feature names
                    self.feature_names[level_name] = feature_names
                    
                    training_data[level_name] = {
                        "X": X,
                        "y": y,
                        "feature_names": feature_names
                    }
                    
                    self.logger.debug(
                        f"Prepared {level_name} data: {X.shape[0]} samples, {X.shape[1]} features"
                    )
            
            return training_data
            
        except Exception as e:
            self.logger.error(f"Error preparing training data: {e}")
            return {}
    
    def _extract_features(self, row: pd.Series) -> List[float]:
        """
        Extract features from a performance record for ML model input.
        
        Features include:
        - Historical score statistics (mean, std, trend)
        - Market regime indicators
        - Temporal features (day of week, month, etc.)
        - Volatility measures
        - Correlation patterns
        """
        features = []
        
        try:
            # Basic statistical features from scores
            for score_type in ['dimension_scores', 'sub_dimension_scores', 
                             'aspect_scores', 'sub_aspect_scores']:
                if score_type in row and isinstance(row[score_type], dict):
                    scores = list(row[score_type].values())
                    if scores:
                        features.extend([
                            np.mean(scores),
                            np.std(scores),
                            np.median(scores),
                            np.min(scores),
                            np.max(scores),
                            len([s for s in scores if s > 0]),  # positive scores count
                            len([s for s in scores if s < 0])   # negative scores count
                        ])
                    else:
                        features.extend([0.0] * 7)
                else:
                    features.extend([0.0] * 7)
            
            # Temporal features
            if 'timestamp' in row:
                try:
                    if isinstance(row['timestamp'], str):
                        dt = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
                    else:
                        dt = row['timestamp']
                    
                    features.extend([
                        float(dt.weekday()),      # Day of week (0-6)
                        float(dt.month),          # Month (1-12)
                        float(dt.day),            # Day of month (1-31)
                        float(dt.hour),           # Hour (0-23)
                        1.0 if dt.weekday() >= 5 else 0.0  # Is weekend
                    ])
                except:
                    features.extend([0.0] * 5)
            else:
                features.extend([0.0] * 5)
            
            # Market features (if available)
            market_features = ['volatility', 'volume', 'price_change', 'market_cap']
            for mf in market_features:
                features.append(float(row.get(mf, 0.0)))
            
            # Ensure fixed feature length
            while len(features) < 50:  # Minimum feature size
                features.append(0.0)
            if len(features) > 50:
                features = features[:50]  # Truncate if too long
                
        except Exception as e:
            self.logger.warning(f"Error extracting features: {e}")
            # Return zero vector of expected length
            features = [0.0] * 50
        
        return features
    
    async def _train_level_model(self, 
                               level: str, 
                               training_data: Dict[str, Any]) -> None:
        """
        Train a model for a specific hierarchy level.
        
        Args:
            level: The hierarchy level ('dimensions', 'sub_dimensions', etc.)
            training_data: Dictionary containing X, y, and feature_names
        """
        try:
            X = training_data["X"]
            y = training_data["y"]
            feature_names = training_data["feature_names"]
            
            # Split data
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=self.validation_split, random_state=42
            )
            
            # Scale features
            scaler = self.scalers[level]
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val)
            
            # Train model
            model = self.models[level]
            if model is None:
                model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
                self.models[level] = model
            
            # Fit model
            model.fit(X_train_scaled, y_train)
            
            # Validate
            train_score = model.score(X_train_scaled, y_train)
            val_score = model.score(X_val_scaled, y_val)
            
            self.logger.info(
                f"Trained {level} model: Train R² = {train_score:.3f}, "
                f"Val R² = {val_score:.3f}"
            )
            
            # Generate coefficients (feature importances, normalized to sum=1.0 per sample)
            # For tree-based models, we can use feature_importances_
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
            else:
                # Fallback: use coefficients from linear models or uniform
                importances = np.ones(len(feature_names)) / len(feature_names)
            
            # Create coefficient mapping for this level
            level_coefficients = {}
            for i, feature_name in enumerate(feature_names):
                # Ensure non-negative importance
                importance = max(0.0, float(importances[i]))
                level_coefficients[feature_name] = importance
            
            # Normalize to sum to 1.0 (so they can be used as weights)
            total = sum(level_coefficients.values())
            if total > 0:
                level_coefficients = {
                    k: v / total for k, v in level_coefficients.items()
                }
            else:
                # Fallback to uniform if all zero
                n_features = len(level_coefficients)
                level_coefficients = {
                    k: 1.0 / n_features for k, v in level_coefficients.items()
                }
            
            # Store learned coefficients with validation
            self.learned_coefficients[level] = self._normalize_coefficients(level_coefficients)
            
            # Validate coefficients
            if not self._validate_coefficients(self.learned_coefficients[level]):
                self.logger.warning(f"Trained coefficients for {level} failed validation")
            
            # Save model and scaler to disk
            await self._save_level_model(level, model, scaler, feature_names, level_coefficients)
            
        except Exception as e:
            self.logger.error(f"Error training {level} model: {e}")
            # Keep existing model if training fails
    
    async def _save_level_model(self, 
                              level: str, 
                              model: Any, 
                              scaler: StandardScaler,
                              feature_names: List[str],
                              coefficients: Dict[str, float]) -> None:
        """Save a level's model, scaler, features, and coefficients to disk"""
        try:
            # Save model
            model_path = self.models_dir / f"{level}_model.joblib"
            joblib.dump(model, model_path)
            
            # Save scaler
            scaler_path = self.models_dir / f"{level}_scaler.joblib"
            joblib.dump(scaler, scaler_path)
            
            # Save feature names
            features_path = self.models_dir / f"{level}_features.joblib"
            joblib.dump(feature_names, features_path)
            
            # Save coefficients as JSON
            import json
            coeffs_path = self.models_dir / f"{level}_coefficients.json"
            with open(coeffs_path, 'w') as f:
                json.dump(coefficients, f, indent=2)
            
            self.logger.debug(f"Saved {level} model artifacts to {self.models_dir}")
            
        except Exception as e:
            self.logger.error(f"Error saving {level} model: {e}")
    
    async def _save_models(self) -> None:
        """Save all models and scalers to disk"""
        for level in self.models.keys():
            if self.models[level] is not None:
                await self._save_level_model(
                    level, 
                    self.models[level], 
                    self.scalers[level],
                    self.feature_names.get(level, []),
                    self.learned_coefficients.get(level, {})
                )
    
    def get_coefficients(self, level: str) -> Dict[str, float]:
        """
        Get learned coefficients for a specific hierarchy level.
        
        Args:
            level: One of 'dimensions', 'sub_dimensions', 'aspects', 'sub_aspects'
            
        Returns:
            Dictionary mapping item names to their weights (summing to 1.0)
        """
        coeffs = self.learned_coefficients.get(level, {}).copy()
        # Validate and normalize before returning
        if coeffs:
            coeffs = self._normalize_coefficients(coeffs)
            if not self._validate_coefficients(coeffs):
                self.logger.warning(f"Coefficients for {level} failed validation after normalization")
        return coeffs
    
    def _normalize_coefficients(self, coefficients: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize coefficients to ensure:
        - All values are non-negative (>= 0)
        - All values are <= 1
        - Sum equals exactly 1.0
        
        Args:
            coefficients: Dictionary of coefficient values
            
        Returns:
            Normalized coefficients dictionary
        """
        if not coefficients:
            return coefficients
        
        # Clamp values to [0, 1] range
        clamped = {k: max(0.0, min(1.0, float(v))) for k, v in coefficients.items()}
        
        # Normalize to sum to 1.0
        total = sum(clamped.values())
        if total > 0:
            normalized = {k: v / total for k, v in clamped.items()}
        else:
            # Fallback to uniform distribution if all values are zero
            n = len(clamped)
            normalized = {k: 1.0 / n for k in clamped.keys()}
        
        # Final validation and rounding to avoid floating point issues
        result = {}
        for k, v in normalized.items():
            result[k] = round(max(0.0, min(1.0, v)), 6)
        
        # Ensure exact sum of 1.0 by adjusting the largest value
        diff = 1.0 - sum(result.values())
        if abs(diff) > 1e-9:
            # Find the largest coefficient and adjust it
            max_key = max(result, key=result.get)
            result[max_key] = round(result[max_key] + diff, 6)
            # Ensure it's still in valid range
            result[max_key] = max(0.0, min(1.0, result[max_key]))
        
        return result
    
    def _validate_coefficients(self, coefficients: Dict[str, float]) -> bool:
        """
        Validate that coefficients meet all constraints:
        - All values are in [0, 1] range
        - Sum equals 1.0 (within floating point tolerance)
        - No negative values
        - No values > 1
        
        Args:
            coefficients: Dictionary of coefficient values
            
        Returns:
            True if valid, False otherwise
        """
        if not coefficients:
            return False
        
        # Check all values are in [0, 1] range
        for key, value in coefficients.items():
            if not isinstance(value, (int, float)):
                self.logger.error(f"Coefficient {key} is not numeric: {value}")
                return False
            if value < 0.0:
                self.logger.error(f"Coefficient {key} is negative: {value}")
                return False
            if value > 1.0:
                self.logger.error(f"Coefficient {key} exceeds 1.0: {value}")
                return False
        
        # Check sum is approximately 1.0
        total = sum(coefficients.values())
        if abs(total - 1.0) > 1e-6:
            self.logger.error(f"Coefficient sum is {total}, expected 1.0")
            return False
        
        return True
    
    def get_all_coefficients(self) -> Dict[str, Dict[str, float]]:
        """Get learned coefficients for all hierarchy levels"""
        return {
            level: coeffs.copy() 
            for level, coeffs in self.learned_coefficients.items()
        }
    
    def is_model_trained(self, level: str) -> bool:
        """Check if a model has been trained for the given level"""
        return (
            self.models.get(level) is not None and 
            len(self.learned_coefficients.get(level, {})) > 0
        )
    
    def get_training_status(self) -> Dict[str, Any]:
        """Get current training status and model info"""
        return {
            "last_training_time": self.last_training_time.isoformat() if self.last_training_time else None,
            "samples_in_history": len(self.performance_history),
            "models_trained": {
                level: self.is_model_trained(level) 
                for level in self.models.keys()
            },
            "feature_counts": {
                level: len(names) 
                for level, names in self.feature_names.items()
            },
            "retrain_interval_hours": self.retrain_interval_hours
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        try:
            status = self.get_training_status()
            is_healthy = (
                self.models is not None and 
                all(model is not None for model in self.models.values() if model is not None)
            )
            
            return {
                "service": self.service_name,
                "status": "healthy" if is_healthy else "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": status
            }
        except Exception as e:
            return {
                "service": self.service_name,
                "status": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }