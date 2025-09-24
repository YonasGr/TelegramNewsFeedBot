"""
Scheduling service for the Telegram News Feed Bot.

This module handles periodic checking of content sources and distributing
updates to subscribed users. Includes robust error handling, retry logic,
and rate limiting to ensure reliable operation.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

from models.database import Session, Source, Subscription
from services.scraper import ScraperService, ScraperError
from services.content_processor import process_content
from utils.logger import get_logger
from config import config

logger = get_logger("scheduler")


class SchedulerService:
    """
    Scheduling service that periodically checks sources for new content.
    
    This service manages the automated checking of all configured sources,
    processes new content, and distributes updates to subscribed users.
    """
    
    def __init__(self, bot):
        """
        Initialize the scheduler service.
        
        Args:
            bot: Telegram bot instance for sending messages
        """
        self.bot = bot
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        logger.info("SchedulerService initialized")
    
    async def start(self) -> None:
        """Start the scheduler service."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._run_scheduler())
        logger.info("Scheduler service started")
    
    async def stop(self) -> None:
        """Stop the scheduler service."""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("Scheduler service stopped")
    
    async def _run_scheduler(self) -> None:
        """Main scheduler loop that runs continuously."""
        logger.info(f"Starting scheduler loop with {config.SCHEDULER_INTERVAL}s interval")
        
        while self.is_running:
            try:
                await self._check_all_sources()
                await asyncio.sleep(config.SCHEDULER_INTERVAL)
            except asyncio.CancelledError:
                logger.info("Scheduler loop cancelled")
                break
            except Exception as e:
                logger.error(f"Unexpected error in scheduler loop: {e}")
                # Wait a bit before retrying to avoid rapid error loops
                await asyncio.sleep(60)
    
    async def _check_all_sources(self) -> None:
        """Check all active sources for new content."""
        start_time = datetime.utcnow()
        logger.info("Starting periodic source check")
        
        try:
            with Session() as session:
                # Get all active sources
                sources = session.query(Source).filter(Source.is_active == True).all()
                
                if not sources:
                    logger.info("No active sources to check")
                    return
                
                logger.info(f"Checking {len(sources)} active sources")
                
                # Process sources in batches to avoid overwhelming the system
                batch_size = 10
                for i in range(0, len(sources), batch_size):
                    batch = sources[i:i + batch_size]
                    await self._process_source_batch(batch, session)
                    
                    # Small delay between batches to be respectful
                    if i + batch_size < len(sources):
                        await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Error in source checking: {e}")
        
        finally:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Source check completed in {duration:.2f} seconds")
    
    async def _process_source_batch(self, sources: List[Source], session: Session) -> None:
        """
        Process a batch of sources concurrently.
        
        Args:
            sources: List of sources to process
            session: Database session
        """
        tasks = []
        for source in sources:
            task = asyncio.create_task(self._check_single_source(source, session))
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any exceptions that occurred
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error checking source {sources[i].url}: {result}")
    
    async def _check_single_source(self, source: Source, session: Session) -> None:
        """
        Check a single source for new content.
        
        Args:
            source: Source to check
            session: Database session
        """
        logger.debug(f"Checking source: {source.url} (type: {source.type})")
        
        try:
            # Update check timestamp
            source.last_checked = datetime.utcnow()
            source.check_count += 1
            
            # Scrape the source
            async with ScraperService() as scraper:
                items = await scraper.scrape_source(source.url, source.type)
            
            if not items:
                logger.debug(f"No items found from source {source.url}")
                session.commit()
                return
            
            # Filter for new items
            cutoff_time = source.last_updated or datetime.utcnow() - timedelta(hours=24)
            new_items = self._filter_new_items(items, cutoff_time)
            
            if new_items:
                logger.info(f"Found {len(new_items)} new items from {source.url}")
                
                # Send updates to subscribers
                await self._send_updates_to_subscribers(source, new_items, session)
                
                # Update source metadata
                source.last_updated = datetime.utcnow()
                source.error_count = 0  # Reset error count on success
            else:
                logger.debug(f"No new items from source {source.url}")
            
            session.commit()
            
        except ScraperError as e:
            logger.error(f"Scraping error for source {source.url}: {e}")
            source.error_count += 1
            
            # Disable source if too many consecutive errors
            if source.error_count >= 10:
                logger.warning(f"Disabling source {source.url} due to {source.error_count} consecutive errors")
                source.is_active = False
            
            session.commit()
            
        except Exception as e:
            logger.error(f"Unexpected error checking source {source.url}: {e}")
            source.error_count += 1
            session.commit()
    
    def _filter_new_items(self, items, cutoff_time: datetime) -> List:
        """
        Filter items to find new content since the cutoff time.
        
        Args:
            items: List of FeedItem objects
            cutoff_time: Only include items newer than this time
            
        Returns:
            List of new items
        """
        new_items = []
        
        for item in items:
            if not item.published_at:
                # If no publish date, consider it new
                new_items.append(item)
                continue
            
            try:
                # Try to parse the published date
                if 'T' in item.published_at:
                    pub_date = datetime.fromisoformat(item.published_at.replace('Z', '+00:00'))
                else:
                    # Handle other date formats as needed
                    pub_date = datetime.strptime(item.published_at, '%Y-%m-%d %H:%M:%S')
                
                if pub_date > cutoff_time:
                    new_items.append(item)
                    
            except (ValueError, TypeError) as e:
                logger.debug(f"Could not parse date '{item.published_at}': {e}")
                # If we can't parse the date, include the item to be safe
                new_items.append(item)
        
        return new_items
    
    async def _send_updates_to_subscribers(self, source: Source, items: List, session: Session) -> None:
        """
        Send new content updates to all subscribers of a source.
        
        Args:
            source: Source that has new content
            items: List of new FeedItem objects
            session: Database session
        """
        # Get all active subscriptions for this source
        subscriptions = session.query(Subscription).filter(
            Subscription.source_id == source.id,
            Subscription.is_active == True,
            Subscription.notification_enabled == True
        ).all()
        
        if not subscriptions:
            logger.debug(f"No active subscribers for source {source.url}")
            return
        
        logger.info(f"Sending updates to {len(subscriptions)} subscribers for source {source.url}")
        
        # Send each item to all subscribers
        for item in items[:config.MAX_ITEMS_PER_UPDATE]:  # Limit items per update
            formatted_content = process_content(item)
            
            for subscription in subscriptions:
                try:
                    await self.bot.send_message(
                        chat_id=subscription.user_id,
                        text=formatted_content,
                        parse_mode="HTML",
                        disable_web_page_preview=False
                    )
                    
                    # Update last notification time
                    subscription.last_notified = datetime.utcnow()
                    
                    # Add small delay to avoid rate limiting
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error sending update to user {subscription.user_id}: {e}")
                    
                    # If it's a blocked user error, we might want to handle it
                    if "blocked" in str(e).lower() or "chat not found" in str(e).lower():
                        logger.warning(f"User {subscription.user_id} appears to have blocked the bot")
                        # Optionally disable the subscription
                        # subscription.is_active = False
    
    async def force_check_source(self, source_id: int) -> bool:
        """
        Force an immediate check of a specific source.
        
        Args:
            source_id: ID of the source to check
            
        Returns:
            True if check was successful, False otherwise
        """
        try:
            with Session() as session:
                source = session.query(Source).filter(Source.id == source_id).first()
                
                if not source:
                    logger.error(f"Source with ID {source_id} not found")
                    return False
                
                logger.info(f"Force checking source: {source.url}")
                await self._check_single_source(source, session)
                return True
                
        except Exception as e:
            logger.error(f"Error in force check for source {source_id}: {e}")
            return False
    
    async def get_scheduler_stats(self) -> dict:
        """
        Get statistics about the scheduler service.
        
        Returns:
            Dictionary with scheduler statistics
        """
        with Session() as session:
            total_sources = session.query(Source).count()
            active_sources = session.query(Source).filter(Source.is_active == True).count()
            error_sources = session.query(Source).filter(Source.error_count > 0).count()
            total_subscriptions = session.query(Subscription).count()
            active_subscriptions = session.query(Subscription).filter(Subscription.is_active == True).count()
            
            return {
                "is_running": self.is_running,
                "check_interval": config.SCHEDULER_INTERVAL,
                "total_sources": total_sources,
                "active_sources": active_sources,
                "error_sources": error_sources,
                "total_subscriptions": total_subscriptions,
                "active_subscriptions": active_subscriptions
            }


