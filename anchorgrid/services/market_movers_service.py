"""
Market Movers Service - Dynamic Ticker Lists

Sources (in priority order):
1. yfinance Screener API (US stocks only)
2. Yahoo Finance Global Page (scraping - global coverage)
3. Google Finance (scraping - global coverage)
4. Fallback to popular stocks

All free sources, no API rate limits
"""

import yfinance as yf
from typing import List, Dict
import asyncio
import requests
from bs4 import BeautifulSoup
from anchorgrid.core.logger import logger

# Cache for 5 minutes
_cache = {}
_cache_timeout = 300  # seconds


async def get_top_gainers(limit: int = 15) -> List[str]:
    """
    Get top gaining stocks GLOBALLY
    1. Try yfinance (US only but fast)
    2. Scrape Yahoo global + Google Finance
    3. Merge and deduplicate
    """
    try:
        # Check cache
        if 'gainers' in _cache:
            return _cache['gainers'][:limit]
        
        # Try multiple sources in parallel for global coverage
        symbols = await _fetch_global_gainers(limit)
        _cache['gainers'] = symbols
        
        logger.info(f"✅ Got {len(symbols)} GLOBAL gainers")
        return symbols
        
    except Exception as e:
        logger.error(f"All global gainers sources failed: {e}")
        return ["AAPL", "GOOGL", "MSFT", "NVDA", "TSLA"][:limit]


async def get_top_losers(limit: int = 15) -> List[str]:
    """
    Get top losing stocks GLOBALLY
    Same strategy as gainers - multi-source
    """
    try:
        # Check cache
        if 'losers' in _cache:
            return _cache['losers'][:limit]
        
        # Try multiple sources in parallel
        symbols = await _fetch_global_losers(limit)
        _cache['losers'] = symbols
        
        logger.info(f"✅ Got {len(symbols)} GLOBAL losers")
        return symbols
        
    except Exception as e:
        logger.error(f"All global losers sources failed: {e}")
        return ["F", "NIO", "LCID", "RIVN"][:limit]


async def get_most_active(limit: int = 15) -> List[str]:
    """
    Get most actively traded stocks GLOBALLY
    Multi-source strategy for global coverage
    """
    try:
        # Check cache
        if 'active' in _cache:
            return _cache['active'][:limit]
        
        # Fetch from global sources
        symbols = await _fetch_global_active(limit)
        _cache['active'] = symbols
        
        logger.info(f"✅ Got {len(symbols)} GLOBAL most active")
        return symbols
        
    except Exception as e:
        logger.error(f"All global active sources failed: {e}")
        return ["AAPL", "TSLA", "NVDA", "AMD"][:limit]


async def get_trending(limit: int = 15) -> List[str]:
    """
    Get trending stocks GLOBALLY
    Yahoo + Google trending combined
    """
    try:
        # Check cache
        if 'trending' in _cache:
            return _cache['trending'][:limit]
        
        logger.info(f"Fetching GLOBAL trending stocks")
        symbols = await _fetch_global_trending(limit)
        _cache['trending'] = symbols
        
        logger.info(f"✅ Got {len(symbols)} GLOBAL trending tickers")
        return symbols
        
    except Exception as e:
        logger.error(f"Global trending failed: {e}, using most active")
        return await get_most_active(limit)


# ========== Custom Scrapers ==========

async def _scrape_yahoo_gainers(limit: int) -> List[str]:
    """Scrape Yahoo Finance gainers page"""
    try:
        url = "https://finance.yahoo.com/gainers"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find ticker symbols in table
        symbols = []
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows[:limit]:
                cells = row.find_all('td')
                if cells:
                    symbol = cells[0].get_text(strip=True)
                    symbols.append(symbol)
        
        logger.info(f"📊 Scraped {len(symbols)} gainers from Yahoo")
        return symbols
        
    except Exception as e:
        logger.error(f"Yahoo gainers scrape failed: {e}")
        # Ultimate fallback: popular stocks
        return ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "NFLX"][:limit]


async def _scrape_yahoo_losers(limit: int) -> List[str]:
    """Scrape Yahoo Finance losers page"""
    try:
        url = "https://finance.yahoo.com/losers"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        symbols = []
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:]
            for row in rows[:limit]:
                cells = row.find_all('td')
                if cells:
                    symbol = cells[0].get_text(strip=True)
                    symbols.append(symbol)
        
        logger.info(f"📊 Scraped {len(symbols)} losers from Yahoo")
        return symbols
        
    except Exception as e:
        logger.error(f"Yahoo losers scrape failed: {e}")
        return ["F", "NIO", "LCID", "RIVN", "BABA", "JD"][:limit]


