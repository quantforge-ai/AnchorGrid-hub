# backend/services/indicators_service.py
"""
Advanced Technical Indicators Service

Calculates professional trading indicators on historical and streaming data:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- SMA/EMA (Simple/Exponential Moving Averages)

Phase 3: Advanced Features
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from anchorgrid.services.quote_service import get_historical_data
from anchorgrid.core.logger import log


class IndicatorCalculator:
    """
    Professional technical indicator calculations
    """
    
    @staticmethod
    def sma(closes: List[float], period: int = 20) -> float:
        """
        Simple Moving Average
        
        Args:
            closes: List of closing prices
            period: Number of periods
            
        Returns:
            SMA value
        """
        if len(closes) < period:
            return 0.0
        return float(pd.Series(closes[-period:]).mean())
    
    @staticmethod
    def ema(closes: List[float], period: int = 20) -> float:
        """
        Exponential Moving Average
        
        More weight to recent prices
        """
        if len(closes) < period:
            return 0.0
        return float(pd.Series(closes).ewm(span=period, adjust=False).mean().iloc[-1])
    
    @staticmethod
    def rsi(closes: List[float], period: int = 14) -> float:
        """
        Relative Strength Index (0-100)
        
        >70 = Overbought
        <30 = Oversold
        """
        if len(closes) < period + 1:
            return 50.0  # Neutral
        
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = pd.Series(gains).rolling(window=period).mean().iloc[-1]
        avg_loss = pd.Series(losses).rolling(window=period).mean().iloc[-1]
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi_value = 100 - (100 / (1 + rs))
        
        return float(rsi_value)
    
    @staticmethod
    def macd(closes: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """
        MACD (Moving Average Convergence Divergence)
        
        Returns:
            {
                "macd": MACD line,
                "signal": Signal line,
                "histogram": MACD - Signal
            }
        """
        if len(closes) < slow:
            return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}
        
        prices = pd.Series(closes)
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            "macd": float(macd_line.iloc[-1]),
            "signal": float(signal_line.iloc[-1]),
            "histogram": float(histogram.iloc[-1])
        }
    
    @staticmethod
    def bollinger(closes: List[float], period: int = 20, std_dev: int = 2) -> Dict:
        """
        Bollinger Bands
        
        Returns:
            {
                "upper": Upper band (SMA + 2σ),
                "middle": Middle band (SMA),
                "lower": Lower band (SMA - 2σ)
            }
        """
        if len(closes) < period:
            return {"upper": 0.0, "middle": 0.0, "lower": 0.0}
        
        series = pd.Series(closes)
        middle = series.rolling(window=period).mean().iloc[-1]
        std = series.rolling(window=period).std().iloc[-1]
        
        return {
            "upper": float(middle + std * std_dev),
            "middle": float(middle),
            "lower": float(middle - std * std_dev)
        }


async def get_indicators(symbol: str, days: int = 90) -> Dict:
    """
    Calculate all technical indicators for a symbol
    
    Args:
        symbol: Stock/crypto symbol
        days: Days of historical data
        
    Returns:
        Dictionary with all indicators
    """
    try:
        # Get historical data
        historical = await get_historical_data(symbol, timeframe="1M")
        
        if not historical or len(historical) < 50:
            log.warning(f"Insufficient data for {symbol} indicators")
            return {"error": "Insufficient historical data (need 50+ days)"}
        
        # Extract closing prices
        closes = [float(candle["close"]) for candle in historical]
        
        # Calculate all indicators
        calc = IndicatorCalculator()
        
        indicators = {
            "symbol": symbol,
            "data_points": len(closes),
            "sma_20": calc.sma(closes, 20),
            "sma_50": calc.sma(closes, 50),
            "ema_20": calc.ema(closes, 20),
            "ema_50": calc.ema(closes, 50),
            "rsi_14": calc.rsi(closes, 14),
            "macd": calc.macd(closes),
            "bollinger_20": calc.bollinger(closes, 20)
        }
        
        # Add alerts
        indicators["alerts"] = await check_alerts(symbol, indicators)
        
        log.info(f"📊 Calculated indicators for {symbol}: RSI={indicators['rsi_14']:.2f}")
        
        return indicators
        
    except Exception as e:
        log.error(f"Error calculating indicators for {symbol}: {e}")
        return {"error": str(e)}


async def check_alerts(symbol: str, indicators: Dict) -> List[str]:
    """
    Check for trading alerts based on indicator thresholds
    
    Args:
        symbol: Stock symbol
        indicators: Calculated indicators
        
    Returns:
        List of alert messages
    """
    alerts = []
    
    # RSI alerts
    rsi = indicators.get("rsi_14", 50)
    if rsi > 70:
        alerts.append(f"🔴 {symbol} RSI Overbought ({rsi:.1f} > 70)")
    elif rsi < 30:
        alerts.append(f"🟢 {symbol} RSI Oversold ({rsi:.1f} < 30)")
    
    # MACD alerts
    macd_data = indicators.get("macd", {})
    macd_val = macd_data.get("macd", 0)
    signal_val = macd_data.get("signal", 0)
    
    if macd_val > signal_val and macd_data.get("histogram", 0) > 0:
        alerts.append(f"📈 {symbol} MACD Bullish Crossover")
    elif macd_val < signal_val and macd_data.get("histogram", 0) < 0:
        alerts.append(f"📉 {symbol} MACD Bearish Crossover")
    
    # Bollinger Bands alerts
    bollinger = indicators.get("bollinger_20", {})
    # Would need current price to check if near bands
    
    return alerts


async def calculate_streaming_indicator(symbol: str, new_price: float, indicator_type: str) -> Optional[float]:
    """
    Update indicator with new streaming price
    
    For real-time chart updates (Phase 4 frontend)
    
    Args:
        symbol: Stock symbol
        new_price: New price tick
        indicator_type: Which indicator to calculate
        
    Returns:
        Updated indicator value
    """
    # TODO: Maintain price buffers in Redis for streaming calculations
    # For now, fetch historical and append new price
    try:
        historical = await get_historical_data(symbol, timeframe="1M")
        
        if not historical:
            return None
        
        closes = [float(c["close"]) for c in historical]
        closes.append(new_price)
        
        calc = IndicatorCalculator()
        
        if indicator_type == "rsi":
            return calc.rsi(closes, 14)
        elif indicator_type == "sma_20":
            return calc.sma(closes, 20)
        elif indicator_type == "ema_20":
            return calc.ema(closes, 20)
        
        return None
        
    except Exception as e:
        log.error(f"Streaming indicator error: {e}")
        return None
