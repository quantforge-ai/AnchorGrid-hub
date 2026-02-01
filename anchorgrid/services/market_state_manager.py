"""
AnchorGrid AI Engine - Market State Manager

The central orchestrator for all market data access.
Implements demand-driven caching with smart TTL policies.

Key Principles:
1. TimescaleDB is the single source of truth
2. AnchorGrid Core is the primary backbone
3. AI never calls APIs directly — only reads from cache
4. On-demand + lazy caching for 90,000+ global tickers
"""
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from dataclasses import dataclass

from loguru import logger
from sqlalchemy import select, func, update, insert
from sqlalchemy.ext.asyncio import AsyncSession

from anchorgrid.db.models.ohlcv import OHLCV


# =============================================================================
# ENUMS & CONFIGURATION
# =============================================================================

class AssetClass(str, Enum):
    """Asset classification for TTL policies"""
    EQUITY = "equity"
    CRYPTO = "crypto"
    FOREX = "forex"
    MACRO = "macro"
    FUNDAMENTALS = "fundamentals"
    NEWS = "news"


class Tier(str, Enum):
    """Cache tier for refresh scheduling"""
    HOT = "hot"      # Top 100-500, refresh every 5-15 min
    WARM = "warm"    # Requested this week, refresh daily
    COLD = "cold"    # Requested once, on-demand only
    FROZEN = "frozen"  # Never requested


@dataclass
class TTLPolicy:
    """Time-to-live configuration per asset class"""
    trading_hours_ttl: timedelta
    off_hours_ttl: timedelta
    primary_source: str
    fallback_sources: list[str]


# Cache policies per asset class
CACHE_POLICIES = {
    AssetClass.EQUITY: TTLPolicy(
        trading_hours_ttl=timedelta(minutes=15),
        off_hours_ttl=timedelta(hours=24),
        primary_source="yfinance",
        fallback_sources=["alpha_vantage", "fmp"],
    ),
    AssetClass.CRYPTO: TTLPolicy(
        trading_hours_ttl=timedelta(minutes=2),
        off_hours_ttl=timedelta(minutes=5),  # Crypto is 24/7
        primary_source="coingecko",
        fallback_sources=["binance", "coinmarketcap"],
    ),
    AssetClass.FOREX: TTLPolicy(
        trading_hours_ttl=timedelta(minutes=5),
        off_hours_ttl=timedelta(minutes=15),
        primary_source="yfinance",
        fallback_sources=["twelve_data"],
    ),
    AssetClass.MACRO: TTLPolicy(
        trading_hours_ttl=timedelta(days=7),
        off_hours_ttl=timedelta(days=30),
        primary_source="fred",
        fallback_sources=[],
    ),
    AssetClass.FUNDAMENTALS: TTLPolicy(
        trading_hours_ttl=timedelta(days=7),
        off_hours_ttl=timedelta(days=7),
        primary_source="fmp",
        fallback_sources=["finnhub"],
    ),
    AssetClass.NEWS: TTLPolicy(
        trading_hours_ttl=timedelta(hours=1),
        off_hours_ttl=timedelta(hours=1),
        primary_source="newsapi",
        fallback_sources=["finnhub"],
    ),
}

# Tier promotion thresholds
TIER_THRESHOLDS = {
    Tier.HOT: 50,    # 50+ requests/week → HOT
    Tier.WARM: 5,    # 5-49 requests/week → WARM
    Tier.COLD: 1,    # 1-4 requests/week → COLD
}


# =============================================================================
# TICKER REGISTRY (In-Memory + Redis for persistence)
# =============================================================================

