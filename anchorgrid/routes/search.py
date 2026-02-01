# backend/routes/search.py
"""
Symbol Search API Routes

Universal symbol search across all markets
"""
from fastapi import APIRouter, HTTPException
from anchorgrid.services.search_service import search_symbol, validate_symbol
from anchorgrid.core.logger import log

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/{symbol}")
async def search_symbol_endpoint(symbol: str):
    """
    Search for any symbol globally
    
    Examples:
    - /search/AAPL → Apple (US)
    - /search/AAPL.L → Apple (London)
    - /search/2330.TW → TSMC (Taiwan)
    - /search/BTC-USD → Bitcoin
    - /search/^TNX → 10-Year Treasury
    - /search/EURUSD=X → EUR/USD forex
    
    Returns:
        Symbol info with current quote
    """
    log.info(f"🔍 Search request: {symbol}")
    
    result = await search_symbol(symbol)
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Symbol '{symbol}' not found"
        )
    
    return result


@router.get("/validate/{symbol}")
async def validate_symbol_endpoint(symbol: str):
    """Quick validation check (returns true/false)"""
    is_valid = await validate_symbol(symbol)
    return {"symbol": symbol, "valid": is_valid}