async def _scrape_yahoo_active(limit: int) -> List[str]:
    """Scrape Yahoo Finance most active page"""
    try:
        url = "https://finance.yahoo.com/most-active"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        symbols = []
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:]
            for row in rows[:limit]:
                cells = row.find_all('td')
                if cells:
                    symbol = cells[0].get_text(strip=True)
                    symbols.append(symbol)
        
        logger.info(f"📊 Scraped {len(symbols)} most active from Yahoo")
        return symbols
        
    except Exception as e:
        logger.error(f"Yahoo active scrape failed: {e}")
        return ["AAPL", "TSLA", "NVDA", "AMD", "COIN"][:limit]


async def _scrape_yahoo_trending(limit: int) -> List[str]:
    """Scrape Yahoo Finance trending tickers page"""
    try:
        url = "https://finance.yahoo.com/trending-tickers"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        symbols = []
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:]
            for row in rows[:limit]:
                cells = row.find_all('td')
                if cells:
                    symbol = cells[0].get_text(strip=True)
                    symbols.append(symbol)
        
        logger.info(f"🔥 Scraped {len(symbols)} trending from Yahoo")
        return symbols
        
    except Exception as e:
        logger.error(f"Yahoo trending scrape failed: {e}")
        return await _scrape_yahoo_active(limit)


# ========== GLOBAL Market Movers (Yahoo Global + Google Finance) ==========

async def _fetch_global_gainers(limit: int) -> List[str]:
    """
    Fetch global gainers from multiple sources and merge
    Priority: Yahoo Global > Google Finance > yfinance US
    """
    try:
        # Fetch from all sources in parallel
        tasks = [
            _scrape_yahoo_global_gainers(limit * 2),  # Get more for dedup
            _scrape_google_finance_gainers(limit * 2),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge results and deduplicate
        all_symbols = []
        for result in results:
            if isinstance(result, list):
                all_symbols.extend(result)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_symbols = []
        for symbol in all_symbols:
            if symbol not in seen:
                seen.add(symbol)
                unique_symbols.append(symbol)
        
        logger.info(f"🌍 Merged global gainers: {len(unique_symbols)} unique symbols")
        return unique_symbols[:limit]
        
    except Exception as e:
        logger.error(f"Global gainers fetch failed: {e}")
        # Fallback to old Yahoo scraper
        return await _scrape_yahoo_gainers(limit)


async def _fetch_global_losers(limit: int) -> List[str]:
    """
    Fetch global losers from multiple sources and merge
    """
    try:
        tasks = [
            _scrape_yahoo_global_losers(limit * 2),
            _scrape_google_finance_losers(limit * 2),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_symbols = []
        for result in results:
            if isinstance(result, list):
                all_symbols.extend(result)
        
        # Deduplicate
        seen = set()
        unique_symbols = []
        for symbol in all_symbols:
            if symbol not in seen:
                seen.add(symbol)
                unique_symbols.append(symbol)
        
        logger.info(f"🌍 Merged global losers: {len(unique_symbols)} unique symbols")
        return unique_symbols[:limit]
        
    except Exception as e:
        logger.error(f"Global losers fetch failed: {e}")
        return await _scrape_yahoo_losers(limit)


async def _scrape_yahoo_global_gainers(limit: int) -> List[str]:
    """Scrape Yahoo Finance GLOBAL gainers page"""
    try:
        # Yahoo doesn't have a clear global gainers URL, so scrape markets/world
        url = "https://finance.yahoo.com/world"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        symbols = []
        # Look for ticker symbols in data attributes or links
        ticker_links = soup.find_all('a', href=True)
        for link in ticker_links:
            href = link.get('href', '')
            if '/quote/' in href:
                symbol = href.split('/quote/')[-1].split('?')[0]
                if symbol and len(symbol) < 10:  # Basic validation
                    symbols.append(symbol)
        
        logger.info(f"🌎 Scraped {len(symbols)} from Yahoo global")
        return symbols[:limit]
        
    except Exception as e:
        logger.error(f"Yahoo global scrape failed: {e}")
        return []


async def _scrape_yahoo_global_losers(limit: int) -> List[str]:
    """Scrape Yahoo Finance GLOBAL losers"""
    # Similar to gainers but for losers
    try:
        url = "https://finance.yahoo.com/world"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        symbols = []
        ticker_links = soup.find_all('a', href=True)
        for link in ticker_links:
            href = link.get('href', '')
            if '/quote/' in href:
                symbol = href.split('/quote/')[-1].split('?')[0]
                if symbol and len(symbol) < 10:
                    symbols.append(symbol)
        
        logger.info(f"🌎 Scraped {len(symbols)} from Yahoo global losers")
        return symbols[:limit]
        
    except Exception as e:
        logger.error(f"Yahoo global losers failed: {e}")
        return []


async def _scrape_google_finance_gainers(limit: int) -> List[str]:
    """Scrape Google Finance top gainers"""
    try:
        url = "https://www.google.com/finance/markets/gainers"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
        }
        
        response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        symbols = []
        # Google Finance has unique structure - look for stock links
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            # Google Finance URLs: /quote/SYMBOL:EXCHANGE
            if '/quote/' in href:
                try:
                    parts = href.split('/quote/')[-1].split(':')
                    if len(parts) == 2:
                        symbol_part, exchange = parts
                        # Convert Google format to yfinance format
                        if exchange == 'NASDAQ' or exchange == 'NYSE':
                            symbols.append(symbol_part)
                        elif exchange == 'NSE':
                            symbols.append(f"{symbol_part}.NS")
                        elif exchange == 'BSE':
                            symbols.append(f"{symbol_part}.BO")
                        elif exchange == 'HKG':
                            symbols.append(f"{symbol_part}.HK")
                        elif exchange == 'TPE':
                            symbols.append(f"{symbol_part}.TW")
                except:
                    continue
        
        logger.info(f"🔍 Scraped {len(symbols)} from Google Finance gainers")
        return symbols[:limit]
        
    except Exception as e:
        logger.error(f"Google Finance scrape failed: {e}")
        return []


async def _scrape_google_finance_losers(limit: int) -> List[str]:
    """Scrape Google Finance top losers"""
    try:
        url = "https://www.google.com/finance/markets/losers"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
        }
        
        response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        symbols = []
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if '/quote/' in href:
                try:
                    parts = href.split('/quote/')[-1].split(':')
                    if len(parts) == 2:
                        symbol_part, exchange = parts
                        if exchange == 'NASDAQ' or exchange == 'NYSE':
                            symbols.append(symbol_part)
                        elif exchange == 'NSE':
                            symbols.append(f"{symbol_part}.NS")
                        elif exchange == 'BSE':
                            symbols.append(f"{symbol_part}.BO")
                        elif exchange == 'HKG':
                            symbols.append(f"{symbol_part}.HK")
                        elif exchange == 'TPE':
                            symbols.append(f"{symbol_part}.TW")
                except:
                    continue
        
        logger.info(f"🔍 Scraped {len(symbols)} from Google Finance losers")
        return symbols[:limit]
        
    except Exception as e:
        logger.error(f"Google Finance losers failed: {e}")
        return []


