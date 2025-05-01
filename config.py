import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")
    
    # Scraper settings
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    USER_AGENT = "Mozilla/5.0 FeedAggregatorBot/1.0"
    
    # Content settings
    MAX_POST_LENGTH = 4000  # Telegram message limit
    MEDIA_CACHE_DIR = "media_cache"

config = Config()