class TickerRegistry:
    """
    Tracks ticker access patterns for tier promotion.
    Uses Redis for persistence, in-memory for speed.
    """
    
    def __init__(self):
        self._access_counts: dict[str, int] = {}  # ticker -> count this week
        self._last_access: dict[str, datetime] = {}
        self._tiers: dict[str, Tier] = {}
        self._redis_client = None
    
    async def init_redis(self):
        """Initialize Redis connection for persistence"""
        try:
            import redis.asyncio as redis
            from anchorgrid.core.config import settings
            self._redis_client = redis.Redis(
                host=getattr(settings, "REDIS_HOST", "localhost"),
                port=getattr(settings, "REDIS_PORT", 6379),
                db=getattr(settings, "REDIS_DB", 0),
            )
            await self._load_from_redis()
        except Exception as e:
            logger.warning(f"Redis not available, using memory-only: {e}")
    
    async def _load_from_redis(self):
        """Load tier data from Redis on startup"""
        if not self._redis_client:
            return
        try:
            keys = await self._redis_client.keys("ticker:*")
            for key in keys:
                data = await self._redis_client.hgetall(key)
                ticker = key.decode().replace("ticker:", "")
                self._access_counts[ticker] = int(data.get(b"count", 0))
                self._tiers[ticker] = Tier(data.get(b"tier", b"cold").decode())
        except Exception as e:
            logger.error(f"Failed to load from Redis: {e}")
    
    async def record_access(self, ticker: str):
        """Record a ticker access and potentially promote tier"""
        ticker = ticker.upper()
        now = datetime.now()
        
        # Increment count
        self._access_counts[ticker] = self._access_counts.get(ticker, 0) + 1
        self._last_access[ticker] = now
        
        # Check tier promotion
        count = self._access_counts[ticker]
        new_tier = self._calculate_tier(count)
        old_tier = self._tiers.get(ticker, Tier.COLD)
        
        if new_tier != old_tier:
            self._tiers[ticker] = new_tier
            logger.info(f"Ticker {ticker} promoted: {old_tier.value} → {new_tier.value}")
        
        # Persist to Redis (async, non-blocking)
        if self._redis_client:
            asyncio.create_task(self._persist_to_redis(ticker))
    
    async def _persist_to_redis(self, ticker: str):
        """Persist ticker data to Redis"""
        try:
            await self._redis_client.hset(f"ticker:{ticker}", mapping={
                "count": self._access_counts.get(ticker, 0),
                "tier": self._tiers.get(ticker, Tier.COLD).value,
                "last_access": self._last_access.get(ticker, datetime.now()).isoformat(),
            })
            await self._redis_client.expire(f"ticker:{ticker}", 7 * 24 * 3600)  # 7 days TTL
        except Exception as e:
            logger.error(f"Failed to persist to Redis: {e}")
    
    def _calculate_tier(self, count: int) -> Tier:
        """Calculate tier based on access count"""
        if count >= TIER_THRESHOLDS[Tier.HOT]:
            return Tier.HOT
        elif count >= TIER_THRESHOLDS[Tier.WARM]:
            return Tier.WARM
        elif count >= TIER_THRESHOLDS[Tier.COLD]:
            return Tier.COLD
        return Tier.FROZEN
    
    def get_tier(self, ticker: str) -> Tier:
        """Get current tier for ticker"""
        return self._tiers.get(ticker.upper(), Tier.COLD)
    
    def get_hot_tickers(self) -> list[str]:
        """Get all HOT tier tickers for scheduled refresh"""
        return [t for t, tier in self._tiers.items() if tier == Tier.HOT]
    
    def get_warm_tickers(self) -> list[str]:
        """Get all WARM tier tickers for daily refresh"""
        return [t for t, tier in self._tiers.items() if tier == Tier.WARM]


# =============================================================================
# MARKET STATE MANAGER (The Core)
# =============================================================================

