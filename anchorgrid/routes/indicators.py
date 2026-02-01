# backend/routes/indicators.py
"""
Technical Indicators API Routes
Real-time and historical technical analysis
"""

from fastapi import APIRouter, HTTPException, Query
from anchorgrid.services.indicators_service import get_indicators
from anchorgrid.core.logger import log

router = APIRouter()


@router.get("/{symbol}")
async def get_symbol_indicators(
    symbol: str,
    days: int = Query(90, ge=30, le=365, description="Days of history (30-365)")
):
    """
    Get all technical indicators for a symbol
    
    Returns:
        - SMA (20, 50)
        - EMA (20, 50)
        - RSI (14)
        - MACD (12, 26, 9)
        - Bollinger Bands (20, 2σ)
        - Trading alerts
    
    Example:
        GET /indicators/AAPL?days=90
    """
    try:
        indicators = await get_indicators(symbol.upper(), days)
        
        if "error" in indicators:
            raise HTTPException(status_code=400, detail=indicators["error"])
        
        log.info(f"📊 Indicators calculated for {symbol}")
        return indicators
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error calculating indicators for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate indicators")
