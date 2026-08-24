"""
Market Data Processing Service

Transforms raw market data (from raw_market_data table) into processed snapshots
(market_data_snapshots table) with technical indicators and ML features.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import select, func, desc, and_
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..core.base_service import DataService
from ..core.config import get_settings
import logging
from app.db.base import async_session_maker
from ..models.models import RawMarketData, MarketDataSnapshot, Asset

logger = logging.getLogger(__name__)
settings = get_settings()


class MarketDataProcessingService(DataService):
    """
    Service for processing raw market data into analytical snapshots.
    
    Pipeline:
    1. Fetch raw data from raw_market_data table
    2. Aggregate into time-aligned intervals (1m, 5m, 15m, 1h, 4h, 1d)
    3. Compute technical indicators (RSI, MACD, Bollinger Bands, ATR, MAs)
    4. Generate ML features
    5. Store in market_data_snapshots table
    """

    INTERVALS = {
        "1m": timedelta(minutes=1),
        "5m": timedelta(minutes=5),
        "15m": timedelta(minutes=15),
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
        "1d": timedelta(days=1),
    }

    def __init__(self, service_name: str = "MarketDataProcessingService"):
        super().__init__(service_name)
        self.lookback_periods = {
            "rsi": 14,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "bb_period": 20,
            "bb_std": 2,
            "atr_period": 14,
            "ma_periods": [7, 14, 30],
            "vol_ma_period": 7,
        }

    async def initialize(self) -> None:
        self.logger.info("MarketDataProcessingService initialized")

    async def shutdown(self) -> None:
        self.logger.info("MarketDataProcessingService shutdown")

    # ------------------------------------------------------------------
    # Core Processing Pipeline
    # ------------------------------------------------------------------
    async def process_raw_to_snapshots(
        self,
        session: Any,
        asset_id: str,
        intervals: Optional[List[str]] = None,
        lookback_hours: int = 24,
    ) -> int:
        """
        Process raw market data for an asset into snapshots.
        
        Args:
            session: Database session
            asset_id: Asset UUID
            intervals: List of intervals to process (default: all)
            lookback_hours: How far back to process
            
        Returns:
            Number of snapshots created/updated
        """
        intervals = intervals or list(self.INTERVALS.keys())
        snapshots_created = 0

        for interval in intervals:
            try:
                count = await self._process_interval(
                    session, asset_id, interval, lookback_hours
                )
                snapshots_created += count
                self.logger.info(
                    f"Processed {count} {interval} snapshots for asset {asset_id}"
                )
            except Exception as exc:
                self.logger.error(
                    f"Failed to process {interval} snapshots for {asset_id}: {exc}"
                )

        return snapshots_created

    async def _process_interval(
        self,
        session: Any,
        asset_id: str,
        interval: str,
        lookback_hours: int,
    ) -> int:
        """Process raw data for a specific interval."""
        # 1. Fetch raw PRICE data for this asset
        raw_data = await self._fetch_raw_price_data(
            session, asset_id, interval, lookback_hours
        )

        if not raw_data:
            return 0

        # 2. Aggregate into time-aligned buckets
        df = self._aggregate_to_interval(raw_data, interval)

        if df.empty:
            return 0

        # 3. Compute technical indicators
        df = self._compute_indicators(df)

        # 4. Generate ML features
        df = self._generate_ml_features(df)

        # 5. Store snapshots
        return await self._store_snapshots(session, asset_id, interval, df)

    # ------------------------------------------------------------------
    # Data Fetching
    # ------------------------------------------------------------------
    async def _fetch_raw_price_data(
        self,
        session: Any,
        asset_id: str,
        interval: str,
        lookback_hours: int,
    ) -> List[Dict[str, Any]]:
        """
        Fetch raw price data from raw_market_data table.
        Filters for PRICE data type within lookback window.
        """
        since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

        stmt = (
            select(RawMarketData)
            .where(
                and_(
                    RawMarketData.asset_id == asset_id,
                    RawMarketData.data_type == "PRICE",
                    RawMarketData.source_timestamp >= since,
                )
            )
            .order_by(RawMarketData.source_timestamp)
        )

        result = await session.execute(stmt)
        records = result.scalars().all()

        return [
            {
                "timestamp": r.source_timestamp,
                "price": float(r.price) if r.price else 0,
                "volume": float(r.volume) if r.volume else 0,
                "quote_volume": float(r.quote_volume) if r.quote_volume else 0,
            }
            for r in records
        ]

    # ------------------------------------------------------------------
    # Aggregation & Alignment
    # ------------------------------------------------------------------
    def _align_timestamp(self, ts: datetime, interval: str) -> datetime:
        """Align timestamp to interval boundary (UTC)."""
        interval_delta = self.INTERVALS[interval]
        # Get epoch seconds
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        seconds_since_epoch = (ts - epoch).total_seconds()
        interval_seconds = interval_delta.total_seconds()
        aligned_seconds = int(seconds_since_epoch / interval_seconds) * interval_seconds
        return epoch + timedelta(seconds=aligned_seconds)

    def _aggregate_to_interval(
        self,
        raw_data: List[Dict[str, Any]],
        interval: str,
    ) -> pd.DataFrame:
        """
        Aggregate raw tick data into OHLCV bars aligned to interval.
        """
        if not raw_data:
            return pd.DataFrame()

        df = pd.DataFrame(raw_data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp")

        # Align timestamps
        df["aligned_ts"] = df.index.map(lambda x: self._align_timestamp(x, interval))
        df = df.set_index("aligned_ts")

        # Resample to OHLCV
        ohlc = df["price"].resample(interval).ohlc()
        vol = df["volume"].resample(interval).sum()
        quote_vol = df["quote_volume"].resample(interval).sum()

        result = pd.concat([ohlc, vol.rename("volume"), quote_vol.rename("quote_volume")], axis=1)
        result.columns = ["open", "high", "low", "close", "volume", "quote_volume"]
        result = result.dropna()

        return result

    # ------------------------------------------------------------------
    # Technical Indicators
    # ------------------------------------------------------------------
    def _compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute all technical indicators and add as columns."""
        df = df.copy()

        # RSI
        df["rsi"] = self._compute_rsi(df["close"], self.lookback_periods["rsi"])

        # MACD
        macd, signal, hist = self._compute_macd(
            df["close"],
            self.lookback_periods["macd_fast"],
            self.lookback_periods["macd_slow"],
            self.lookback_periods["macd_signal"],
        )
        df["macd"] = macd
        df["macd_signal"] = signal
        df["macd_histogram"] = hist

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self._compute_bollinger_bands(
            df["close"],
            self.lookback_periods["bb_period"],
            self.lookback_periods["bb_std"],
        )
        df["bb_upper"] = bb_upper
        df["bb_middle"] = bb_middle
        df["bb_lower"] = bb_lower

        # ATR
        df["atr"] = self._compute_atr(
            df["high"], df["low"], df["close"], self.lookback_periods["atr_period"]
        )

        # Moving Averages
        for period in self.lookback_periods["ma_periods"]:
            df[f"ma_{period}"] = df["close"].rolling(window=period).mean()

        # Volume MA
        df["volume_ma_7"] = df["volume"].rolling(window=self.lookback_periods["vol_ma_period"]).mean()
        df["volume_ratio"] = df["volume"] / df["volume_ma_7"]

        # Volatility (rolling std of returns)
        returns = df["close"].pct_change()
        df["volatility"] = returns.rolling(window=20).std() * np.sqrt(252)  # Annualized

        return df

    def _compute_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Compute RSI using Wilder's smoothing."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _compute_macd(
        self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Compute MACD line, signal line, and histogram."""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def _compute_bollinger_bands(
        self, prices: pd.Series, period: int = 20, std_dev: int = 2
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Compute Bollinger Bands."""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower

    def _compute_atr(
        self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> pd.Series:
        """Compute Average True Range."""
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr

    # ------------------------------------------------------------------
    # ML Features
    # ------------------------------------------------------------------
    def _generate_ml_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate ML-ready features for each snapshot.
        Features are stored as JSONB in the snapshots table.
        """
        df = df.copy()

        # Price-based features
        df["return_1"] = df["close"].pct_change(1)
        df["return_3"] = df["close"].pct_change(3)
        df["return_7"] = df["close"].pct_change(7)

        # Momentum features
        df["momentum_3"] = df["close"] / df["close"].shift(3) - 1
        df["momentum_7"] = df["close"] / df["close"].shift(7) - 1

        # Volatility features
        df["vol_5"] = df["return_1"].rolling(5).std()
        df["vol_10"] = df["return_1"].rolling(10).std()

        # Volume features
        df["vol_change_1"] = df["volume"].pct_change(1)
        df["vol_change_3"] = df["volume"].pct_change(3)

        # Relative features
        df["price_to_ma7"] = df["close"] / df["ma_7"] - 1
        df["price_to_ma14"] = df["close"] / df["ma_14"] - 1
        df["price_to_ma30"] = df["close"] / df["ma_30"] - 1

        # BB position
        df["bb_position"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

        return df

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------
    async def _store_snapshots(
        self,
        session: Any,
        asset_id: str,
        interval: str,
        df: pd.DataFrame,
    ) -> int:
        """Store processed snapshots in market_data_snapshots table."""
        snapshots = []

        for timestamp, row in df.iterrows():
            # Extract ML features
            feature_cols = [
                "return_1", "return_3", "return_7",
                "momentum_3", "momentum_7",
                "vol_5", "vol_10",
                "vol_change_1", "vol_change_3",
                "price_to_ma7", "price_to_ma14", "price_to_ma30",
                "bb_position",
                "rsi", "macd", "macd_signal", "macd_histogram",
                "bb_upper", "bb_middle", "bb_lower",
                "atr", "ma_7", "ma_14", "ma_30",
                "volatility", "volume_ma_7", "volume_ratio",
            ]
            ml_features = {
                col: float(row[col]) if pd.notna(row[col]) else None
                for col in feature_cols
                if col in row.index
            }

            snapshot = {
                "asset_id": asset_id,
                "snapshot_time": timestamp.to_pydatetime().replace(tzinfo=timezone.utc),
                "interval": interval,
                "open": float(row["open"]) if pd.notna(row["open"]) else None,
                "high": float(row["high"]) if pd.notna(row["high"]) else None,
                "low": float(row["low"]) if pd.notna(row["low"]) else None,
                "close": float(row["close"]) if pd.notna(row["close"]) else None,
                "volume": float(row["volume"]) if pd.notna(row["volume"]) else None,
                "turnover": float(row["quote_volume"]) if pd.notna(row["quote_volume"]) else None,
                "rsi": float(row["rsi"]) if pd.notna(row["rsi"]) else None,
                "macd": float(row["macd"]) if pd.notna(row["macd"]) else None,
                "macd_signal": float(row["macd_signal"]) if pd.notna(row["macd_signal"]) else None,
                "macd_histogram": float(row["macd_histogram"]) if pd.notna(row["macd_histogram"]) else None,
                "bb_upper": float(row["bb_upper"]) if pd.notna(row["bb_upper"]) else None,
                "bb_middle": float(row["bb_middle"]) if pd.notna(row["bb_middle"]) else None,
                "bb_lower": float(row["bb_lower"]) if pd.notna(row["bb_lower"]) else None,
                "atr": float(row["atr"]) if pd.notna(row["atr"]) else None,
                "ma_7": float(row["ma_7"]) if pd.notna(row["ma_7"]) else None,
                "ma_14": float(row["ma_14"]) if pd.notna(row["ma_14"]) else None,
                "ma_30": float(row["ma_30"]) if pd.notna(row["ma_30"]) else None,
                "volatility": float(row["volatility"]) if pd.notna(row["volatility"]) else None,
                "volume_ma_7": float(row["volume_ma_7"]) if pd.notna(row["volume_ma_7"]) else None,
                "volume_ratio": float(row["volume_ratio"]) if pd.notna(row["volume_ratio"]) else None,
                "features": ml_features,
                "source": "BINANCE",
                "is_fresh": True,
                "freshness_score": 100.0,
            }
            snapshots.append(snapshot)

        if not snapshots:
            return 0

        # Bulk upsert using ON CONFLICT
        stmt = pg_insert(MarketDataSnapshot).values(snapshots)
        stmt = stmt.on_conflict_do_update(
            index_elements=["asset_id", "snapshot_time", "interval"],
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,
                "turnover": stmt.excluded.turnover,
                "rsi": stmt.excluded.rsi,
                "macd": stmt.excluded.macd,
                "macd_signal": stmt.excluded.macd_signal,
                "macd_histogram": stmt.excluded.macd_histogram,
                "bb_upper": stmt.excluded.bb_upper,
                "bb_middle": stmt.excluded.bb_middle,
                "bb_lower": stmt.excluded.bb_lower,
                "atr": stmt.excluded.atr,
                "ma_7": stmt.excluded.ma_7,
                "ma_14": stmt.excluded.ma_14,
                "ma_30": stmt.excluded.ma_30,
                "volatility": stmt.excluded.volatility,
                "volume_ma_7": stmt.excluded.volume_ma_7,
                "volume_ratio": stmt.excluded.volume_ratio,
                "features": stmt.excluded.features,
                "source": stmt.excluded.source,
                "is_fresh": stmt.excluded.is_fresh,
                "freshness_score": stmt.excluded.freshness_score,
                "created_at": datetime.utcnow(),
            },
        )
        await session.execute(stmt)
        await session.commit()

        return len(snapshots)

    # ------------------------------------------------------------------
    # Utility: Batch Process All Assets
    # ------------------------------------------------------------------
    async def process_all_crypto_assets(
        self,
        session: Any,
        intervals: Optional[List[str]] = None,
        lookback_hours: int = 24,
    ) -> int:
        """Process all crypto assets in the database."""
        stmt = select(Asset).where(Asset.market == "CRYPTO")
        result = await session.execute(stmt)
        assets = result.scalars().all()

        total = 0
        for asset in assets:
            total += await self.process_raw_to_snapshots(
                session, asset.id, intervals, lookback_hours
            )
        return total