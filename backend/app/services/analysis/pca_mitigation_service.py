from typing import Any

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from app.core.config import get_settings

from ..core import AnalysisService
from ..core.dependency_container import get_global_container

settings = get_settings()


class MulticollinearityMitigationService(AnalysisService):
    """Implement PCA and regularization to mitigate multicollinearity risk."""

    def __init__(
        self,
        service_name: str = "MulticollinearityMitigationService",
        pca_threshold: float = 0.95,
        vif_threshold: float = 5.0,
    ):
        super().__init__(service_name)
        self.pca_threshold = pca_threshold
        self.vif_threshold = vif_threshold
        self.pca_model: PCA | None = None
        self.scaler: StandardScaler | None = None
        self.feature_names: list[str] = []
        self.explained_variance_ratio_: list[float] = []

    async def initialize(self) -> None:
        self.logger.info("MulticollinearityMitigationService initialized")

    async def shutdown(self) -> None:
        self.logger.info("MulticollinearityMitigationService shutdown")

    async def analyze(self, data: dict[str, Any]) -> dict[str, Any]:
        """Run multicollinearity analysis and mitigation."""
        if "features" not in data or "feature_names" not in data:
            return {"error": "Missing features or feature_names"}

        features = np.array(data["features"])
        feature_names = data["feature_names"]

        results = {
            "vif_analysis": await self._calculate_vif(features, feature_names),
            "pca_analysis": await self._perform_pca(features, feature_names),
            "recommendations": {},
        }

        # Generate recommendations based on analysis
        results["recommendations"] = {
            "use_pca": results["pca_analysis"]["n_components"] < len(feature_names),
            "recommended_components": results["pca_analysis"]["n_components"],
            "ridge_regression": results["vif_analysis"]["avg_vif"] > self.vif_threshold,
            "feature_removal": self._get_removal_recommendations(results["vif_analysis"]),
        }

        return results

    async def _calculate_vif(
        self, features: np.ndarray, feature_names: list[str]
    ) -> dict[str, Any]:
        """Calculate Variance Inflation Factor for each feature."""
        try:
            from statsmodels.stats.outliers_influence import variance_inflation_factor

            df = pd.DataFrame(features, columns=feature_names)
            vif_data = {}

            for i, col in enumerate(feature_names):
                vif = variance_inflation_factor(df.values, i)
                vif_data[col] = float(vif)

            avg_vif = np.mean(list(vif_data.values()))
            max_vif = np.max(list(vif_data.values())) if vif_data else 0

            return {
                "vif_values": vif_data,
                "avg_vif": float(avg_vif),
                "max_vif": float(max_vif),
                "high_vif_features": [
                    f for f, v in vif_data.items() if v > self.vif_threshold
                ],
                "multicollinearity_detected": max_vif > self.vif_threshold,
            }
        except ImportError:
            # Fallback method using correlation matrix
            corr_matrix = np.corrcoef(features.T)
            vif_approx = np.diag(np.linalg.inv(corr_matrix))
            return {
                "vif_values": dict(zip(feature_names, vif_approx.tolist())),
                "avg_vif": float(np.mean(vif_approx)),
                "max_vif": float(np.max(vif_approx)),
                "high_vif_features": [
                    f
                    for f, v in zip(feature_names, vif_approx)
                    if v > self.vif_threshold
                ],
                "multicollinearity_detected": np.max(vif_approx) > self.vif_threshold,
            }

    async def _perform_pca(
        self, features: np.ndarray, feature_names: list[str]
    ) -> dict[str, Any]:
        """Perform PCA and determine optimal number of components."""
        if len(features) < 2:
            return {"error": "Insufficient samples for PCA"}

        # Standardize features
        self.scaler = StandardScaler()
        features_scaled = self.scaler.fit_transform(features)

        # Perform PCA
        self.pca_model = PCA()
        self.pca_model.fit(features_scaled)

        # Determine components for threshold variance
        cumsum = np.cumsum(self.pca_model.explained_variance_ratio_)
        n_components = np.argmax(cumsum >= self.pca_threshold) + 1
        if cumsum[-1] < self.pca_threshold:
            n_components = len(self.pca_model.explained_variance_ratio_)

        self.feature_names = feature_names
        self.explained_variance_ratio_ = self.pca_model.explained_variance_ratio_.tolist()

        return {
            "n_components": int(n_components),
            "explained_variance_ratio": self.explained_variance_ratio_,
            "cumulative_explained_variance": cumsum.tolist(),
            "components": self.pca_model.components_.tolist()[:n_components],
            "variance_explained": float(cumsum[n_components - 1]),
            "reduction_ratio": float(
                1 - (n_components / len(feature_names))
            ),
            "multicollinearity_severe": float(
                1 - (n_components / len(feature_names))
            )
            > 0.5,
        }

    def transform_features(
        self, features: np.ndarray
    ) -> np.ndarray | None:
        """Transform features using fitted PCA model."""
        if self.pca_model is None or self.scaler is None:
            return None

        features_scaled = self.scaler.transform(features)
        return self.pca_model.transform(features_scaled)

    def get_feature_importance(
        self, feature_names: list[str] | None = None
    ) -> dict[str, float]:
        """Get feature importance from PCA loadings."""
        if self.pca_model is None:
            return {}

        names = feature_names or self.feature_names
        # Use absolute loading on first principal component as importance
        importance = np.abs(self.pca_model.components_[0])
        return dict(zip(names, importance.tolist()))


get_global_container().register(
    "MulticollinearityMitigationService", MulticollinearityMitigationService, singleton=True
)