async def _fetch_global_active(limit: int) -> List[str]:
    """
    Fetch globally most active stocks from multiple sources
    """
    try:
        tasks = [
            _scrape_yahoo_global_active(limit * 2),
            _scrape_google_finance_active(limit * 2),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_symbols = []
        for result in results:
            if isinstance(result, list):
                all_symbols.extend(result)
        
        # Deduplicate
        seen = set()
        unique_symbols = []
        for symbol in all_symbols:
            if symbol not in seen:
                seen.add(symbol)
                unique_symbols.append(symbol)
        
        logger.info(f"🌍 Merged global most active: {len(unique_symbols)} unique symbols")
        return unique_symbols[:limit]
        
    except Exception as e:
        logger.error(f"Global active fetch failed: {e}")
        return await _scrape_yahoo_active(limit)


async def _fetch_global_trending(limit: int) -> List[str]:
    """
    Fetch globally trending stocks
    """
    try:
        tasks = [
            _scrape_yahoo_trending(limit),
            _scrape_google_finance_trending(limit),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_symbols = []
        for result in results:
            if isinstance(result, list):
                all_symbols.extend(result)
        
        # Deduplicate
        seen = set()
        unique_symbols = []
        for symbol in all_symbols:
            if symbol not in seen:
                seen.add(symbol)
                unique_symbols.append(symbol)
        
        logger.info(f"🌍 Merged global trending: {len(unique_symbols)} unique symbols")
        return unique_symbols[:limit]
        
    except Exception as e:
        logger.error(f"Global trending fetch failed: {e}")
        return await _scrape_yahoo_trending(limit)


async def _scrape_yahoo_global_active(limit: int) -> List[str]:
    """Scrape Yahoo Finance global most active"""
    try:
        url = "https://finance.yahoo.com/most-active"  # This might be US-focused
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        symbols = []
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:]
            for row in rows[:limit]:
                cells = row.find_all('td')
                if cells:
                    symbol = cells[0].get_text(strip=True)
                    symbols.append(symbol)
        
        logger.info(f"🌎 Scraped {len(symbols)} from Yahoo most active")
        return symbols
        
    except Exception as e:
        logger.error(f"Yahoo global active failed: {e}")
        return []


async def _scrape_google_finance_active(limit: int) -> List[str]:
    """Scrape Google Finance most active stocks"""
    try:
        url = "https://www.google.com/finance/markets/most-active"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
        }
        
        response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        symbols = []
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if '/quote/' in href:
                try:
                    parts = href.split('/quote/')[-1].split(':')
                    if len(parts) == 2:
                        symbol_part, exchange = parts
                        if exchange == 'NASDAQ' or exchange == 'NYSE':
                            symbols.append(symbol_part)
                        elif exchange == 'NSE':
                            symbols.append(f"{symbol_part}.NS")
                        elif exchange == 'BSE':
                            symbols.append(f"{symbol_part}.BO")
                        elif exchange == 'HKG':
                            symbols.append(f"{symbol_part}.HK")
                        elif exchange == 'TPE':
                            symbols.append(f"{symbol_part}.TW")
                except:
                    continue
        
        logger.info(f"🔍 Scraped {len(symbols)} from Google Finance most active")
        return symbols[:limit]
        
    except Exception as e:
        logger.error(f"Google Finance most active failed: {e}")
        return []


