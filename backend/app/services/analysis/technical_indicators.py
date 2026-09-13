"""
Technical Indicator Computation Module

Computes real technical indicators from candle data for the scoring pipeline.
All indicators use standard financial formulas on actual price/volume data.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import math


@dataclass
class Candle:
    """Simplified candle data for indicator computation."""
    open: float
    high: float
    low: float
    close: float
    volume: float


def compute_rsi(closes: List[float], period: int = 14) -> Optional[float]:
    """
    Compute Relative Strength Index (RSI) using Wilder's smoothing.
    Standard 14-period RSI as defined by J. Welles Wilder Jr.
    """
    if len(closes) < period + 1:
        return None

    gains = []
    losses = []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))

    if len(gains) < period:
        return None

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def compute_sma(closes: List[float], period: int) -> Optional[float]:
    """Compute Simple Moving Average for the given period."""
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period


def compute_ema(values: List[float], period: int) -> Optional[float]:
    """Compute Exponential Moving Average."""
    if len(values) < period:
        return None

    multiplier = 2.0 / (period + 1)
    ema = sum(values[:period]) / period

    for value in values[period:]:
        ema = (value - ema) * multiplier + ema

    return ema


def compute_macd(
    closes: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Optional[Dict[str, float]]:
    """
    Compute MACD (Moving Average Convergence Divergence).
    Returns macd_line, signal_line, and histogram.
    """
    if len(closes) < slow_period + signal_period:
        return None

    fast_ema = compute_ema(closes, fast_period)
    slow_ema = compute_ema(closes, slow_period)

    if fast_ema is None or slow_ema is None:
        return None

    macd_line = fast_ema - slow_ema

    macd_values = []
    for i in range(slow_period, len(closes) + 1):
        subset = closes[:i]
        f = compute_ema(subset, fast_period)
        s = compute_ema(subset, slow_period)
        if f is not None and s is not None:
            macd_values.append(f - s)

    if len(macd_values) < signal_period:
        return {"macd": macd_line, "signal": 0.0, "histogram": macd_line}

    signal_ema = compute_ema(macd_values, signal_period)
    signal_line = signal_ema if signal_ema is not None else 0.0

    return {
        "macd": macd_line,
        "signal": signal_line,
        "histogram": macd_line - signal_line,
    }


def compute_bollinger_bands(
    closes: List[float],
    period: int = 20,
    num_std: float = 2.0
) -> Optional[Dict[str, float]]:
    """
    Compute Bollinger Bands.
    Returns upper_band, middle_band (SMA), lower_band, and percent_b.
    """
    if len(closes) < period:
        return None

    middle = sum(closes[-period:]) / period
    variance = sum((c - middle) ** 2 for c in closes[-period:]) / period
    std_dev = math.sqrt(variance)

    upper = middle + num_std * std_dev
    lower = middle - num_std * std_dev

    band_width = upper - lower
    percent_b = (closes[-1] - lower) / band_width if band_width > 0 else 0.5

    return {
        "upper": upper,
        "middle": middle,
        "lower": lower,
        "percent_b": percent_b,
        "bandwidth": band_width / middle if middle > 0 else 0,
    }


def compute_atr(candles: List[Candle], period: int = 14) -> Optional[float]:
    """
    Compute Average True Range (ATR).
    Measures volatility based on true range.
    """
    if len(candles) < period + 1:
        return None

    true_ranges = []
    for i in range(1, len(candles)):
        high = candles[i].high
        low = candles[i].low
        prev_close = candles[i - 1].close

        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close),
        )
        true_ranges.append(tr)

    if len(true_ranges) < period:
        return None

    atr = sum(true_ranges[:period]) / period
    for i in range(period, len(true_ranges)):
        atr = (atr * (period - 1) + true_ranges[i]) / period

    return atr


def compute_volume_ratio(volumes: List[float], period: int = 20) -> Optional[float]:
    """
    Compute volume ratio: current volume / average volume.
    Values > 1 indicate above-average volume.
    """
    if len(volumes) < period or period == 0:
        return None

    avg_volume = sum(volumes[-period:]) / period
    if avg_volume == 0:
        return 1.0

    return volumes[-1] / avg_volume


def compute_volatility(closes: List[float], period: int = 20) -> Optional[float]:
    """
    Compute annualized volatility from daily returns.
    Uses standard deviation of log returns.
    """
    if len(closes) < period + 1:
        return None

    log_returns = []
    for i in range(1, len(closes)):
        if closes[i - 1] > 0 and closes[i] > 0:
            log_returns.append(math.log(closes[i] / closes[i - 1]))

    if len(log_returns) < 2:
        return None

    mean_return = sum(log_returns) / len(log_returns)
    variance = sum((r - mean_return) ** 2 for r in log_returns) / (len(log_returns) - 1)
    daily_vol = math.sqrt(variance)

    return daily_vol * math.sqrt(252)


def compute_momentum(closes: List[float], period: int = 10) -> Optional[float]:
    """
    Compute price momentum: rate of change over period.
    Returns percentage change.
    """
    if len(closes) < period + 1:
        return None

    old_price = closes[-(period + 1)]
    if old_price == 0:
        return 0.0

    return (closes[-1] - old_price) / old_price


def compute_stochastic(
    candles: List[Candle],
    k_period: int = 14,
    d_period: int = 3
) -> Optional[Dict[str, float]]:
    """
    Compute Stochastic Oscillator (%K and %D).
    """
    if len(candles) < k_period:
        return None

    recent = candles[-k_period:]
    high_high = max(c.high for c in recent)
    low_low = min(c.low for c in recent)

    current_close = candles[-1].close
    range_val = high_high - low_low

    k_value = ((current_close - low_low) / range_val * 100) if range_val > 0 else 50.0

    if len(candles) < k_period + d_period - 1:
        return {"k": k_value, "d": k_value}

    k_values = []
    for i in range(k_period, len(candles) + 1):
        subset = candles[i - k_period:i]
        hh = max(c.high for c in subset)
        ll = min(c.low for c in subset)
        rng = hh - ll
        k = ((candles[i - 1].close - ll) / rng * 100) if rng > 0 else 50.0
        k_values.append(k)

    d_value = sum(k_values[-d_period:]) / d_period

    return {"k": k_value, "d": d_value}


def compute_all_indicators(candles: List[Candle]) -> Dict[str, Any]:
    """
    Compute all technical indicators from candle data.
    Returns a dictionary of indicator names to values.
    """
    closes = [c.close for c in candles]
    volumes = [c.volume for c in candles]

    indicators = {}

    rsi = compute_rsi(closes)
    if rsi is not None:
        indicators["rsi"] = round(rsi, 2)

    sma_20 = compute_sma(closes, 20)
    if sma_20 is not None:
        indicators["sma_20"] = round(sma_20, 2)

    sma_50 = compute_sma(closes, 50)
    if sma_50 is not None:
        indicators["sma_50"] = round(sma_50, 2)

    ema_12 = compute_ema(closes, 12)
    if ema_12 is not None:
        indicators["ema_12"] = round(ema_12, 2)

    macd = compute_macd(closes)
    if macd is not None:
        indicators["macd"] = round(macd["macd"], 4)
        indicators["macd_signal"] = round(macd["signal"], 4)
        indicators["macd_histogram"] = round(macd["histogram"], 4)

    bb = compute_bollinger_bands(closes)
    if bb is not None:
        indicators["bb_upper"] = round(bb["upper"], 2)
        indicators["bb_middle"] = round(bb["middle"], 2)
        indicators["bb_lower"] = round(bb["lower"], 2)
        indicators["bb_percent_b"] = round(bb["percent_b"], 4)

    atr = compute_atr(candles)
    if atr is not None:
        indicators["atr"] = round(atr, 2)

    vol_ratio = compute_volume_ratio(volumes)
    if vol_ratio is not None:
        indicators["volume_ratio"] = round(vol_ratio, 4)

    volatility = compute_volatility(closes)
    if volatility is not None:
        indicators["volatility"] = round(volatility, 4)

    momentum = compute_momentum(closes)
    if momentum is not None:
        indicators["momentum"] = round(momentum, 4)

    stoch = compute_stochastic(candles)
    if stoch is not None:
        indicators["stoch_k"] = round(stoch["k"], 2)
        indicators["stoch_d"] = round(stoch["d"], 2)

    if sma_20 is not None and closes:
        indicators["price_vs_sma20"] = round((closes[-1] - sma_20) / sma_20, 4) if sma_20 > 0 else 0.0

    if sma_50 is not None and closes:
        indicators["price_vs_sma50"] = round((closes[-1] - sma_50) / sma_50, 4) if sma_50 > 0 else 0.0

    if bb is not None and sma_20 is not None and closes:
        indicators["price_vs_bb"] = round((closes[-1] - bb["middle"]) / bb["middle"], 4) if bb["middle"] > 0 else 0.0

    return indicators
