"""
Historical Data Service - International Multi-Source Scraping

Fetches historical OHLCV data from multiple sources for redundancy:
1. Yahoo Finance (Primary - 100+ exchanges)
2. Investing.com (Backup - global coverage)
3. Exchange-Direct (TWSE, HKEX, NSE, B3 - most accurate)

All free, no API keys, custom scraping only.
"""

import asyncio
import pandas as pd
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import httpx
from quantgrid.core.logger import logger

# Cache for historical data (symbol -> {period -> DataFrame})
_history_cache: Dict[str, Dict[str, pd.DataFrame]] = {}
_cache_timestamps: Dict[str, datetime] = {}

# Cache durations by period (in seconds)
CACHE_DURATIONS = {
    "1d": 60,        # 1 minute (realtime)
    "1w": 300,       # 5 minutes
    "1mo": 900,      # 15 minutes
    "3mo": 1800,     # 30 minutes
    "6mo": 3600,     # 1 hour
    "1y": 7200,      # 2 hours
    "5y": 86400,     # 24 hours
}


async def get_historical_data(
    symbol: str,
    period: str = "1y",
    interval: str = "1d"
) -> Optional[pd.DataFrame]:
    """
    Get historical OHLCV data with multi-source redundancy
    
    Args:
        symbol: Stock symbol (e.g., "AAPL", "2330.TW", "RELIANCE.NS")
        period: Time period (1d, 1w, 1mo, 3mo, 6mo, 1y, 5y)
        interval: Data interval (1d, 1wk, 1mo)
    
    Returns:
        DataFrame with columns: date, open, high, low, close, volume
    """
    
    # Check cache
    cache_key = f"{symbol}_{period}_{interval}"
    if cache_key in _history_cache:
        cached_time = _cache_timestamps.get(cache_key)
        cache_duration = CACHE_DURATIONS.get(period, 3600)
        
        if cached_time and (datetime.now() - cached_time).seconds < cache_duration:
            logger.info(f"📦 Returning cached historical data for {symbol}")
            return _history_cache[cache_key]
    
    logger.info(f"🔍 Fetching historical data for {symbol} ({period})")
    
    # Try sources in parallel (first success wins)
    tasks = [
        fetch_yahoo_finance_history(symbol, period, interval),
        fetch_investing_com_history(symbol, period),
        fetch_exchange_specific_history(symbol, period),
    ]
    
    for completed in asyncio.as_completed(tasks):
        try:
            result = await completed
            if result is not None and not result.empty:
                # Cache successful result
                if symbol not in _history_cache:
                    _history_cache[symbol] = {}
                _history_cache[cache_key] = result
                _cache_timestamps[cache_key] = datetime.now()
                
                logger.info(f"✅ Got {len(result)} records for {symbol} from scraping")
                return result
        except Exception as e:
            logger.warning(f"Source failed for {symbol}: {e}")
            continue
    
    logger.error(f"❌ All sources failed for {symbol}")
    return None


# ========== SOURCE 1: Yahoo Finance (Primary - Global) ==========

async def fetch_yahoo_finance_history(
    symbol: str,
    period: str = "1y",
    interval: str = "1d"
) -> Optional[pd.DataFrame]:
    """
    Scrape Yahoo Finance historical data page
    Supports 100+ international exchanges
    """
    try:
        # Convert symbol format if needed (e.g., NSE:RELIANCE -> RELIANCE.NS)
        yahoo_symbol = normalize_yahoo_symbol(symbol)
        
        url = f"https://finance.yahoo.com/quote/{yahoo_symbol}/history"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find historical data table
            table = soup.find('table', {'data-test': 'historical-prices'})
            if not table:
                # Try alternative selector
                table = soup.find('table')
            
            if not table:
                logger.warning(f"Yahoo Finance: No table found for {symbol}")
                return None
            
            # Parse rows
            rows = table.find('tbody').find_all('tr')
            data = []
            
            for row in rows[:365]:  # Max 1 year of daily data
                cols = row.find_all('td')
                if len(cols) >= 6:
                    try:
                        date_str = cols[0].text.strip()
                        open_price = parse_price(cols[1].text)
                        high_price = parse_price(cols[2].text)
                        low_price = parse_price(cols[3].text)
                        close_price = parse_price(cols[4].text)
                        volume = parse_volume(cols[6].text) if len(cols) > 6 else 0
                        
                        data.append({
                            'date': pd.to_datetime(date_str),
                            'open': open_price,
                            'high': high_price,
                            'low': low_price,
                            'close': close_price,
                            'volume': volume
                        })
                    except (ValueError, IndexError) as e:
                        continue
            
            if data:
                df = pd.DataFrame(data)
                df = df.sort_values('date').reset_index(drop=True)
                logger.info(f"📊 Yahoo Finance: Scraped {len(df)} records for {symbol}")
                return df
            
            return None
            
    except Exception as e:
        logger.error(f"Yahoo Finance scrape failed for {symbol}: {e}")
        return None


