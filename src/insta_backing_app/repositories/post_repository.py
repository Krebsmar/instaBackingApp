"""Repository for Post data access."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from insta_backing_app.models.post import Post


class PostRepository:
    """Data access layer for Post entities."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_pk(self, media_pk: str) -> Post | None:
        """Get post by primary key."""
        return self.db.get(Post, media_pk)

    def exists(self, media_pk: str) -> bool:
        """Check if post exists."""
        stmt = select(Post.media_pk).where(Post.media_pk == media_pk)
        return self.db.execute(stmt).scalar() is not None

    def create(self, post: Post) -> Post:
        """Create a new post record."""
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def mark_as_liked(self, media_pk: str) -> None:
        """Mark post as liked."""
        post = self.get_by_pk(media_pk)
        if post:
            post.liked = True
            post.liked_at = datetime.now(timezone.utc)
            self.db.commit()

    def get_by_username(self, username: str) -> list[Post]:
        """Get all posts for a target username."""
        stmt = select(Post).where(Post.target_username == username)
        return list(self.db.execute(stmt).scalars().all())

    def get_unliked(self) -> list[Post]:
        """Get all unliked posts."""
        stmt = select(Post).where(Post.liked == False)
        return list(self.db.execute(stmt).scalars().all())

    def has_posts_for_user(self, username: str) -> bool:
        """Check if any posts exist for a target username."""
        stmt = select(Post.media_pk).where(Post.target_username == username).limit(1)
        return self.db.execute(stmt).scalar() is not None
