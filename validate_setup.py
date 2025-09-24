#!/usr/bin/env python3
"""
Setup validation script for the Telegram News Feed Bot.

This script validates the bot configuration and dependencies
to ensure everything is properly set up before running the bot.
"""

import sys
import os
import traceback
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.8 or higher."""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required, found {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} is supported")
    return True


def check_dependencies():
    """Check if all required dependencies are installed."""
    print("\n📦 Checking dependencies...")
    
    required_modules = [
        'aiogram',
        'aiohttp', 
        'sqlalchemy',
        'pydantic',
        'python-dotenv',
        'beautifulsoup4',
        'feedparser',
        'redis'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            # Handle module name variations
            import_name = module
            if module == 'python-dotenv':
                import_name = 'dotenv'
            elif module == 'beautifulsoup4':
                import_name = 'bs4'
            
            __import__(import_name)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - Not installed")
            missing_modules.append(module)
        except Exception as e:
            print(f"⚠️ {module} - Error: {e}")
    
    if missing_modules:
        print(f"\n📋 To install missing dependencies, run:")
        print(f"pip install {' '.join(missing_modules)}")
        return False
    
    return True


def check_environment():
    """Check environment variables and configuration."""
    print("\n⚙️ Checking environment configuration...")
    
    # Load .env file if exists
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file found")
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            print("⚠️ python-dotenv not installed, skipping .env loading")
    else:
        print("ℹ️ No .env file found (this is OK if using system environment variables)")
    
    # Check required environment variables
    required_vars = {
        'TELEGRAM_BOT_TOKEN': 'Telegram bot token from @BotFather',
        'ADMIN_IDS': 'Comma-separated list of admin user IDs'
    }
    
    missing_vars = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            print(f"❌ {var} - Not set ({description})")
            missing_vars.append(var)
        else:
            # Mask token for security
            if 'TOKEN' in var:
                masked_value = value[:10] + '...' if len(value) > 10 else '***'
                print(f"✅ {var} - Set ({masked_value})")
            else:
                print(f"✅ {var} - Set ({value})")
    
    # Check optional but recommended variables
    optional_vars = {
        'DATABASE_URL': 'sqlite:///database.db',
        'REDIS_URL': 'redis://localhost:6379/0',
        'LOG_LEVEL': 'INFO'
    }
    
    for var, default in optional_vars.items():
        value = os.getenv(var, default)
        print(f"ℹ️ {var} - {value}")
    
    if missing_vars:
        print(f"\n📋 Required environment variables missing:")
        for var in missing_vars:
            print(f"  - {var}")
        return False
    
    return True


def check_configuration():
    """Check bot configuration validation."""
    print("\n🔧 Checking configuration validation...")
    
    try:
        from config import config
        config.validate()
        print("✅ Configuration validation passed")
        
        # Show key configuration values
        print(f"  - Bot token: {'Set' if config.BOT_TOKEN else 'Missing'}")
        print(f"  - Admin IDs: {len(config.ADMIN_IDS)} configured")
        print(f"  - Database: {config.DATABASE_URL}")
        print(f"  - Request timeout: {config.REQUEST_TIMEOUT}s")
        print(f"  - Max retries: {config.MAX_RETRIES}")
        print(f"  - Scheduler interval: {config.SCHEDULER_INTERVAL}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False


def check_database():
    """Check database initialization."""
    print("\n🗄️ Checking database setup...")
    
    try:
        from models.database import init_db, Session, User, Source, Subscription
        
        # Try to initialize database
        init_db()
        print("✅ Database initialized successfully")
        
        # Test basic operations
        with Session() as session:
            user_count = session.query(User).count()
            source_count = session.query(Source).count()
            subscription_count = session.query(Subscription).count()
            
            print(f"  - Users: {user_count}")
            print(f"  - Sources: {source_count}")
            print(f"  - Subscriptions: {subscription_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        print("Traceback:")
        traceback.print_exc()
        return False


def check_file_structure():
    """Check if all required files are present."""
    print("\n📁 Checking file structure...")
    
    required_files = [
        'main.py',
        'config.py',
        'bot/handlers.py',
        'bot/keyboards.py',
        'models/database.py',
        'models/schemas.py',
        'services/scraper.py',
        'services/scheduler.py',
        'services/content_processor.py',
        'utils/logger.py',
        'requirements.txt'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n📋 Missing files: {len(missing_files)}")
        return False
    
    return True


def main():
    """Run all validation checks."""
    print("🚀 Telegram News Feed Bot - Setup Validation")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("File Structure", check_file_structure),
        ("Environment", check_environment),
        ("Configuration", check_configuration),
        ("Database", check_database)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        try:
            if check_func():
                passed += 1
            else:
                print(f"\n❌ {name} check failed")
        except Exception as e:
            print(f"\n💥 {name} check crashed: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"📊 Validation Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All checks passed! Your bot is ready to run.")
        print("\n📋 To start the bot:")
        print("  python main.py")
        print("\n📋 To run tests:")
        print("  python -m pytest tests/")
        return True
    else:
        print("⚠️ Some checks failed. Please fix the issues above before running the bot.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)