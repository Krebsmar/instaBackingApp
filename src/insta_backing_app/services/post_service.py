"""Service for processing Instagram posts."""

from datetime import datetime, timezone

from insta_backing_app.config import get_settings
from insta_backing_app.logging_config import get_logger
from insta_backing_app.models import Post, get_db_session
from insta_backing_app.repositories import PostRepository
from insta_backing_app.services.instagram_client import (
    InstagramClient,
    InstagramRateLimitError,
)

logger = get_logger(__name__)


class PostService:
    """Service for fetching and liking Instagram posts."""

    def __init__(self, instagram_client: InstagramClient):
        self.client = instagram_client
        self.settings = get_settings()

    def _get_repo(self) -> PostRepository:
        """Get repository with fresh DB session."""
        return PostRepository(get_db_session())

    def process_posts(self, username: str, user_id: str) -> dict:
        """Process posts for a user. Returns stats."""
        stats = {"fetched": 0, "new": 0, "liked": 0, "skipped": 0, "errors": 0}
        
        logger.info("Processing posts", username=username)
        
        try:
            medias = self.client.get_user_medias(user_id, self.settings.ig_posts_amount)
            stats["fetched"] = len(medias)
        except InstagramRateLimitError:
            logger.warning("Rate limit reached while fetching posts", username=username)
            return stats
        except Exception as e:
            logger.error("Failed to fetch posts", username=username, error=str(e))
            stats["errors"] += 1
            return stats

        if not medias:
            logger.debug("No posts found", username=username)
            return stats

        repo = self._get_repo()

        for media in medias:
            media_pk = str(media.pk)
            
            # Check if already processed
            if repo.exists(media_pk):
                logger.debug("Post already processed", media_pk=media_pk)
                stats["skipped"] += 1
                continue

            stats["new"] += 1

            # Determine product type for reels
            product_type = None
            if hasattr(media, "product_type"):
                product_type = media.product_type

            # Create record first
            post_record = Post(
                media_pk=media_pk,
                media_id=str(media.id) if media.id else None,
                media_type=media.media_type,
                product_type=product_type,
                target_username=username,
                taken_at=media.taken_at or datetime.now(timezone.utc),
                liked=False,
                caption_text=media.caption_text[:500] if media.caption_text else None,
            )
            repo.create(post_record)

            # Try to like
            try:
                success = self.client.like_media(media_pk)
                if success:
                    repo.mark_as_liked(media_pk)
                    stats["liked"] += 1
                    
                    media_type_name = {1: "Photo", 2: "Video", 8: "Album"}.get(
                        media.media_type, "Unknown"
                    )
                    if product_type == "clips":
                        media_type_name = "Reel"
                    
                    logger.info(
                        "Post liked",
                        username=username,
                        media_pk=media_pk,
                        media_type=media_type_name,
                    )
                else:
                    logger.warning("Like returned false", media_pk=media_pk)
                    stats["errors"] += 1
            except InstagramRateLimitError:
                logger.warning("Rate limit reached during post like")
                break
            except Exception as e:
                logger.error("Failed to like post", media_pk=media_pk, error=str(e))
                stats["errors"] += 1

        logger.info(
            "Posts processed",
            username=username,
            **stats,
        )
        return stats
