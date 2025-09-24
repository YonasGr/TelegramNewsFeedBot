"""
Content scraping service for the Telegram News Feed Bot.

This module provides functionality to scrape content from various sources
including RSS feeds, social media platforms, and generic websites.
Includes robust error handling, retry logic, and rate limiting.
"""

import re
import asyncio
import aiohttp
import feedparser
from bs4 import BeautifulSoup
from typing import List, Optional
from urllib.parse import urlparse, urljoin
from datetime import datetime, timedelta

from models.schemas import FeedItem
from config import config
from utils.logger import get_logger

logger = get_logger("scraper")


class ScraperError(Exception):
    """Custom exception for scraping-related errors."""
    pass


class ScraperService:
    """
    Content scraping service that handles multiple source types.
    
    This service provides unified scraping functionality for RSS feeds,
    social media platforms, and generic websites with proper error handling
    and retry mechanisms.
    """
    
    def __init__(self):
        """Initialize the scraper service with HTTP session and configuration."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT),
            headers={"User-Agent": config.USER_AGENT},
            connector=aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
        )
        logger.info("ScraperService initialized")
    
    async def detect_source_type(self, url: str) -> str:
        """
        Detect the type of source based on URL patterns.
        
        Args:
            url: The URL to analyze
            
        Returns:
            Source type string (rss, twitter, facebook, instagram, website)
            
        Raises:
            ScraperError: If URL is invalid or detection fails
        """
        try:
            parsed_url = urlparse(url)
            if not parsed_url.netloc:
                raise ScraperError(f"Invalid URL: {url}")
                
            domain = parsed_url.netloc.lower()
            logger.debug(f"Detecting source type for domain: {domain}")
            
            # Social media platform detection
            if "twitter.com" in domain or "x.com" in domain:
                return "twitter"
            elif "facebook.com" in domain or "fb.com" in domain:
                return "facebook"
            elif "instagram.com" in domain:
                return "instagram"
            elif "youtube.com" in domain or "youtu.be" in domain:
                return "youtube"
            elif "reddit.com" in domain:
                return "reddit"
            
            # RSS feed detection by URL pattern
            if re.search(r"\.(rss|xml)$|/feed|/rss|/atom", url, re.I):
                return "rss"
            
            # Try to detect RSS feed by content
            try:
                return await self._detect_rss_by_content(url)
            except Exception as e:
                logger.debug(f"RSS content detection failed for {url}: {e}")
            
            return "website"
            
        except Exception as e:
            logger.error(f"Error detecting source type for {url}: {e}")
            raise ScraperError(f"Failed to detect source type: {e}")
    
    async def _detect_rss_by_content(self, url: str) -> str:
        """
        Try to detect RSS feed by analyzing page content.
        
        Args:
            url: URL to check
            
        Returns:
            "rss" if RSS feed detected, "website" otherwise
        """
        async with self.session.get(url) as response:
            if response.status != 200:
                return "website"
                
            content_type = response.headers.get('content-type', '').lower()
            if 'xml' in content_type or 'rss' in content_type:
                return "rss"
            
            text = await response.text()
            soup = BeautifulSoup(text, 'lxml')
            
            # Check for RSS/Atom feed indicators
            if soup.find('rss') or soup.find('feed') or soup.find('atom'):
                return "rss"
            
            # Look for RSS feed links in HTML
            rss_links = soup.find_all('link', type=['application/rss+xml', 'application/atom+xml'])
            if rss_links:
                return "rss"
            
            return "website"
    
    async def scrape_source(self, source_url: str, source_type: str) -> List[FeedItem]:
        """
        Scrape content from a source based on its type.
        
        Args:
            source_url: URL of the source to scrape
            source_type: Type of source (rss, twitter, etc.)
            
        Returns:
            List of FeedItem objects containing scraped content
            
        Raises:
            ScraperError: If scraping fails after all retries
        """
        logger.info(f"Scraping {source_type} source: {source_url}")
        
        for attempt in range(config.MAX_RETRIES + 1):
            try:
                if source_type == "rss":
                    return await self._scrape_rss(source_url)
                elif source_type == "twitter":
                    return await self._scrape_twitter(source_url)
                elif source_type == "facebook":
                    return await self._scrape_facebook(source_url)
                elif source_type == "instagram":
                    return await self._scrape_instagram(source_url)
                elif source_type == "youtube":
                    return await self._scrape_youtube(source_url)
                elif source_type == "reddit":
                    return await self._scrape_reddit(source_url)
                else:
                    return await self._scrape_website(source_url)
                    
            except Exception as e:
                logger.warning(f"Scraping attempt {attempt + 1} failed for {source_url}: {e}")
                
                if attempt < config.MAX_RETRIES:
                    delay = config.RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All scraping attempts failed for {source_url}")
                    raise ScraperError(f"Failed to scrape source after {config.MAX_RETRIES + 1} attempts: {e}")
    
    async def _scrape_rss(self, url: str) -> List[FeedItem]:
        """
        Scrape an RSS/Atom feed.
        
        Args:
            url: RSS feed URL
            
        Returns:
            List of FeedItem objects from the feed
        """
        async with self.session.get(url) as response:
            if response.status != 200:
                raise ScraperError(f"HTTP {response.status} error for RSS feed {url}")
            
            content = await response.text()
            feed = feedparser.parse(content)
            
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"Feed parser warning for {url}: {feed.bozo_exception}")
            
            items = []
            for entry in feed.entries[:config.MAX_ITEMS_PER_UPDATE]:
                # Clean up content
                description = entry.get('description', entry.get('summary', ''))
                content = self._clean_html_content(description)
                
                # Parse publication date
                published_at = ""
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published_at = datetime(*entry.published_parsed[:6]).isoformat()
                    except (ValueError, TypeError):
                        pass
                elif entry.get('published'):
                    published_at = entry.published
                
                items.append(FeedItem(
                    title=entry.get('title', 'No title'),
                    url=entry.get('link', url),
                    content=content,
                    published_at=published_at,
                    source_type="rss"
                ))
            
            logger.info(f"Scraped {len(items)} items from RSS feed {url}")
            return items
    
    async def _scrape_twitter(self, url: str) -> List[FeedItem]:
        """
        Scrape Twitter profile (placeholder implementation).
        
        Note: Twitter scraping is challenging due to API restrictions and authentication requirements.
        In production, you should use the official Twitter API v2 or a service like Nitter.
        
        Args:
            url: Twitter profile URL
            
        Returns:
            Empty list (placeholder implementation)
        """
        logger.warning(f"Twitter scraping is not fully implemented for {url}")
        logger.info("To implement Twitter scraping, consider:")
        logger.info("1. Using Twitter API v2 with proper authentication")
        logger.info("2. Using alternative services like Nitter (https://nitter.net)")
        logger.info("3. Using RSS feeds from services that convert Twitter to RSS")
        
        # Placeholder: Try to find alternative RSS feeds
        username = url.split('/')[-1].replace('@', '')
        alternative_feeds = [
            f"https://nitter.net/{username}/rss",
            f"https://twitrss.me/twitter_user_to_rss/?user={username}",
        ]
        
        for feed_url in alternative_feeds:
            try:
                logger.info(f"Trying alternative RSS feed: {feed_url}")
                return await self._scrape_rss(feed_url)
            except Exception as e:
                logger.debug(f"Alternative feed failed: {e}")
                continue
        
        return []
    
    async def _scrape_facebook(self, url: str) -> List[FeedItem]:
        """
        Scrape Facebook page (placeholder - requires API access).
        
        Facebook requires official API access through the Graph API.
        Alternative approaches may violate Terms of Service.
        
        Args:
            url: Facebook page URL
            
        Returns:
            Empty list with warning message
        """
        logger.warning(f"Facebook scraping is not implemented for {url}")
        logger.info("To implement Facebook scraping, you need:")
        logger.info("1. Facebook Graph API access token")
        logger.info("2. App review and approval from Facebook")
        logger.info("3. Compliance with Facebook's Platform Policy")
        logger.info("See: https://developers.facebook.com/docs/graph-api/")
        
        return [FeedItem(
            title="Facebook Scraping Not Available",
            url=url,
            content="Facebook scraping requires official API access. Please set up Facebook Graph API credentials.",
            published_at=datetime.now().isoformat(),
            source_type="facebook"
        )]
    
    async def _scrape_instagram(self, url: str) -> List[FeedItem]:
        """
        Scrape Instagram profile (placeholder - requires API access).
        
        Instagram requires official API access through the Instagram Basic Display API
        or Instagram Graph API for business accounts.
        
        Args:
            url: Instagram profile URL
            
        Returns:
            Empty list with warning message
        """
        logger.warning(f"Instagram scraping is not implemented for {url}")
        logger.info("To implement Instagram scraping, you need:")
        logger.info("1. Instagram Basic Display API or Instagram Graph API")
        logger.info("2. App review and approval from Meta")
        logger.info("3. User consent for accessing their content")
        logger.info("See: https://developers.facebook.com/docs/instagram-api/")
        
        return [FeedItem(
            title="Instagram Scraping Not Available",
            url=url,
            content="Instagram scraping requires official API access. Please set up Instagram API credentials.",
            published_at=datetime.now().isoformat(),
            source_type="instagram"
        )]
    
    async def _scrape_youtube(self, url: str) -> List[FeedItem]:
        """
        Scrape YouTube channel via RSS feed.
        
        YouTube provides RSS feeds for channels that can be used without API access.
        
        Args:
            url: YouTube channel URL
            
        Returns:
            List of FeedItem objects from the channel
        """
        try:
            # Extract channel ID from URL
            if "/channel/" in url:
                channel_id = url.split("/channel/")[1].split("/")[0]
            elif "/c/" in url or "/user/" in url:
                # For custom URLs, we'd need to resolve to channel ID
                # This is a simplified approach
                logger.warning(f"Custom YouTube URLs require additional resolution: {url}")
                return []
            else:
                logger.error(f"Unable to parse YouTube URL: {url}")
                return []
            
            # Use YouTube RSS feed
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            logger.info(f"Using YouTube RSS feed: {rss_url}")
            
            return await self._scrape_rss(rss_url)
            
        except Exception as e:
            logger.error(f"Error scraping YouTube channel {url}: {e}")
            return []
    
    async def _scrape_reddit(self, url: str) -> List[FeedItem]:
        """
        Scrape Reddit subreddit via RSS feed.
        
        Reddit provides RSS feeds for subreddits and user posts.
        
        Args:
            url: Reddit subreddit URL
            
        Returns:
            List of FeedItem objects from the subreddit
        """
        try:
            # Convert Reddit URL to RSS feed
            if url.endswith('/'):
                rss_url = url + ".rss"
            else:
                rss_url = url + "/.rss"
            
            logger.info(f"Using Reddit RSS feed: {rss_url}")
            return await self._scrape_rss(rss_url)
            
        except Exception as e:
            logger.error(f"Error scraping Reddit URL {url}: {e}")
            return []
    
    async def _scrape_website(self, url: str) -> List[FeedItem]:
        """
        Scrape a generic website by looking for article-like content.
        
        Args:
            url: Website URL to scrape
            
        Returns:
            List of FeedItem objects found on the website
        """
        async with self.session.get(url) as response:
            if response.status != 200:
                raise ScraperError(f"HTTP {response.status} error for website {url}")
            
            text = await response.text()
            soup = BeautifulSoup(text, 'lxml')
            
            # Try to find article-like elements
            article_selectors = [
                'article',
                '.article',
                '.post',
                '.entry',
                '.content article',
                '[role="article"]',
                '.news-item',
                '.blog-post'
            ]
            
            articles = []
            for selector in article_selectors:
                found = soup.select(selector)
                if found:
                    articles.extend(found)
                    break
            
            # Fallback to common content containers
            if not articles:
                articles = soup.find_all(['div'], class_=re.compile(r'content|post|article|entry', re.I))
            
            # Final fallback to paragraphs
            if not articles:
                articles = soup.find_all('p')
            
            items = []
            page_title = soup.title.string.strip() if soup.title else "Website Update"
            
            for i, article in enumerate(articles[:config.MAX_ITEMS_PER_UPDATE]):
                text_content = article.get_text(strip=True)
                
                # Only include substantial content
                if len(text_content) < 100:
                    continue
                
                # Try to find a title within the article
                title_elem = article.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                title = title_elem.get_text(strip=True) if title_elem else f"{page_title} - Item {i+1}"
                
                # Try to find a link
                link_elem = article.find('a', href=True)
                item_url = urljoin(url, link_elem['href']) if link_elem else url
                
                # Clean and truncate content
                content = self._clean_html_content(text_content)
                if len(content) > 500:
                    content = content[:500] + "..."
                
                items.append(FeedItem(
                    title=title,
                    url=item_url,
                    content=content,
                    published_at="",
                    source_type="website"
                ))
            
            logger.info(f"Scraped {len(items)} items from website {url}")
            return items
    
    def _clean_html_content(self, content: str) -> str:
        """
        Clean HTML content by removing tags and normalizing whitespace.
        
        Args:
            content: Raw HTML content
            
        Returns:
            Cleaned text content
        """
        if not content:
            return ""
        
        # Parse HTML and extract text
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and normalize whitespace
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    async def close(self) -> None:
        """
        Clean up resources by closing the HTTP session.
        
        This method should be called when the scraper service is no longer needed
        to ensure proper cleanup of network connections.
        """
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("ScraperService session closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.close()
