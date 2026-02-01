"""
SEC EDGAR Scraper - Company Filings (NO API KEY)

Scrapes SEC EDGAR for company filings:
- 10-K (Annual reports)
- 10-Q (Quarterly reports)
- 8-K (Current events)

Uses SEC's public API and RSS feeds.
Rate limit: 10 requests/second per SEC guidelines.
"""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from loguru import logger
import asyncio


class SECScraper:
    """
    Scrape SEC EDGAR filings without authentication.
    
    Features:
    - Company CIK lookup
    - Filing list retrieval
    - Direct filing download
    - Respects SEC rate limits (10/sec)
    """
    
    SOURCE_NAME = "sec_edgar"
    BASE_URL = "https://www.sec.gov"
    API_URL = "https://data.sec.gov"
    
    # Filing types
    FILING_TYPES = {
        "10-K": "Annual Report",
        "10-Q": "Quarterly Report",
        "8-K": "Current Report",
        "DEF 14A": "Proxy Statement",
        "13F": "Institutional Holdings",
        "S-1": "IPO Registration",
    }
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'QuantForge AI tanishq@quantforge.ai',  # SEC requires contact info
            'Accept-Encoding': 'gzip, deflate',
        }
        self.rate_limiter = asyncio.Semaphore(10)  # 10 concurrent requests max
        logger.info("SEC EDGAR scraper initialized (NO API KEY REQUIRED)")
    
    async def get_company_cik(self, ticker: str) -> Optional[str]:
        """
        Get company CIK (Central Index Key) from ticker.
        
        Args:
            ticker: Stock symbol (e.g., "AAPL")
        
        Returns:
            CIK string or None
        """
        url = f"{self.API_URL}/submissions/CIK{ticker}.json"
        
        try:
            async with self.rate_limiter:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url, headers=self.headers)
                    
                    if response.status_code == 404:
                        # Try company tickers endpoint
                        tickers_url = f"{self.API_URL}/files/company_tickers.json"
                        resp = await client.get(tickers_url, headers=self.headers)
                        tickers_data = resp.json()
                        
                        # Search for ticker
                        for cik, info in tickers_data.items():
                            if info.get('ticker', '').upper() == ticker.upper():
                                return str(info['cik_str']).zfill(10)
                        
                        return None
                    
                    response.raise_for_status()
                    data = response.json()
                    return data.get('cik')
            
        except Exception as e:
            logger.error(f"Failed to get CIK for {ticker}: {e}")
            return None
    
    async def get_filings(
        self,
        ticker: str,
        filing_type: str = "10-K",
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent filings for a company.
        
        Args:
            ticker: Stock symbol
            filing_type: Type of filing (10-K, 10-Q, 8-K)
            count: Number of filings to retrieve
        
        Returns:
            List of filing metadata dicts
        """
        cik = await self.get_company_cik(ticker)
        if not cik:
            logger.warning(f"No CIK found for {ticker}")
            return []
        
        # SEC submissions endpoint
        url = f"{self.API_URL}/submissions/CIK{cik.zfill(10)}.json"
        
        try:
            async with self.rate_limiter:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()
            
            data = response.json()
            recent_filings = data.get('filings', {}).get('recent', {})
            
            # Filter by filing type
            filings = []
            forms = recent_filings.get('form', [])
            dates = recent_filings.get('filingDate', [])
            accessions = recent_filings.get('accessionNumber', [])
            
            for i, form in enumerate(forms):
                if form == filing_type and len(filings) < count:
                    filings.append({
                        "ticker": ticker.upper(),
                        "cik": cik,
                        "filing_type": form,
                        "filing_date": dates[i],
                        "accession_number": accessions[i],
                        "url": f"{self.BASE_URL}/Archives/edgar/data/{cik}/{accessions[i].replace('-', '')}/{accessions[i]}.txt",
                        "source": self.SOURCE_NAME,
                    })
            
            logger.info(f"Found {len(filings)} {filing_type} filings for {ticker}")
            return filings
            
        except Exception as e:
            logger.error(f"Failed to get filings for {ticker}: {e}")
            return []
    
    async def download_filing(self, accession_number: str, cik: str) -> Optional[str]:
        """
        Download filing content.
        
        Args:
            accession_number: SEC accession number
            cik: Company CIK
        
        Returns:
            Filing text content or None
        """
        url = f"{self.BASE_URL}/Archives/edgar/data/{cik}/{accession_number.replace('-', '')}/{accession_number}.txt"
        
        try:
            async with self.rate_limiter:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()
            
            logger.info(f"Downloaded filing {accession_number}")
            return response.text
            
        except Exception as e:
            logger.error(f"Failed to download filing {accession_number}: {e}")
            return None


# Singleton instance
sec_scraper = SECScraper()

