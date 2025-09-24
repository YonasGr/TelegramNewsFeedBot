"""
Tests for database models and operations.

This module contains tests for the database models, initialization,
and basic CRUD operations.
"""

import pytest
import tempfile
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.database import Base, User, Source, Subscription, init_db


class TestDatabase:
    """Test database initialization and basic operations."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        # Create temporary file
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Create engine and session
        engine = create_engine(f'sqlite:///{path}')
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        
        yield SessionLocal
        
        # Clean up
        os.unlink(path)
    
    def test_database_initialization(self, temp_db):
        """Test that database tables are created correctly."""
        session = temp_db()
        
        # Test that we can create a session without errors
        assert session is not None
        
        # Test that tables exist by trying basic operations
        user_count = session.query(User).count()
        source_count = session.query(Source).count()
        subscription_count = session.query(Subscription).count()
        
        assert user_count == 0
        assert source_count == 0
        assert subscription_count == 0
        
        session.close()
    
    def test_user_creation(self, temp_db):
        """Test creating and retrieving users."""
        session = temp_db()
        
        # Create a test user
        user = User(
            id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User",
            language_code="en"
        )
        
        session.add(user)
        session.commit()
        
        # Retrieve the user
        retrieved_user = session.query(User).filter(User.id == 123456789).first()
        
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
        assert retrieved_user.first_name == "Test"
        assert retrieved_user.last_name == "User"
        assert retrieved_user.language_code == "en"
        assert retrieved_user.is_active is True
        
        session.close()
    
    def test_source_creation(self, temp_db):
        """Test creating and retrieving sources."""
        session = temp_db()
        
        # Create a test user first
        user = User(id=123456789, username="testuser")
        session.add(user)
        session.commit()
        
        # Create a test source
        source = Source(
            url="https://example.com/feed.rss",
            type="rss",
            title="Test RSS Feed",
            description="A test RSS feed",
            added_by=123456789
        )
        
        session.add(source)
        session.commit()
        
        # Retrieve the source
        retrieved_source = session.query(Source).filter(Source.url == "https://example.com/feed.rss").first()
        
        assert retrieved_source is not None
        assert retrieved_source.type == "rss"
        assert retrieved_source.title == "Test RSS Feed"
        assert retrieved_source.is_active is True
        assert retrieved_source.added_by == 123456789
        assert retrieved_source.check_count == 0
        assert retrieved_source.error_count == 0
        
        session.close()
    
    def test_subscription_creation(self, temp_db):
        """Test creating subscriptions and relationships."""
        session = temp_db()
        
        # Create test user and source
        user = User(id=123456789, username="testuser")
        source = Source(
            url="https://example.com/feed.rss",
            type="rss",
            added_by=123456789
        )
        
        session.add(user)
        session.add(source)
        session.commit()
        
        # Create subscription
        subscription = Subscription(
            user_id=user.id,
            source_id=source.id
        )
        
        session.add(subscription)
        session.commit()
        
        # Test relationships
        retrieved_subscription = session.query(Subscription).first()
        assert retrieved_subscription is not None
        assert retrieved_subscription.user_id == 123456789
        assert retrieved_subscription.source_id == source.id
        assert retrieved_subscription.is_active is True
        assert retrieved_subscription.notification_enabled is True
        
        # Test relationship access
        assert retrieved_subscription.user.username == "testuser"
        assert retrieved_subscription.source.url == "https://example.com/feed.rss"
        
        session.close()
    
    def test_unique_constraints(self, temp_db):
        """Test that unique constraints work properly."""
        session = temp_db()
        
        # Create test data
        user = User(id=123456789, username="testuser")
        source = Source(url="https://example.com/feed.rss", type="rss", added_by=123456789)
        
        session.add(user)
        session.add(source)
        session.commit()
        
        # Create first subscription
        subscription1 = Subscription(user_id=user.id, source_id=source.id)
        session.add(subscription1)
        session.commit()
        
        # Try to create duplicate subscription
        subscription2 = Subscription(user_id=user.id, source_id=source.id)
        session.add(subscription2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            session.commit()
        
        session.rollback()
        session.close()


if __name__ == "__main__":
    pytest.main([__file__])