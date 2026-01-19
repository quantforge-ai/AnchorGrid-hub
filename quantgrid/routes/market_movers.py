"""
Market Movers API Routes

Endpoints for dynamic ticker lists (gainers/losers/active/trending)
PUBLIC endpoints - no authentication required
"""

from fastapi import APIRouter, Query
from typing import List
from quantgrid.services.market_movers_service import (
    get_top_gainers,
    get_top_losers,
    get_most_active,
    get_trending,
    get_tech_sector,
    get_finance_sector,
    clear_cache
)

router = APIRouter(prefix="/market-movers", tags=["market-movers"])


@router.get("/gainers")
async def get_gainers(
    limit: int = 15
) -> List[str]:
    """Get top gaining stocks (yfinance + scraping fallback)"""
    return await get_top_gainers(limit)


@router.get("/losers")
async def get_losers(
    limit: int = 15
) -> List[str]:
    """Get top losing stocks (yfinance + scraping fallback)"""
    return await get_top_losers(limit)


@router.get("/active")
async def get_active(
    limit: int = 15
) -> List[str]:
    """Get most actively traded stocks (yfinance + scraping fallback)"""
    return await get_most_active(limit)


@router.get("/trending")
async def get_trending_tickers(
    limit: int = 15
) -> List[str]:
    """Get trending stocks (Yahoo Finance scraping)"""
    return await get_trending(limit)


@router.get("/tech")
async def get_tech_stocks(
    limit: int = 15
) -> List[str]:
    """Get global technology sector stocks (dynamic Google Finance + curated fallback)"""
    return await get_tech_sector(limit)


@router.get("/finance")
async def get_finance_stocks(
    limit: int = 15
) -> List[str]:
    """Get global finance sector stocks (dynamic Google Finance + curated fallback)"""
    return await get_finance_sector(limit)


@router.post("/refresh")
async def refresh_cache() -> dict:
    """Clear market movers cache (forces fresh fetch)"""
    clear_cache()
    return {"message": "Market movers cache cleared"}

