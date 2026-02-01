"""
AnchorGrid FastAPI Server - Main Entry Point

Simple server for testing AnchorGrid-Core components.
Provides REST API endpoints for scrapers, indicators, and Hub.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn

app = FastAPI(
    title="AnchorGrid Core API",
    description="Zero-cost financial data infrastructure with federated learning",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AnchorGrid Core API",
        "version": "1.0.0",
        "features": {
            "scrapers": "9 zero-cost data sources",
            "indicators": "RSI, MACD, Bollinger Bands, etc.",
            "hub": "Federated learning infrastructure",
            "cli": "anchorgrid login/push/status"
        }
    }


@app.get("/api/quote/{symbol}")
async def get_quote(symbol: str):
    """
    Get real-time quote for a symbol using multi-source scrapers
    
    Example: /api/quote/AAPL
    """
    try:
        from anchorgrid.plugins.finance.connectors import yfinance_scraper
        
        quote = yfinance_scraper.get_quote(symbol)
        
        if not quote:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        return quote
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/indicators/{symbol}")
async def get_indicators(
    symbol: str,
    period: str = "1mo"
):
    """
    Get technical indicators for a symbol
    
    Example: /api/indicators/AAPL?period=3mo
    """
    try:
        from anchorgrid.scrapers import yfinance_scraper
        from anchorgrid.plugins.finance.extractors.indicators import rsi, macd, ema
        import numpy as np
        
        # Get historical data
        hist = yfinance_scraper.get_historical(symbol, period=period)
        
        if not hist or 'data' not in hist:
            raise HTTPException(status_code=404, detail=f"No historical data for {symbol}")
        
        # Extract closing prices
        data_points = hist['data']
        prices = np.array([float(d['Close']) for d in data_points])
        
        # Calculate indicators
        rsi_14 = rsi(prices, 14)
        macd_line, macd_signal, macd_hist = macd(prices)
        ema_20 = ema(prices, 20)
        ema_50 = ema(prices, 50)
        
        return {
            "symbol": symbol,
            "period": period,
            "current_price": float(prices[-1]),
            "indicators": {
                "rsi_14": float(rsi_14[-1]) if not np.isnan(rsi_14[-1]) else None,
                "macd": {
                    "line": float(macd_line[-1]) if not np.isnan(macd_line[-1]) else None,
                    "signal": float(macd_signal[-1]) if not np.isnan(macd_signal[-1]) else None,
                    "histogram": float(macd_hist[-1]) if not np.isnan(macd_hist[-1]) else None
                },
                "ema_20": float(ema_20[-1]) if not np.isnan(ema_20[-1]) else None,
                "ema_50": float(ema_50[-1]) if not np.isnan(ema_50[-1]) else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hub/status")
async def hub_status():
    """
    Get Hub (federated learning) status
    """
    try:
        from anchorgrid.hub.registry import AdapterRegistry
        
        return {
            "status": "operational",
            "features": {
                "registry": "operational",
                "merging": "operational",
                "evaluation": "operational (needs PEFT)",
                "cli": "fully functional"
            },
            "next_steps": {
                "install_ml": "pip install anchorgrid[ml]",
                "submit_adapter": "anchorgrid push adapter.zip"
            }
        }
    except Exception as e:
        return {
            "status"error",
            "message": str(e)
        }


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║  AnchorGrid Core API Server                                ║
    ║  Zero-Cost Financial Intelligence Infrastructure          ║
    ╚═══════════════════════════════════════════════════════════╝
    
    📡 Server: http://localhost:8000
    📚 Docs: http://localhost:8000/docs
    
    Endpoints:
      GET  /                      - Health check
      GET  /api/quote/{symbol}    - Real-time quote
      GET  /api/indicators/{symbol} - Technical indicators
      GET  /api/hub/status         - Hub status
    
    Press CTRL+C to stop
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
