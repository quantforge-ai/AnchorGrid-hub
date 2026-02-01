"""
Symbol Search Service

Universal symbol search using yfinance
Supports: stocks (global), crypto, forex, bonds, commodities, indices
"""

import yfinance as yf
from typing import Dict, Optional
from loguru import logger as log


async def search_symbol(symbol: str) -> Optional[Dict]:
    """
    Search for symbol and return detailed info
    
    Args:
        symbol: Symbol to search (AAPL, BTC-USD, ^TNX, etc.)
    
    Returns:
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "type": "stock",
            "exchange": "NASDAQ",
            "currency": "USD",
            "quote": {
                "price": 273.08,
                "change": -0.68,
                "change_percent": -0.25,
                ...
            }
        }
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Check if symbol is valid
        if not info or 'symbol' not in info:
            log.warning(f"❌ Symbol not found: {symbol}")
            return None
        
        # Detect asset type
        asset_type = detect_asset_type(symbol, info)
        
        # Get current quote
        quote = {
            "price": info.get('currentPrice') or info.get('regularMarketPrice', 0.0),
            "change": info.get('regularMarketChange', 0.0),
            "change_percent": info.get('regularMarketChangePercent', 0.0),
            "open": info.get('regularMarketOpen', 0.0),
            "high": info.get('regularMarketDayHigh', 0.0),
            "low": info.get('regularMarketDayLow', 0.0),
            "volume": info.get('regularMarketVolume', 0),
        }
        
        result = {
            "symbol": symbol.upper(),
            "name": info.get('longName') or info.get('shortName', symbol),
            "type": asset_type,
            "exchange": info.get('exchange', 'N/A'),
            "currency": info.get('currency', 'USD'),
            "quote": quote
        }
        
        log.info(f"✅ Found symbol: {symbol} ({result['name']})")
        return result
        
    except Exception as e:
        log.error(f"❌ Search failed for {symbol}: {e}")
        return None


def detect_asset_type(symbol: str, info: Dict) -> str:
    """
    Detect asset type from symbol format and info
    
    Returns: stock, crypto, forex, bond, commodity, or index
    """
    symbol_upper = symbol.upper()
    
    # Crypto (BTC-USD, ETH-USD)
    if '-USD' in symbol_upper or 'CRYPTO' in info.get('quoteType', ''):
        return 'crypto'
    
    # Forex (EURUSD=X)
    if '=X' in symbol_upper or info.get('quoteType') == 'CURRENCY':
        return 'forex'
    
    # Bonds/Treasury (^TNX, ^TYX)
    if symbol_upper.startswith('^T'):
        return 'bond'
    
    # Indices (^GSPC, ^DJI)
    if symbol_upper.startswith('^') or info.get('quoteType') == 'INDEX':
        return 'index'
    
    # Commodities (GC=F, CL=F)
    if '=F' in symbol_upper or info.get('quoteType') == 'FUTURE':
        return 'commodity'
    
    # Default to stock (includes international)
    return 'stock'


async def validate_symbol(symbol: str) -> bool:
    """Quick validation check (lightweight)"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return bool(info and 'symbol' in info)
    except:
        return False
