"""
Finance Plugin Agent - The Financial Analyst

Combines:
- Universal Reasoning (Engine) - The "Brain"
- Financial Tools (Connectors) - The "Hands"
- Technical Analysis (Extractors) - The "Eyes"

This is Plugin #1 demonstrating how domain-specific logic
works with the universal infrastructure.
"""

import numpy as np
from typing import Dict, Any, Optional
from loguru import logger
from datetime import datetime

# Import the Universal Brain
from anchorgrid.core.engine import engine

# Import the Domain-Specific Tools  
from anchorgrid.plugins.finance.connectors.yahoo_scraper import yfinance_scraper
from anchorgrid.plugins.finance.extractors.indicators import rsi


class FinanceAgent:
    """
    Plugin #1: The Financial Analyst
    
    Demonstrates the Universal Protocol pattern:
    1. Gather Data (Connectors) - Domain-specific 
    2. Extract Features (Extractors) - Domain-specific
    3. Reason (Engine) - Universal
    """
    
    def __init__(self):
        """Initialize the Finance Agent"""
        self.domain = "finance"
        logger.info(f"💼 Finance Plugin initialized (Domain: {self.domain})")
    
    def analyze_stock(self, ticker: str) -> None:
        """
        Analyze a stock using real-time data + local AI reasoning.
        
        Workflow:
        1. Fetch live data from Yahoo Finance (zero cost)
        2. Calculate technical indicators (RSI, trend)
        3. Send to Universal Engine for reasoning
        4. Stream response token-by-token
        
        Args:
            ticker: Stock symbol (e.g., 'AAPL', 'TSLA')
        """
        logger.info(f"🔎 Finance Plugin activated for: {ticker.upper()}")
        print(f"\n📡 Fetching live data for {ticker.upper()}...")
        
        try:
            # ================================================================
            # Step 1: Gather Data (The "Hands")
            # ================================================================
            
            quote = yfinance_scraper.get_quote(ticker)
            
            if not quote or 'price' not in quote:
                print(f"❌ Error: Could not fetch data for {ticker}")
                print("💡 Tip: Check the ticker symbol or your internet connection")
                return
            
            price = float(quote.get('price', 0))
            change = float(quote.get('change_percent', 0))
            volume = quote.get('volume', 'N/A')
            market_cap = quote.get('market_cap', 'N/A')
            
            # ================================================================
            # Step 2: Extract Features (The "Eyes")
            # ================================================================
            
            print(f"📊 Calculating technical indicators...")
            
            # Get historical data for RSI calculation
            history = yfinance_scraper.get_historical(ticker, period="3mo")
            
            # Default neutral RSI if calculation fails
            rsi_val = 50.0
            signal = "NEUTRAL"
            
            if history is not None and len(history) > 14:
                try:
                    # Extract closing prices
                    closes = history['Close'].values
                    
                    # Convert to numpy array (type safety)
                    closes = np.array(closes, dtype=float)
                    
                    # Calculate RSI
                    rsi_series = rsi(closes, period=14)
                    
                    # Safe extraction of last value
                    if len(rsi_series) > 0:
                        last_val = rsi_series[-1]
                        
                        # Check for NaN (division by zero or insufficient data)
                        if not np.isnan(last_val):
                            rsi_val = float(last_val)
                            
                            # Determine trend signal
                            if rsi_val > 70:
                                signal = "OVERBOUGHT (Sell Risk)"
                            elif rsi_val < 30:
                                signal = "OVERSOLD (Buy Opportunity)"
                            else:
                                signal = "NEUTRAL"
                        else:
                            logger.warning(f"RSI returned NaN for {ticker} - using neutral default")
                    
                except Exception as e:
                    logger.warning(f"RSI calculation failed: {e} - using neutral default")
            else:
                logger.warning(f"Insufficient historical data for {ticker} - using neutral RSI")
            
            # ================================================================
            # Step 3: Build Context (The "Short-term Memory")
            # ================================================================
            
            context_data = f"""
ASSET: {ticker.upper()}
CURRENT_PRICE: ${price:.2f}
CHANGE_TODAY: {change:+.2f}%
VOLUME: {volume}
MARKET_CAP: {market_cap}

TECHNICAL_ANALYSIS:
- RSI (14-day): {rsi_val:.1f}
- Signal: {signal}

DATA_SOURCE: Yahoo Finance (Live Data)
TIMESTAMP: {datetime.now().isoformat()}
            """.strip()
            
            # ================================================================
            # Step 4: Reason (The "Brain")
            # ================================================================
            
            print("\n💭 Thinking... (Streaming from Local Llama3)\n")
            print("─" * 60)
            
            # The Engine doesn't know it's analyzing a stock
            # It just sees data and reasons about it
            
            prompt = (
                f"Act as a senior Wall Street quantitative analyst. "
                f"Review this data for {ticker.upper()} and provide:\n"
                "1. Quick Summary (2-3 sentences)\n"
                "2. Key Observations from the data\n"
                "3. Risk Assessment\n"
                "4. Clear Recommendation (Buy/Hold/Sell) with justification\n\n"
                "Base your analysis ONLY on the data provided. Be specific and cite numbers."
            )
            
            response = engine.think(
                prompt=prompt,
                context=context_data,
                domain=self.domain
            )
            
            print("\n" + "─" * 60)
            
        except Exception as e:
            error_msg = f"❌ Finance Plugin Error: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            
            # Print full traceback for debugging
            import traceback
            traceback.print_exc()
    
    def get_capabilities(self) -> Dict[str, str]:
        """Return plugin capabilities"""
        return {
            "domain": "finance",
            "connectors": "Yahoo Finance, SEC EDGAR, FRED",
            "extractors": "RSI, MACD, Bollinger Bands, ATR",
            "engine": "Universal LLM (Ollama)",
            "cost": "Zero (all data sources free)"
        }


# ============================================================================
# Export the Agent (Singleton)
# ============================================================================

finance_agent = FinanceAgent()