# Legacy functions for backward compatibility
async def check_sources(bot) -> None:
    """
    Legacy function for checking sources.
    
    This function is maintained for backward compatibility.
    Use SchedulerService class for new implementations.
    """
    logger.warning("Using legacy check_sources function. Consider migrating to SchedulerService.")
    scheduler = SchedulerService(bot)
    await scheduler._check_all_sources()


async def send_updates(bot, source, items) -> None:
    """
    Legacy function for sending updates.
    
    This function is maintained for backward compatibility.
    Use SchedulerService class for new implementations.
    """
    logger.warning("Using legacy send_updates function. Consider migrating to SchedulerService.")
    scheduler = SchedulerService(bot)
    
    with Session() as session:
        await scheduler._send_updates_to_subscribers(source, items, session)


async def start_scheduler(bot) -> None:
    """
    Start the scheduler service (legacy interface).
    
    This function creates and starts a SchedulerService instance.
    The scheduler will run until the program is terminated.
    """
    logger.info("Starting scheduler service (legacy interface)")
    scheduler = SchedulerService(bot)
    await scheduler.start()
    
    # Keep the scheduler running
    try:
        while scheduler.is_running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Scheduler interrupted by user")
    finally:
        await scheduler.stop()
        logger.info("Scheduler service stopped")
