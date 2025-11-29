"""Post model for Instagram posts (photos, albums, reels)."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from insta_backing_app.models.base import Base


class Post(Base):
    """Model representing an Instagram post (photo, album, reel)."""

    __tablename__ = "posts"

    media_pk: Mapped[str] = mapped_column(String(64), primary_key=True)
    media_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    media_type: Mapped[int] = mapped_column(Integer, nullable=False)
    product_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    target_username: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    taken_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    liked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    liked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    caption_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_posts_taken_at", "taken_at"),
        Index("ix_posts_media_type", "media_type"),
        Index("ix_posts_liked", "liked"),
    )

    @property
    def media_type_name(self) -> str:
        """Human-readable media type."""
        types = {1: "Photo", 2: "Video", 8: "Album"}
        return types.get(self.media_type, "Unknown")

    @property
    def is_reel(self) -> bool:
        """Check if post is a reel."""
        return self.media_type == 2 and self.product_type == "clips"

    def __repr__(self) -> str:
        return f"<Post(pk={self.media_pk}, type={self.media_type_name}, liked={self.liked})>"
