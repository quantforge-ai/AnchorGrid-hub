"""
QuantForge AI Engine - Technical Indicators

PURE MATH - No I/O, No DB access, Fully deterministic.

All functions take numpy arrays and return numpy arrays.
"""
import numpy as np
from numpy.typing import NDArray


def sma(prices: NDArray[np.float64], period: int) -> NDArray[np.float64]:
    """
    Simple Moving Average
    
    Args:
        prices: Array of closing prices
        period: Lookback period
        
    Returns:
        Array of SMA values (NaN for first period-1 values)
    """
    if len(prices) < period:
        return np.full_like(prices, np.nan)
    
    result = np.full_like(prices, np.nan)
    cumsum = np.cumsum(prices)
    result[period-1:] = (cumsum[period-1:] - np.concatenate([[0], cumsum[:-period]])) / period
    return result


def ema(prices: NDArray[np.float64], period: int) -> NDArray[np.float64]:
    """
    Exponential Moving Average
    
    Args:
        prices: Array of closing prices
        period: Lookback period
        
    Returns:
        Array of EMA values
    """
    if len(prices) < period:
        return np.full_like(prices, np.nan)
    
    alpha = 2 / (period + 1)
    result = np.zeros_like(prices)
    result[0] = prices[0]
    
    for i in range(1, len(prices)):
        result[i] = alpha * prices[i] + (1 - alpha) * result[i-1]
    
    # First period-1 values are warmup
    result[:period-1] = np.nan
    return result


def rsi(prices: NDArray[np.float64], period: int = 14) -> NDArray[np.float64]:
    """
    Relative Strength Index
    
    Args:
        prices: Array of closing prices
        period: Lookback period (default 14)
        
    Returns:
        Array of RSI values (0-100)
    """
    if len(prices) < period + 1:
        return np.full_like(prices, np.nan)
    
    # Calculate price changes
    deltas = np.diff(prices)
    
    # Separate gains and losses
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # Calculate average gains and losses using EMA
    avg_gain = np.zeros(len(gains))
    avg_loss = np.zeros(len(losses))
    
    # Initial averages
    avg_gain[period-1] = np.mean(gains[:period])
    avg_loss[period-1] = np.mean(losses[:period])
    
    # Smoothed averages
    for i in range(period, len(gains)):
        avg_gain[i] = (avg_gain[i-1] * (period - 1) + gains[i]) / period
        avg_loss[i] = (avg_loss[i-1] * (period - 1) + losses[i]) / period
    
    # Calculate RSI
    rs = np.where(avg_loss != 0, avg_gain / avg_loss, 100)
    rsi_values = 100 - (100 / (1 + rs))
    
    # Pad result to match input length
    result = np.full(len(prices), np.nan)
    result[period:] = rsi_values[period-1:]
    
    return result


def macd(
    prices: NDArray[np.float64],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """
    Moving Average Convergence Divergence
    
    Args:
        prices: Array of closing prices
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line period (default 9)
        
    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    ema_fast = ema(prices, fast)
    ema_slow = ema(prices, slow)
    
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def bollinger_bands(
    prices: NDArray[np.float64],
    period: int = 20,
    std_dev: float = 2.0,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """
    Bollinger Bands
    
    Args:
        prices: Array of closing prices
        period: Lookback period (default 20)
        std_dev: Standard deviation multiplier (default 2.0)
        
    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    middle = sma(prices, period)
    
    # Calculate rolling standard deviation
    std = np.full_like(prices, np.nan)
    for i in range(period - 1, len(prices)):
        std[i] = np.std(prices[i - period + 1:i + 1])
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return upper, middle, lower


def atr(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    close: NDArray[np.float64],
    period: int = 14,
) -> NDArray[np.float64]:
    """
    Average True Range
    
    Args:
        high: Array of high prices
        low: Array of low prices
        close: Array of closing prices
        period: Lookback period (default 14)
        
    Returns:
        Array of ATR values
    """
    if len(high) < 2:
        return np.full_like(high, np.nan)
    
    # Calculate True Range
    prev_close = np.concatenate([[close[0]], close[:-1]])
    tr1 = high - low
    tr2 = np.abs(high - prev_close)
    tr3 = np.abs(low - prev_close)
    
    true_range = np.maximum(tr1, np.maximum(tr2, tr3))
    
    # Calculate ATR using EMA
    return ema(true_range, period)


def vwap(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    close: NDArray[np.float64],
    volume: NDArray[np.int64],
) -> NDArray[np.float64]:
    """
    Volume Weighted Average Price (cumulative)
    
    Args:
        high: Array of high prices
        low: Array of low prices
        close: Array of closing prices
        volume: Array of volumes
        
    Returns:
        Array of VWAP values
    """
    typical_price = (high + low + close) / 3
    tp_volume = typical_price * volume
    
    cumulative_tp_volume = np.cumsum(tp_volume)
    cumulative_volume = np.cumsum(volume)
    
    return np.where(
        cumulative_volume != 0,
        cumulative_tp_volume / cumulative_volume,
        np.nan,
    )


def obv(
    close: NDArray[np.float64],
    volume: NDArray[np.int64],
) -> NDArray[np.int64]:
    """
    On-Balance Volume
    
    Args:
        close: Array of closing prices
        volume: Array of volumes
        
    Returns:
        Array of OBV values
    """
    if len(close) < 2:
        return np.array([volume[0]] if len(volume) > 0 else [])
    
    # Calculate direction
    direction = np.sign(np.diff(close))
    direction = np.concatenate([[0], direction])
    
    # Calculate OBV
    signed_volume = direction * volume
    return np.cumsum(signed_volume)

