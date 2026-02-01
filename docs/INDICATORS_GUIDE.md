# AnchorGrid Indicators Guide

The `anchorgrid.indicators` package contains high-performance quantitative calculation modules. It is optimized for sub-millisecond execution and supports incremental updates for real-time trading systems.

## Core Modules

### 1. Technical Indicators (`indicators.py`)
Standard quantitative metrics:
- **Trend**: SMA, EMA, MACD
- **Momentum**: RSI, Stochastic
- **Volatility**: Bollinger Bands, ATR
- **Volume**: VWAP, OBV

### 2. Regime Overlays (`regime.py`)
Dynamic market classification:
- **Volatility Regimes**: Low, Medium, High
- **Trend Regimes**: Bullish, Bearish, Sideways
- **Cycle Analysis**: Identifying overextended states

### 3. Signal Composition (`composite.py`)
Utilities for merging multiple indicators into a single actionable score.
- Weighted scoring systems
- Signal confidence thresholds

## Performance Features

### O(1) Incremental Updates
Unlike traditional libraries that recalculate the entire series, AnchorGrid indicators support an "Update" mode:
```python
from anchorgrid.indicators import RSI

# Initialize
rsi_engine = RSI(period=14)
history = rsi_engine.calculate(prices)

# Real-time update (only processes the newest tick)
new_price = 150.25
latest_rsi = rsi_engine.update(new_price)
```

## Usage Example

```python
from anchorgrid.indicators import macd, detect_volatility_regime

# Calculate MACD
macd_line, signal, hist = macd(price_series)

# Detect regime
regime = detect_volatility_regime(returns)
if regime == "high":
    print("Warning: Volatile market detected. Reducing position size.")
```

---

## Integration
Indicators are tightly integrated with the `quant_service.py` to provide ready-to-use analysis for the AI platform and Terminal.
