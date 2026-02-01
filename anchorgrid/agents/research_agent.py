"""
Research Agent
==============

Specializes in fundamental analysis using SEC filings and news.
"""

from typing import Dict, List, Optional
from loguru import logger

from anchorgrid.core.llm_router import LLMRouter
from anchorgrid.services.rag_service import RAGService
from anchorgrid.plugins.finance.connectors.sec_scraper import sec_scraper
from anchorgrid.plugins.finance.connectors.news_rss import news_rss_scraper
from anchorgrid.core.zon_engine import ZONEngine


class ResearchAgent:
    """
    Fundamental analysis specialist.
    
    Capabilities:
    - Analyze SEC filings (10-K, 10-Q, 8-K)
    - Extract earnings insights
    - Assess news sentiment
    - Identify catalysts and risks
    - Utilize RAG for historical memory
    """
    
    def __init__(self, llm_router: LLMRouter):
        self.llm_router = llm_router
        self.rag_service = RAGService()
        self.sec_scraper = sec_scraper
        self.news_scraper = news_rss_scraper
        self.zon_engine = ZONEngine()
    
    async def research(self, symbol: str, query: str) -> str:
        """
        Perform fundamental research for a symbol.
        """
        logger.info(f"Research Agent: Researching {symbol}")
        
        try:
            # 1. Fetch Data in Parallel
            import asyncio
            
            # Use RAG for historical context
            rag_task = self.rag_service.search(
                query=f"{symbol} fundamentals earnings",
                limit=3
            )
            
            # Fetch recent SEC filings
            sec_task = self.sec_scraper.get_recent_filings(symbol, count=3)
            
            # Fetch recent news
            news_task = self.news_scraper.search_ticker_news(symbol, limit=8)
            
            rag_results, sec_filings, news_articles = await asyncio.gather(
                rag_task, sec_task, news_task, return_exceptions=True
            )
            
            # 2. Build Context (Compressed with ZON where possible)
            context_parts = []
            
            # RAG Results
            if not isinstance(rag_results, Exception) and rag_results:
                context_parts.append("=== HISTORICAL CONTEXT (RAG) ===")
                for i, res in enumerate(rag_results, 1):
                    content = res.get("content", "")[:300]
                    context_parts.append(f"{i}. {content}...")
            
            # SEC Filings
            if not isinstance(sec_filings, Exception) and sec_filings:
                context_parts.append("\n=== RECENT SEC FILINGS ===")
                # Group for ZON
                filing_list = [
                    {"type": f["form_type"], "date": f["filing_date"]} 
                    for f in sec_filings
                ]
                context_parts.append(self.zon_engine.encode(filing_list))
            
            # News Articles
            if not isinstance(news_articles, Exception) and news_articles:
                context_parts.append("\n=== RECENT NEWS ===")
                news_list = [
                    {"title": n["title"], "src": n["source"]} 
                    for n in news_articles[:5]
                ]
                context_parts.append(self.zon_engine.encode(news_list))
                
            context = "\n".join(context_parts)
            
            # 3. Build Prompt
            prompt = f"""You are QuantForge's Fundamental Research expert.
            
**CRITICAL**: Only use the context provided below. Do not invent financial facts.

{context}

=== USER QUERY ===
{query} (Symbol: {symbol})

=== INSTRUCTIONS ===
1. Summarize the bull and bear cases.
2. Identify upcoming catalysts or recent earnings hits/misses.
3. Assess overall news sentiment.
4. Provide a high-level Investment Thesis.

=== RESPONSE FORMAT ===
**Thesis**: [BULLISH/BEARISH/NEUTRAL]
**Key Drivers**:
- [Driver 1]
- [Driver 2]
**Catalysts**:
- [Catalyst 1]
**Risks**:
- [Risk 1]
**Sentiment**: [Summary %]
**Confidence**: [0-100]%
"""
            
            # 4. Call LLM
            response = await self.llm_router.complete(
                prompt,
                temperature=0.3,
                max_tokens=600
            )
            
            return response

        except Exception as e:
            logger.error(f"ResearchAgent error for {symbol}: {e}")
            return f"Error researching {symbol}: Fundamental analysis engine failed to aggregate data."
