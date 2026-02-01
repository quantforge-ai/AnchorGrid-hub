"""
QuantForge AI Engine - Composite Signal Scoring

Combines multiple indicators into weighted signals.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Signal(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class CompositeScore:
    """Weighted composite signal score"""
    signal: Signal
    score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    components: dict[str, float]


def calculate_rsi_signal(rsi: float) -> tuple[float, str]:
    """Convert RSI to signal score and reason"""
    if rsi < 30:
        return (0.8, "oversold")
    elif rsi < 40:
        return (0.4, "near_oversold")
    elif rsi > 70:
        return (-0.8, "overbought")
    elif rsi > 60:
        return (-0.4, "near_overbought")
    else:
        return (0.0, "neutral")


def calculate_macd_signal(
    macd_line: float,
    signal_line: float,
    histogram: float,
    prev_histogram: Optional[float] = None,
) -> tuple[float, str]:
    """Convert MACD to signal score and reason"""
    score = 0.0
    reason = "neutral"
    
    # Crossover detection
    if macd_line > signal_line and histogram > 0:
        score = 0.6
        reason = "bullish_crossover"
        if prev_histogram is not None and prev_histogram <= 0:
            score = 0.9
            reason = "fresh_bullish_crossover"
    elif macd_line < signal_line and histogram < 0:
        score = -0.6
        reason = "bearish_crossover"
        if prev_histogram is not None and prev_histogram >= 0:
            score = -0.9
            reason = "fresh_bearish_crossover"
    
    return (score, reason)


def calculate_ema_signal(
    price: float,
    ema_20: float,
    ema_50: float,
) -> tuple[float, str]:
    """Convert EMA positions to signal score"""
    score = 0.0
    reasons = []
    
    # Price vs EMAs
    if price > ema_20 > ema_50:
        score = 0.7
        reasons.append("uptrend")
    elif price < ema_20 < ema_50:
        score = -0.7
        reasons.append("downtrend")
    elif price > ema_20:
        score = 0.3
        reasons.append("above_ema20")
    elif price < ema_20:
        score = -0.3
        reasons.append("below_ema20")
    
    return (score, "_".join(reasons) if reasons else "neutral")


def calculate_composite_score(
    price: float,
    rsi: Optional[float],
    macd: Optional[tuple[float, float, float]],
    ema_20: Optional[float],
    ema_50: Optional[float],
    weights: Optional[dict[str, float]] = None,
) -> CompositeScore:
    """
    Calculate weighted composite signal.
    
    Default weights:
    - RSI: 0.25
    - MACD: 0.35
    - EMA: 0.40
    """
    if weights is None:
        weights = {"rsi": 0.25, "macd": 0.35, "ema": 0.40}
    
    components = {}
    total_score = 0.0
    total_weight = 0.0
    confidence_factors = []
    
    # RSI component
    if rsi is not None:
        rsi_score, rsi_reason = calculate_rsi_signal(rsi)
        components["rsi"] = {"score": rsi_score, "value": rsi, "reason": rsi_reason}
        total_score += rsi_score * weights["rsi"]
        total_weight += weights["rsi"]
        confidence_factors.append(abs(rsi_score))
    
    # MACD component
    if macd is not None:
        macd_score, macd_reason = calculate_macd_signal(macd[0], macd[1], macd[2])
        components["macd"] = {
            "score": macd_score,
            "line": macd[0],
            "signal": macd[1],
            "histogram": macd[2],
            "reason": macd_reason,
        }
        total_score += macd_score * weights["macd"]
        total_weight += weights["macd"]
        confidence_factors.append(abs(macd_score))
    
    # EMA component
    if ema_20 is not None and ema_50 is not None:
        ema_score, ema_reason = calculate_ema_signal(price, ema_20, ema_50)
        components["ema"] = {
            "score": ema_score,
            "ema_20": ema_20,
            "ema_50": ema_50,
            "reason": ema_reason,
        }
        total_score += ema_score * weights["ema"]
        total_weight += weights["ema"]
        confidence_factors.append(abs(ema_score))
    
    # Normalize score
    if total_weight > 0:
        normalized_score = total_score / total_weight
    else:
        normalized_score = 0.0
    
    # Calculate confidence
    confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
    
    # Determine signal
    if normalized_score >= 0.6:
        signal = Signal.STRONG_BUY
    elif normalized_score >= 0.2:
        signal = Signal.BUY
    elif normalized_score <= -0.6:
        signal = Signal.STRONG_SELL
    elif normalized_score <= -0.2:
        signal = Signal.SELL
    else:
        signal = Signal.HOLD
    
    return CompositeScore(
        signal=signal,
        score=normalized_score,
        confidence=confidence,
        components=components,
    )

