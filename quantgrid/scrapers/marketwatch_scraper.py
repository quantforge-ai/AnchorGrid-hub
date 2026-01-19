"""
MarketWatch Scraper - Backup Data Source

Scrapes MarketWatch.com stock pages.
Often real-time or <1 minute delay.

Features:
- Real-time or <1min delay
- ~50 requests/min safe
- Good for single lookups
- Slower for batch operations
"""
import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger


class MarketWatchScraper:
    """Backup scraper for real-time quotes"""
    
    SOURCE_NAME = "marketwatch"
    BASE_URL = "https://www.marketwatch.com/investing/stock"
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        logger.info(f"Initialized {self.SOURCE_NAME} scraper")
    
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Scrape MarketWatch for a single symbol.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL", "MSFT")
        
        Returns:
            Quote data dict or None if failed
        """
        url = f"{self.BASE_URL}/{symbol.lower()}"
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # MarketWatch uses <bg-quote> custom elements
            price_elem = soup.find('bg-quote', {'class': 'value'})
            if not price_elem:
                logger.warning(f"{symbol}: Price element not found on MarketWatch")
                return None
            
            price = float(price_elem.text.strip().replace('$', '').replace(',', ''))
            
            # Extract change
            change_elem = soup.find('bg-quote', {'class': 'change--point--q'})
            change_pct_elem = soup.find('bg-quote', {'class': 'change--percent--q'})
            
            change = 0.0
            change_percent = 0.0
            
            if change_elem:
                change = float(change_elem.text.strip())
            
            if change_pct_elem:
                change_percent = float(change_pct_elem.text.strip().replace('%', ''))
            
            quote = {
                "symbol": symbol,
                "price": price,
                "change": change,
                "change_percent": change_percent,
                "timestamp": datetime.now().isoformat(),
                "source": self.SOURCE_NAME
            }
            
            logger.debug(f"{symbol}: ${price:.2f} from {self.SOURCE_NAME}")
            return quote
            
        except httpx.HTTPStatusError as e:
            logger.error(f"{symbol}: MarketWatch HTTP error {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"{symbol}: MarketWatch scraping failed - {e}")
            return None


# Singleton instance
marketwatch_scraper = MarketWatchScraper()

