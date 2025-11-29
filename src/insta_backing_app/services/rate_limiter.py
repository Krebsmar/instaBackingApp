"""Rate limiter service for Instagram API compliance."""

import random
import time
from datetime import timedelta

from insta_backing_app.config import get_settings
from insta_backing_app.logging_config import get_logger
from insta_backing_app.models import get_db_session
from insta_backing_app.repositories import CounterType, RateLimitRepository

logger = get_logger(__name__)


class RateLimiter:
    """Service for managing rate limits and delays."""

    def __init__(self):
        self.settings = get_settings()
        self._backoff_count = 0

    def _get_repo(self) -> RateLimitRepository:
        """Get repository with fresh session."""
        return RateLimitRepository(get_db_session())

    def can_make_request(self) -> bool:
        """Check if we can make an API request."""
        repo = self._get_repo()
        count = repo.get_count(CounterType.REQUESTS_HOUR)
        can_proceed = count < self.settings.ig_max_requests_per_hour
        
        if not can_proceed:
            remaining = repo.get_time_until_reset(CounterType.REQUESTS_HOUR)
            logger.warning(
                "Request limit reached",
                current=count,
                max=self.settings.ig_max_requests_per_hour,
                reset_in_seconds=remaining.total_seconds(),
            )
        
        return can_proceed

    def can_like(self) -> bool:
        """Check if we can perform a like action."""
        repo = self._get_repo()
        
        # Check hourly limit
        hourly_count = repo.get_count(CounterType.LIKES_HOUR)
        if hourly_count >= self.settings.ig_max_likes_per_hour:
            remaining = repo.get_time_until_reset(CounterType.LIKES_HOUR)
            logger.warning(
                "Hourly like limit reached",
                current=hourly_count,
                max=self.settings.ig_max_likes_per_hour,
                reset_in_seconds=remaining.total_seconds(),
            )
            return False

        # Check daily limit
        daily_count = repo.get_count(CounterType.LIKES_DAY)
        if daily_count >= self.settings.ig_max_likes_per_day:
            remaining = repo.get_time_until_reset(CounterType.LIKES_DAY)
            logger.warning(
                "Daily like limit reached",
                current=daily_count,
                max=self.settings.ig_max_likes_per_day,
                reset_in_seconds=remaining.total_seconds(),
            )
            return False

        return True

    def record_request(self) -> None:
        """Record an API request."""
        repo = self._get_repo()
        repo.increment(CounterType.REQUESTS_HOUR, window_hours=1)

    def record_like(self) -> None:
        """Record a like action."""
        repo = self._get_repo()
        repo.increment(CounterType.LIKES_HOUR, window_hours=1)
        repo.increment(CounterType.LIKES_DAY, window_hours=24)

    def _apply_jitter(self, base_delay: float) -> float:
        """Apply random jitter to delay."""
        jitter_factor = self.settings.ig_delay_jitter_percent / 100.0
        min_delay = base_delay * (1 - jitter_factor)
        max_delay = base_delay * (1 + jitter_factor)
        return random.uniform(min_delay, max_delay)

    def wait_between_requests(self) -> None:
        """Wait between API requests with jitter."""
        delay = self._apply_jitter(self.settings.ig_delay_between_requests)
        logger.debug("Waiting between requests", delay_seconds=round(delay, 2))
        time.sleep(delay)

    def wait_between_likes(self) -> None:
        """Wait between like actions with jitter."""
        delay = self._apply_jitter(self.settings.ig_delay_between_likes)
        logger.debug("Waiting between likes", delay_seconds=round(delay, 2))
        time.sleep(delay)

    def wait_between_accounts(self) -> None:
        """Wait between processing different accounts."""
        delay = self._apply_jitter(self.settings.ig_delay_between_accounts)
        logger.debug("Waiting between accounts", delay_seconds=round(delay, 2))
        time.sleep(delay)

    def apply_backoff(self) -> float:
        """Apply exponential backoff after error. Returns wait time."""
        self._backoff_count += 1
        delay = min(
            self.settings.ig_backoff_base_seconds * (self.settings.ig_backoff_multiplier ** (self._backoff_count - 1)),
            self.settings.ig_backoff_max_seconds,
        )
        logger.warning(
            "Applying backoff",
            backoff_count=self._backoff_count,
            delay_seconds=delay,
        )
        time.sleep(delay)
        return delay

    def reset_backoff(self) -> None:
        """Reset backoff counter after successful operation."""
        if self._backoff_count > 0:
            logger.debug("Resetting backoff counter", previous_count=self._backoff_count)
            self._backoff_count = 0

    def get_time_until_can_like(self) -> timedelta:
        """Get time until we can like again."""
        repo = self._get_repo()
        
        hourly_remaining = repo.get_time_until_reset(CounterType.LIKES_HOUR)
        daily_remaining = repo.get_time_until_reset(CounterType.LIKES_DAY)
        
        # Return the shorter wait time
        if repo.get_count(CounterType.LIKES_HOUR) >= self.settings.ig_max_likes_per_hour:
            return hourly_remaining
        if repo.get_count(CounterType.LIKES_DAY) >= self.settings.ig_max_likes_per_day:
            return daily_remaining
        
        return timedelta(0)

    def get_status(self) -> dict:
        """Get current rate limit status."""
        repo = self._get_repo()
        return {
            "requests_hour": {
                "current": repo.get_count(CounterType.REQUESTS_HOUR),
                "max": self.settings.ig_max_requests_per_hour,
            },
            "likes_hour": {
                "current": repo.get_count(CounterType.LIKES_HOUR),
                "max": self.settings.ig_max_likes_per_hour,
            },
            "likes_day": {
                "current": repo.get_count(CounterType.LIKES_DAY),
                "max": self.settings.ig_max_likes_per_day,
            },
            "backoff_count": self._backoff_count,
        }
