"""Target account model for tracking Instagram accounts to process."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from insta_backing_app.models.base import Base, TimestampMixin


class TargetAccount(Base, TimestampMixin):
    """Model for target Instagram accounts to back."""

    __tablename__ = "target_accounts"

    username: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    process_stories: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    process_posts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_story_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_post_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<TargetAccount(username={self.username}, enabled={self.enabled})>"
