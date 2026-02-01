# backend/routes/quotes.py
"""
Market Data Quotes API Routes
Real-time and historical price data
"""
from fastapi import APIRouter, HTTPException, Query
from anchorgrid.services.quote_service import (
    get_realtime_quote,
    get_historical_data,
    get_batch_quotes
)
from anchorgrid.core.logger import log
from typing import Literal

router = APIRouter(prefix="/quotes", tags=["Quotes"])


@router.get("/batch")
async def batch_quotes(symbols: str = Query(..., description="Comma-separated symbols, e.g. AAPL,MSFT,GOOGL")):
    """
    Fetch multiple quotes in ONE request (reduces API calls!)
    
    **Example:**
    ```
    GET /quotes/batch?symbols=AAPL,MSFT,GOOGL
    ```
    
    **Response:**
    ```json
    {
      "AAPL": {"symbol": "AAPL", "price": 182.31, ...},
      "MSFT": {"symbol": "MSFT", "price": 415.23, ...},
      "GOOGL": {"symbol": "GOOGL", "price": 145.67, ...}
    }
    ```
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    log.info(f"📦 Batch quote request for {len(symbol_list)} symbols")
    
    quotes = await get_batch_quotes(symbol_list)
    return quotes


@router.get("/{symbol}")
async def realtime_quote(symbol: str):
    """
    Get current real-time quote for a symbol
    
    **Example:**
    ```
    GET /quotes/AAPL
    ```
    
    **Response:**
    ```json
    {
      "symbol": "AAPL",
      "price": 182.31,
      "change": 2.15,
      "change_percent": 1.19,
      "high": 183.50,
      "low": 180.12,
      "open": 181.00,
      "previous_close": 180.16,
      "timestamp": "2025-01-20T15:30:00",
      "source": "finnhub"
    }
    ```
    """
    log.info(f"📊 Quote request for {symbol}")
    
    quote = await get_realtime_quote(symbol)
    
    if not quote:
        raise HTTPException(
            status_code=404,
            detail=f"Quote not found for {symbol}. Symbol may be invalid or market closed."
        )
    
    return quote


@router.get("/{symbol}/historical")
async def historical_quote(
    symbol: str,
    timeframe: Literal["1M", "3M", "6M", "1Y", "5Y"] = Query(
        default="1M",
        description="Time period for historical data"
    )
):
    """
    Get historical OHLCV candles for a symbol
    
    **Example:**
    ```
    GET /quotes/historical/AAPL?timeframe=3M
    ```
    
    **Response:**
    ```json
    {
      "symbol": "AAPL",
      "timeframe": "3M",
      "candles": [
        {
          "timestamp": "2024-10-20T00:00:00",
          "open": 178.50,
          "high": 181.20,
          "low": 177.30,
          "close": 180.16,
          "volume": 52341231
        },
        ...
      ]
    }
    ```
    """
    log.info(f"📈 Historical data request for {symbol} ({timeframe})")
    
    candles = await get_historical_data(symbol, timeframe)
    
    if not candles:
        raise HTTPException(
            status_code=404,
            detail=f"Historical data not available for {symbol}"
        )
    
    return {
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "count": len(candles),
        "candles": candles
    }


@router.post("/batch")
async def batch_quotes(symbols: list[str]):
    """
    Get quotes for multiple symbols at once (for watchlists)
    
    **Request Body:**
    ```json
    {
      "symbols": ["AAPL", "TSLA", "MSFT"]
    }
    ```
    
    **Response:**
    ```json
    {
      "AAPL": { "symbol": "AAPL", "price": 182.31, ... },
      "TSLA": { "symbol": "TSLA", "price": 245.67, ... },
      "MSFT": { "symbol": "MSFT", "price": 380.12, ... }
    }
    ```
    """
    if not symbols:
        raise HTTPException(status_code=400, detail="No symbols provided")
    
    if len(symbols) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 symbols per batch request"
        )
    
    log.info(f"📊 Batch quote request for {len(symbols)} symbols")
    
    quotes = await get_batch_quotes(symbols)
    
    return quotes


@router.get("/market-movers")
async def get_market_movers():
    """
    Get market movers (gainers, losers, most active)
    Real-time data from yfinance
    """
    from anchorgrid.services import quote_service
    
    try:
        # Fetch real data using quote_service
        gainers = await quote_service.get_top_gainers(limit=10)
        losers = await quote_service.get_top_losers(limit=10)
        
        # Most active: combine gainers and losers, sort by volume
        # Assuming gainers and losers return dicts with 'volume'
        most_active = gainers + losers
        most_active.sort(key=lambda x: x.get("volume", 0), reverse=True)
        most_active = most_active[:10]
        
        return {
            "gainers": gainers,
            "losers": losers,
            "most_active": most_active,
            "source": "yfinance",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        log.error(f"Error fetching market movers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch market movers: {str(e)}"
        )


@router.get("/top-gainers/market")
async def get_top_market_gainers():
    """
    Get top gaining stocks (real-time sorted by change %)
    
    Returns actual top gainers based on current market data.
    """
    from anchorgrid.services.quote_service import get_top_gainers
    
    gainers = await get_top_gainers(limit=8)
    log.info(f"📈 Top gainers: {', '.join([g['symbol'] for g in gainers])}") # Adjusted to handle list of dicts
    
    return {
        "symbols": gainers,
        "mode": "gainers"
    }


@router.get("/top-losers/market")
async def get_top_market_losers():
    """
    Get top losing stocks (real-time sorted by change %)
    
    Returns actual top losers based on current market data.
    """
    from anchorgrid.services.quote_service import get_top_losers
    
    losers = await get_top_losers(limit=8)
    log.info(f"📉 Top losers: {', '.join(losers)}")
    
    return {
        "symbols": losers,
        "mode": "losers"
    }
