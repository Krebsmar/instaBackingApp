"""Service for processing Instagram stories."""

from datetime import datetime, timezone

from insta_backing_app.logging_config import get_logger
from insta_backing_app.models import Story, get_db_session
from insta_backing_app.repositories import StoryRepository
from insta_backing_app.services.instagram_client import (
    InstagramClient,
    InstagramRateLimitError,
)

logger = get_logger(__name__)


class StoryService:
    """Service for fetching and liking Instagram stories."""

    def __init__(self, instagram_client: InstagramClient):
        self.client = instagram_client

    def _get_repo(self) -> StoryRepository:
        """Get repository with fresh DB session."""
        return StoryRepository(get_db_session())

    def process_stories(self, username: str, user_id: str) -> dict:
        """Process stories for a user. Returns stats."""
        stats = {"fetched": 0, "new": 0, "liked": 0, "skipped": 0, "errors": 0}
        
        logger.info("Processing stories", username=username)
        
        try:
            stories = self.client.get_user_stories(user_id)
            stats["fetched"] = len(stories)
        except InstagramRateLimitError:
            logger.warning("Rate limit reached while fetching stories", username=username)
            return stats
        except Exception as e:
            logger.error("Failed to fetch stories", username=username, error=str(e))
            stats["errors"] += 1
            return stats

        if not stories:
            logger.debug("No stories found", username=username)
            return stats

        repo = self._get_repo()

        for story in stories:
            story_pk = str(story.pk)
            
            # Check if already processed
            if repo.exists(story_pk):
                logger.debug("Story already processed", story_pk=story_pk)
                stats["skipped"] += 1
                continue

            stats["new"] += 1

            # Create record first
            story_record = Story(
                story_pk=story_pk,
                story_id=str(story.id) if story.id else None,
                target_username=username,
                taken_at=story.taken_at or datetime.now(timezone.utc),
                liked=False,
            )
            repo.create(story_record)

            # Try to like
            try:
                success = self.client.like_story(str(story.id), story_pk)
                if success:
                    repo.mark_as_liked(story_pk)
                    stats["liked"] += 1
                    logger.info(
                        "Story liked",
                        username=username,
                        story_pk=story_pk,
                    )
                else:
                    logger.warning("Like returned false", story_pk=story_pk)
                    stats["errors"] += 1
            except InstagramRateLimitError:
                logger.warning("Rate limit reached during story like")
                break
            except Exception as e:
                logger.error("Failed to like story", story_pk=story_pk, error=str(e))
                stats["errors"] += 1

        logger.info(
            "Stories processed",
            username=username,
            **stats,
        )
        return stats

    def cleanup_old_stories(self, hours: int = 24) -> int:
        """Delete stories older than specified hours."""
        repo = self._get_repo()
        count = repo.delete_old_stories(hours)
        
        if count > 0:
            logger.info("Cleaned up old stories", count=count, threshold_hours=hours)
        
        return count
