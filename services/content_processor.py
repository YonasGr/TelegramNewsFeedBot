from models.schemas import FeedItem
from config import config

def process_content(item: FeedItem) -> str:
    """Format content for Telegram"""
    source_emoji = {
        "twitter": "🐦",
        "facebook": "📘",
        "instagram": "📸",
        "rss": "📰",
        "website": "🌐"
    }.get(item.source_type, "📄")
    
    content = f"{source_emoji} <b>{item.title}</b>\n\n"
    content += f"{item.content}\n\n"
    content += f"🔗 <a href='{item.url}'>Read more</a>\n"
    
    if item.published_at:
        content += f"⏰ {item.published_at}\n"
    
    return content[:config.MAX_POST_LENGTH]
