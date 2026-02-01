"""
Risk Manager Agent
==================

Specializes in portfolio risk, position sizing, and trade safety.
"""

from typing import Dict, Optional
from loguru import logger

from anchorgrid.core.llm_router import LLMRouter
from anchorgrid.services.quant_service import QuantService, TechnicalAnalysis
from anchorgrid.services.market_state_manager import market_state_manager
from anchorgrid.db import get_timescale_session


class RiskManager:
    """
    Risk and sizing specialist.
    
    Capabilities:
    - ATR-based position sizing
    - Volatility assessment
    - Stop-loss and Take-profit recommendations
    - Concentration risk awareness
    """
    
    def __init__(self, llm_router: LLMRouter):
        self.llm_router = llm_router
        self.quant_service = QuantService()
    
    async def analyze_risk(
        self,
        symbol: str, 
        query: str,
        portfolio_value: float = 100000,
        risk_per_trade: float = 0.02 # 2% risk
    ) -> str:
        """
        Analyze risk for a potential trade.
        """
        logger.info(f"Risk Manager: Analyzing risk for {symbol}")
        
        try:
            # 1. Fetch Volatility Data (ATR)
            async with get_timescale_session() as session:
                if not market_state_manager._initialized:
                    await market_state_manager.initialize()
                
                asset_class = market_state_manager._infer_asset_class(symbol)
                ohlcv = await market_state_manager.get_market_data(
                    ticker=symbol,
                    asset_class=asset_class,
                    session=session,
                    interval="1d",
                    lookback_days=30
                )
                
            if not ohlcv or len(ohlcv) < 14:
                return f"Insufficient data to calculate risk metrics for {symbol}."
            
            prices = [row["close"] for row in ohlcv]
            highs = [row["high"] for row in ohlcv]
            lows = [row["low"] for row in ohlcv]
            
            analysis: TechnicalAnalysis = self.quant_service.analyze(
                ticker=symbol,
                prices=prices,
                highs=highs,
                lows=lows
            )
            
            atr = analysis.atr_14 or (analysis.price * 0.02) # Fallback to 2% volatility
            current_price = analysis.price
            
            # 2. Math Calculations
            # Risk Amount = Portfolio * Risk %
            risk_amount = portfolio_value * risk_per_trade
            
            # Stop distance = 2x ATR (standard)
            stop_distance = atr * 2
            
            # Shares to buy
            shares = int(risk_amount / stop_distance) if stop_distance > 0 else 0
            position_value = shares * current_price
            
            # 3. Build Context
            risk_context = f"""
Ticker: {symbol}
Current Price: {current_price:.2f}
ATR (14): {atr:.2f}
Portfolio Value: ${portfolio_value:,.2f}
Risk Per Trade (2%): ${risk_amount:,.2f}

Calculated:
- Suggested Shares: {shares}
- Position Value: ${position_value:,.2f}
- Stop Distance: {stop_distance:.2f} (2x ATR)
- Suggested SL: {current_price - stop_distance:.2f}
"""
            
            # 4. Prompt LLM to validate and suggest strategy
            prompt = f"""You are QuantForge's Risk Management expert.
            
=== CALCULATED RISK METRICS ===
{risk_context}

=== USER QUERY ===
{query}

=== INSTRUCTIONS ===
1. Evaluate the risk of this position.
2. If volatility is extreme (ATR > 5% of price), suggest reducing size.
3. Recommend a trailing stop or multi-stage profit take strategy.
4. Issue a Warning if the position size is > 10% of the portfolio.

=== RESPONSE FORMAT ===
**Risk Profile**: [LOW/MEDIUM/HIGH]
**Position Sizing**:
- Shares: [X]
- Value: [$X]
- % of Portfolio: [X]%
**Safety Levels**:
- Stop Loss: [Price]
- Take Profit: [Price]
**Warning**: [Any concerns or "None"]
**Confidence**: [0-100]%
"""
            
            response = await self.llm_router.complete(
                prompt,
                temperature=0.2,
                max_tokens=400
            )
            
            return response

        except Exception as e:
            logger.error(f"RiskManager error for {symbol}: {e}")
            return f"Error calculating risk for {symbol}: Sizing engine unavailable."
