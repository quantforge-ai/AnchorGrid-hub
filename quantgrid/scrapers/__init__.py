"""Scraper package for zero-cost data ingestion"""

# Market Data
from quantgrid.scrapers.yahoo_scraper import yfinance_scraper
from quantgrid.scrapers.nasdaq_scraper import nasdaq_scraper  
from quantgrid.scrapers.marketwatch_scraper import marketwatch_scraper
from quantgrid.scrapers.aggregator import multi_source_aggregator

# Macro & Economic Data
from quantgrid.scrapers.fred_scraper import fred_scraper
from quantgrid.scrapers.central_banks import central_bank_scraper

# Company Data
from quantgrid.scrapers.sec_scraper import sec_scraper

# News Data
from quantgrid.scrapers.news_rss import news_rss_scraper

__all__ = [
    # Market Data
    "yfinance_scraper",
    "nasdaq_scraper",
    "marketwatch_scraper",
    "multi_source_aggregator",
    # Macro Data
    "fred_scraper",
    "central_bank_scraper",
    # Company Data
    "sec_scraper",
    # News
    "news_rss_scraper",
]


