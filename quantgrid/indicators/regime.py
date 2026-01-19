"""
QuantForge AI Engine - Market Regime Detection

Identifies volatility and trend regimes.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import numpy as np
from numpy.typing import NDArray


class VolatilityRegime(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXTREME = "extreme"


class TrendRegime(str, Enum):
    STRONG_UPTREND = "strong_uptrend"
    UPTREND = "uptrend"
    SIDEWAYS = "sideways"
    DOWNTREND = "downtrend"
    STRONG_DOWNTREND = "strong_downtrend"


@dataclass
class RegimeState:
    """Current market regime"""
    volatility: VolatilityRegime
    trend: TrendRegime
    volatility_percentile: float  # 0-100
    trend_strength: float  # 0-1


def detect_volatility_regime(
    returns: NDArray[np.float64],
    lookback: int = 20,
    thresholds: Optional[dict] = None,
) -> tuple[VolatilityRegime, float]:
    """
    Detect volatility regime using rolling std of returns.
    
    Args:
        returns: Array of log returns
        lookback: Period for rolling std
        thresholds: Custom threshold dict
        
    Returns:
        Tuple of (regime, percentile)
    """
    if thresholds is None:
        thresholds = {
            "low": 25,
            "normal": 75,
            "high": 95,
        }
    
    if len(returns) < lookback:
        return VolatilityRegime.NORMAL, 50.0
    
    # Current volatility (annualized)
    current_vol = np.std(returns[-lookback:]) * np.sqrt(252) * 100
    
    # Historical volatility distribution
    rolling_vols = []
    for i in range(lookback, len(returns) + 1):
        window = returns[i-lookback:i]
        vol = np.std(window) * np.sqrt(252) * 100
        rolling_vols.append(vol)
    
    # Calculate percentile
    percentile = (np.sum(np.array(rolling_vols) <= current_vol) / len(rolling_vols)) * 100
    
    # Determine regime
    if percentile <= thresholds["low"]:
        regime = VolatilityRegime.LOW
    elif percentile <= thresholds["normal"]:
        regime = VolatilityRegime.NORMAL
    elif percentile <= thresholds["high"]:
        regime = VolatilityRegime.HIGH
    else:
        regime = VolatilityRegime.EXTREME
    
    return regime, percentile


def detect_trend_regime(
    prices: NDArray[np.float64],
    ema_short: NDArray[np.float64],
    ema_long: NDArray[np.float64],
) -> tuple[TrendRegime, float]:
    """
    Detect trend regime using EMAs and price position.
    
    Args:
        prices: Array of prices
        ema_short: Short-term EMA (e.g., 20)
        ema_long: Long-term EMA (e.g., 50)
        
    Returns:
        Tuple of (regime, strength 0-1)
    """
    if len(prices) < 2:
        return TrendRegime.SIDEWAYS, 0.0
    
    # Get latest values
    price = prices[-1]
    short = ema_short[-1]
    long_ = ema_long[-1]
    
    # Handle NaN
    if np.isnan(short) or np.isnan(long_):
        return TrendRegime.SIDEWAYS, 0.0
    
    # Calculate signals
    price_vs_short = (price - short) / short if short != 0 else 0
    price_vs_long = (price - long_) / long_ if long_ != 0 else 0
    short_vs_long = (short - long_) / long_ if long_ != 0 else 0
    
    # Calculate trend strength (0-1)
    strength = min(1.0, abs(short_vs_long) * 10)
    
    # Determine regime
    if price > short > long_ and short_vs_long > 0.02:
        if strength > 0.5:
            return TrendRegime.STRONG_UPTREND, strength
        return TrendRegime.UPTREND, strength
    elif price < short < long_ and short_vs_long < -0.02:
        if strength > 0.5:
            return TrendRegime.STRONG_DOWNTREND, strength
        return TrendRegime.DOWNTREND, strength
    else:
        return TrendRegime.SIDEWAYS, strength

