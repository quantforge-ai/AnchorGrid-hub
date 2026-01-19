"""
Historical Data API Routes

Endpoints for fetching historical price data from international sources
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
import pandas as pd
from quantgrid.core.dependencies import get_current_user
from quantgrid.services.historical_data_service import (
    get_historical_data,
    clear_cache
)

router = APIRouter(prefix="/historical", tags=["historical-data"])


@router.get("/{symbol}")
async def get_symbol_history(
    symbol: str,
    period: str = Query("1y", regex="^(1d|1w|1mo|3mo|6mo|1y|5y)$"),
    interval: str = Query("1d", regex="^(1d|1wk|1mo)$"),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get historical OHLCV data for a symbol
    
    Supports 100+ international exchanges via multi-source scraping:
    - Yahoo Finance (primary)
    - Investing.com (backup)
    - Exchange-direct scrapers (TWSE, HKEX, NSE, B3)
    
    Examples:
        - /historical/AAPL?period=1y
        - /historical/2330.TW?period=6mo
        - /historical/RELIANCE.NS?period=1y
    """
    df = await get_historical_data(symbol, period, interval)
    
    if df is None or df.empty:
        return {
            "symbol": symbol,
            "data": [],
            "count": 0,
            "error": "No data available"
        }
    
    # Convert DataFrame to JSON-friendly format
    data = df.to_dict('records')
    
    # Format dates as strings
    for record in data:
        if 'date' in record:
            record['date'] = record['date'].isoformat() if hasattr(record['date'], 'isoformat') else str(record['date'])
    
    return {
        "symbol": symbol,
        "period": period,
        "interval": interval,
        "data": data,
        "count": len(data)
    }


@router.post("/refresh/{symbol}")
async def refresh_symbol_cache(
    symbol: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Clear cache for specific symbol (forces fresh fetch)"""
    clear_cache(symbol)
    return {"message": f"Cache cleared for {symbol}"}


@router.post("/refresh-all")
async def refresh_all_cache(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Clear all historical data cache"""
    clear_cache()
    return {"message": "All historical cache cleared"}
