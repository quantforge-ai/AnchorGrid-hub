# backend/services/news_service.py
"""
Production-Grade Multi-Source News Aggregator - Tier 1

Smart news routing with fallbacks and caching:
- Finnhub: Primary (real-time stocks/forex/general)
- CoinGecko: Crypto specialist (unlimited)
- FRED: Macro/Treasury yields (official, unlimited)

Phase 2E: News Integration
"""

import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from textblob import TextBlob
from anchorgrid.core.config import get_settings
from anchorgrid.services.redis_service import get_redis_client
from anchorgrid.services.shadow_watch import track_activity
from anchorgrid.core.logger import log
import json

settings = get_settings()

# API Configuration
FINNHUB_KEY = settings.FINNHUB_API_KEY
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
FRED_BASE = "https://api.stlouisfed.org/fred"
FRED_KEY = settings.fred_api_key if hasattr(settings, 'fred_api_key') else "demo"  # TODO: Add to .env


def analyze_sentiment(text: str) -> str:
    """
    Analyze sentiment using TextBlob
    
    Returns: "positive", "neutral", or "negative"
    """
    try:
        score = TextBlob(text).sentiment.polarity
        if score > 0.1:
            return "positive"
        elif score < -0.1:
            return "negative"
        else:
            return "neutral"
    except:
        return "neutral"


async def get_general_news(category: str = "general", limit: int = 20) -> List[Dict]:
    """
    Get general financial news (Finnhub primary, CoinGecko fallback)
    
    Args:
        category: News category (general, forex, crypto, merger)
        limit: Max articles
        
    Returns:
        List of news articles with sentiment
    """
    cache_key = f"news:general:{category}"
    
    # Try cache first
    redis_client = await get_redis_client()
    if redis_client:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                log.debug(f"📰 Cache HIT: {cache_key}")
                return json.loads(cached)
        except Exception as e:
            log.warning(f"Redis get failed: {e}")
    
    # Fetch from Finnhub
    url = "https://finnhub.io/api/v1/news"
    params = {"category": category, "token": FINNHUB_KEY}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            log.info(f"📡 Fetching {category} news from Finnhub")
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            news = resp.json()[:limit]
            
            # Enrich with sentiment and source
            for item in news:
                item["source"] = "finnhub"
                item["sentiment"] = analyze_sentiment(item.get("headline", ""))
            
            # Cache for 10 minutes
            if redis_client:
                try:
                    await redis_client.setex(cache_key, 600, json.dumps(news))
                    log.debug(f"💾 Cached news: {cache_key}")
                except Exception as e:
                    log.warning(f"Redis set failed: {e}")
            
            return news
            
        except Exception as e:
            log.warning(f"Finnhub failed: {e}, trying CoinGecko fallback")
            
            # Fallback to CoinGecko for crypto/general news
            try:
                cg_news = await _coingecko_news(limit)
                if cg_news and redis_client:
                    await redis_client.setex(cache_key, 600, json.dumps(cg_news))
                return cg_news
            except Exception as e2:
                log.error(f"All news sources failed: {e2}")
                return []


async def get_symbol_news(symbol: str, asset_type: str = "stock", days: int = 7) -> List[Dict]:
    """
    Get news for specific symbol
    
    Args:
        symbol: Stock/crypto symbol
        asset_type: "stock" or "crypto"
        days: Lookback period
        
    Returns:
        List of news articles
    """
    cache_key = f"news:symbol:{symbol}:{asset_type}"
    
    # Try cache first
    redis_client = await get_redis_client()
    if redis_client:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                log.debug(f"📰 Cache HIT: {cache_key}")
                return json.loads(cached)
        except Exception as e:
            log.warning(f"Redis get failed: {e}")
    
    # Route based on asset type
    if asset_type == "crypto":
        # CoinGecko for crypto (no symbol-specific, use general)
        news = await _coingecko_news(20)
    else:
        # Finnhub for stocks
        news = await _finnhub_symbol_news(symbol, days)
    
    # Cache for 15 minutes
    if redis_client and news:
        try:
            await redis_client.setex(cache_key, 900, json.dumps(news))
            log.debug(f"💾 Cached symbol news: {cache_key}")
        except Exception as e:
            log.warning(f"Redis set failed: {e}")
    
    return news


