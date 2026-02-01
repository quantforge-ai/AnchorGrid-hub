"""
Finance Connectors - Data Sources for Financial Markets

Connectors are the universal term for data sources.
In Finance, we connect to: Yahoo Finance, SEC EDGAR, Federal Reserve, etc.
"""

from anchorgrid.plugins.finance.connectors.yahoo_scraper import yfinance_scraper
from anchorgrid.plugins.finance.connectors.nasdaq_scraper import nasdaq_scraper
from anchorgrid.plugins.finance.connectors.marketwatch_scraper import marketwatch_scraper
from anchorgrid.plugins.finance.connectors.aggregator import multi_source_aggregator

from anchorgrid.plugins.finance.connectors.fred_scraper import fred_scraper
from anchorgrid.plugins.finance.connectors.central_banks import central_bank_scraper

from anchorgrid.plugins.finance.connectors.sec_scraper import sec_scraper

from anchorgrid.plugins.finance.connectors.news_rss import news_rss_scraper

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
