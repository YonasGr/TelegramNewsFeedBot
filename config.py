"""
Configuration settings for the Telegram News Feed Bot.

This module handles all environment variables and application settings,
providing a centralized configuration management system.
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Application configuration class.
    
    Manages all configuration settings including bot credentials,
    database connections, scraper settings, and content limitations.
    """
    
    # Bot credentials
    BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # Admin user IDs (comma-separated in env)
    ADMIN_IDS: List[int] = [
        int(id_str.strip()) for id_str in os.getenv("ADMIN_IDS", "").split(",") 
        if id_str.strip().isdigit()
    ]
    
    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///database.db")
    
    # Redis configuration for FSM storage
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Scraper settings
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    USER_AGENT: str = os.getenv("USER_AGENT", "Mozilla/5.0 FeedAggregatorBot/1.0")
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", "5"))  # seconds between retries
    
    # Content settings
    MAX_POST_LENGTH: int = int(os.getenv("MAX_POST_LENGTH", "4000"))  # Telegram message limit
    MEDIA_CACHE_DIR: str = os.getenv("MEDIA_CACHE_DIR", "media_cache")
    
    # Scheduler settings
    SCHEDULER_INTERVAL: int = int(os.getenv("SCHEDULER_INTERVAL", "300"))  # 5 minutes default
    MAX_ITEMS_PER_UPDATE: int = int(os.getenv("MAX_ITEMS_PER_UPDATE", "5"))
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate required configuration settings.
        
        Raises:
            ValueError: If required settings are missing or invalid
        """
        if not cls.BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        if not cls.ADMIN_IDS:
            raise ValueError("At least one ADMIN_ID must be configured")
        
        if cls.REQUEST_TIMEOUT <= 0:
            raise ValueError("REQUEST_TIMEOUT must be positive")
        
        if cls.MAX_RETRIES < 0:
            raise ValueError("MAX_RETRIES cannot be negative")


# Global configuration instance
config = Config()
