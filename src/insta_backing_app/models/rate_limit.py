"""Rate limit counter model for tracking API usage."""

from datetime import datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from insta_backing_app.models.base import Base, TZDateTime


class RateLimitCounter(Base):
    """Model for tracking rate limit counters."""

    __tablename__ = "rate_limit_counters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    counter_type: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    window_start: Mapped[datetime] = mapped_column(TZDateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(TZDateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<RateLimitCounter(type={self.counter_type}, count={self.count})>"
