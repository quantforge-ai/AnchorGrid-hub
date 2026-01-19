"""
News RSS Feed Scraper (NO API KEY)

Replaces NewsAPI with free RSS feeds from:
- Reuters
- Bloomberg
- CNBC
- MarketWatch
- Yahoo Finance
- Company investor relations

Zero cost, unlimited usage.
"""
import httpx
import feedparser
from typing import Optional, Dict, Any, List
from datetime import datetime
from loguru import logger
from bs4 import BeautifulSoup


class NewsRSSScraper:
    """
    Scrape news from public RSS feeds.
    
    Sources:
    - Reuters Business
    - Bloomberg Markets
    - CNBC Markets
    - MarketWatch
    - Yahoo Finance
    """
    
    SOURCE_NAME = "news_rss"
    
    RSS_FEEDS = {
        "reuters_business": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
        "bloomberg_markets": "https://www.bloomberg.com/feed/podcast/markets-daily.xml",
        "cnbc_markets": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
        "marketwatch_topstories": "http://feeds.marketwatch.com/marketwatch/topstories/",
        "yahoo_finance": "https://finance.yahoo.com/news/rssindex",
        "seeking_alpha": "https://seekingalpha.com/feed.xml",
    }
    
    def __init__(self):
        self.headers = {'User-Agent': 'QuantForge AI'}
        logger.info("News RSS scraper initialized (NO API KEY)")
    
    async def get_feed(self, feed_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch articles from an RSS feed.
        
        Args:
            feed_name: Name of feed (e.g., "reuters_business")
            limit: Max articles to return
        
        Returns:
            List of article dicts
        """
        url = self.RSS_FEEDS.get(feed_name)
        if not url:
            logger.warning(f"Unknown feed: {feed_name}")
            return []
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
            
            # Parse RSS feed
            feed = feedparser.parse(response.text)
            
            articles = []
            for entry in feed.entries[:limit]:
                try:
                    # Parse published date
                    published = entry.get('published_parsed')
                    if published:
                        pub_date = datetime(*published[:6])
                    else:
                        pub_date = datetime.now()
                    
                    articles.append({
                        "title": entry.get('title', ''),
                        "summary": entry.get('summary', ''),
                        "url": entry.get('link', ''),
                        "published_at": pub_date.isoformat(),
                        "source": feed_name,
                    })
                except Exception as e:
                    logger.debug(f"Failed to parse entry: {e}")
                    continue
            
            logger.info(f"Fetched {len(articles)} articles from {feed_name}")
            return articles
            
        except Exception as e:
            logger.error(f"Failed to fetch {feed_name}: {e}")
            return []
    
    async def get_all_feeds(self, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch from all RSS feeds.
        
        Args:
            limit: Articles per feed
        
        Returns:
            Dict mapping feed_name -> articles
        """
        results = {}
        
        for feed_name in self.RSS_FEEDS.keys():
            articles = await self.get_feed(feed_name, limit)
            results[feed_name] = articles
        
        total = sum(len(articles) for articles in results.values())
        logger.info(f"Fetched {total} total articles from {len(results)} feeds")
        
        return results
    
    async def search_ticker_news(
        self,
        ticker: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search news for a specific ticker across all feeds.
        
        Args:
            ticker: Stock symbol
            limit: Max total articles
        
        Returns:
            List of relevant articles
        """
        all_articles = []
        
        # Get from all feeds
        feed_results = await self.get_all_feeds(limit=50)
        
        # Filter by ticker
        ticker_upper = ticker.upper()
        for feed_name, articles in feed_results.items():
            for article in articles:
                title = article.get('title', '').upper()
                summary = article.get('summary', '').upper()
                
                if ticker_upper in title or ticker_upper in summary:
                    article['ticker'] = ticker.upper()
                    all_articles.append(article)
        
        # Sort by date
        all_articles.sort(
            key=lambda x: x.get('published_at', ''),
            reverse=True
        )
        
        logger.info(f"Found {len(all_articles[:limit])} articles for {ticker}")
        return all_articles[:limit]


# Singleton instance
news_rss_scraper = NewsRSSScraper()

