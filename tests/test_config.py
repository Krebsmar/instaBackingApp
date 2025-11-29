"""Tests for configuration module."""

import os

import pytest


class TestSettings:
    """Tests for Settings class."""

    def test_target_usernames_list_single(self, monkeypatch):
        """Test parsing single username."""
        monkeypatch.setenv("IG_USERNAME", "test")
        monkeypatch.setenv("IG_PASSWORD", "test")
        monkeypatch.setenv("IG_TARGET_USERNAMES", "user1")
        
        # Clear cache
        from insta_backing_app.config import get_settings
        get_settings.cache_clear()
        
        from insta_backing_app.config import Settings
        settings = Settings()
        
        assert settings.target_usernames_list == ["user1"]

    def test_target_usernames_list_multiple(self, monkeypatch):
        """Test parsing multiple usernames."""
        monkeypatch.setenv("IG_USERNAME", "test")
        monkeypatch.setenv("IG_PASSWORD", "test")
        monkeypatch.setenv("IG_TARGET_USERNAMES", "user1, user2, user3")
        
        from insta_backing_app.config import get_settings
        get_settings.cache_clear()
        
        from insta_backing_app.config import Settings
        settings = Settings()
        
        assert settings.target_usernames_list == ["user1", "user2", "user3"]

    def test_default_values(self, monkeypatch):
        """Test default configuration values."""
        monkeypatch.setenv("IG_USERNAME", "test")
        monkeypatch.setenv("IG_PASSWORD", "test")
        monkeypatch.setenv("IG_TARGET_USERNAMES", "user1")
        
        from insta_backing_app.config import get_settings
        get_settings.cache_clear()
        
        from insta_backing_app.config import Settings
        settings = Settings()
        
        assert settings.ig_cycle_seconds == 3600
        assert settings.ig_posts_amount == 20
        assert settings.ig_cleanup_hours == 24
        assert settings.ig_max_likes_per_hour == 40
        assert settings.ig_max_likes_per_day == 800

    def test_log_level_validation(self, monkeypatch):
        """Test log level validation."""
        monkeypatch.setenv("IG_USERNAME", "test")
        monkeypatch.setenv("IG_PASSWORD", "test")
        monkeypatch.setenv("IG_TARGET_USERNAMES", "user1")
        monkeypatch.setenv("LOG_LEVEL", "debug")
        
        from insta_backing_app.config import get_settings
        get_settings.cache_clear()
        
        from insta_backing_app.config import Settings
        settings = Settings()
        
        assert settings.log_level == "DEBUG"

    def test_invalid_log_level(self, monkeypatch):
        """Test invalid log level raises error."""
        monkeypatch.setenv("IG_USERNAME", "test")
        monkeypatch.setenv("IG_PASSWORD", "test")
        monkeypatch.setenv("IG_TARGET_USERNAMES", "user1")
        monkeypatch.setenv("LOG_LEVEL", "INVALID")
        
        from insta_backing_app.config import get_settings
        get_settings.cache_clear()
        
        from insta_backing_app.config import Settings
        
        with pytest.raises(ValueError):
            Settings()
