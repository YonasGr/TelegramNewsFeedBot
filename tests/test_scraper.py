"""
Tests for the scraper service.

This module contains tests for the content scraping functionality,
including RSS feeds, website scraping, and source detection.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from services.scraper import ScraperService, ScraperError
from models.schemas import FeedItem


class TestScraperService:
    """Test the scraper service functionality."""
    
    @pytest.fixture
    async def scraper(self):
        """Create a scraper service instance for testing."""
        scraper = ScraperService()
        yield scraper
        await scraper.close()
    
    def test_source_type_detection_twitter(self, scraper):
        """Test Twitter URL detection."""
        urls = [
            "https://twitter.com/username",
            "https://x.com/username",
            "https://www.twitter.com/username/",
        ]
        
        for url in urls:
            result = asyncio.run(scraper.detect_source_type(url))
            assert result == "twitter"
    
    def test_source_type_detection_facebook(self, scraper):
        """Test Facebook URL detection."""
        urls = [
            "https://facebook.com/page",
            "https://www.facebook.com/page/",
            "https://fb.com/page"
        ]
        
        for url in urls:
            result = asyncio.run(scraper.detect_source_type(url))
            assert result == "facebook"
    
    def test_source_type_detection_instagram(self, scraper):
        """Test Instagram URL detection."""
        urls = [
            "https://instagram.com/username",
            "https://www.instagram.com/username/",
        ]
        
        for url in urls:
            result = asyncio.run(scraper.detect_source_type(url))
            assert result == "instagram"
    
    def test_source_type_detection_youtube(self, scraper):
        """Test YouTube URL detection."""
        urls = [
            "https://youtube.com/channel/UCxxx",
            "https://www.youtube.com/channel/UCxxx",
            "https://youtu.be/video_id"
        ]
        
        for url in urls:
            result = asyncio.run(scraper.detect_source_type(url))
            assert result == "youtube"
    
    def test_source_type_detection_reddit(self, scraper):
        """Test Reddit URL detection."""
        urls = [
            "https://reddit.com/r/technology",
            "https://www.reddit.com/r/python/",
        ]
        
        for url in urls:
            result = asyncio.run(scraper.detect_source_type(url))
            assert result == "reddit"
    
    def test_source_type_detection_rss(self, scraper):
        """Test RSS URL detection by pattern."""
        urls = [
            "https://example.com/feed.rss",
            "https://example.com/feed.xml",
            "https://example.com/rss/",
            "https://example.com/atom.xml",
            "https://example.com/feeds/all.atom"
        ]
        
        for url in urls:
            result = asyncio.run(scraper.detect_source_type(url))
            assert result == "rss"
    
    def test_invalid_url_detection(self, scraper):
        """Test detection with invalid URLs."""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "",
            "javascript:alert('xss')"
        ]
        
        for url in invalid_urls:
            with pytest.raises(ScraperError):
                asyncio.run(scraper.detect_source_type(url))
    
    @patch('services.scraper.feedparser.parse')
    async def test_rss_scraping_success(self, mock_feedparser, scraper):
        """Test successful RSS feed scraping."""
        # Mock feedparser response
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': 'Test Article 1',
                'link': 'https://example.com/article1',
                'description': 'This is test article 1',
                'published': '2024-01-01T12:00:00Z'
            },
            {
                'title': 'Test Article 2', 
                'link': 'https://example.com/article2',
                'description': 'This is test article 2',
                'published': '2024-01-02T12:00:00Z'
            }
        ]
        mock_feedparser.return_value = mock_feed
        
        # Mock aiohttp response
        with patch.object(scraper.session, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="<rss><channel></channel></rss>")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await scraper._scrape_rss("https://example.com/feed.rss")
            
            assert len(result) == 2
            assert result[0].title == "Test Article 1"
            assert result[0].url == "https://example.com/article1"
            assert result[0].source_type == "rss"
            assert result[1].title == "Test Article 2"
    
    async def test_rss_scraping_http_error(self, scraper):
        """Test RSS scraping with HTTP error."""
        with patch.object(scraper.session, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(ScraperError, match="HTTP 404"):
                await scraper._scrape_rss("https://example.com/feed.rss")
    
    async def test_website_scraping_success(self, scraper):
        """Test successful website scraping."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Website</title></head>
        <body>
            <article>
                <h2>Article Title 1</h2>
                <p>This is a test article with substantial content that should be extracted by the scraper. It contains enough text to meet the minimum content length requirement.</p>
                <a href="/article1">Read more</a>
            </article>
            <article>
                <h3>Article Title 2</h3>
                <p>This is another test article with enough content to be included in the scraping results. The scraper should extract this content successfully.</p>
                <a href="/article2">Read more</a>
            </article>
        </body>
        </html>
        """
        
        with patch.object(scraper.session, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=html_content)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await scraper._scrape_website("https://example.com")
            
            assert len(result) >= 1  # Should extract at least one article
            assert result[0].source_type == "website"
            assert result[0].url.startswith("https://example.com")
            assert len(result[0].content) >= 100  # Substantial content
    
    async def test_website_scraping_no_content(self, scraper):
        """Test website scraping with no substantial content."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Empty Website</title></head>
        <body>
            <p>Short</p>
            <p>Too short</p>
        </body>
        </html>
        """
        
        with patch.object(scraper.session, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=html_content)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await scraper._scrape_website("https://example.com")
            
            # Should return empty list if no substantial content found
            assert len(result) == 0
    
    async def test_html_content_cleaning(self, scraper):
        """Test HTML content cleaning functionality."""
        dirty_html = """
        <div>
            <script>alert('xss')</script>
            <style>body { color: red; }</style>
            <p>This is clean content.</p>
            <p>Multiple    spaces   and
            
            newlines should be normalized.</p>
        </div>
        """
        
        cleaned = scraper._clean_html_content(dirty_html)
        
        assert "alert('xss')" not in cleaned
        assert "color: red" not in cleaned
        assert "This is clean content." in cleaned
        assert "Multiple spaces and newlines should be normalized." in cleaned
    
    async def test_scraper_retry_logic(self, scraper):
        """Test retry logic on failures."""
        with patch('services.scraper.config.MAX_RETRIES', 2), \
             patch('services.scraper.config.RETRY_DELAY', 0.1):
            
            with patch.object(scraper, '_scrape_rss') as mock_scrape:
                # First two calls fail, third succeeds
                mock_scrape.side_effect = [
                    Exception("Network error"),
                    Exception("Timeout error"),
                    [FeedItem(title="Success", url="http://example.com", content="Test", published_at="", source_type="rss")]
                ]
                
                result = await scraper.scrape_source("https://example.com/feed.rss", "rss")
                
                assert len(result) == 1
                assert result[0].title == "Success"
                assert mock_scrape.call_count == 3
    
    async def test_scraper_max_retries_exceeded(self, scraper):
        """Test behavior when max retries are exceeded."""
        with patch('services.scraper.config.MAX_RETRIES', 1), \
             patch('services.scraper.config.RETRY_DELAY', 0.1):
            
            with patch.object(scraper, '_scrape_rss') as mock_scrape:
                mock_scrape.side_effect = Exception("Persistent error")
                
                with pytest.raises(ScraperError, match="Failed to scrape source after"):
                    await scraper.scrape_source("https://example.com/feed.rss", "rss")
                
                assert mock_scrape.call_count == 2  # Initial attempt + 1 retry
    
    async def test_facebook_placeholder(self, scraper):
        """Test Facebook scraping placeholder."""
        result = await scraper._scrape_facebook("https://facebook.com/page")
        
        assert len(result) == 1
        assert "Facebook Scraping Not Available" in result[0].title
        assert "requires official API access" in result[0].content
    
    async def test_instagram_placeholder(self, scraper):
        """Test Instagram scraping placeholder."""
        result = await scraper._scrape_instagram("https://instagram.com/user")
        
        assert len(result) == 1
        assert "Instagram Scraping Not Available" in result[0].title
        assert "requires official API access" in result[0].content
    
    async def test_youtube_rss_conversion(self, scraper):
        """Test YouTube channel RSS feed conversion."""
        channel_url = "https://youtube.com/channel/UCxxxxxxxxxxxxx"
        
        with patch.object(scraper, '_scrape_rss') as mock_scrape_rss:
            mock_scrape_rss.return_value = [
                FeedItem(title="Video 1", url="https://youtube.com/watch?v=xxx", content="Description", published_at="", source_type="rss")
            ]
            
            result = await scraper._scrape_youtube(channel_url)
            
            assert len(result) == 1
            mock_scrape_rss.assert_called_once()
            called_url = mock_scrape_rss.call_args[0][0]
            assert "feeds/videos.xml" in called_url
            assert "channel_id=UCxxxxxxxxxxxxx" in called_url
    
    async def test_reddit_rss_conversion(self, scraper):
        """Test Reddit subreddit RSS feed conversion."""
        subreddit_url = "https://reddit.com/r/technology"
        
        with patch.object(scraper, '_scrape_rss') as mock_scrape_rss:
            mock_scrape_rss.return_value = [
                FeedItem(title="Post 1", url="https://reddit.com/post1", content="Content", published_at="", source_type="rss")
            ]
            
            result = await scraper._scrape_reddit(subreddit_url)
            
            assert len(result) == 1
            mock_scrape_rss.assert_called_once()
            called_url = mock_scrape_rss.call_args[0][0]
            assert called_url == "https://reddit.com/r/technology/.rss"


if __name__ == "__main__":
    pytest.main([__file__])