"""
QuantForge AI Engine - RAG Service

Retrieval-Augmented Generation service for the AI assistant.
Combines vector search with market data to provide grounded answers.
"""
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from loguru import logger

from anchorgrid.engine.memory.weaviate_store import (
    weaviate_store,
    VectorDocument,
    SearchResult,
)
from anchorgrid.services.embedding_service import embedding_service


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class RAGContext:
    """Context retrieved for RAG injection"""
    query: str
    ticker: str
    documents: list[SearchResult]
    formatted_context: str
    total_tokens_estimate: int
    timestamp: datetime


# =============================================================================
# RAG SERVICE
# =============================================================================

class RAGService:
    """
    RAG (Retrieval-Augmented Generation) service.
    
    Retrieves relevant context from Weaviate to inject into LLM prompts.
    This provides the AI with factual, grounded information.
    
    Flow:
    1. User asks: "Why did NVDA drop yesterday?"
    2. Embed the question
    3. Search Weaviate for relevant docs (news, price data, analysis)
    4. Format context for LLM injection
    5. Return structured context
    """
    
    def __init__(self):
        self.store = weaviate_store
        self.embedder = embedding_service
        self._initialized = False
    
    async def initialize(self):
        """Initialize the RAG service"""
        if self._initialized:
            return
        
        await self.store.initialize()
        self._initialized = True
        logger.info("RAG Service initialized")
    
    # -------------------------------------------------------------------------
    # CONTEXT RETRIEVAL
    # -------------------------------------------------------------------------
    
    async def get_context(
        self,
        query: str,
        ticker: str = None,
        content_types: list[str] = None,
        tenant_id: str = "default",
        top_k: int = 5,
        max_tokens: int = 2000,
    ) -> RAGContext:
        """
        Retrieve relevant context for a user query.
        
        Args:
            query: User's question
            ticker: Filter by specific ticker (optional)
            content_types: Filter by content types (optional)
            tenant_id: Tenant ID for multi-tenancy
            top_k: Number of documents to retrieve
            max_tokens: Maximum tokens for context (for LLM limit)
            
        Returns:
            RAGContext with formatted context for LLM injection
        """
        if not self._initialized:
            await self.initialize()
        
        # Embed the query
        query_vector = await self.embedder.embed(query)
        
        # Search for relevant documents
        results = await self.store.search(
            query_vector=query_vector,
            ticker=ticker,
            content_type=content_types[0] if content_types and len(content_types) == 1 else None,
            tenant_id=tenant_id,
            top_k=top_k,
        )
        
        # Filter by multiple content types if needed
        if content_types and len(content_types) > 1:
            results = [r for r in results if r.content_type in content_types]
        
        # Format context for LLM
        formatted, token_count = self._format_context(results, max_tokens)
        
        return RAGContext(
            query=query,
            ticker=ticker or "any",
            documents=results,
            formatted_context=formatted,
            total_tokens_estimate=token_count,
            timestamp=datetime.now(),
        )
    
    def _format_context(
        self,
        results: list[SearchResult],
        max_tokens: int,
    ) -> tuple[str, int]:
        """Format search results into LLM-injectable context"""
        if not results:
            return "No relevant information found in the database.", 10
        
        lines = ["### Relevant Information:"]
        token_count = 5  # Approximate for header
        
        for i, doc in enumerate(results, 1):
            # Format each document
            doc_text = f"\n**[{doc.content_type.upper()}]** ({doc.ticker}, {doc.source})\n"
            doc_text += f"*{doc.timestamp.strftime('%Y-%m-%d %H:%M')}*\n"
            doc_text += f"{doc.content}\n"
            
            # Estimate tokens (rough: 4 chars per token)
            doc_tokens = len(doc_text) // 4
            
            if token_count + doc_tokens > max_tokens:
                lines.append("\n*(Additional context truncated for length)*")
                break
            
            lines.append(doc_text)
            token_count += doc_tokens
        
        return "\n".join(lines), token_count
    
    # -------------------------------------------------------------------------
    # DOCUMENT INDEXING
    # -------------------------------------------------------------------------
    
    async def index_document(
        self,
        content: str,
        ticker: str,
        content_type: str,
        source: str,
        tenant_id: str = "default",
        timestamp: datetime = None,
    ) -> str:
        """
        Index a new document for RAG retrieval.
        
        Args:
            content: Text content to index
            ticker: Stock/crypto symbol
            content_type: "news", "analysis", "price_summary", "fundamental"
            source: Source of the content
            tenant_id: Tenant ID
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            UUID of the indexed document
        """
        if not self._initialized:
            await self.initialize()
        
        # Create document
        doc = VectorDocument(
            content=content,
            ticker=ticker,
            content_type=content_type,
            source=source,
            timestamp=timestamp or datetime.now(),
            tenant_id=tenant_id,
        )
        
        # Generate embedding
        vector = await self.embedder.embed(content)
        
        # Store in Weaviate
        uuid = await self.store.upsert(doc, vector)
        
        logger.info(f"Indexed {content_type} for {ticker}: {uuid[:8]}...")
        return uuid
    
    async def index_price_summary(
        self,
        ticker: str,
        price: float,
        change_pct: float,
        volume: int,
        signals: dict = None,
        tenant_id: str = "default",
    ) -> str:
        """
        Index a price summary for RAG.
        
        Creates a natural language summary of price action.
        """
        # Generate summary text
        direction = "up" if change_pct >= 0 else "down"
        summary = f"{ticker} closed at ${price:.2f}, {direction} {abs(change_pct):.2f}% on volume of {volume:,}."
        
        if signals:
            if signals.get("rsi"):
                rsi = signals["rsi"]
                rsi_status = "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral"
                summary += f" RSI is {rsi:.1f} ({rsi_status})."
            
            if signals.get("regime"):
                summary += f" Market regime: {signals['regime']}."
            
            if signals.get("signal"):
                summary += f" Signal: {signals['signal']}."
        
        return await self.index_document(
            content=summary,
            ticker=ticker,
            content_type="price_summary",
            source="quantforge",
            tenant_id=tenant_id,
        )
    
    async def index_news(
        self,
        ticker: str,
        title: str,
        summary: str,
        source: str,
        published_at: datetime,
        tenant_id: str = "default",
    ) -> str:
        """Index a news article for RAG"""
        content = f"{title}\n\n{summary}"
        
        return await self.index_document(
            content=content,
            ticker=ticker,
            content_type="news",
            source=source,
            timestamp=published_at,
            tenant_id=tenant_id,
        )
    
    async def index_analysis(
        self,
        ticker: str,
        analysis: str,
        tenant_id: str = "default",
    ) -> str:
        """Index an AI-generated analysis for RAG"""
        return await self.index_document(
            content=analysis,
            ticker=ticker,
            content_type="analysis",
            source="quantforge_ai",
            tenant_id=tenant_id,
        )
    
    # -------------------------------------------------------------------------
    # LIFECYCLE
    # -------------------------------------------------------------------------
    
    async def clear_old_documents(
        self,
        ticker: str = None,
        older_than_days: int = 30,
        tenant_id: str = "default",
    ) -> int:
        """Clear documents older than specified days"""
        # For now, just clear by ticker
        # TODO: Add time-based filtering in Weaviate queries
        if ticker:
            return await self.store.delete_by_ticker(ticker, tenant_id)
        return 0


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

rag_service = RAGService()
