"""Repository for Story data access."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from insta_backing_app.models.story import Story


class StoryRepository:
    """Data access layer for Story entities."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_pk(self, story_pk: str) -> Story | None:
        """Get story by primary key."""
        return self.db.get(Story, story_pk)

    def exists(self, story_pk: str) -> bool:
        """Check if story exists."""
        stmt = select(Story.story_pk).where(Story.story_pk == story_pk)
        return self.db.execute(stmt).scalar() is not None

    def create(self, story: Story) -> Story:
        """Create a new story record."""
        self.db.add(story)
        self.db.commit()
        self.db.refresh(story)
        return story

    def mark_as_liked(self, story_pk: str) -> None:
        """Mark story as liked."""
        story = self.get_by_pk(story_pk)
        if story:
            story.liked = True
            story.liked_at = datetime.now(timezone.utc)
            self.db.commit()

    def get_stories_for_cleanup(self, hours: int = 24) -> list[Story]:
        """Get stories older than specified hours that are liked."""
        threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
        stmt = select(Story).where(Story.liked == True, Story.taken_at < threshold)
        return list(self.db.execute(stmt).scalars().all())

    def delete_old_stories(self, hours: int = 24) -> int:
        """Delete stories older than specified hours that are liked."""
        threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
        stmt = delete(Story).where(Story.liked == True, Story.taken_at < threshold)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

    def get_by_username(self, username: str) -> list[Story]:
        """Get all stories for a target username."""
        stmt = select(Story).where(Story.target_username == username)
        return list(self.db.execute(stmt).scalars().all())
