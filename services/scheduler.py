import asyncio
from datetime import datetime, timedelta
from models.database import Session, Source
from services.scraper import ScraperService
from services.content_processor import process_content
from utils.logger import logger

async def check_sources(bot):
    """Check all sources for new content"""
    logger.info("Starting source checks...")
    
    with Session() as session:
        sources = session.query(Source).all()
        scraper = ScraperService()
        
        for source in sources:
            try:
                items = await scraper.scrape_source(source.url, source.type)
                new_items = [item for item in items if not item.published_at or 
                           datetime.strptime(item.published_at, '%Y-%m-%dT%H:%M:%SZ') > source.last_checked]
                
                if new_items:
                    logger.info(f"Found {len(new_items)} new items from {source.url}")
                    await send_updates(bot, source, new_items)
                    
                    # Update last checked time
                    source.last_checked = datetime.utcnow()
                    session.commit()
            except Exception as e:
                logger.error(f"Error checking source {source.url}: {str(e)}")
        
        await scraper.close()

async def send_updates(bot, source, items):
    """Send new content to subscribers"""
    with Session() as session:
        subscriptions = session.query(Subscription).filter(Subscription.source_id == source.id).all()
        
        for item in items:
            formatted = process_content(item)
            
            for sub in subscriptions:
                try:
                    await bot.send_message(
                        chat_id=sub.user_id,
                        text=formatted,
                        disable_web_page_preview=False
                    )
                except Exception as e:
                    logger.error(f"Error sending to user {sub.user_id}: {str(e)}")

async def start_scheduler(bot):
    """Run periodic checks"""
    while True:
        await check_sources(bot)
        await asyncio.sleep(300)  # Check every 5 minutes
