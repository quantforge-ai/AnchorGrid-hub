"""
Market Analyst Agent
====================

Specializes in technical analysis using quantitative indicators.
"""

import re
from typing import Dict, List, Optional
from loguru import logger

from anchorgrid.core.llm_router import LLMRouter
from anchorgrid.services.quant_service import QuantService, TechnicalAnalysis
from anchorgrid.services.quote_service import QuoteService
from anchorgrid.services.market_state_manager import market_state_manager, AssetClass
from anchorgrid.core.zon_engine import ZONEngine
from anchorgrid.db import get_timescale_session


class MarketAnalyst:
    """
    Technical analysis specialist.
    
    Capabilities:
    - Interpret RSI, MACD, Bollinger Bands
    - Identify support/resistance levels
    - Detect regime changes (trend/range/volatile)
    - Generate high-conviction signals with grounding
    """
    
    def __init__(self, llm_router: LLMRouter):
        self.llm_router = llm_router
        self.quant_service = QuantService()
        self.quote_service = QuoteService()
        self.zon_engine = ZONEngine()
    
    async def analyze(self, symbol: str, query: str) -> str:
        """
        Perform technical analysis for a symbol.
        """
        logger.info(f"Market Analyst: Analyzing {symbol}")
        
        # 1. Fetch data
        try:
            # Get real-time quote
            quote = await self.quote_service.get_quote_async(symbol)
            if not quote:
                return f"Unable to fetch real-time data for {symbol}."
            
            # Get historical data for indicators
            async with get_timescale_session() as session:
                if not market_state_manager._initialized:
                    await market_state_manager.initialize()
                
                asset_class = market_state_manager._infer_asset_class(symbol)
                ohlcv = await market_state_manager.get_market_data(
                    ticker=symbol,
                    asset_class=asset_class,
                    session=session,
                    interval="1d",
                    lookback_days=100
                )
            
            if not ohlcv or len(ohlcv) < 30:
                return f"Insufficient historical data for {symbol} to run technical analysis."
            
            # 2. Run Technical Analysis
            prices = [row["close"] for row in ohlcv]
            highs = [row["high"] for row in ohlcv]
            lows = [row["low"] for row in ohlcv]
            
            analysis: TechnicalAnalysis = self.quant_service.analyze(
                ticker=symbol,
                prices=prices,
                highs=highs,
                lows=lows
            )
            
            # 3. Convert to ZON for token efficiency
            zon_quote = self.zon_engine.encode_quote(quote)
            
            # Extract keys for signals to keep it compact
            signals_data = {
                "rsi": round(analysis.rsi_14, 2) if analysis.rsi_14 else None,
                "macd": {
                    "line": round(analysis.macd_line, 4) if analysis.macd_line else None,
                    "hist": round(analysis.macd_histogram, 4) if analysis.macd_histogram else None
                },
                "ema_20": round(analysis.ema_20, 2) if analysis.ema_20 else None,
                "ema_50": round(analysis.ema_50, 2) if analysis.ema_50 else None,
                "bb_pos": round(analysis.composite.components.get("bollinger_position", 0), 2),
                "regime": analysis.regime.trend.value
            }
            zon_signals = self.zon_engine.encode(signals_data)
            
            # 4. Build Prompt
            prompt = f"""You are QuantForge's Technical Analysis expert.
            
**CRITICAL**: Only use the data provided below. Do not use internal knowledge for prices.

=== MARKET DATA (ZON) ===
Quote: {zon_quote}
Signals: {zon_signals}

=== USER QUERY ===
{query}

=== INSTRUCTIONS ===
1. Interpret RSI, MACD, and EMA crossover.
2. Identify the current market regime.
3. Provide a clear BUY/SELL/HOLD signal.
4. Suggest precise Entry, Stop Loss, and Target levels based on the data.

=== RESPONSE FORMAT ===
**Signal**: [BUY/SELL/HOLD]
**Reasoning**: [1-2 sentences]
**Levels**:
- Entry: [Price]
- SL: [Price]
- TP: [Price]
**Confidence**: [0-100]%
"""
            
            # 5. Call LLM
            response = await self.llm_router.complete(
                prompt, 
                temperature=0.2, # Low temperature for factual analysis
                max_tokens=400
            )
            
            # 6. Audit: Simple price grounding check
            if not self._verify_price_grounding(response, quote["price"]):
                logger.warning(f"MarketAnalyst: Potential hallucination in response for {symbol}")
                response += "\n\n⚠️ *Note: Suggested levels are based on technical projections and should be verified manually.*"
            
            return response

        except Exception as e:
            logger.error(f"MarketAnalyst error for {symbol}: {e}")
            return f"Error analyzing {symbol}: Technical analysis engine encountered an issue."

    def _verify_price_grounding(self, response: str, actual_price: float) -> bool:
        """Simple check to see if suggested prices are within a sane range of current price"""
        # Extract numbers followed by optional decimals
        prices = re.findall(r'\b\d+(?:\.\d+)?\b', response)
        for p_str in prices:
            try:
                p = float(p_str)
                # If a number is wildly off (e.g. 10x current price), it might be a hallucination
                # unless the current price is very small.
                if actual_price > 1 and (p > actual_price * 5 or p < actual_price * 0.1):
                    return False
            except ValueError:
                continue
        return True
