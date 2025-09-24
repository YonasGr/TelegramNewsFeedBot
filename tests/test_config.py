"""
Tests for configuration management.

This module contains tests for the configuration validation
and environment variable handling.
"""

import pytest
import os
from unittest.mock import patch
from config import Config


class TestConfig:
    """Test configuration management."""
    
    def test_config_validation_success(self):
        """Test successful configuration validation."""
        # Mock valid environment
        with patch.dict(os.environ, {
            'TELEGRAM_BOT_TOKEN': '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11',
            'ADMIN_IDS': '123456789,987654321'
        }):
            config = Config()
            # Should not raise any exception
            config.validate()
    
    def test_config_validation_missing_token(self):
        """Test validation failure with missing bot token."""
        with patch.dict(os.environ, {
            'TELEGRAM_BOT_TOKEN': '',
            'ADMIN_IDS': '123456789'
        }):
            config = Config()
            with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
                config.validate()
    
    def test_config_validation_missing_admin_ids(self):
        """Test validation failure with missing admin IDs."""
        with patch.dict(os.environ, {
            'TELEGRAM_BOT_TOKEN': '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11',
            'ADMIN_IDS': ''
        }):
            config = Config()
            with pytest.raises(ValueError, match="At least one ADMIN_ID"):
                config.validate()
    
    def test_config_validation_invalid_timeout(self):
        """Test validation failure with invalid timeout."""
        with patch.dict(os.environ, {
            'TELEGRAM_BOT_TOKEN': '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11',
            'ADMIN_IDS': '123456789',
            'REQUEST_TIMEOUT': '-1'
        }):
            config = Config()
            with pytest.raises(ValueError, match="REQUEST_TIMEOUT must be positive"):
                config.validate()
    
    def test_config_validation_invalid_retries(self):
        """Test validation failure with invalid retry count."""
        with patch.dict(os.environ, {
            'TELEGRAM_BOT_TOKEN': '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11',
            'ADMIN_IDS': '123456789',
            'MAX_RETRIES': '-1'
        }):
            config = Config()
            with pytest.raises(ValueError, match="MAX_RETRIES cannot be negative"):
                config.validate()
    
    def test_admin_ids_parsing(self):
        """Test admin IDs parsing from comma-separated string."""
        with patch.dict(os.environ, {
            'ADMIN_IDS': '123456789,  987654321 , 555666777'
        }):
            config = Config()
            expected_ids = [123456789, 987654321, 555666777]
            assert config.ADMIN_IDS == expected_ids
    
    def test_admin_ids_parsing_invalid(self):
        """Test admin IDs parsing with invalid values."""
        with patch.dict(os.environ, {
            'ADMIN_IDS': '123456789,invalid,987654321,,'
        }):
            config = Config()
            # Should only include valid numeric IDs
            expected_ids = [123456789, 987654321]
            assert config.ADMIN_IDS == expected_ids
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            
            assert config.DATABASE_URL == "sqlite:///database.db"
            assert config.REDIS_URL == "redis://localhost:6379/0"
            assert config.REQUEST_TIMEOUT == 30
            assert config.MAX_RETRIES == 3
            assert config.RETRY_DELAY == 5
            assert config.SCHEDULER_INTERVAL == 300
            assert config.MAX_ITEMS_PER_UPDATE == 5
            assert config.MAX_POST_LENGTH == 4000
            assert config.LOG_LEVEL == "INFO"
    
    def test_environment_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test',
            'REQUEST_TIMEOUT': '60',
            'MAX_RETRIES': '5',
            'SCHEDULER_INTERVAL': '600',
            'LOG_LEVEL': 'DEBUG'
        }):
            config = Config()
            
            assert config.DATABASE_URL == "postgresql://test"
            assert config.REQUEST_TIMEOUT == 60
            assert config.MAX_RETRIES == 5
            assert config.SCHEDULER_INTERVAL == 600
            assert config.LOG_LEVEL == "DEBUG"


if __name__ == "__main__":
    pytest.main([__file__])