# ========== SOURCE 2: Investing.com (Backup - Comprehensive) ==========

async def fetch_investing_com_history(
    symbol: str,
    period: str = "1y"
) -> Optional[pd.DataFrame]:
    """
    Scrape Investing.com historical data
    Strong international coverage (Asia, LATAM, EU)
    """
    try:
        # Map symbol to Investing.com format (would need lookup table)
        # For now, return None and focus on Yahoo/Exchange
        # TODO: Implement Investing.com symbol mapping
        return None
        
    except Exception as e:
        logger.error(f"Investing.com scrape failed for {symbol}: {e}")
        return None


# ========== SOURCE 3: Exchange-Specific (Most Accurate) ==========

async def fetch_exchange_specific_history(
    symbol: str,
    period: str = "1y"
) -> Optional[pd.DataFrame]:
    """
    Route to exchange-specific scraper based on symbol suffix
    """
    try:
        if '.TW' in symbol or '.TWO' in symbol:
            return await scrape_twse_taiwan(symbol, period)
        elif '.HK' in symbol:
            return await scrape_hkex(symbol, period)
        elif '.NS' in symbol or '.BO' in symbol:
            return await scrape_nse_bse_india(symbol, period)
        elif '.SA' in symbol:
            return await scrape_b3_brazil(symbol, period)
        else:
            return None
    except Exception as e:
        logger.error(f"Exchange-specific scrape failed for {symbol}: {e}")
        return None


# ========== Exchange Scrapers ==========

async def scrape_twse_taiwan(symbol: str, period: str) -> Optional[pd.DataFrame]:
    """Taiwan Stock Exchange scraper"""
    try:
        # Extract stock number (e.g., "2330.TW" -> "2330")
        stock_no = symbol.split('.')[0]
        
        # TWSE provides monthly data - fetch last few months
        url = f"https://www.twse.com.tw/en/page/trading/exchange/STOCK_DAY.html"
        params = {
            'date': datetime.now().strftime('%Y%m01'),
            'stockNo': stock_no
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse table (implementation details)
            # TODO: Complete TWSE scraper
            return None
            
    except Exception as e:
        logger.error(f"TWSE scrape failed: {e}")
        return None


async def scrape_hkex(symbol: str, period: str) -> Optional[pd.DataFrame]:
    """Hong Kong Stock Exchange scraper"""
    # TODO: Implement HKEX scraper
    return None


async def scrape_nse_bse_india(symbol: str, period: str) -> Optional[pd.DataFrame]:
    """NSE/BSE India scraper"""
    # TODO: Implement NSE/BSE scraper
    return None


async def scrape_b3_brazil(symbol: str, period: str) -> Optional[pd.DataFrame]:
    """B3 Brazil scraper"""
    # TODO: Implement B3 scraper
    return None


# ========== Helper Functions ==========

def normalize_yahoo_symbol(symbol: str) -> str:
    """
    Convert various symbol formats to Yahoo Finance format
    Examples:
        "AAPL" -> "AAPL"
        "2330.TW" -> "2330.TW"
        "RELIANCE.NS" -> "RELIANCE.NS"
    """
    return symbol.upper()


def parse_price(price_str: str) -> float:
    """Parse price string to float (handles commas, currency symbols)"""
    try:
        # Remove commas, currency symbols, whitespace
        cleaned = price_str.replace(',', '').replace('$', '').strip()
        return float(cleaned)
    except (ValueError, AttributeError):
        return 0.0


def parse_volume(volume_str: str) -> int:
    """Parse volume string to int (handles K, M, B multipliers)"""
    try:
        cleaned = volume_str.replace(',', '').strip().upper()
        
        if 'K' in cleaned:
            return int(float(cleaned.replace('K', '')) * 1000)
        elif 'M' in cleaned:
            return int(float(cleaned.replace('M', '')) * 1_000_000)
        elif 'B' in cleaned:
            return int(float(cleaned.replace('B', '')) * 1_000_000_000)
        else:
            return int(float(cleaned))
    except (ValueError, AttributeError):
        return 0


def clear_cache(symbol: Optional[str] = None):
    """Clear historical data cache"""
    global _history_cache, _cache_timestamps
    
    if symbol:
        # Clear specific symbol
        if symbol in _history_cache:
            del _history_cache[symbol]
        keys_to_delete = [k for k in _cache_timestamps if k.startswith(symbol)]
        for key in keys_to_delete:
            del _cache_timestamps[key]
        logger.info(f"🗑️ Cleared cache for {symbol}")
    else:
        # Clear all
        _history_cache = {}
        _cache_timestamps = {}
        logger.info("🗑️ Cleared all historical data cache")
