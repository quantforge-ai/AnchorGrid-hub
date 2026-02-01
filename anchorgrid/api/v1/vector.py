"""
QuantForge AI Engine - Vector Store Routes

Endpoints for semantic memory and RAG operations.
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from anchorgrid.api.deps import RequestContext, get_request_context


router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class DocumentIngest(BaseModel):
    """Single document to ingest"""
    content: str
    ticker: Optional[str] = None
    source: str = "manual"
    content_type: str = "general"  # "news" | "analysis" | "price_summary" | "fundamental"


class DocumentBatchIngest(BaseModel):
    """Batch of documents to ingest"""
    documents: list[DocumentIngest]


class SearchQuery(BaseModel):
    """Semantic search query"""
    query: str
    ticker: Optional[str] = None
    content_type: Optional[str] = None
    top_k: int = 5


class SearchResultItem(BaseModel):
    """Single search result"""
    content: str
    ticker: str
    content_type: str
    source: str
    timestamp: str
    score: float


class RAGContextResponse(BaseModel):
    """RAG context for LLM injection"""
    query: str
    ticker: str
    document_count: int
    formatted_context: str
    token_estimate: int


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/ingest")
async def ingest_documents(
    request: DocumentBatchIngest,
    ctx: RequestContext = Depends(get_request_context),
) -> dict:
    """
    Batch ingest documents into vector store.
    
    Documents are embedded and stored with tenant isolation.
    
    **Requires Authentication**
    """
    from anchorgrid.services.rag_service import rag_service
    
    tenant_id = str(ctx.tenant_id) if ctx.tenant_id else "default"
    indexed = []
    
    for doc in request.documents:
        try:
            uuid = await rag_service.index_document(
                content=doc.content,
                ticker=doc.ticker or "GENERAL",
                content_type=doc.content_type,
                source=doc.source,
                tenant_id=tenant_id,
            )
            indexed.append({"ticker": doc.ticker, "uuid": uuid[:8]})
        except Exception as e:
            indexed.append({"ticker": doc.ticker, "error": str(e)})
    
    return {
        "status": "completed",
        "count": len(indexed),
        "tenant_id": tenant_id,
        "results": indexed,
    }


@router.post("/search", response_model=list[SearchResultItem])
async def search_vectors(
    request: SearchQuery,
    ctx: RequestContext = Depends(get_request_context),
) -> list[SearchResultItem]:
    """
    Semantic search in vector store.
    
    Returns top-k results filtered by ticker and content type.
    
    **Requires Authentication**
    """
    from anchorgrid.services.rag_service import rag_service
    
    tenant_id = str(ctx.tenant_id) if ctx.tenant_id else "default"
    
    context = await rag_service.get_context(
        query=request.query,
        ticker=request.ticker,
        content_types=[request.content_type] if request.content_type else None,
        tenant_id=tenant_id,
        top_k=request.top_k,
    )
    
    return [
        SearchResultItem(
            content=doc.content,
            ticker=doc.ticker,
            content_type=doc.content_type,
            source=doc.source,
            timestamp=doc.timestamp.isoformat(),
            score=doc.score,
        )
        for doc in context.documents
    ]


@router.get("/context/{ticker}", response_model=RAGContextResponse)
async def get_rag_context(
    ticker: str,
    query: str = Query(..., description="User question about the ticker"),
    top_k: int = Query(5, le=20),
    ctx: RequestContext = Depends(get_request_context),
) -> RAGContextResponse:
    """
    Get RAG context for LLM prompt injection.
    
    Returns formatted context ready to inject into LLM prompt.
    
    **Requires Authentication**
    
    Example:
    ```
    GET /vector/context/AAPL?query=Why did Apple drop?&top_k=5
    ```
    """
    from anchorgrid.services.rag_service import rag_service
    
    tenant_id = str(ctx.tenant_id) if ctx.tenant_id else "default"
    
    context = await rag_service.get_context(
        query=query,
        ticker=ticker,
        tenant_id=tenant_id,
        top_k=top_k,
    )
    
    return RAGContextResponse(
        query=context.query,
        ticker=context.ticker,
        document_count=len(context.documents),
        formatted_context=context.formatted_context,
        token_estimate=context.total_tokens_estimate,
    )


@router.post("/index-price")
async def index_price_summary(
    ticker: str,
    price: float,
    change_pct: float,
    volume: int,
    rsi: Optional[float] = None,
    regime: Optional[str] = None,
    signal: Optional[str] = None,
    ctx: RequestContext = Depends(get_request_context),
) -> dict:
    """
    Index a price summary for RAG.
    
    Creates a natural language summary of price action.
    Called automatically after market data ingestion.
    
    **Requires Authentication**
    """
    from anchorgrid.services.rag_service import rag_service
    
    tenant_id = str(ctx.tenant_id) if ctx.tenant_id else "default"
    
    signals = {}
    if rsi is not None:
        signals["rsi"] = rsi
    if regime:
        signals["regime"] = regime
    if signal:
        signals["signal"] = signal
    
    uuid = await rag_service.index_price_summary(
        ticker=ticker,
        price=price,
        change_pct=change_pct,
        volume=volume,
        signals=signals,
        tenant_id=tenant_id,
    )
    
    return {"status": "indexed", "ticker": ticker, "uuid": uuid[:8]}


@router.delete("/{ticker}")
async def delete_ticker_documents(
    ticker: str,
    ctx: RequestContext = Depends(get_request_context),
) -> dict:
    """
    Delete all documents for a ticker.
    
    **Requires Authentication**
    """
    from anchorgrid.engine.memory.weaviate_store import weaviate_store
    
    tenant_id = str(ctx.tenant_id) if ctx.tenant_id else "default"
    
    count = await weaviate_store.delete_by_ticker(ticker, tenant_id)
    
    return {"status": "deleted", "ticker": ticker, "count": count}

