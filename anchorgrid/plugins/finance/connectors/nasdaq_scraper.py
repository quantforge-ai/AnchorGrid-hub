"""
NASDAQ Scraper - Backup Data Source

Scrapes NASDAQ.com public stock pages directly.
Near-exchange data (5-15 seconds delay from exchange).

Features:
- Direct exchange data
- US stocks only (NASDAQ/NYSE)
- ~30 requests/min safe rate
- 2-3 seconds per request
"""
import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger


class NASDAQScraper:
    """Backup scraper for US stocks"""
    
    SOURCE_NAME = "nasdaq"
    BASE_URL = "https://www.nasdaq.com/market-activity/stocks"
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        logger.info(f"Initialized {self.SOURCE_NAME} scraper")
    
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Scrape NASDAQ.com for a single symbol.
        
        Args:
            symbol: Stock symbol (US only, e.g., "AAPL", "MSFT")
        
        Returns:
            Quote data dict or None if failed
        """
        url = f"{self.BASE_URL}/{symbol.lower()}"
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract price (CSS class: symbol-page-header__pricing-price)
            price_elem = soup.find('span', {'class': 'symbol-page-header__pricing-price'})
            if not price_elem:
                logger.warning(f"{symbol}: Price element not found on NASDAQ")
                return None
            
            price_text = price_elem.text.strip().replace('$', '').replace(',', '')
            price = float(price_text)
            
            # Extract change
            change_elem = soup.find('span', {'class': 'symbol-page-header__pricing-change'})
            change = 0.0
            change_percent = 0.0
            
            if change_elem:
                change_text = change_elem.text.strip().split()
                if len(change_text) >= 2:
                    change = float(change_text[0])
                    change_percent = float(change_text[1].replace('%', '').replace('(', '').replace(')', ''))
            
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
            logger.error(f"{symbol}: NASDAQ HTTP error {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"{symbol}: NASDAQ scraping failed - {e}")
            return None


# Singleton instance
nasdaq_scraper = NASDAQScraper()

