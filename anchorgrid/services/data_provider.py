"""
Data Provider Service
Calculates multi-dimensional market health using Weighted Indices and Breadth analysis.
"""

import asyncio
import random
import math
from datetime import datetime
from typing import Dict, List, Optional

class DataProvider:
    """
    Service responsible for aggregating market data into Intelligence Indices.
    """
    
    def __init__(self):
        # In a real app, this would connect to scrapers or a cache
        pass

    async def get_mode_data(self, mode_type: str) -> Dict:
        """
        Fetch and calculate all Intelligence Layers for a specific mode.
        """
        # Simulate network latency
        await asyncio.sleep(0.1)
        
        # 1. Generate/Fetch raw price data (Mocking for now)
        base_change = random.uniform(-2.0, 3.5)
        breadth = random.uniform(0.3, 0.8)
        
        # 2. Calculate Perspectives
        market_cap_index = base_change * 1.1 # Dominated by big caps
        breadth_index = base_change * breadth # Democratic view
        
        # 3. Detect Divergence
        divergence = self._detect_divergence(market_cap_index, breadth_index)
        
        # 4. Detect Regime
        regime = self._detect_regime(mode_type, market_cap_index, breadth_index)
        
        # 5. Generate Wave Data (120 points for Braille chart)
        wave_data = self._generate_wave_data(base_change)
        
        return {
            "mode_type": mode_type,
            "change_pct": market_cap_index,
            "breadth_pct": breadth,
            "regime": regime,
            "divergence": divergence,
            "wave_data": wave_data,
            "stats": {
                "open": 4200.50 + random.uniform(-10, 10),
                "high": 4250.00 + random.uniform(5, 20),
                "low": 4180.00 - random.uniform(5, 20),
                "close": 4220.30 + market_cap_index * 10,
                "volume": random.randint(5000, 15000)
            },
            "rsi": random.randint(30, 70),
            "macd": random.uniform(-2.0, 2.0)
        }

    def _detect_divergence(self, market_cap_index: float, breadth_index: float) -> str:
        """Detect alignment between big caps and market breadth."""
        cap_up = market_cap_index > 0
        breadth_up = breadth_index > 0
        
        if cap_up and breadth_up:
            return "ALIGNED"
        elif not cap_up and not breadth_up:
            return "ALIGNED"
        else:
            return "DIVERGENT"

    def _detect_regime(self, mode: str, mc_index: float, breadth: float) -> str:
        """Determine market regime based on indicators."""
        if mode == "CRYPTO":
            if breadth > 0.7: return "ALTCOIN SEASON"
            if mc_index > 5.0: return "PARABOLIC"
            return "CONSOLIDATION"
        
        if mode == "STOCKS" or mode in ["AMERICAS", "ASIA-PACIFIC", "EUROPE", "MEA", "FRONTIER", "TECH LEADERS"]:
            if mc_index > 1.0 and breadth > 0.6: return "BULL MARKET"
            if mc_index < -1.0: return "BEARISH"
            return "NEUTRAL"
            
        return "STABLE"

    def _generate_wave_data(self, base_change: float) -> List[float]:
        """Generate 120 points for smooth Braille rendering."""
        points = []
        val = 100.0
        freq = random.uniform(8, 15)
        amp = random.uniform(3, 7)
        for i in range(120):
            # Sine wave + smooth trend + minimal noise
            trend = (base_change / 60) * i # Steeper trend for visibility
            v = val + trend + math.sin(i / freq) * amp + random.uniform(-0.2, 0.2)
            points.append(v)
        return points
