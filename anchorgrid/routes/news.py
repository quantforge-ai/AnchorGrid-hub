# backend/routes/news.py
"""
News API Routes
Multi-source financial news endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from anchorgrid.core.dependencies import get_current_user
from anchorgrid.db.models import User
from anchorgrid.services.news_service import (
    get_general_news,
    get_symbol_news,
    get_treasury_yields,
    get_portfolio_news,
    track_news_view
)
from anchorgrid.core.logger import log

router = APIRouter()


@router.get("/general")
async def general_news(
    category: str = Query("general", description="News category (general, forex, crypto, merger)"),
    limit: int = Query(20, ge=1, le=100, description="Max articles (1-100)")
):
    """
    Get general financial news
    
    Categories:
        - general: Market-wide news
        - forex: Foreign exchange news
        - crypto: Cryptocurrency news
        - merger: M&A news
    
    Sources: Finnhub (primary), CoinGecko (fallback)
    """
    try:
        news = await get_general_news(category, limit)
        log.info(f"📰 General news requested: category={category}, count={len(news)}")
        return {"category": category, "count": len(news), "news": news}
    except Exception as e:
        log.error(f"Error fetching general news: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch news")


@router.get("/symbol/{symbol}")
async def symbol_news(
    symbol: str,
    asset_type: str = Query("stock", description="Asset type (stock or crypto)"),
    days: int = Query(7, ge=1, le=30, description="Lookback days (1-30)")
):
    """
    Get news for specific symbol
    
    Args:
        symbol: Stock ticker or crypto symbol
        asset_type: "stock" or "crypto"
        days: Days of history
    
    Sources: Finnhub (stocks), CoinGecko (crypto)
    """
    try:
        news = await get_symbol_news(symbol.upper(), asset_type, days)
        log.info(f"📰 Symbol news requested: {symbol}, type={asset_type}, count={len(news)}")
        return {"symbol": symbol, "asset_type": asset_type, "count": len(news), "news": news}
    except Exception as e:
        log.error(f"Error fetching symbol news for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch news for {symbol}")


@router.get("/treasury")
async def treasury_yields_endpoint():
    """
    Get current US Treasury yields
    
    Returns 2-year, 10-year, and 30-year rates
    
    Source: FRED (Federal Reserve Economic Data)
    """
    try:
        yields = await get_treasury_yields()
        log.info("📰 Treasury yields requested")
        return yields
    except Exception as e:
        log.error(f"Error fetching Treasury yields: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Treasury yields")


@router.get("/portfolio")
async def portfolio_news_endpoint(
    limit: int = Query(15, ge=1, le=50, description="Max articles (1-50)"),
    current_user: User = Depends(get_current_user)
):
    """
    Get personalized news feed based on portfolio holdings
    
    Aggregates news from all owned positions
    
    Requires authentication
    """
    try:
        news = await get_portfolio_news(current_user.id, limit)
        log.info(f"📰 Portfolio news requested by user {current_user.id}, count={len(news)}")
        return {"user_id": current_user.id, "count": len(news), "news": news}
    except Exception as e:
        log.error(f"Error fetching portfolio news: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch portfolio news")


@router.post("/track")
async def track_news_view_endpoint(
    article_id: str,
    symbol: str = None,
    current_user: User = Depends(get_current_user)
):
    """
    Track news article view for Shadow Watch
    
    Updates user's interest library based on news consumption
    """
    try:
        await track_news_view(current_user.id, article_id, symbol)
        log.info(f"📰 News view tracked: user {current_user.id}, article {article_id}")
        return {"message": "News view tracked", "article_id": article_id}
    except Exception as e:
        log.error(f"Error tracking news view: {e}")
        raise HTTPException(status_code=500, detail="Failed to track news view")
