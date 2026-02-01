# AnchorGrid Scrapers Guide

The `anchorgrid.scrapers` package provides zero-cost financial data extraction. It is designed to work without expensive API keys by utilizing optimized web scrapers and public data endpoints.

## Available Scrapers

### 1. Yahoo Finance Scraper (`yfinance_scraper.py`)
Primary source for real-time and historical market data.
- Quotes (Price, Change, Volume)
- Historical OHLCV data
- Key Statistics

### 2. SEC EDGAR Scraper (`sec_scraper.py`)
Direct access to company filings from the SEC database.
- 10-K (Annual Reports)
- 10-Q (Quarterly Reports)
- 8-K (Current Events)

### 3. FRED Scraper (`fred_scraper.py`)
Economic data from the Federal Reserve Bank of St. Louis.
- Interest Rates
- GDP and Employment data
- CPI and Inflation metrics

### 4. News Aggregator (`news_rss_scraper.py`)
Aggregates financial news from 6 major sources via RSS.
- Real-time sentiment analysis support
- Category-specific feeds

### 5. Central Banks Scraper (`central_bank_scraper.py`)
Data from global central banks (ECB, BOJ, BOE, RBI).

## Usage Example

```python
from anchorgrid.scrapers import yfinance_scraper, sec_scraper

# Get real-time quote
quote = yfinance_scraper.get_quote("AAPL")
print(f"AAPL Price: {quote['price']}")

# Fetch latest 10-K filing
filings = sec_scraper.get_filings("TSLA", "10-K", count=1)
print(f"Latest Filing URL: {filings[0]['url']}")
```

## API Discovery Tool

The Discovery Tool is located in `anchorgrid.tools.api_discovery`. It allows you to auto-generate scrapers for any new financial website by analyzing network traffic and identifying JSON endpoints.

---

## Best Practices
- **Rate Limiting**: Scrapers include built-in jitter and delays. Avoid high-frequency hammering of public endpoints.
- **Failover**: Use the multi-source aggregator to automatically switch providers if one source is blocked.
- **Caching**: Always use the `MarketStateManager` service to cache results and reduce network load.