async def _finnhub_symbol_news(symbol: str, days: int) -> List[Dict]:
    """Fetch company-specific news from Finnhub"""
    url = "https://finnhub.io/api/v1/company-news"
    to_date = datetime.utcnow().strftime("%Y-%m-%d")
    from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    params = {
        "symbol": symbol.upper(),
        "from": from_date,
        "to": to_date,
        "token": FINNHUB_KEY
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            log.info(f"📡 Fetching news for {symbol} from Finnhub")
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            news = resp.json()
            
            # Enrich
            for item in news:
                item["source"] = "finnhub"
                item["sentiment"] = analyze_sentiment(item.get("headline", ""))
            
            return sorted(news, key=lambda x: x.get("datetime", 0), reverse=True)
        except Exception as e:
            log.error(f"Finnhub symbol news failed for {symbol}: {e}")
            return []


async def _coingecko_news(limit: int = 20) -> List[Dict]:
    """Fetch crypto news from CoinGecko"""
    url = f"{COINGECKO_BASE}/news"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            log.info("📡 Fetching crypto news from CoinGecko")
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            
            news = data.get("data", [])[:limit]
            
            # Normalize format to match Finnhub
            for item in news:
                item["source"] = "coingecko"
                item["headline"] = item.get("title", "")
                item["sentiment"] = analyze_sentiment(item.get("title", ""))
                item["datetime"] = item.get("updated_at", 0)
            
            return news
        except Exception as e:
            log.error(f"CoinGecko news failed: {e}")
            return []


async def get_treasury_yields() -> Dict:
    """
    Get current Treasury yields from FRED
    
    Returns:
        {
            "source": "fred",
            "treasury_yields": {
                "2-year": {"rate": "4.25", "date": "2025-12-21"},
                "10-year": {"rate": "4.50", "date": "2025-12-21"},
                "30-year": {"rate": "4.75", "date": "2025-12-21"}
            }
        }
    """
    cache_key = "news:macro:treasury_yields"
    
    # Try cache first (1-hour TTL for macro data)
    redis_client = await get_redis_client()
    if redis_client:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                log.debug("📰 Cache HIT: treasury yields")
                return json.loads(cached)
        except Exception as e:
            log.warning(f"Redis get failed: {e}")
    
    # Fetch from FRED
    series_map = {
        "DGS2": "2-year",
        "DGS10": "10-year",
        "DGS30": "30-year"
    }
    
    yields = {}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for series_id, name in series_map.items():
            url = f"{FRED_BASE}/series/observations"
            params = {
                "series_id": series_id,
                "api_key": FRED_KEY,
                "file_type": "json",
                "limit": 1,
                "sort_order": "desc"
            }
            
            try:
                log.info(f"📡 Fetching {name} Treasury yield from FRED")
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                
                if data.get("observations"):
                    obs = data["observations"][0]
                    yields[name] = {
                        "rate": obs.get("value", "N/A"),
                        "date": obs.get("date", "N/A")
                    }
                else:
                    yields[name] = {"rate": "N/A", "date": "N/A"}
                    
            except Exception as e:
                log.warning(f"FRED {name} failed: {e}")
                yields[name] = {"rate": "N/A", "date": "N/A"}
    
    result = {
        "source": "fred",
        "treasury_yields": yields
    }
    
    # Cache for 1 hour
    if redis_client:
        try:
            await redis_client.setex(cache_key, 3600, json.dumps(result))
            log.debug("💾 Cached Treasury yields")
        except Exception as e:
            log.warning(f"Redis set failed: {e}")
    
    return result


async def get_portfolio_news(user_id: int, limit: int = 15) -> List[Dict]:
    """
    Get personalized news feed based on user's portfolio holdings
    
    Args:
        user_id: User ID
        limit: Max articles
        
    Returns:
        Aggregated news from all holdings
    """
    from anchorgrid.services.portfolio_service import get_portfolio_summary
    
    try:
        # Get user's holdings
        summary = await get_portfolio_summary(user_id)
        symbols = [pos["symbol"] for pos in summary["positions"] if pos["quantity"] > 0]
        
        if not symbols:
            # No holdings, return general news
            return await get_general_news(limit=limit)
        
        # Aggregate news from top holdings
        all_news = []
        for symbol in symbols[:5]:  # Top 5 positions only
            # Simple asset type detection (TODO: improve)
            asset_type = "crypto" if symbol in ["BTC", "ETH", "USDT", "BNB"] else "stock"
            news = await get_symbol_news(symbol, asset_type, days=3)
            
            # Tag with symbol
            for item in news:
                item["related_symbol"] = symbol
            
            all_news.extend(news)
        
        # Deduplicate and sort by date
        seen = set()
        unique_news = []
        for item in all_news:
            item_id = item.get("id") or item.get("headline", "")
            if item_id not in seen:
                seen.add(item_id)
                unique_news.append(item)
        
        unique_news.sort(key=lambda x: x.get("datetime", 0), reverse=True)
        
        return unique_news[:limit]
        
    except Exception as e:
        log.error(f"Portfolio news failed: {e}")
        return await get_general_news(limit=limit)


async def track_news_view(user_id: int, article_id: str, symbol: Optional[str] = None):
    """
    Track news view for Shadow Watch
    
    Args:
        user_id: User ID
        article_id: Article identifier
        symbol: Related symbol (if applicable)
    """
    await track_activity(
        user_id=user_id,
        symbol=symbol or "NEWS",
        action="news_view",
        event_metadata={"article_id": article_id}
    )
    log.info(f"📰 News view tracked: user {user_id}, article {article_id}")
