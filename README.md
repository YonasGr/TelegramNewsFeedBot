# Telegram News Feed Bot

A powerful and feature-rich Telegram bot that aggregates content from various sources including RSS feeds, websites, and social media platforms, delivering personalized news updates directly to users.

## 🌟 Features

### Content Sources
- **📰 RSS/Atom Feeds** - Full support for standard RSS 2.0 and Atom feeds
- **🌐 Generic Websites** - Intelligent article extraction from any website
- **🐦 Twitter/X** - Via RSS alternatives (Nitter, etc.)
- **📺 YouTube Channels** - Automatic RSS feed detection
- **🔴 Reddit Subreddits** - Native RSS feed support
- **📘 Facebook Pages** - Placeholder (requires API access)
- **📸 Instagram Profiles** - Placeholder (requires API access)

### User Features
- **🔔 Smart Subscriptions** - Subscribe to specific sources of interest
- **📋 Source Discovery** - Browse and explore available content sources
- **⚙️ Personalized Settings** - Manage notification preferences
- **📊 Usage Statistics** - Track your reading habits
- **🌍 Multi-language Support** - Localized interface

### Admin Features
- **➕ Source Management** - Add and remove content sources
- **👥 User Management** - Monitor user activity and subscriptions
- **📈 Analytics Dashboard** - Comprehensive bot statistics
- **🔧 System Monitoring** - Health checks and error tracking
- **🔄 Manual Updates** - Force immediate source checking

