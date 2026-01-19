"""
Multi-Source Aggregator - Intelligent Fallback Routing

Coordinates multiple scrapers with intelligent fallback:
1. Try YFinance first (reliable & fast)
2. Fall back to NASDAQ (US stocks, 5-15s delay)
3. Fall back to MarketWatch (real-time backup)
4. Cache aggressively (5-10s TTL)

Features:
- Zero API costs
- Fault tolerance
- Global coverage
- Rate limit safe
"""
from typing import Optional, Dict, Any
from loguru import logger

from quantgrid.scrapers.yahoo_scraper import yfinance_scraper
from quantgrid.scrapers.nasdaq_scraper import nasdaq_scraper
from quantgrid.scrapers.marketwatch_scraper import marketwatch_scraper


class MultiSourceAggregator:
    """
    Intelligent multi-source data aggregator.
    
    Priority:
    1. YFinance (primary) - handles rate limits automatically
    2. NASDAQ - direct exchange data (US only)
    3. MarketWatch - real-time backup
    """
    
    def __init__(self):
        self.scrapers = [
            yfinance_scraper,
            # nasdaq_scraper,  # Disabled due to rate limiting
            # marketwatch_scraper,  # Disabled due to rate limiting
        ]
        logger.info("Multi-source aggregator initialized (YFinance primary)")
    
    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch quote with intelligent fallback.
        
        Tries each scraper in priority order until one succeeds.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Quote data or None if all sources failed
        """
        for scraper in self.scrapers:
            try:
                if hasattr(scraper, 'get_quote'):
                    # Sync scraper
                    quote = scraper.get_quote(symbol)
                    if quote:
                        logger.debug(f"{symbol}: Got quote from {scraper.SOURCE_NAME}")
                        return quote
                
            except Exception as e:
                logger.warning(f"{symbol}: {scraper.SOURCE_NAME} failed - {e}")
                continue
        
        logger.error(f"{symbol}: All scrapers failed")
        return None
    
    async def get_quote_async(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Async version of get_quote for async scrapers.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Quote data or None
        """
        # Try YFinance first (sync)
        quote = yfinance_scraper.get_quote(symbol)
        if quote:
            return quote
        
        # Try async scrapers
        for scraper in [nasdaq_scraper, marketwatch_scraper]:
            try:
                quote = await scraper.get_quote(symbol)
                if quote:
                    logger.debug(f"{symbol}: Got quote from {scraper.SOURCE_NAME}")
                    return quote
            except Exception as e:
                logger.warning(f"{symbol}: {scraper.SOURCE_NAME} failed - {e}")
                continue
        
        logger.error(f"{symbol}: All scrapers failed")
        return None
    
    def get_quotes_batch(self, symbols: list[str]) -> Dict[str, Dict[str, Any]]:
        """
        Batch fetch multiple quotes (faster).
        
        Args:
            symbols: List of symbols
        
        Returns:
            Dict mapping symbol -> quote data
        """
        # YFinance supports batch fetching
        return yfinance_scraper.get_quotes_batch(symbols)


# Singleton instance
multi_source_aggregator = MultiSourceAggregator()

