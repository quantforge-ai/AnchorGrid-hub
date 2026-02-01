"""
QuantForge Orchestrator Agent
==============================

Central coordinator that routes queries to specialist agents and manages
conversation context.
"""

import re
import asyncio
from typing import List, Dict, Optional
from datetime import datetime

from anchorgrid.agents.market_analyst import MarketAnalyst
from anchorgrid.agents.research_agent import ResearchAgent
from anchorgrid.agents.risk_manager import RiskManager
from anchorgrid.agents.context_manager import ConversationContext
from anchorgrid.core.llm_router import LLMRouter
from anchorgrid.core.zon_engine import ZONEngine
from loguru import logger


class Orchestrator:
    """
    Master coordinator for multi-agent system.
    
    Responsibilities:
    - Query classification and routing
    - Agent coordination
    - Conversation context management
    - Response aggregation
    """
    
    def __init__(self, llm_router: LLMRouter):
        self.llm_router = llm_router
        self.zon_engine = ZONEngine()
        
        # Initialize specialist agents
        self.market_analyst = MarketAnalyst(llm_router)
        self.research_agent = ResearchAgent(llm_router)
        self.risk_manager = RiskManager(llm_router)
        
        # Conversation contexts (user_id → context)
        self.contexts: Dict[str, ConversationContext] = {}
        
        # Query classification patterns
        self.patterns = {
            "market_analysis": [
                r"analyze",
                r"technical",
                r"indicators?",
                r"chart",
                r"price action",
                r"RSI",
                r"MACD",
                r"moving average",
            ],
            "research": [
                r"research",
                r"fundamental",
                r"earnings",
                r"10-K",
                r"10-Q",
                r"SEC",
                r"news",
                r"sentiment",
            ],
            "risk": [
                r"risk",
                r"position siz(e|ing)",
                r"portfolio",
                r"allocation",
                r"exposure",
                r"stop loss",
            ],
            # comparisons usually trigger both research and analysis
            "comparison": [
                r"compare",
                r"vs\.?",
                r"versus",
                r"better",
                r"or",
            ],
        }
    
    def get_or_create_context(self, user_id: str) -> ConversationContext:
        """Get existing context or create new one"""
        if user_id not in self.contexts:
            self.contexts[user_id] = ConversationContext()
        return self.contexts[user_id]
    
    def classify_query(self, query: str) -> List[str]:
        """
        Classify query to determine which agents to invoke.
        """
        query_lower = query.lower()
        agents = []
        
        for agent_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    if agent_type == "comparison":
                        agents.extend(["market_analysis", "research"])
                    else:
                        agents.append(agent_type)
                    break
        
        # Default to market analysis if no match
        if not agents:
            agents = ["market_analysis"]
        
        return list(set(agents)) # Unique list
    
    def extract_symbols(self, query: str) -> List[str]:
        """Extract ticker symbols from query"""
        # Match 1-5 uppercase letters
        pattern = r'\b[A-Z]{1,5}(?:\.[A-Z]{1,3})?\b'
        symbols = re.findall(pattern, query)
        
        # Filter out common words
        stopwords = {"I", "A", "US", "AM", "PM", "CEO", "CFO", "USD", "INR"}
        symbols = [s for s in symbols if s not in stopwords]
        
        return symbols
    
    async def handle_query(
        self,
        user_id: str,
        query: str,
        include_reasoning: bool = False
    ) -> Dict:
        """Main entry point for query processing"""
        start_time = datetime.now()
        
        # 1. Get/Update Context
        ctx = self.get_or_create_context(user_id)
        symbols = self.extract_symbols(query)
        if not symbols:
            # Fallback to last discussed symbol
            last_sym = ctx.get_last_symbol()
            if last_sym:
                symbols = [last_sym]
        
        if not symbols:
            return {
                "status": "error",
                "message": "Please specify a stock symbol (e.g., AAPL).",
                "query": query
            }
            
        # Update context tracker
        for sym in symbols:
            ctx.symbols_mentioned.add(sym)
        
        # 2. Classify Query
        agent_types = self.classify_query(query)
        logger.info(f"Orchestrator: Routing {query} to {agent_types} for {symbols}")
        
        # 3. Build context-aware prompt
        context_str = ctx.get_context_for_llm()
        enhanced_query = f"{context_str}\n\nCurrent query: {query}"
        
        # 4. Invoke Agents in Parallel
        tasks = []
        if "market_analysis" in agent_types:
            tasks.append(self._invoke_market_analyst(symbols, enhanced_query))
        if "research" in agent_types:
            tasks.append(self._invoke_research_agent(symbols, enhanced_query))
        if "risk" in agent_types:
            tasks.append(self._invoke_risk_manager(symbols, enhanced_query))
        
        agent_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter valid results
        valid_results = []
        for res in agent_results:
            if isinstance(res, Exception):
                logger.error(f"Agent execution error: {res}")
            else:
                valid_results.append(res)
        
        if not valid_results:
            return {"status": "error", "message": "All agents failed.", "query": query}
        
        # 5. Aggregate Findings
        aggregated = await self._aggregate_findings(query, symbols, valid_results)
        
        # Update history
        ctx.add_turn(query, aggregated["summary"])
        ctx.last_analysis = aggregated
        
        return {
            "status": "success",
            "query": query,
            "symbols": symbols,
            "agent_types": agent_types,
            "summary": aggregated["summary"],
            "signals": aggregated.get("signals", {}),
            "execution_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
            "timestamp": datetime.now().isoformat(),
            **({"reasoning": valid_results} if include_reasoning else {})
        }

    async def _invoke_market_analyst(self, symbols: List[str], query: str) -> Dict:
        # Use first symbol for specific analysis for now
        res = await self.market_analyst.analyze(symbols[0], query)
        return {"agent": "market_analyst", "result": res}

    async def _invoke_research_agent(self, symbols: List[str], query: str) -> Dict:
        res = await self.research_agent.research(symbols[0], query)
        return {"agent": "research_agent", "result": res}

    async def _invoke_risk_manager(self, symbols: List[str], query: str) -> Dict:
        res = await self.risk_manager.analyze_risk(symbols[0], query)
        return {"agent": "risk_manager", "result": res}

    async def _aggregate_findings(
        self, query: str, symbols: List[str], agent_results: List[Dict]
    ) -> Dict:
        """Synthesize findings into a consensus report"""
        findings = []
        for r in agent_results:
            findings.append(f"**{r['agent']}**:\n{r['result']}")
        
        prompt = f"""You are QuantForge AI's consensus builder.
User asked: "{query}" for {', '.join(symbols)}

Agent findings:
{chr(10).join(findings)}

Instructions:
1. Synthesize into a coherent summary.
2. Identify consensus signal (BUY/SELL/HOLD).
3. Provide final recommendation.

Format:
SUMMARY: [2-3 sentences]
SIGNAL: [BUY/SELL/HOLD]
CONFIDENCE: [0-100]%
REASONING: [Key points]
"""
        try:
            synthesis = await self.llm_router.complete(prompt, temperature=0.3)
            
            # Simple parsing
            signal_match = re.search(r'SIGNAL:\s*(\w+)', synthesis)
            conf_match = re.search(r'CONFIDENCE:\s*(\d+)', synthesis)
            
            return {
                "summary": synthesis,
                "signals": {
                    "action": signal_match.group(1) if signal_match else "HOLD",
                    "confidence": int(conf_match.group(1)) if conf_match else 50,
                }
            }
        except Exception as e:
            logger.error(f"Aggregation failed: {e}")
            return {
                "summary": "\n\n".join(findings),
                "signals": {"action": "HOLD", "confidence": 50}
            }