### Technical Features
- **🚀 High Performance** - Asynchronous processing and caching
- **🛡️ Robust Error Handling** - Comprehensive retry logic and fallbacks
- **📝 Detailed Logging** - Full audit trail and debugging support
- **🔄 Automatic Updates** - Configurable polling intervals
- **💾 Persistent Storage** - SQLite/PostgreSQL database support
- **🧠 Smart Content Processing** - Intelligent article extraction and formatting

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- A Telegram Bot Token (get one from [@BotFather](https://t.me/BotFather))
- Redis server (optional, for FSM storage)
- SQLite or PostgreSQL database

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YonasGr/TelegramNewsFeedBot.git
   cd TelegramNewsFeedBot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize the database**
   ```bash
   python -c "from models.database import init_db; init_db()"
   ```

5. **Start the bot**
   ```bash
   python main.py
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321

# Database Configuration
DATABASE_URL=sqlite:///database.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/newsbot

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379/0

# Scraper Settings
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RETRY_DELAY=5
USER_AGENT=Mozilla/5.0 FeedAggregatorBot/1.0

# Scheduler Settings
SCHEDULER_INTERVAL=300
MAX_ITEMS_PER_UPDATE=5

# Content Settings
MAX_POST_LENGTH=4000
MEDIA_CACHE_DIR=media_cache

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs
```

### Database Setup

#### SQLite (Default)
```env
DATABASE_URL=sqlite:///database.db
```

#### PostgreSQL
```env
DATABASE_URL=postgresql://username:password@localhost:5432/newsbot
```

## 🤖 Bot Commands

### User Commands
- `/start` - Start the bot and show main menu
- `/help` - Display help information
- `/menu` - Show the main menu
- `/sources` - List all available sources
- `/subscriptions` - Manage your subscriptions

### Admin Commands
- `/add_source` - Add a new content source
- `/admin` - Access admin panel
- `/stats` - View bot statistics

## 📱 Usage Guide

### For Users

1. **Start the bot** by sending `/start`
2. **Browse sources** using the "📋 View Sources" button
3. **Subscribe** to interesting sources
4. **Manage subscriptions** in the "📊 My Subscriptions" menu
5. **Receive updates** automatically as new content is published

### For Administrators

1. **Add sources** using `/add_source` command
2. **Monitor bot health** via `/stats` command
3. **Manage users** through the admin panel
4. **Force updates** when needed

### Adding Sources

The bot supports various source types:

#### RSS Feeds
```
https://feeds.feedburner.com/TechCrunch
https://rss.cnn.com/rss/edition.rss
```

#### Websites
```
https://news.ycombinator.com/
https://www.reddit.com/r/technology
```

#### YouTube Channels
```
https://www.youtube.com/channel/UCBJycsmduvYEL83R_U4JriQ
```

#### Twitter (via alternatives)
```
https://twitter.com/username
# Will try Nitter and other RSS alternatives
```

## 🔧 Architecture

### Core Components

```
TelegramNewsFeedBot/
├── bot/
│   ├── handlers.py          # Message and callback handlers
│   └── keyboards.py         # Inline keyboard layouts
├── models/
│   ├── database.py          # SQLAlchemy models
│   └── schemas.py           # Pydantic schemas
├── services/
│   ├── scraper.py           # Content scraping service
│   ├── scheduler.py         # Periodic update scheduler
│   └── content_processor.py # Content formatting
├── utils/
│   └── logger.py            # Logging utilities
├── config.py                # Configuration management
├── main.py                  # Application entry point
└── requirements.txt         # Python dependencies
```

### Database Schema

#### Users Table
- User ID (Telegram user ID)
- Username, first name, last name
- Language preferences
- Activity tracking

#### Sources Table
- URL and source type
- Metadata (title, description)
- Status and error tracking
- Check statistics

#### Subscriptions Table
- User-source relationships
- Notification preferences
- Activity status

## 🛠️ Development

### Setting Up Development Environment

1. **Clone and install dependencies** (as above)
2. **Set up pre-commit hooks**
   ```bash
   pip install pre-commit
   pre-commit install
   ```
3. **Run tests**
   ```bash
   python -m pytest tests/
   ```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=. --cov-report=html
```

### Code Style

This project follows PEP 8 guidelines and uses:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Ensure all tests pass
6. Submit a pull request

## 📊 Monitoring and Logging

### Log Files
- Main application logs: `logs/telegramnewsfeedbot_YYYYMMDD.log`
- Error logs are highlighted for easy debugging
- Structured logging with timestamps and source information

### Health Monitoring
- Database connection status
- Scraper service health
- Scheduler operation status
- User activity metrics

## 🚨 Troubleshooting

### Common Issues

#### Bot Not Responding
1. Check if bot token is valid
2. Verify network connectivity
3. Check log files for errors

#### Sources Not Updating
1. Verify source URLs are accessible
2. Check scraper service logs
3. Test source manually using admin commands

#### Database Errors
1. Ensure database server is running
2. Check database URL configuration
3. Verify database permissions

#### Memory Issues
1. Monitor memory usage in logs
2. Adjust batch sizes in configuration
3. Consider using Redis for FSM storage

### Getting Help

- Check the [Issues](https://github.com/YonasGr/TelegramNewsFeedBot/issues) page
- Review the logs for detailed error information
- Enable debug logging for troubleshooting

## 🔒 Security Considerations

### API Keys and Tokens
- Never commit API keys to version control
- Use environment variables for sensitive data
- Rotate tokens regularly

### User Privacy
- Minimal data collection
- Secure database storage
- GDPR compliance considerations

### Rate Limiting
- Respectful scraping intervals
- Built-in retry logic with exponential backoff
- Configurable request timeouts

## 📋 Roadmap

### Planned Features
- [ ] **Multi-language Support** - Full internationalization
- [ ] **Custom Filters** - Keyword-based content filtering
- [ ] **Scheduled Digests** - Daily/weekly summary emails
- [ ] **AI-Powered Recommendations** - Smart content suggestions
- [ ] **Advanced Analytics** - User engagement metrics
- [ ] **Mobile App** - Companion mobile application
- [ ] **API Integration** - RESTful API for external access
- [ ] **Plugin System** - Extensible architecture for custom sources

### Social Media Integration
- **Twitter API v2** - Official API integration
- **Facebook Graph API** - Page content access
- **Instagram Basic Display** - Post retrieval
- **LinkedIn API** - Professional content feeds
- **TikTok API** - Video content updates

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [aiogram](https://github.com/aiogram/aiogram) - Modern Telegram Bot API framework
- [aiohttp](https://github.com/aio-libs/aiohttp) - Async HTTP client/server
- [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) - Database ORM
- [feedparser](https://github.com/kurtmckee/feedparser) - RSS/Atom feed parsing
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing

## 📞 Support

For support, feature requests, or bug reports:
- Create an [Issue](https://github.com/YonasGr/TelegramNewsFeedBot/issues)
- Check the [Wiki](https://github.com/YonasGr/TelegramNewsFeedBot/wiki) for documentation
- Join our [Community Chat](https://t.me/NewsFeedBotSupport) (coming soon)

---

Made with ❤️ by the News Feed Bot Team