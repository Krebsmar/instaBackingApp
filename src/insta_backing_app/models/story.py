"""Story model for Instagram stories."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from insta_backing_app.models.base import Base, TZDateTime


class Story(Base):
    """Model representing an Instagram story."""

    __tablename__ = "stories"

    story_pk: Mapped[str] = mapped_column(String(64), primary_key=True)
    story_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_username: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    taken_at: Mapped[datetime] = mapped_column(TZDateTime(timezone=True), nullable=False)
    liked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    liked_at: Mapped[datetime | None] = mapped_column(TZDateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(
        TZDateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_stories_taken_at", "taken_at"),
        Index("ix_stories_liked_taken_at", "liked", "taken_at"),
    )

    def __repr__(self) -> str:
        return f"<Story(pk={self.story_pk}, user={self.target_username}, liked={self.liked})>"
