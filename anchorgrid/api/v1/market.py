"""
QuantForge AI Engine - Market Data Routes

Endpoints for market data and technical analysis.
Uses real data from TimescaleDB when available, falls back to sample data.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field

from anchorgrid.api.deps import RequestContext, get_request_context
from anchorgrid.services.quant_service import quant_service, TechnicalAnalysis


router = APIRouter()


# =============================================================================
# Response Schemas
# =============================================================================

class OHLCV(BaseModel):
    """Single OHLCV bar"""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class MarketDataResponse(BaseModel):
    """Market data with OHLCV history"""
    ticker: str
    latest_price: float
    change_24h: float
    change_percent: float
    volume_24h: int
    data_source: str = "sample"  # "database" or "sample"
    ohlcv: list[OHLCV]


class MACDValues(BaseModel):
    """MACD indicator values"""
    line: Optional[float] = None
    signal: Optional[float] = None
    histogram: Optional[float] = None


class BollingerBands(BaseModel):
    """Bollinger Bands values"""
    upper: Optional[float] = None
    middle: Optional[float] = None
    lower: Optional[float] = None


class RegimeInfo(BaseModel):
    """Market regime information"""
    volatility: str
    trend: str
    volatility_percentile: float
    trend_strength: float


class SignalsResponse(BaseModel):
    """Technical analysis signals"""
    ticker: str
    timestamp: str
    price: float
    data_source: str = "sample"  # "database" or "sample"
    
    # Indicators
    rsi: Optional[float] = None
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    macd: MACDValues
    bollinger: BollingerBands
    atr: Optional[float] = None
    
    # Regime
    regime: RegimeInfo
    
    # Signal
    signal: str
    composite_score: float
    confidence: float
    components: dict


# =============================================================================
# Helper Functions
# =============================================================================

async def get_prices_from_db(ticker: str, limit: int = 100):
    """
    Try to fetch prices from TimescaleDB.
    Returns (prices, highs, lows, ohlcv_records) or None if no data.
    """
    try:
        from anchorgrid.db.session import timescale_session_maker
        from anchorgrid.services.market_data_service import market_data_service
        
        async with timescale_session_maker() as session:
            rows = await market_data_service.get_ohlcv(
                session,
                ticker=ticker,
                limit=limit,
            )
            
            if not rows:
                return None
            
            # Convert to lists (reverse for chronological order)
            rows = list(reversed(rows))
            prices = [r.close for r in rows]
            highs = [r.high for r in rows]
            lows = [r.low for r in rows]
            
            ohlcv_records = [
                OHLCV(
                    timestamp=r.timestamp.isoformat(),
                    open=r.open,
                    high=r.high,
                    low=r.low,
                    close=r.close,
                    volume=r.volume,
                )
                for r in rows
            ]
            
            return prices, highs, lows, ohlcv_records
    except Exception:
        # Database not available or error
        return None


SAMPLE_PRICES = [
    100.0, 102.0, 101.0, 103.0, 105.0,
    104.0, 106.0, 108.0, 107.0, 109.0,
    111.0, 110.0, 112.0, 114.0, 113.0,
    115.0, 117.0, 116.0, 118.0, 120.0,
    119.0, 121.0, 123.0, 122.0, 124.0,
    126.0, 125.0, 127.0, 129.0, 128.0,
]


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/{ticker}")
async def get_market_data(
    ticker: str,
    interval: str = Query("1d", description="1m, 5m, 1h, 1d"),
    limit: int = Query(100, le=1000),
    force_refresh: bool = Query(False, description="Force refresh from source"),
    ctx: RequestContext = Depends(get_request_context),
) -> MarketDataResponse:
    """
    Get market data for a ticker.
    
    Returns latest price and historical OHLCV data.
    Uses cache-first strategy: serves from DB if fresh, fetches if stale.
    
    **Requires Authentication**
    
    - **ticker**: Stock/crypto symbol (e.g., AAPL, BTC-USD, RELIANCE.NS)
    - **interval**: Time interval (1m, 5m, 1h, 1d)
    - **limit**: Number of bars to return (max 1000)
    - **force_refresh**: Bypass cache and fetch fresh data
    
    **Cache Behavior:**
    - First request for new ticker → fetches from yfinance (FREE) → caches
    - Subsequent requests → served from cache (0 API calls)
    - Automatic tier promotion for popular tickers
    """
    from anchorgrid.services.market_state_manager import market_state_manager, AssetClass
    from anchorgrid.db import get_timescale_session
    
    # Infer asset class from ticker
    asset_class = market_state_manager._infer_asset_class(ticker)
    
    # Initialize manager if needed
    if not market_state_manager._initialized:
        await market_state_manager.initialize()
    
    # Get data through MarketStateManager (cache-first)
    async with get_timescale_session() as session:
        try:
            data = await market_state_manager.get_market_data(
                ticker=ticker,
                asset_class=asset_class,
                session=session,
                interval=interval,
                lookback_days=limit,  # Approximate
                force_refresh=force_refresh,
            )
            
            if data:
                # Convert to response format
                ohlcv_records = [
                    OHLCV(
                        timestamp=row["timestamp"],
                        open=row["open"],
                        high=row["high"],
                        low=row["low"],
                        close=row["close"],
                        volume=row["volume"],
                    )
                    for row in data[:limit]
                ]
                
                prices = [row["close"] for row in data]
                latest_price = prices[-1] if prices else 0.0
                change_24h = (prices[-1] - prices[-2]) if len(prices) > 1 else 0.0
                change_pct = (change_24h / prices[-2] * 100) if len(prices) > 1 and prices[-2] != 0 else 0.0
                
                return MarketDataResponse(
                    ticker=ticker.upper(),
                    latest_price=latest_price,
                    change_24h=change_24h,
                    change_percent=round(change_pct, 2),
                    volume_24h=int(sum(row["volume"] for row in data[-1:])),
                    data_source="cache" if not force_refresh else "fresh",
                    ohlcv=ohlcv_records,
                )
        except Exception as e:
            # Log but don't fail - fall through to empty response
            from loguru import logger
            logger.error(f"MarketStateManager failed for {ticker}: {e}")
    
    # Fallback: try legacy direct DB query
    db_data = await get_prices_from_db(ticker, limit)
    
    if db_data:
        prices, highs, lows, ohlcv_records = db_data
        latest_price = prices[-1] if prices else 0.0
        change_24h = (latest_price - prices[-2]) if len(prices) > 1 else 0.0
        change_percent = (change_24h / prices[-2] * 100) if len(prices) > 1 and prices[-2] != 0 else 0.0
        
        return MarketDataResponse(
            ticker=ticker.upper(),
            latest_price=latest_price,
            change_24h=change_24h,
            change_percent=round(change_percent, 2),
            volume_24h=int(sum(r.volume for r in ohlcv_records[-1:])),
            data_source="database",
            ohlcv=ohlcv_records,
        )
    
    # No data available - return empty with guidance
    return MarketDataResponse(
        ticker=ticker.upper(),
        latest_price=0.0,
        change_24h=0.0,
        change_percent=0.0,
        volume_24h=0,
        data_source="no_data",
        ohlcv=[],
    )


@router.get("/{ticker}/signals")
async def get_signals(
    ticker: str,
    ctx: RequestContext = Depends(get_request_context),
) -> SignalsResponse:
    """
    Get calculated quant signals for a ticker.
    
    Returns technical indicators, regime detection, and composite signal.
    Uses database data if available, otherwise uses sample data.
    
    **Requires Authentication**
    
    This endpoint calculates:
    - **RSI** (14-period)
    - **MACD** (12, 26, 9)
    - **EMA** (20, 50)
    - **Bollinger Bands** (20, 2σ)
    - **ATR** (14-period)
    - **Market Regime** (volatility + trend)
    - **Composite Signal** (weighted score)
    """
    # Try to get data from database
    db_data = await get_prices_from_db(ticker, 100)
    
    if db_data and len(db_data[0]) >= 30:
        prices, highs, lows, _ = db_data
        data_source = "database"
    else:
        # Fall back to sample data
        prices = SAMPLE_PRICES
        highs = None
        lows = None
        data_source = "sample"
    
    # Run technical analysis
    analysis = quant_service.analyze(
        ticker=ticker.upper(),
        prices=prices,
        highs=highs,
        lows=lows,
    )
    
    return SignalsResponse(
        ticker=analysis.ticker,
        timestamp=analysis.timestamp.isoformat(),
        price=analysis.price,
        data_source=data_source,
        rsi=analysis.rsi_14,
        ema_20=analysis.ema_20,
        ema_50=analysis.ema_50,
        macd=MACDValues(
            line=analysis.macd_line,
            signal=analysis.macd_signal,
            histogram=analysis.macd_histogram,
        ),
        bollinger=BollingerBands(
            upper=analysis.bb_upper,
            middle=analysis.bb_middle,
            lower=analysis.bb_lower,
        ),
        atr=analysis.atr_14,
        regime=RegimeInfo(
            volatility=analysis.regime.volatility.value,
            trend=analysis.regime.trend.value,
            volatility_percentile=analysis.regime.volatility_percentile,
            trend_strength=analysis.regime.trend_strength,
        ),
        signal=analysis.composite.signal.value,
        composite_score=analysis.composite.score,
        confidence=analysis.composite.confidence,
        components=analysis.composite.components,
    )


@router.post("/{ticker}/analyze")
async def analyze_prices(
    ticker: str,
    prices: list[float],
    highs: Optional[list[float]] = None,
    lows: Optional[list[float]] = None,
    ctx: RequestContext = Depends(get_request_context),
) -> SignalsResponse:
    """
    Run technical analysis on provided price data.
    
    **Requires Authentication**
    
    Use this endpoint when you have your own price data.
    
    - **prices**: List of closing prices (oldest first)
    - **highs**: Optional list of high prices (for ATR)
    - **lows**: Optional list of low prices (for ATR)
    """
    if len(prices) < 30:
        raise HTTPException(
            status_code=400,
            detail="At least 30 price points required for analysis"
        )
    
    analysis = quant_service.analyze(
        ticker=ticker.upper(),
        prices=prices,
        highs=highs,
        lows=lows,
    )
    
    return SignalsResponse(
        ticker=analysis.ticker,
        timestamp=analysis.timestamp.isoformat(),
        price=analysis.price,
        data_source="provided",
        rsi=analysis.rsi_14,
        ema_20=analysis.ema_20,
        ema_50=analysis.ema_50,
        macd=MACDValues(
            line=analysis.macd_line,
            signal=analysis.macd_signal,
            histogram=analysis.macd_histogram,
        ),
        bollinger=BollingerBands(
            upper=analysis.bb_upper,
            middle=analysis.bb_middle,
            lower=analysis.bb_lower,
        ),
        atr=analysis.atr_14,
        regime=RegimeInfo(
            volatility=analysis.regime.volatility.value,
            trend=analysis.regime.trend.value,
            volatility_percentile=analysis.regime.volatility_percentile,
            trend_strength=analysis.regime.trend_strength,
        ),
        signal=analysis.composite.signal.value,
        composite_score=analysis.composite.score,
        confidence=analysis.composite.confidence,
        components=analysis.composite.components,
    )


@router.post("/{ticker}/ingest")
async def quick_ingest(
    ticker: str,
    source: str = Query("yfinance", description="yfinance or binance"),
    lookback_days: int = Query(30, ge=1, le=365),
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Quick ingest: fetch data and store immediately (synchronous).
    
    For async ingestion, use /feeds/ingest instead.
    """
    try:
        from anchorgrid.engine.ingestion.yfinance_connector import yfinance_connector
        from anchorgrid.engine.ingestion.binance_connector import binance_connector
        from anchorgrid.db.session import timescale_session_maker
        from anchorgrid.services.market_data_service import market_data_service
        
        # Get connector
        if source == "yfinance":
            connector = yfinance_connector
        elif source == "binance":
            connector = binance_connector
        else:
            raise HTTPException(status_code=400, detail=f"Unknown source: {source}")
        
        if connector is None:
            raise HTTPException(status_code=503, detail=f"{source} connector not available")
        
        # Fetch data
        data = connector.fetch_ohlcv(ticker, interval="1d", lookback_days=lookback_days)
        
        if not data:
            return {"status": "no_data", "ticker": ticker, "rows": 0}
        
        # Store in database
        async with timescale_session_maker() as session:
            count = await market_data_service.upsert_ohlcv(session, data)
        
        return {
            "status": "success",
            "ticker": ticker,
            "source": source,
            "rows": count,
        }
        
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Connector not installed: {e}")
