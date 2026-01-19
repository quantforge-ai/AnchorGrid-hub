# backend/services/mock_quote_service.py
"""
Mock Quote Service - Static data for instant performance
Replace with real data source later (Polygon, Alpha Vantage, or custom scraper)
"""
from typing import Dict, List
from datetime import datetime


# Static mock data - 10 popular tickers
MOCK_QUOTES = {
    "AAPL": {"symbol": "AAPL", "price": 273.08, "change": -0.68, "change_percent": -0.25, "high": 274.08, "low": 272.28, "open": 272.81, "previous_close": 273.76},
    "MSFT": {"symbol": "MSFT", "price": 428.12, "change": 2.45, "change_percent": 0.58, "high": 429.50, "low": 426.10, "open": 426.50, "previous_close": 425.67},
    "GOOGL": {"symbol": "GOOGL", "price": 178.34, "change": -1.22, "change_percent": -0.68, "high": 179.88, "low": 177.90, "open": 179.00, "previous_close": 179.56},
    "AMZN": {"symbol": "AMZN", "price": 215.45, "change": 3.12, "change_percent": 1.47, "high": 216.20, "low": 213.50, "open": 213.80, "previous_close": 212.33},
    "META": {"symbol": "META", "price": 598.77, "change": -4.33, "change_percent": -0.72, "high": 602.50, "low": 596.40, "open": 601.20, "previous_close": 603.10},
    "TSLA": {"symbol": "TSLA", "price": 387.42, "change": 8.56, "change_percent": 2.26, "high": 390.10, "low": 382.50, "open": 383.40, "previous_close": 378.86},
    "NVDA": {"symbol": "NVDA", "price": 187.72, "change": -2.51, "change_percent": -1.32, "high": 190.41, "low": 186.80, "open": 189.50, "previous_close": 190.23},
    "JPM": {"symbol": "JPM", "price": 245.67, "change": 1.23, "change_percent": 0.50, "high": 246.30, "low": 244.20, "open": 244.80, "previous_close": 244.44},
    "V": {"symbol": "V", "price": 312.88, "change": 0.67, "change_percent": 0.21, "high": 313.50, "low": 311.90, "open": 312.20, "previous_close": 312.21},
    "MA": {"symbol": "MA", "price": 528.45, "change": -1.89, "change_percent": -0.36, "high": 530.70, "low": 527.20, "open": 529.80, "previous_close": 530.34},
}


async def get_batch_quotes_mock(symbols: List[str]) -> Dict[str, Dict]:
    """
    Get mock quotes for multiple symbols - INSTANT response
    
    Args:
        symbols: List of stock symbols
        
    Returns:
        Dict mapping symbols to quote data
    """
    results = {}
    timestamp = datetime.utcnow().isoformat()
    
    for symbol in symbols:
        symbol_upper = symbol.upper()
        if symbol_upper in MOCK_QUOTES:
            quote_data = MOCK_QUOTES[symbol_upper].copy()
            quote_data["timestamp"] = timestamp
            quote_data["source"] = "mock"
            results[symbol_upper] = quote_data
    
    return results


async def get_realtime_quote_mock(symbol: str) -> Dict | None:
    """
    Get single mock quote - INSTANT response
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Quote data dict or None
    """
    symbol_upper = symbol.upper()
    if symbol_upper in MOCK_QUOTES:
        quote_data = MOCK_QUOTES[symbol_upper].copy()
        quote_data["timestamp"] = datetime.utcnow().isoformat()
        quote_data["source"] = "mock"
        return quote_data
    return None