class MarketStateManager:
    """
    The central orchestrator for all market data access.
    
    This class ensures:
    1. Cache-first strategy (TimescaleDB)
    2. On-demand fetching with FREE sources
    3. Automatic tier promotion
    4. Smart TTL policies per asset class
    
    Usage:
        manager = MarketStateManager()
        data = await manager.get_market_data("AAPL", AssetClass.EQUITY, session)
    """
    
    def __init__(self):
        self.registry = TickerRegistry()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the manager (call on app startup)"""
        if self._initialized:
            return
        await self.registry.init_redis()
        self._initialized = True
        logger.info("MarketStateManager initialized")
    
    # -------------------------------------------------------------------------
    # MAIN ENTRY POINT
    # -------------------------------------------------------------------------
    
    async def get_market_data(
        self,
        ticker: str,
        asset_class: AssetClass,
        session: AsyncSession,
        interval: str = "1d",
        lookback_days: int = 30,
        force_refresh: bool = False,
    ) -> list[dict]:
        """
        Get market data for a ticker with smart caching.
        
        Flow:
        1. Check TimescaleDB cache
        2. If fresh → return immediately (0 API calls)
        3. If stale → fetch from primary source → cache → return
        
        Args:
            ticker: Stock/crypto symbol (e.g., "AAPL", "BTCUSDT")
            asset_class: Type of asset for TTL policy
            session: Database session
            interval: Candle interval
            lookback_days: Days of history
            force_refresh: Bypass cache and fetch fresh
            
        Returns:
            List of OHLCV dictionaries
        """
        ticker = ticker.upper()
        
        # Record access for tier tracking
        await self.registry.record_access(ticker)
        
        # Check cache freshness
        if not force_refresh:
            cached_data = await self._get_from_cache(
                ticker, asset_class, session, interval, lookback_days
            )
            if cached_data:
                logger.debug(f"Cache HIT for {ticker} ({len(cached_data)} rows)")
                return cached_data
        
        # Cache miss or force refresh → fetch from source
        logger.info(f"Cache MISS for {ticker}, fetching from source")
        fresh_data = await self._fetch_and_cache(
            ticker, asset_class, session, interval, lookback_days
        )
        
        return fresh_data
    
    # -------------------------------------------------------------------------
    # CACHE OPERATIONS
    # -------------------------------------------------------------------------
    
    async def _get_from_cache(
        self,
        ticker: str,
        asset_class: AssetClass,
        session: AsyncSession,
        interval: str,
        lookback_days: int,
    ) -> list[dict] | None:
        """
        Check TimescaleDB for fresh data.
        Returns None if data is stale or doesn't exist.
        """
        policy = CACHE_POLICIES.get(asset_class, CACHE_POLICIES[AssetClass.EQUITY])
        ttl = self._get_current_ttl(asset_class, policy)
        
        # Query for data within TTL
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        freshness_cutoff = datetime.now() - ttl
        
        stmt = (
            select(OHLCV)
            .where(OHLCV.ticker == ticker)
            .where(OHLCV.interval == interval)
            .where(OHLCV.timestamp >= cutoff_date)
            .order_by(OHLCV.timestamp.desc())
        )
        
        result = await session.execute(stmt)
        rows = result.scalars().all()
        
        if not rows:
            return None
        
        # Check if most recent data is within TTL
        most_recent = rows[0].timestamp
        if most_recent < freshness_cutoff:
            logger.debug(f"{ticker} data is stale (last update: {most_recent})")
            return None
        
        # Convert to dicts
        return [
            {
                "timestamp": row.timestamp.isoformat(),
                "ticker": row.ticker,
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.volume,
                "interval": row.interval,
            }
            for row in rows
        ]
    
    async def _fetch_and_cache(
        self,
        ticker: str,
        asset_class: AssetClass,
        session: AsyncSession,
        interval: str,
        lookback_days: int,
    ) -> list[dict]:
        """
        Fetch fresh data from source and cache in TimescaleDB.
        """
        policy = CACHE_POLICIES.get(asset_class, CACHE_POLICIES[AssetClass.EQUITY])
        
        # Try primary source first, then fallbacks
        sources = [policy.primary_source] + policy.fallback_sources
        data = None
        
        for source in sources:
            try:
                data = await self._fetch_from_source(
                    ticker, source, interval, lookback_days
                )
                if data:
                    logger.info(f"Fetched {len(data)} rows from {source}")
                    break
            except Exception as e:
                logger.warning(f"Source {source} failed for {ticker}: {e}")
                continue
        
        if not data:
            logger.error(f"All sources failed for {ticker}")
            return []
        
        # Upsert to TimescaleDB
        await self._upsert_to_db(session, data)
        
        return [
            {
                "timestamp": row.timestamp.isoformat(),
                "ticker": row.ticker,
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.volume,
                "interval": row.interval,
            }
            for row in data
        ]
    
    async def _fetch_from_source(
        self,
        ticker: str,
        source: str,
        interval: str,
        lookback_days: int,
    ):
        """
        Fetch data from custom scrapers (YFinance + backups).
        
        NOTE: Now uses quote_service instead of old API connectors.
        Zero API costs, global coverage.
        """
        from anchorgrid.services.quote_service import quote_service
        from anchorgrid.db.models.ohlcv import OHLCV
        from datetime import datetime, timedelta
        
        # For now, we'll use yfinance historical data
        # The quote_service handles real-time quotes
        # For historical OHLCV, we use yfinance directly
        try:
            from anchorgrid.plugins.finance.connectors.yahoo_scraper import yfinance_scraper
            
            # Fetch historical data
            hist_data = yfinance_scraper.get_historical(
                ticker, 
                period=f"{lookback_days}d" if lookback_days <= 730 else "max",
                interval=interval
            )
            
            if not hist_data or not hist_data.get("data"):
                logger.warning(f"No historical data for {ticker} from {source}")
                return None
            
            # Convert to OHLCV objects
            ohlcv_list = []
            for row in hist_data["data"]:
                try:
                    ohlcv = OHLCV(
                        ticker=ticker.upper(),
                        timestamp=row.get("Date") if isinstance(row.get("Date"), datetime) else datetime.fromisoformat(str(row.get("Date"))),
                        interval=interval,
                        open=float(row.get("Open", 0)),
                        high=float(row.get("High", 0)),
                        low=float(row.get("Low", 0)),
                        close=float(row.get("Close", 0)),
                        volume=int(row.get("Volume", 0)),
                        adj_close=float(row.get("Adj Close", row.get("Close", 0))),
                        source=source,
                    )
                    ohlcv_list.append(ohlcv)
                except Exception as e:
                    logger.debug(f"Skipping row for {ticker}: {e}")
                    continue
            
            logger.info(f"Fetched {len(ohlcv_list)} historical bars for {ticker}")
            return ohlcv_list
            
        except Exception as e:
            logger.error(f"Failed to fetch from {source} for {ticker}: {e}")
            return None

    
    async def _upsert_to_db(self, session: AsyncSession, data: list):
        """Upsert OHLCV data to TimescaleDB"""
        from anchorgrid.services.market_data_service import market_data_service
        await market_data_service.upsert_ohlcv(session, data)
    
    # -------------------------------------------------------------------------
    # TTL HELPERS
    # -------------------------------------------------------------------------
    
    def _get_current_ttl(self, asset_class: AssetClass, policy: TTLPolicy) -> timedelta:
        """
        Get appropriate TTL based on market hours.
        For now, uses a simple time check. Can be enhanced with exchange calendars.
        """
        now = datetime.now()
        hour = now.hour
        
        # Simplified: US market hours = 9:30-16:00 ET ≈ 14:30-21:30 UTC
        # For India: 9:15-15:30 IST ≈ 3:45-10:00 UTC
        # Crypto: always volatile TTL
        
        if asset_class == AssetClass.CRYPTO:
            return policy.trading_hours_ttl  # Crypto is always "trading"
        
        # Simple weekday + hours check
        is_weekday = now.weekday() < 5
        is_trading_hours = 9 <= hour <= 17  # Rough approximation
        
        if is_weekday and is_trading_hours:
            return policy.trading_hours_ttl
        return policy.off_hours_ttl
    
    # -------------------------------------------------------------------------
    # TIER-BASED REFRESH (For Celery Beat)
    # -------------------------------------------------------------------------
    
    def get_hot_tickers(self) -> list[str]:
        """Get HOT tier tickers for frequent refresh"""
        return self.registry.get_hot_tickers()
    
    def get_warm_tickers(self) -> list[str]:
        """Get WARM tier tickers for daily refresh"""
        return self.registry.get_warm_tickers()
    
    async def refresh_hot_tier(self, session: AsyncSession):
        """Refresh all HOT tier tickers (call every 5-15 min)"""
        tickers = self.get_hot_tickers()
        logger.info(f"Refreshing {len(tickers)} HOT tier tickers")
        
        for ticker in tickers:
            try:
                # Determine asset class from ticker pattern
                asset_class = self._infer_asset_class(ticker)
                await self.get_market_data(
                    ticker, asset_class, session, force_refresh=True
                )
            except Exception as e:
                logger.error(f"Failed to refresh {ticker}: {e}")
    
    def _infer_asset_class(self, ticker: str) -> AssetClass:
        """Infer asset class from ticker pattern"""
        ticker = ticker.upper()
        
        # Crypto patterns
        if ticker.endswith(("USDT", "USD", "BTC", "ETH")) or ticker in ["BTC", "ETH", "SOL"]:
            return AssetClass.CRYPTO
        
        # Forex patterns
        if len(ticker) == 6 and ticker[:3] in ["EUR", "USD", "GBP", "JPY", "AUD", "CAD"]:
            return AssetClass.FOREX
        
        # Macro patterns
        if ticker in ["GDP", "CPI", "UNRATE", "FEDFUNDS", "VIX"]:
            return AssetClass.MACRO
        
        # Default to equity
        return AssetClass.EQUITY


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

market_state_manager = MarketStateManager()
