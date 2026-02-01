"""
QuantForge AI Engine - Incremental State Machine

O(1) updates for real-time indicator calculation.
No historical recompute required.
"""
from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class EMAState:
    """Incremental EMA state"""
    period: int
    alpha: float = field(init=False)
    value: Optional[float] = None
    count: int = 0
    
    def __post_init__(self):
        self.alpha = 2 / (self.period + 1)
    
    def update(self, price: float) -> Optional[float]:
        """Update EMA with new price (O(1))"""
        self.count += 1
        
        if self.value is None:
            self.value = price
        else:
            self.value = self.alpha * price + (1 - self.alpha) * self.value
        
        # Return None during warmup
        if self.count < self.period:
            return None
        return self.value


@dataclass
class RSIState:
    """Incremental RSI state"""
    period: int = 14
    avg_gain: float = 0.0
    avg_loss: float = 0.0
    prev_price: Optional[float] = None
    count: int = 0
    gains_buffer: list = field(default_factory=list)
    losses_buffer: list = field(default_factory=list)
    
    def update(self, price: float) -> Optional[float]:
        """Update RSI with new price (O(1) after warmup)"""
        if self.prev_price is None:
            self.prev_price = price
            return None
        
        # Calculate change
        change = price - self.prev_price
        gain = max(0, change)
        loss = max(0, -change)
        self.prev_price = price
        self.count += 1
        
        # Warmup phase: collect first `period` changes
        if self.count <= self.period:
            self.gains_buffer.append(gain)
            self.losses_buffer.append(loss)
            
            if self.count == self.period:
                self.avg_gain = sum(self.gains_buffer) / self.period
                self.avg_loss = sum(self.losses_buffer) / self.period
                self.gains_buffer.clear()
                self.losses_buffer.clear()
            return None
        
        # Incremental update (O(1))
        self.avg_gain = (self.avg_gain * (self.period - 1) + gain) / self.period
        self.avg_loss = (self.avg_loss * (self.period - 1) + loss) / self.period
        
        if self.avg_loss == 0:
            return 100.0
        
        rs = self.avg_gain / self.avg_loss
        return 100 - (100 / (1 + rs))


@dataclass
class MACDState:
    """Incremental MACD state"""
    fast_period: int = 12
    slow_period: int = 26
    signal_period: int = 9
    fast_ema: EMAState = field(init=False)
    slow_ema: EMAState = field(init=False)
    signal_ema: EMAState = field(init=False)
    
    def __post_init__(self):
        self.fast_ema = EMAState(self.fast_period)
        self.slow_ema = EMAState(self.slow_period)
        self.signal_ema = EMAState(self.signal_period)
    
    def update(self, price: float) -> Optional[tuple[float, float, float]]:
        """Update MACD with new price"""
        fast = self.fast_ema.update(price)
        slow = self.slow_ema.update(price)
        
        if fast is None or slow is None:
            return None
        
        macd_line = fast - slow
        signal_line = self.signal_ema.update(macd_line)
        
        if signal_line is None:
            return None
        
        histogram = macd_line - signal_line
        return (macd_line, signal_line, histogram)


@dataclass
class IndicatorState:
    """Combined state for all indicators on a single ticker"""
    ema_20: EMAState = field(default_factory=lambda: EMAState(20))
    ema_50: EMAState = field(default_factory=lambda: EMAState(50))
    rsi_14: RSIState = field(default_factory=lambda: RSIState(14))
    macd: MACDState = field(default_factory=MACDState)
    
    def update(self, price: float) -> dict:
        """
        Update all indicators with new price.
        
        Returns dict of indicator values.
        """
        return {
            "ema_20": self.ema_20.update(price),
            "ema_50": self.ema_50.update(price),
            "rsi_14": self.rsi_14.update(price),
            "macd": self.macd.update(price),
        }

