import re
import aiohttp
import feedparser
from bs4 import BeautifulSoup
from typing import Optional, Literal
from urllib.parse import urlparse
from models.schemas import FeedItem
from config import config

class ScraperService:
    def __init__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT),
            headers={"User-Agent": config.USER_AGENT}
        )
    
    async def detect_source_type(self, url: str) -> str:
        """Detect the type of source based on URL patterns"""
        domain = urlparse(url).netloc.lower()
        
        if "twitter.com" in domain or "x.com" in domain:
            return "twitter"
        elif "facebook.com" in domain:
            return "facebook"
        elif "instagram.com" in domain:
            return "instagram"
        elif re.search(r"\.rss$|feed|atom", url, re.I):
            return "rss"
        else:
            # Try to detect RSS feed
            try:
                async with self.session.get(url) as response:
                    text = await response.text()
                    soup = BeautifulSoup(text, 'lxml')
                    if soup.find('rss') or soup.find('feed'):
                        return "rss"
            except:
                pass
            
            return "website"
    
    async def scrape_source(self, source_url: str, source_type: str) -> list[FeedItem]:
        """Scrape content from a source based on its type"""
        if source_type == "rss":
            return await self._scrape_rss(source_url)
        elif source_type == "twitter":
            return await self._scrape_twitter(source_url)
        elif source_type == "facebook":
            return await self._scrape_facebook(source_url)
        elif source_type == "instagram":
            return await self._scrape_instagram(source_url)
        else:
            return await self._scrape_website(source_url)
    
    async def _scrape_rss(self, url: str) -> list[FeedItem]:
        """Scrape an RSS/Atom feed"""
        async with self.session.get(url) as response:
            content = await response.text()
            feed = feedparser.parse(content)
            
            items = []
            for entry in feed.entries:
                items.append(FeedItem(
                    title=entry.get('title', 'No title'),
                    url=entry.get('link', url),
                    content=entry.get('description', ''),
                    published_at=entry.get('published', ''),
                    source_type="rss"
                ))
            
            return items
    
    async def _scrape_twitter(self, url: str) -> list[FeedItem]:
        """Scrape Twitter profile (using unofficial API)"""
        # Note: Twitter scraping is challenging due to API restrictions
        # In production, you'd need to use their official API or a proxy service
        profile = url.split('/')[-1]
        api_url = f"https://api.twitter.com/2/users/by/username/{profile}"
        
        # This is a placeholder - you'd need proper authentication
        async with self.session.get(api_url) as response:
            data = await response.json()
            
            # Process tweets
            items = []
            for tweet in data.get('data', []):
                items.append(FeedItem(
                    title=f"Tweet from {profile}",
                    url=f"https://twitter.com/{profile}/status/{tweet['id']}",
                    content=tweet.get('text', ''),
                    published_at=tweet.get('created_at', ''),
                    source_type="twitter"
                ))
            
            return items
    
    async def _scrape_facebook(self, url: str) -> list[FeedItem]:
        """Scrape Facebook page (placeholder - requires API access)"""
        # Facebook requires official API access
        return []
    
    async def _scrape_instagram(self, url: str) -> list[FeedItem]:
        """Scrape Instagram profile (placeholder - requires API access)"""
        # Instagram requires official API access
        return []
    
    async def _scrape_website(self, url: str) -> list[FeedItem]:
        """Scrape a generic website by looking for article-like content"""
        async with self.session.get(url) as response:
            text = await response.text()
            soup = BeautifulSoup(text, 'lxml')
            
            # Try to find article-like elements
            articles = soup.find_all(['article', 'div.article', 'div.post'])
            if not articles:
                articles = soup.find_all(['p', 'div.content'])
            
            items = []
            for article in articles[:5]:  # Limit to 5 items
                text = article.get_text(strip=True)
                if len(text) > 100:  # Only include substantial content
                    items.append(FeedItem(
                        title=soup.title.string if soup.title else "Website Update",
                        url=url,
                        content=text[:500] + "..." if len(text) > 500 else text,
                        published_at="",
                        source_type="website"
                    ))
            
            return items
    
    async def close(self):
        await self.session.close()
