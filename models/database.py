"""
Database models and configuration for the Telegram News Feed Bot.

This module defines all database tables and relationships using SQLAlchemy ORM,
providing a clean interface for data persistence and retrieval.
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import config

# Base class for all database models
Base = declarative_base()


class User(Base):
    """
    User model representing Telegram users who interact with the bot.
    
    This model stores basic user information and tracks user preferences
    and interaction history with the bot.
    """
    __tablename__ = 'users'
    
    # Primary key - Telegram user ID
    id = Column(Integer, primary_key=True, doc="Telegram user ID")
    
    # User information
    username = Column(String, nullable=True, doc="Telegram username")
    first_name = Column(String, nullable=True, doc="User's first name")
    last_name = Column(String, nullable=True, doc="User's last name")
    
    # User preferences and status
    is_active = Column(Boolean, default=True, doc="Whether user is active")
    language_code = Column(String, default='en', doc="User's preferred language")
    timezone = Column(String, nullable=True, doc="User's timezone")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, doc="When user first started the bot")
    last_active = Column(DateTime, default=datetime.utcnow, doc="Last interaction with bot")
    
    # Relationships
    sources = relationship("Source", back_populates="user", doc="Sources added by this user")
    subscriptions = relationship("Subscription", back_populates="user", doc="User's subscriptions")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"


class Source(Base):
    """
    Source model representing content sources that the bot monitors.
    
    This model stores information about various content sources like RSS feeds,
    social media profiles, and websites that the bot scrapes for updates.
    """
    __tablename__ = 'sources'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True, doc="Unique source identifier")
    
    # Source information
    url = Column(String, nullable=False, unique=True, doc="Source URL")
    type = Column(String, nullable=False, doc="Source type (rss, twitter, facebook, etc.)")
    title = Column(String, nullable=True, doc="Human-readable source title")
    description = Column(String, nullable=True, doc="Source description")
    
    # Source status and metadata
    is_active = Column(Boolean, default=True, doc="Whether source is actively monitored")
    added_by = Column(Integer, ForeignKey('users.id'), nullable=False, doc="User who added this source")
    last_checked = Column(DateTime, nullable=True, doc="Last time source was checked for updates")
    last_updated = Column(DateTime, nullable=True, doc="Last time source had new content")
    check_count = Column(Integer, default=0, doc="Number of times source has been checked")
    error_count = Column(Integer, default=0, doc="Number of consecutive errors")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, doc="When source was added")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, doc="Last modification time")
    
    # Relationships
    user = relationship("User", back_populates="sources", doc="User who added this source")
    subscriptions = relationship("Subscription", back_populates="source", cascade="all, delete-orphan", doc="Subscriptions to this source")
    
    def __repr__(self) -> str:
        return f"<Source(id={self.id}, type='{self.type}', url='{self.url[:50]}...')>"


class Subscription(Base):
    """
    Subscription model representing user subscriptions to content sources.
    
    This model creates a many-to-many relationship between users and sources,
    allowing users to subscribe to multiple sources and sources to have multiple subscribers.
    """
    __tablename__ = 'subscriptions'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True, doc="Unique subscription identifier")
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, doc="Subscriber user ID")
    source_id = Column(Integer, ForeignKey('sources.id'), nullable=False, doc="Subscribed source ID")
    
    # Subscription settings
    is_active = Column(Boolean, default=True, doc="Whether subscription is active")
    notification_enabled = Column(Boolean, default=True, doc="Whether to send notifications for this subscription")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, doc="When subscription was created")
    last_notified = Column(DateTime, nullable=True, doc="Last time user was notified about this source")
    
    # Relationships
    user = relationship("User", back_populates="subscriptions", doc="Subscribed user")
    source = relationship("Source", back_populates="subscriptions", doc="Subscribed source")
    
    # Ensure one subscription per user-source pair
    __table_args__ = (
        UniqueConstraint('user_id', 'source_id', name='unique_user_source_subscription'),
    )
    
    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user_id={self.user_id}, source_id={self.source_id})>"


# Database engine configuration
engine = create_engine(
    config.DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections every hour
)

# Session factory
Session = sessionmaker(bind=engine)


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    
    This function should be called once when setting up the application
    to ensure all database tables are created according to the model definitions.
    
    Raises:
        SQLAlchemyError: If database initialization fails
    """
    try:
        Base.metadata.create_all(engine)
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise


def get_session():
    """
    Get a new database session.
    
    This is a convenience function that can be used as a context manager
    to ensure proper session cleanup.
    
    Returns:
        SQLAlchemy session instance
    """
    return Session()
