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
- SQLite or PostgreSQL database
- Redis server (optional, recommended for production - see Configuration section)

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

## 🐳 Docker Installation (Recommended)

Docker provides an isolated environment and simplified deployment. Choose one of the following methods:

### Option 1: Quick Start with Docker Compose

1. **Clone the repository**
   ```bash
   git clone https://github.com/YonasGr/TelegramNewsFeedBot.git
   cd TelegramNewsFeedBot
   ```

2. **Configure environment variables**
   ```bash
   cp .env.docker .env
   # Edit .env with your bot token and admin IDs
   nano .env
   ```

3. **Start with Docker Compose** (choose one)
   ```bash
   # Using the convenience script (recommended)
   ./docker-run.sh prod     # Production setup
   ./docker-run.sh dev      # Development setup
   
   # Or manually with docker compose
   docker compose up -d                                    # Production
   docker compose -f docker-compose.dev.yml up -d        # Development
   ```

### Option 2: Docker Build and Run

1. **Build the Docker image**
   ```bash
   docker build -t telegram-news-bot .
   ```

2. **Create required directories**
   ```bash
   mkdir -p data logs media_cache
   ```

3. **Run the container**
   ```bash
   docker run -d \
     --name telegram-news-bot \
     --env-file .env \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/logs:/app/logs \
     -v $(pwd)/media_cache:/app/media_cache \
     telegram-news-bot
   ```

### Docker Environment Variables

All environment variables from the `.env.example` file are supported. Key variables for Docker:

```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321

# Database (Docker Compose handles this)
DATABASE_URL=sqlite:///data/database.db

# Redis (Docker Compose handles this automatically)
# When using docker-compose.yml, Redis is included and configured
# The bot will automatically connect to the Redis service
REDIS_URL=redis://redis:6379/0

# For standalone Docker (without docker-compose):
# - Comment out REDIS_URL to use in-memory storage
# - Or point to an external Redis instance
```

**Note**: The production docker-compose configuration includes Redis by default for optimal performance and state persistence.

### Managing the Docker Deployment

```bash
# Using the convenience script (recommended)
./docker-run.sh status     # Check service status
./docker-run.sh logs       # View bot logs
./docker-run.sh stop       # Stop all services
./docker-run.sh help       # Show all available commands

# Or manually with docker compose
docker compose logs -f telegram-bot    # View logs
docker compose down                     # Stop services
docker compose pull && docker compose up -d --build  # Update and restart
docker compose exec telegram-bot bash  # Access container shell
```

### Development with Docker

The `docker-compose.dev.yml` includes additional services for development:

- **PostgreSQL**: Database server with sample data
- **pgAdmin**: Database management interface
- **Redis Commander**: Redis monitoring and management
- **Volume Mounting**: Live code changes without rebuilds

```bash
# Start development environment
./docker-run.sh dev
# OR
docker compose -f docker-compose.dev.yml up -d

# Access management interfaces
# pgAdmin: http://localhost:8080 (admin@newsbot.dev / admin)
# Redis Commander: http://localhost:8081

# View logs in real-time
./docker-run.sh logs
```

### Docker Environment Variables

All environment variables work the same in Docker. Key differences:

| Variable | Docker Default | Notes |
|----------|----------------|-------|
| `DATABASE_URL` | `sqlite:///data/database.db` | Uses mounted volume |
| `REDIS_URL` | `redis://redis:6379/0` | Points to Redis container |
| `LOG_DIR` | `logs` | Mounted volume for persistence |
| `MEDIA_CACHE_DIR` | `media_cache` | Mounted volume for persistence |

### Production Deployment

For production deployments, consider the following best practices:

#### 1. Use Docker Compose with External Volumes
```bash
# Create named volumes for persistence
docker volume create telegram-bot-data
docker volume create telegram-bot-logs

# Update docker-compose.yml to use named volumes
```

#### 2. Configure Logging Properly
```bash
# View logs with rotation
docker compose logs --tail=100 -f telegram-bot

# Set appropriate LOG_LEVEL in .env
LOG_LEVEL=INFO  # Use WARNING or ERROR for production to reduce log volume
```

#### 3. Enable Redis for State Persistence
Redis is **highly recommended** for production to ensure:
- FSM states persist across restarts
- No loss of user conversation context during deployments
- Support for horizontal scaling if needed

```env
# Production: Always use Redis
REDIS_URL=redis://redis:6379/0
```

#### 4. Monitor Resource Usage
```bash
# Check resource usage
docker stats telegram-news-bot

# Monitor logs for errors
docker compose logs -f telegram-bot | grep ERROR
```

#### 5. Set Up Health Monitoring
```bash
# Check container health
docker compose ps

# The bot includes a built-in health check that validates:
# - Configuration is valid
# - Database is accessible
# - Bot can start successfully
```

#### 6. Security Best Practices
- Store sensitive environment variables securely (use Docker secrets or external secret management)
- Run the bot as a non-root user (already configured in Dockerfile)
- Keep dependencies up to date: `docker compose pull && docker compose up -d --build`
- Regularly backup your database and configuration
- Use HTTPS if exposing any web interfaces
- Limit admin access to trusted user IDs only

#### 7. Backup Strategy
```bash
# Backup database
docker cp telegram-news-bot:/app/data/database.db ./backups/database-$(date +%Y%m%d).db

# Backup logs (optional)
docker cp telegram-news-bot:/app/logs ./backups/logs-$(date +%Y%m%d)/
```

#### 8. Update and Restart Procedure
```bash
# 1. Pull latest changes
git pull origin main

# 2. Rebuild and restart
docker compose down
docker compose up -d --build

# 3. Verify bot is running
docker compose logs -f telegram-bot
```
   docker compose ps
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

# Redis Configuration (optional - for FSM state persistence)
# If not configured or unreachable, the bot will use in-memory storage
# Note: In-memory storage means FSM states (like multi-step commands) will be lost on restart
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

### Redis Configuration Details

Redis is **optional** and used for FSM (Finite State Machine) storage. The bot will:

- ✅ **With Redis**: FSM states persist across bot restarts (recommended for production)
- ⚠️ **Without Redis**: FSM states are stored in memory and lost on restart (acceptable for development/testing)

**When do you need Redis?**
- Production deployments where users may be in the middle of multi-step operations during restarts
- Multiple bot instances sharing state (horizontal scaling)

**When is in-memory storage acceptable?**
- Development and testing environments
- Single-user or low-traffic bots
- Deployments where brief service interruptions are acceptable

The bot automatically detects Redis availability and falls back gracefully to in-memory storage with clear logging.

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