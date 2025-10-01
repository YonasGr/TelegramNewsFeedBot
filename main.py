"""
Main entry point for the Telegram News Feed Bot.

This module initializes and starts the bot with all necessary components
including handlers, scheduler, and database connections.
"""

import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from bot.handlers import setup_handlers
from utils.logger import setup_logger, logger
from config import config
from models.database import init_db
from services.scheduler import SchedulerService


async def main():
    """
    Main function that initializes and starts the bot.
    
    Sets up logging, validates configuration, initializes database,
    configures bot components, and starts the polling loop.
    """
    try:
        # Set up logging
        setup_logger(level=config.LOG_LEVEL)
        logger.info("Starting Telegram News Feed Bot...")
        
        # Validate configuration
        try:
            config.validate()
            logger.info("Configuration validated successfully")
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            logger.error("Please check your environment variables and try again.")
            sys.exit(1)
        
        # Initialize database
        try:
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            sys.exit(1)
        
        # Set up FSM storage
        storage = None
        try:
            # Try Redis first with async connection test
            storage = RedisStorage.from_url(config.REDIS_URL)
            # Test the connection by creating a dummy key
            await storage.redis.ping()
            logger.info("✓ Successfully connected to Redis for FSM storage")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            logger.info("Falling back to in-memory storage (data will not persist across restarts)")
            storage = MemoryStorage()
        
        # Initialize bot and dispatcher with DefaultBotProperties for aiogram 3.7+
        bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        dp = Dispatcher(storage=storage)
        
        # Set up handlers
        setup_handlers(dp)
        logger.info("Bot handlers configured")
        
        # Initialize and start scheduler
        scheduler = SchedulerService(bot)
        scheduler_task = asyncio.create_task(scheduler.start())
        logger.info("Scheduler service started")
        
        try:
            # Start bot polling
            logger.info("Starting bot polling...")
            await dp.start_polling(bot)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Error during bot polling: {e}")
        finally:
            # Clean shutdown
            logger.info("Shutting down...")
            await scheduler.stop()
            scheduler_task.cancel()
            
            try:
                await scheduler_task
            except asyncio.CancelledError:
                pass
            
            await bot.session.close()
            logger.info("Bot shutdown complete")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