async def _scrape_google_finance_trending(limit: int) -> List[str]:
    """Scrape Google Finance trending stocks"""
    try:
        # Google Finance doesn't have a dedicated trending page, use gainers as proxy
        url = "https://www.google.com/finance/markets/gainers"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
        }
        
        response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        symbols = []
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if '/quote/' in href:
                try:
                    parts = href.split('/quote/')[-1].split(':')
                    if len(parts) == 2:
                        symbol_part, exchange = parts
                        if exchange == 'NASDAQ' or exchange == 'NYSE':
                            symbols.append(symbol_part)
                        elif exchange == 'NSE':
                            symbols.append(f"{symbol_part}.NS")
                        elif exchange == 'BSE':
                            symbols.append(f"{symbol_part}.BO")
                        elif exchange == 'HKG':
                            symbols.append(f"{symbol_part}.HK")
                        elif exchange == 'TPE':
                            symbols.append(f"{symbol_part}.TW")
                except:
                    continue
        
        logger.info(f"🔍 Scraped {len(symbols)} from Google Finance trending")
        return symbols[:limit]
        
    except Exception as e:
        logger.error(f"Google Finance trending failed: {e}")
        return []








async def get_tech_sector(limit: int = 15) -> List[str]:
    """
    Get global technology sector leaders
    Dynamic: Google Finance tech sector
    Fallback: Curated global tech leaders
    """
    try:
        # Check cache
        if 'tech' in _cache:
            return _cache['tech'][:limit]
        
        # Try dynamic scraping
        symbols = await _scrape_google_finance_tech(limit)
        
        # If scraping fails or returns too few, use curated fallback
        if not symbols or len(symbols) < 5:
            logger.warning("Dynamic tech sector failed, using curated fallback")
            symbols = _get_curated_tech_leaders()
        
        _cache['tech'] = symbols
        logger.info(f"✅ Got {len(symbols)} tech sector stocks")
        return symbols[:limit]
        
    except Exception as e:
        logger.error(f"Tech sector fetch failed: {e}, using curated")
        return _get_curated_tech_leaders()[:limit]


async def get_finance_sector(limit: int = 15) -> List[str]:
    """
    Get global finance sector leaders
    Dynamic: Google Finance finance sector
    Fallback: Curated global finance leaders
    """
    try:
        # Check cache
        if 'finance' in _cache:
            return _cache['finance'][:limit]
        
        # Try dynamic scraping
        symbols = await _scrape_google_finance_finance(limit)
        
        # If scraping fails or returns too few, use curated fallback
        if not symbols or len(symbols) < 5:
            logger.warning("Dynamic finance sector failed, using curated fallback")
            symbols = _get_curated_finance_leaders()
        
        _cache['finance'] = symbols
        logger.info(f"✅ Got {len(symbols)} finance sector stocks")
        return symbols[:limit]
        
    except Exception as e:
        logger.error(f"Finance sector fetch failed: {e}, using curated")
        return _get_curated_finance_leaders()[:limit]


