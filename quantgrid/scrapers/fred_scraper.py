"""
FRED Scraper - Federal Reserve Economic Data (NO API KEY)

Scrapes FRED public data without needing API keys.
Uses public download endpoints and RSS feeds.

Data Sources:
- FRED public download URLs (CSV format)
- FRED RSS feeds
- FRED release calendars
"""
import httpx
import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from loguru import logger


class FREDScraper:
    """
    Scrape FRED data without API keys.
    
    Uses public download URLs that work without authentication.
    """
    
    SOURCE_NAME = "fred_public"
    BASE_URL = "https://fred.stlouisfed.org"
    GRAPH_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
    
    # Common macro series IDs
    SERIES_MAP = {
        # Interest Rates
        "FED_RATE": "FEDFUNDS",
        "10Y_TREASURY": "DGS10",
        "2Y_TREASURY": "DGS2",
        "30Y_MORTGAGE": "MORTGAGE30US",
        
        # Economic Indicators
        "GDP": "GDP",
        "UNEMPLOYMENT": "UNRATE",
        "CPI": "CPIAUCSL",
        "INFLATION": "CPIAUCSL",
        "JOBLESS_CLAIMS": "ICSA",
        "RETAIL_SALES": "RSXFS",
        
        # Money Supply
        "M2": "M2SL",
        "M1": "M1SL",
        
        # Market Indicators
        "SP500": "SP500",
        "VIX": "VIXCLS",
        
        # Housing
        "HOUSING_STARTS": "HOUST",
        "HOME_SALES": "HSN1F",
        "CASE_SHILLER": "CSUSHPISA",
        
        # Manufacturing
        "ISM_MANUFACTURING": "MANEMP",
        "INDUSTRIAL_PRODUCTION": "INDPRO",
    }
    
    def __init__(self):
        logger.info("FRED scraper initialized (NO API KEY REQUIRED)")
    
    async def get_series(
        self,
        series_id: str,
        lookback_days: int = 365
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch FRED series data via public CSV download.
        
        Args:
            series_id: FRED series ID (e.g., "FEDFUNDS", "GDP")
            lookback_days: Days of historical data
        
        Returns:
            Dict with series data or None
        """
        # Map common names to series IDs
        series_id = self.SERIES_MAP.get(series_id.upper(), series_id.upper())
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        # FRED public CSV URL (works without API key!)
        url = f"{self.GRAPH_URL}?id={series_id}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
            
            # Parse CSV
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            
            # Filter by date range
            df['DATE'] = pd.to_datetime(df['DATE'])
            df = df[df['DATE'] >= start_date]
            
            # Convert to dict format
            data = {
                "series_id": series_id,
                "name": series_id,  # FRED doesn't give name in CSV
                "data": df.to_dict(orient='records'),
                "source": self.SOURCE_NAME,
                "last_updated": datetime.now().isoformat(),
            }
            
            logger.info(f"Fetched {len(df)} observations for {series_id} from FRED")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch {series_id} from FRED: {e}")
            return None
    
    async def get_multiple_series(
        self,
        series_ids: List[str],
        lookback_days: int = 365
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch multiple series at once.
        
        Args:
            series_ids: List of FRED series IDs
            lookback_days: Days of historical data
        
        Returns:
            Dict mapping series_id -> data
        """
        results = {}
        
        for series_id in series_ids:
            data = await self.get_series(series_id, lookback_days)
            if data:
                results[series_id] = data
        
        logger.info(f"Fetched {len(results)}/{len(series_ids)} FRED series")
        return results
    
    async def get_latest_value(self, series_id: str) -> Optional[float]:
        """
        Get just the latest value for a series (fast).
        
        Args:
            series_id: FRED series ID
        
        Returns:
            Latest value or None
        """
        data = await self.get_series(series_id, lookback_days=30)
        
        if data and data.get("data"):
            # Get last non-null value
            for row in reversed(data["data"]):
                value = row.get(series_id)
                if value and value != '.':
                    return float(value)
        
        return None


# Singleton instance
fred_scraper = FREDScraper()

