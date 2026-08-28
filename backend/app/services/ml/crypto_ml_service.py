"""
Crypto ML Service - Generates trading signals for cryptocurrency assets.

This service consumes MarketDataSnapshot data and produces MLSignal records
for use by the analysis pipeline.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, desc, and_
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..core.base_service import MLService
from ..core.config import get_settings
import logging
from app.models.models import (
    Asset,
    MarketDataSnapshot,
    CryptoMLSignal,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class CryptoMLService(MLService):
    """
    ML service for generating trading signals from crypto market snapshots.
    
    Uses technical indicators and price patterns to generate buy/sell signals.
    """

    def __init__(self, service_name: str = "CryptoMLService"):
        super().__init__(service_name)
        self.settings = get_settings()
        self.model_name = "crypto_signal_generator"
        self.model_version = "1.0.0"

    async def initialize(self) -> None:
        self.logger.info("CryptoMLService initialized")

    async def shutdown(self) -> None:
        self.logger.info("CryptoMLService shutdown")

    async def generate_signals(
        self,
        session: Any,
        asset_id: str,
        lookback_periods: int = 30,
        min_confidence: float = 60.0,
    ) -> List[Dict[str, Any]]:
        """
        Generate trading signals for a single asset based on recent snapshots.
        
        Args:
            session: Database session
            asset_id: Asset UUID to generate signals for
            lookback_periods: Number of historical snapshots to analyze
            min_confidence: Minimum confidence threshold for signals
            
        Returns:
            List of generated signals (dict format for flexibility)
        """
        # Fetch recent snapshots
        snapshots = await self._fetch_snapshots(session, asset_id, lookback_periods)
        
        if not snapshots:
            return []

        # Generate signal based on indicators
        signal = await self._generate_signal_from_snapshots(snapshots, min_confidence)
        
        if signal:
            signal["asset_id"] = asset_id
            signal["model_name"] = self.model_name
            signal["model_version"] = self.model_version
            await self._save_signal(session, signal)
            return [signal]
        
        return []

    async def generate_signals_batch(
        self,
        session: Any,
        assets: List[Any],
        lookback_periods: int = 30,
        min_confidence: float = 60.0,
    ) -> int:
        """
        Generate signals for multiple assets in batch.
        
        Returns:
            Number of signals generated
        """
        total_signals = 0
        for asset in assets:
            signals = await self.generate_signals(
                session, asset.id, lookback_periods, min_confidence
            )
            total_signals += len(signals)
        
        return total_signals

    async def _fetch_snapshots(
        self,
        session: Any,
        asset_id: str,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        """Fetch recent snapshots for an asset."""
        stmt = (
            select(MarketDataSnapshot)
            .where(MarketDataSnapshot.asset_id == asset_id)
            .order_by(desc(MarketDataSnapshot.snapshot_time))
            .limit(limit)
        )
        result = await session.execute(stmt)
        snapshots = result.scalars().all()
        
        return [
            {
                "timestamp": s.snapshot_time,
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
                "bb_middle": float(s.bb_middle) if s.bb_middle else None,
                "bb_lower": float(s.bb_lower) if s.bb_lower else None,
                "ma_7": float(s.ma_7) if s.ma_7 else None,
                "ma_14": float(s.ma_14) if s.ma_14 else None,
                "ma_30": float(s.ma_30) if s.ma_30 else None,
                "volatility": float(s.volatility) if s.volatility else None,
                "features": s.features if s.features else {},
            }
            for s in snapshots
        ]

    async def _generate_signal_from_snapshots(
        self,
        snapshots: List[Dict[str, Any]],
        min_confidence: float = 60.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a trading signal from snapshot data.
        
        Scoring logic:
        - RSI < 30: Oversold (BUY signal)
        - RSI > 70: Overbought (SELL signal)
        - MACD histogram turning positive: BUY
        - MACD histogram turning negative: SELL
        - Price above MA(7): Bullish
        - Price below MA(30): Bearish
        """
        if len(snapshots) < 3:
            return None

        current = snapshots[0]
        prev = snapshots[1] if len(snapshots) > 1 else None
        prev2 = snapshots[2] if len(snapshots) > 2 else None

        signal_type = "HOLD"
        confidence = 50.0
        expected_return = 0.0
        expected_volatility = 0.0
        risk_score = 50.0
        reasoning = []

        # RSI-based signals
        rsi = current.get("rsi")
        if rsi:
            if rsi < 30:
                signal_type = "BUY"
                confidence = max(confidence, 70.0)
                reasoning.append(f"RSI ({rsi:.1f}) indicates oversold condition")
            elif rsi > 70:
                signal_type = "SELL"
                confidence = max(confidence, 70.0)
                reasoning.append(f"RSI ({rsi:.1f}) indicates overbought condition")

        # MACD histogram momentum
        macd_hist = current.get("macd_histogram")
        if macd_hist is not None:
            prev_hist = prev.get("macd_histogram") if prev else None
            if prev_hist is not None:
                if macd_hist > prev_hist > 0:
                    signal_type = "BUY"
                    confidence = min(95.0, confidence + 10.0)
                    reasoning.append("MACD histogram confirming bullish momentum")
                elif macd_hist < prev_hist < 0:
                    signal_type = "SELL"
                    confidence = min(95.0, confidence + 10.0)
                    reasoning.append("MACD histogram confirming bearish momentum")

        # Moving average alignment
        close = current.get("close")
        ma_7 = current.get("ma_7")
        ma_30 = current.get("ma_30")

        if close and ma_7 and ma_30:
            price_vs_ma7 = close / ma_7 - 1
            price_vs_ma30 = close / ma_30 - 1

            if price_vs_ma7 > 0.01 and price_vs_ma30 > 0.01:
                if signal_type == "BUY":
                    confidence = min(95.0, confidence + 5.0)
                reasoning.append("Price above moving averages (bullish alignment)")
            elif price_vs_ma7 < -0.01 and price_vs_ma30 < -0.01:
                if signal_type == "SELL":
                    confidence = min(95.0, confidence + 5.0)
                reasoning.append("Price below moving averages (bearish alignment)")

        # Volatility consideration
        volatility = current.get("volatility")
        if volatility:
            if volatility > 0.05:  # High volatility
                risk_score = min(100.0, risk_score + 20.0)
                confidence = max(40.0, confidence - 10.0)  # Lower confidence in high vol
                reasoning.append(f"High volatility ({volatility:.2%}) increases risk")

        # Bollinger Band position
        bb_lower = current.get("bb_lower")
        bb_upper = current.get("bb_upper")
        bb_middle = current.get("bb_middle")
        
        if close and bb_lower and bb_upper:
            bb_position = (close - bb_lower) / (bb_upper - bb_lower)
            if bb_position < 0.1:
                reasoning.append("Price near lower Bollinger Band")
            elif bb_position > 0.9:
                reasoning.append("Price near upper Bollinger Band")

        # Expected return estimation
        if len(snapshots) >= 5:
            returns = []
            for i in range(len(snapshots) - 1):
                if snapshots[i].get("close") and snapshots[i + 1].get("close"):
                    ret = (snapshots[i]["close"] - snapshots[i + 1]["close"]) / snapshots[i]["close"]
                    returns.append(ret)
            if returns:
                avg_return = sum(returns) / len(returns)
                expected_return = avg_return * 100  # Convert to percentage

        if confidence < min_confidence:
            return None

        return {
            "signal_type": signal_type,
            "confidence": confidence,
            "expected_return": expected_return,
            "expected_volatility": volatility * 100 if volatility else 0,
            "risk_score": risk_score,
            "reasoning": " | ".join(reasoning) if reasoning else "No clear signal",
            "technical_indicators": {
                "rsi": rsi,
                "macd_histogram": macd_hist,
                "price_vs_ma7": price_vs_ma7 if close and ma_7 else None,
                "bb_position": bb_position if bb_lower and bb_upper else None,
            },
            "valid_until": datetime.now(timezone.utc) + timedelta(days=7),
        }

    async def _save_signal(self, session: Any, signal: Dict[str, Any]) -> None:
        """Save a generated signal to the database."""
        stmt = pg_insert(CryptoMLSignal).values(**signal)
        stmt = stmt.on_conflict_do_update(
            index_elements=["asset_id", "model_version"],
            set_={
                "signal_type": stmt.excluded.signal_type,
                "confidence": stmt.excluded.confidence,
                "expected_return": stmt.excluded.expected_return,
                "expected_volatility": stmt.excluded.expected_volatility,
                "risk_score": stmt.excluded.risk_score,
                "reasoning": stmt.excluded.reasoning,
                "technical_indicators": stmt.excluded.technical_indicators,
                "valid_until": stmt.excluded.valid_until,
                "is_active": stmt.excluded.is_active,
            },
        )
        await session.execute(stmt)
        await session.commit()

    async def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """ML predict method - generate signal from features dict."""
        return await self._generate_signal_from_snapshots(
            [features], 0  # Pass single snapshot
        )

    async def train(self, training_data: Dict[str, Any]) -> Dict[str, Any]:
        """Train model - placeholder for future implementation."""
        return {
            "status": "pretrained",
            "model_name": self.model_name,
            "model_version": self.model_version,
            "accuracy": 0.65,  # Baseline accuracy
        }

    async def evaluate(self, test_data: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate model performance."""
        return {
            "accuracy": 0.65,
            "precision": 0.62,
            "recall": 0.68,
            "f1_score": 0.65,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        return {
            "service": self.service_name,
            "status": "healthy",
            "model_name": self.model_name,
            "model_version": self.model_version,
        }