async def _scrape_google_finance_tech(limit: int) -> List[str]:
    """Scrape Google Finance technology sector"""
    try:
        url = "https://www.google.com/finance/markets/technology"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
        }
        
        response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        symbols = []
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if '/quote/' in href:
                try:
                    parts = href.split('/quote/')[-1].split(':')
                    if len(parts) == 2:
                        symbol_part, exchange = parts
                        if exchange == 'NASDAQ' or exchange == 'NYSE':
                            symbols.append(symbol_part)
                        elif exchange == 'NSE':
                            symbols.append(f"{symbol_part}.NS")
                        elif exchange == 'BSE':
                            symbols.append(f"{symbol_part}.BO")
                        elif exchange == 'HKG':
                            symbols.append(f"{symbol_part}.HK")
                        elif exchange == 'TPE':
                            symbols.append(f"{symbol_part}.TW")
                        elif exchange == 'KRX':
                            symbols.append(f"{symbol_part}.KS")
                except:
                    continue
        
        logger.info(f"🔍 Scraped {len(symbols)} from Google Finance tech sector")
        return symbols[:limit]
        
    except Exception as e:
        logger.error(f"Google Finance tech scrape failed: {e}")
        return []


async def _scrape_google_finance_finance(limit: int) -> List[str]:
    """Scrape Google Finance financial sector"""
    try:
        url = "https://www.google.com/finance/markets/financials"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
        }
        
        response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        symbols = []
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if '/quote/' in href:
                try:
                    parts = href.split('/quote/')[-1].split(':')
                    if len(parts) == 2:
                        symbol_part, exchange = parts
                        if exchange == 'NASDAQ' or exchange == 'NYSE':
                            symbols.append(symbol_part)
                        elif exchange == 'NSE':
                            symbols.append(f"{symbol_part}.NS")
                        elif exchange == 'BSE':
                            symbols.append(f"{symbol_part}.BO")
                        elif exchange == 'HKG':
                            symbols.append(f"{symbol_part}.HK")
                        elif exchange == 'TPE':
                            symbols.append(f"{symbol_part}.TW")
                except:
                    continue
        
        logger.info(f"🔍 Scraped {len(symbols)} from Google Finance finance sector")
        return symbols[:limit]
        
    except Exception as e:
        logger.error(f"Google Finance finance scrape failed: {e}")
        return []


def _get_curated_tech_leaders() -> List[str]:
    """Curated global tech leaders (fallback)"""
    return [
        # US Tech Giants
        "AAPL", "MSFT", "GOOGL", "NVDA", "META", "AMZN", "TSLA", "AMD",
        # Taiwan Semiconductors
        "2330.TW",  # TSMC
        "2317.TW",  # Hon Hai (Foxconn)
        # Korea Tech
        "005930.KS",  # Samsung Electronics
        # Chinese Tech
        "BABA", "JD", "PDD", "BIDU",
        # Indian Tech
        "TCS.NS",     # Tata Consultancy
        "INFY.NS",    # Infosys
    ]


def _get_curated_finance_leaders() -> List[str]:
    """Curated global finance leaders (fallback)"""
    return [
        # US Banks
        "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW",
        # Indian Finance
        "HDFCBANK.NS",  # HDFC Bank
        "ICICIBANK.NS", # ICICI Bank
        "KOTAKBANK.NS", # Kotak Mahindra
        # Hong Kong Finance
        "0939.HK",      # China Construction Bank
        "0005.HK",      # HSBC
        # Chinese Finance
        "BABA",         # Ant Financial parent
    ]


def split_by_region(symbols: List[str]) -> Dict[str, List[str]]:
    """
    Split stock symbols into regional categories for multi-train display
    
    Args:
        symbols: List of stock symbols (with exchange extensions)
        
    Returns:
        Dict with keys: 'us', 'europe', 'asia', 'others'
        Each containing list of symbols from that region
    """
    regions = {
        'us': [],
        'europe': [],
        'asia': [],
        'others': []
    }
    
    for symbol in symbols:
        # Europe extensions
        if any(ext in symbol for ext in ['.L', '.DE', '.PA', '.AS', '.MC', '.MI', '.SW']):
            regions['europe'].append(symbol)
        # Asia extensions
        elif any(ext in symbol for ext in ['.NS', '.BO', '.TW', '.HK', '.KS', '.T', '.SS', '.SZ']):
            regions['asia'].append(symbol)
        # Others (LATAM, Oceania)
        elif any(ext in symbol for ext in ['.SA', '.AX', '.NZ']):
            regions['others'].append(symbol)
        # Default to US (no extension or .US)
        else:
            regions['us'].append(symbol)
    
    return regions


def clear_cache():
    """Clear market movers cache (call on manual refresh)"""
    global _cache
    _cache = {}
    logger.info("🗑️ Market movers cache cleared")
