"""
QuantForge AI Engine - Data Feeds Routes

Endpoints for triggering data ingestion and checking job status.
"""
from typing import Optional

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from quantgrid.api.deps import RequestContext, get_request_context
from quantgrid.workers.celery_app import celery_app

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class IngestRequest(BaseModel):
    """Request to trigger data ingestion"""
    ticker: str = Field(..., description="Symbol to ingest (e.g., AAPL, BTCUSDT)")
    sources: list[str] = Field(
        default=["yfinance"],
        description="Data sources to use (yfinance, binance)"
    )
    interval: str = Field(default="1d", description="Candle interval (1m, 5m, 1h, 1d)")
    lookback_days: int = Field(default=30, ge=1, le=365, description="Days of history")


class IngestResponse(BaseModel):
    """Response from ingestion trigger"""
    status: str
    job_ids: list[str]
    ticker: str
    sources: list[str]


class JobStatus(BaseModel):
    """Status of an ingestion job"""
    job_id: str
    status: str  # PENDING, STARTED, SUCCESS, FAILURE, REVOKED
    result: Optional[dict] = None
    error: Optional[str] = None


class DataSource(BaseModel):
    """Data source info"""
    name: str
    status: str
    type: str
    description: Optional[str] = None


# =============================================================================
# Routes
# =============================================================================

@router.post("/ingest", response_model=IngestResponse)
async def trigger_ingestion(
    request: IngestRequest,
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Trigger data ingestion for a ticker.
    
    Queues background jobs to fetch from specified sources.
    Each source creates a separate Celery task.
    """
    from quantgrid.workers.tasks.ingestion_tasks import ingest_ohlcv
    
    job_ids = []
    
    for source in request.sources:
        # Validate source
        valid_sources = [
            "yfinance", "binance", "alpha_vantage", "finnhub", "twelve_data",
            "fmp", "polygon", "newsapi", "coinmarketcap", "coingecko", "fred"
        ]
        if source.lower() not in valid_sources:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown source: {source}. Available: {', '.join(valid_sources)}"
            )
        
        # Queue Celery task
        task = ingest_ohlcv.delay(
            ticker=request.ticker,
            source=source,
            interval=request.interval,
            lookback_days=request.lookback_days,
        )
        job_ids.append(task.id)
    
    return IngestResponse(
        status="queued",
        job_ids=job_ids,
        ticker=request.ticker,
        sources=request.sources,
    )


@router.post("/ingest/batch")
async def trigger_batch_ingestion(
    tickers: list[str],
    source: str = "yfinance",
    interval: str = "1d",
    lookback_days: int = 30,
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Trigger ingestion for multiple tickers at once.
    """
    from quantgrid.workers.tasks.ingestion_tasks import ingest_multiple
    
    task = ingest_multiple.delay(
        tickers=tickers,
        source=source,
        interval=interval,
        lookback_days=lookback_days,
    )
    
    return {
        "status": "queued",
        "job_id": task.id,
        "tickers": tickers,
        "source": source,
    }


@router.get("/sources", response_model=list[DataSource])
async def list_data_sources():
    """List all available data sources and their status"""
    
    # Dynamic availability checking
    def check_available(module_path: str, var_name: str) -> bool:
        try:
            module = __import__(module_path, fromlist=[var_name])
            return getattr(module, var_name, False)
        except ImportError:
            return False
    
    sources = [
        # Equity data
        DataSource(
            name="yfinance",
            status="active" if check_available("backend.engine.ingestion.yfinance_connector", "YFINANCE_AVAILABLE") else "unavailable",
            type="equity",
            description="US equities via Yahoo Finance (FREE, unlimited)"
        ),
        DataSource(
            name="alpha_vantage",
            status="active" if check_available("backend.engine.ingestion.alpha_vantage_connector", "ALPHA_VANTAGE_AVAILABLE") else "no_api_key",
            type="equity",
            description="Stocks/forex with adjusted data (FREE: 500/day)"
        ),
        DataSource(
            name="finnhub",
            status="active" if check_available("backend.engine.ingestion.finnhub_connector", "FINNHUB_AVAILABLE") else "no_api_key",
            type="equity",
            description="Stocks, news, fundamentals (FREE: 60/min)"
        ),
        DataSource(
            name="twelve_data",
            status="active" if check_available("backend.engine.ingestion.twelve_data_connector", "TWELVE_DATA_AVAILABLE") else "no_api_key",
            type="equity",
            description="Multi-asset data (FREE: 800/day)"
        ),
        DataSource(
            name="fmp",
            status="active" if check_available("backend.engine.ingestion.fmp_connector", "FMP_AVAILABLE") else "no_api_key",
            type="equity",
            description="Financial fundamentals (FREE: 250/day)"
        ),
        DataSource(
            name="polygon",
            status="active" if check_available("backend.engine.ingestion.polygon_connector", "POLYGON_AVAILABLE") else "no_api_key",
            type="equity",
            description="Premium market data (Paid)"
        ),
        
        # Crypto data
        DataSource(
            name="binance",
            status="active" if check_available("backend.engine.ingestion.binance_connector", "BINANCE_AVAILABLE") else "unavailable",
            type="crypto",
            description="Cryptocurrency via Binance (FREE, high limits)"
        ),
        DataSource(
            name="coingecko",
            status="active",  # Always available, no key needed
            type="crypto",
            description="Crypto OHLC and prices (FREE, no key)"
        ),
        DataSource(
            name="coinmarketcap",
            status="active" if check_available("backend.engine.ingestion.coinmarketcap_connector", "COINMARKETCAP_AVAILABLE") else "no_api_key",
            type="crypto",
            description="Crypto rankings and quotes (FREE: 333/day)"
        ),
        
        # News
        DataSource(
            name="newsapi",
            status="active" if check_available("backend.engine.ingestion.newsapi_connector", "NEWSAPI_AVAILABLE") else "no_api_key",
            type="news",
            description="News headlines from 80k sources (FREE: 100/day)"
        ),
        
        # Macro
        DataSource(
            name="fred",
            status="active" if check_available("backend.engine.ingestion.fred_connector", "FRED_AVAILABLE") else "no_api_key",
            type="macro",
            description="Federal Reserve economic data (FREE with key)"
        ),
    ]
    
    return sources


@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_ingestion_status(job_id: str):
    """Get status of an ingestion job"""
    result = AsyncResult(job_id, app=celery_app)
    
    response = JobStatus(
        job_id=job_id,
        status=result.status,
    )
    
    if result.successful():
        response.result = result.result
    elif result.failed():
        response.error = str(result.result) if result.result else "Unknown error"
    
    return response


@router.delete("/jobs/{job_id}")
async def cancel_ingestion_job(
    job_id: str,
    ctx: RequestContext = Depends(get_request_context),
):
    """Cancel a pending or running ingestion job"""
    result = AsyncResult(job_id, app=celery_app)
    result.revoke(terminate=True)
    
    return {"status": "cancelled", "job_id": job_id}
