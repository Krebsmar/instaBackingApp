"""Configuration management using Pydantic Settings (12-Factor compliant)."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Instagram Credentials
    ig_username: str = Field(..., description="Instagram username")
    ig_password: str = Field(..., description="Instagram password")

    # Target Accounts
    ig_target_usernames: str = Field(..., description="Comma-separated target usernames")

    # Processing Settings
    ig_cycle_seconds: int = Field(default=3600, ge=300, description="Cycle interval in seconds")
    ig_posts_amount: int = Field(default=20, ge=1, le=50, description="Posts per account")
    ig_cleanup_hours: int = Field(default=24, ge=1, description="Story cleanup threshold")
    ig_process_stories: bool = Field(default=True, description="Process stories")
    ig_process_posts: bool = Field(default=True, description="Process posts")

    # Rate Limiting - Delays
    ig_delay_between_requests: float = Field(default=2.0, ge=0.5)
    ig_delay_between_likes: float = Field(default=3.0, ge=1.0)
    ig_delay_between_accounts: float = Field(default=10.0, ge=5.0)
    ig_delay_jitter_percent: int = Field(default=30, ge=0, le=50)

    # Rate Limiting - Limits
    ig_max_likes_per_hour: int = Field(default=40, ge=1)
    ig_max_likes_per_day: int = Field(default=800, ge=1)
    ig_max_requests_per_hour: int = Field(default=150, ge=1)

    # Rate Limiting - Backoff
    ig_backoff_base_seconds: int = Field(default=60, ge=10)
    ig_backoff_max_seconds: int = Field(default=3600, ge=60)
    ig_backoff_multiplier: float = Field(default=2.0, ge=1.1)

    # Session Management
    ig_session_keepalive_seconds: int = Field(default=1800, ge=300)
    ig_max_login_attempts: int = Field(default=3, ge=1)

    # Database
    database_url: str = Field(default="sqlite:///data/insta_backing.db")

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return upper

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        allowed = {"json", "text"}
        lower = v.lower()
        if lower not in allowed:
            raise ValueError(f"log_format must be one of {allowed}")
        return lower

    @property
    def target_usernames_list(self) -> list[str]:
        """Parse comma-separated usernames into list."""
        return [u.strip() for u in self.ig_target_usernames.split(",") if u.strip()]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
