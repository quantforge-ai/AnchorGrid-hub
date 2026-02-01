"""
Finance Extractors - Feature Engineering for Financial Analysis

Extractors are the universal term for feature engineering.
In Finance, we extract: RSI, MACD, Bollinger Bands, ATR, etc.
"""

from anchorgrid.plugins.finance.extractors.indicators import (
    sma, ema, rsi, macd, bollinger_bands, atr, vwap, obv
)
from anchorgrid.plugins.finance.extractors.regime import (
    VolatilityRegime,
    TrendRegime,
    RegimeState,
    detect_volatility_regime,
    detect_trend_regime,
)
from anchorgrid.plugins.finance.extractors.composite import (
    Signal,
    CompositeScore,
    calculate_composite_score,
)
from anchorgrid.plugins.finance.extractors.state import IndicatorState

__all__ = [
    # Indicators
    "sma", "ema", "rsi", "macd", "bollinger_bands", 
    "atr", "vwap", "obv",
    # Regime
    "VolatilityRegime", "TrendRegime", "RegimeState",
    "detect_volatility_regime", "detect_trend_regime",
    # Composite
    "Signal", "CompositeScore", "calculate_composite_score",
    # State
    "IndicatorState",
]
