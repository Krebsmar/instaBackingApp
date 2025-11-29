"""Repository for RateLimitCounter access."""

from datetime import datetime, timedelta, timezone
from enum import Enum

from sqlalchemy import select
from sqlalchemy.orm import Session

from insta_backing_app.models.rate_limit import RateLimitCounter


class CounterType(str, Enum):
    """Types of rate limit counters."""

    LIKES_HOUR = "likes_hour"
    LIKES_DAY = "likes_day"
    REQUESTS_HOUR = "requests_hour"


class RateLimitRepository:
    """Data access layer for RateLimitCounter entities."""

    def __init__(self, db: Session):
        self.db = db

    def get_counter(self, counter_type: CounterType) -> RateLimitCounter | None:
        """Get counter by type."""
        stmt = select(RateLimitCounter).where(RateLimitCounter.counter_type == counter_type.value)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_or_create(self, counter_type: CounterType, window_hours: int = 1) -> RateLimitCounter:
        """Get existing counter or create new one."""
        counter = self.get_counter(counter_type)
        now = datetime.now(timezone.utc)

        if counter is None:
            window_end = now + timedelta(hours=window_hours)
            counter = RateLimitCounter(
                counter_type=counter_type.value,
                count=0,
                window_start=now,
                window_end=window_end,
            )
            self.db.add(counter)
            self.db.commit()
            self.db.refresh(counter)
        elif now >= counter.window_end:
            # Window expired, reset
            counter.count = 0
            counter.window_start = now
            counter.window_end = now + timedelta(hours=window_hours)
            self.db.commit()

        return counter

    def increment(self, counter_type: CounterType, window_hours: int = 1) -> int:
        """Increment counter and return new value."""
        counter = self.get_or_create(counter_type, window_hours)
        counter.count += 1
        self.db.commit()
        return counter.count

    def get_count(self, counter_type: CounterType) -> int:
        """Get current count, resetting if window expired."""
        counter = self.get_or_create(counter_type)
        return counter.count

    def reset(self, counter_type: CounterType) -> None:
        """Reset a counter."""
        counter = self.get_counter(counter_type)
        if counter:
            now = datetime.now(timezone.utc)
            counter.count = 0
            counter.window_start = now
            self.db.commit()

    def get_time_until_reset(self, counter_type: CounterType) -> timedelta:
        """Get time remaining until counter resets."""
        counter = self.get_counter(counter_type)
        if counter is None:
            return timedelta(0)
        
        now = datetime.now(timezone.utc)
        if now >= counter.window_end:
            return timedelta(0)
        
        return counter.window_end - now
