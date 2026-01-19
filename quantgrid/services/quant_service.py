"""
QuantGrid AI Engine - Quantitative Analysis Service

Wires the quantitative engine with the API layer.
Provides high-level analysis functions.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import numpy as np

from quantgrid.indicators import (
    # Indicators
    ema,
    rsi,
    macd,
    bollinger_bands,
    atr,
    # Regime
    VolatilityRegime,
    TrendRegime,
    RegimeState,
    detect_volatility_regime,
    detect_trend_regime,
    # Composite
    Signal,
    CompositeScore,
    calculate_composite_score,
    # State
    IndicatorState,
)


@dataclass
class TechnicalAnalysis:
    """Complete technical analysis result for a ticker"""
    ticker: str
    timestamp: datetime
    price: float
    
    # Indicators
    ema_20: Optional[float]
    ema_50: Optional[float]
    rsi_14: Optional[float]
    macd_line: Optional[float]
    macd_signal: Optional[float]
    macd_histogram: Optional[float]
    bb_upper: Optional[float]
    bb_middle: Optional[float]
    bb_lower: Optional[float]
    atr_14: Optional[float]
    
    # Regime
    regime: RegimeState
    
    # Signal
    composite: CompositeScore


class QuantService:
    """
    Quantitative analysis service.
    
    Provides technical analysis, regime detection, and signal generation.
    """
    
    def __init__(self):
        # Per-ticker state machines for real-time updates
        self._ticker_states: dict[str, IndicatorState] = {}
    
    def get_ticker_state(self, ticker: str) -> IndicatorState:
        """Get or create state machine for a ticker"""
        if ticker not in self._ticker_states:
            self._ticker_states[ticker] = IndicatorState()
        return self._ticker_states[ticker]
    
    def update_price(self, ticker: str, price: float) -> dict:
        """
        Update indicators with new price (O(1) operation).
        
        Use this for real-time streaming updates.
        """
        state = self.get_ticker_state(ticker)
        return state.update(price)
    
    def analyze(
        self,
        ticker: str,
        prices: list[float],
        highs: Optional[list[float]] = None,
        lows: Optional[list[float]] = None,
        timestamp: Optional[datetime] = None,
    ) -> TechnicalAnalysis:
        """
        Run full technical analysis on price history.
        
        Args:
            ticker: Stock/crypto ticker symbol
            prices: List of closing prices (oldest first)
            highs: Optional list of high prices (for ATR)
            lows: Optional list of low prices (for ATR)
            timestamp: Analysis timestamp (default: now)
            
        Returns:
            TechnicalAnalysis with all indicators and signals
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Convert to numpy arrays
        close = np.array(prices, dtype=np.float64)
        current_price = close[-1]
        
        # Calculate indicators
        ema_20_arr = ema(close, 20)
        ema_50_arr = ema(close, 50)
        rsi_arr = rsi(close, 14)
        macd_line_arr, macd_signal_arr, macd_hist_arr = macd(close)
        bb_upper_arr, bb_middle_arr, bb_lower_arr = bollinger_bands(close)
        
        # ATR requires high/low
        atr_value = None
        if highs and lows:
            high = np.array(highs, dtype=np.float64)
            low = np.array(lows, dtype=np.float64)
            atr_arr = atr(high, low, close)
            atr_value = float(atr_arr[-1]) if not np.isnan(atr_arr[-1]) else None
        
        # Get latest values
        ema_20_val = float(ema_20_arr[-1]) if not np.isnan(ema_20_arr[-1]) else None
        ema_50_val = float(ema_50_arr[-1]) if not np.isnan(ema_50_arr[-1]) else None
        rsi_val = float(rsi_arr[-1]) if not np.isnan(rsi_arr[-1]) else None
        macd_line_val = float(macd_line_arr[-1]) if not np.isnan(macd_line_arr[-1]) else None
        macd_signal_val = float(macd_signal_arr[-1]) if not np.isnan(macd_signal_arr[-1]) else None
        macd_hist_val = float(macd_hist_arr[-1]) if not np.isnan(macd_hist_arr[-1]) else None
        
        # Regime detection
        returns = np.diff(np.log(close))
        vol_regime, vol_pct = detect_volatility_regime(returns)
        trend_regime, trend_strength = detect_trend_regime(close, ema_20_arr, ema_50_arr)
        
        regime = RegimeState(
            volatility=vol_regime,
            trend=trend_regime,
            volatility_percentile=vol_pct,
            trend_strength=trend_strength,
        )
        
        # Composite signal
        macd_tuple = None
        if macd_line_val is not None and macd_signal_val is not None and macd_hist_val is not None:
            macd_tuple = (macd_line_val, macd_signal_val, macd_hist_val)
        
        composite = calculate_composite_score(
            price=current_price,
            rsi=rsi_val,
            macd=macd_tuple,
            ema_20=ema_20_val,
            ema_50=ema_50_val,
        )
        
        return TechnicalAnalysis(
            ticker=ticker,
            timestamp=timestamp,
            price=current_price,
            ema_20=ema_20_val,
            ema_50=ema_50_val,
            rsi_14=rsi_val,
            macd_line=macd_line_val,
            macd_signal=macd_signal_val,
            macd_histogram=macd_hist_val,
            bb_upper=float(bb_upper_arr[-1]) if not np.isnan(bb_upper_arr[-1]) else None,
            bb_middle=float(bb_middle_arr[-1]) if not np.isnan(bb_middle_arr[-1]) else None,
            bb_lower=float(bb_lower_arr[-1]) if not np.isnan(bb_lower_arr[-1]) else None,
            atr_14=atr_value,
            regime=regime,
            composite=composite,
        )
    
    def get_signal(
        self,
        price: float,
        rsi: Optional[float],
        macd: Optional[tuple[float, float, float]],
        ema_20: Optional[float],
        ema_50: Optional[float],
    ) -> CompositeScore:
        """
        Get trading signal from current indicator values.
        
        Use this when you have pre-calculated indicators.
        """
        return calculate_composite_score(
            price=price,
            rsi=rsi,
            macd=macd,
            ema_20=ema_20,
            ema_50=ema_50,
        )


# Singleton instance
quant_service = QuantService()
