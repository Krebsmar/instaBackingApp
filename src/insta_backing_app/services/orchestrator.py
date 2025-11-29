"""Main processing orchestrator for the backing service."""

from datetime import datetime, timezone

from insta_backing_app.config import get_settings
from insta_backing_app.logging_config import get_logger
from insta_backing_app.services.account_manager import AccountManager
from insta_backing_app.services.instagram_client import (
    InstagramClient,
    InstagramChallengeError,
    InstagramLoginError,
    InstagramRateLimitError,
)
from insta_backing_app.services.post_service import PostService
from insta_backing_app.services.rate_limiter import RateLimiter
from insta_backing_app.services.story_service import StoryService

logger = get_logger(__name__)


class ProcessingOrchestrator:
    """Orchestrates the main processing cycle."""

    def __init__(self):
        self.settings = get_settings()
        self.rate_limiter = RateLimiter()
        self.instagram_client = InstagramClient(self.rate_limiter)
        self.account_manager = AccountManager(self.instagram_client)
        self.story_service = StoryService(self.instagram_client)
        self.post_service = PostService(self.instagram_client)
        self._cycle_count = 0

    def run_cycle(self) -> dict:
        """Run a complete processing cycle."""
        self._cycle_count += 1
        cycle_id = f"cycle-{self._cycle_count}-{datetime.now(timezone.utc).strftime('%H%M%S')}"
        
        logger.info("Starting processing cycle", cycle_id=cycle_id)
        
        stats = {
            "cycle_id": cycle_id,
            "accounts_processed": 0,
            "stories": {"fetched": 0, "new": 0, "liked": 0, "skipped": 0, "errors": 0},
            "posts": {"fetched": 0, "new": 0, "liked": 0, "skipped": 0, "errors": 0},
            "cleanup": {"stories_deleted": 0},
            "errors": [],
        }

        try:
            # Ensure we're logged in
            self.instagram_client.ensure_logged_in()
            self.rate_limiter.reset_backoff()
        except InstagramChallengeError as e:
            logger.error("Challenge required, cannot proceed", error=str(e))
            stats["errors"].append(f"Challenge required: {e}")
            return stats
        except InstagramLoginError as e:
            logger.error("Login failed, cannot proceed", error=str(e))
            stats["errors"].append(f"Login failed: {e}")
            return stats

        # Sync and get accounts
        try:
            accounts = self.account_manager.sync_accounts()
        except Exception as e:
            logger.error("Failed to sync accounts", error=str(e))
            stats["errors"].append(f"Account sync failed: {e}")
            return stats

        if not accounts:
            logger.warning("No enabled accounts to process")
            return stats

        logger.info("Processing accounts", count=len(accounts))

        # Process each account
        for account in accounts:
            if not account.user_id:
                logger.warning("Account has no user_id, skipping", username=account.username)
                continue

            logger.info(
                "Processing account",
                username=account.username,
                process_stories=account.process_stories and self.settings.ig_process_stories,
                process_posts=account.process_posts and self.settings.ig_process_posts,
            )

            try:
                # Process stories
                if account.process_stories and self.settings.ig_process_stories:
                    story_stats = self.story_service.process_stories(
                        account.username, account.user_id
                    )
                    for key in stats["stories"]:
                        stats["stories"][key] += story_stats.get(key, 0)
                    self.account_manager.update_story_check(account.username)

                # Process posts
                if account.process_posts and self.settings.ig_process_posts:
                    post_stats = self.post_service.process_posts(
                        account.username, account.user_id
                    )
                    for key in stats["posts"]:
                        stats["posts"][key] += post_stats.get(key, 0)
                    self.account_manager.update_post_check(account.username)

                self.account_manager.record_success(account.username)
                stats["accounts_processed"] += 1

            except InstagramRateLimitError:
                logger.warning(
                    "Rate limit hit, stopping cycle early",
                    accounts_remaining=len(accounts) - stats["accounts_processed"] - 1,
                )
                stats["errors"].append("Rate limit reached")
                break
            except Exception as e:
                logger.error(
                    "Error processing account",
                    username=account.username,
                    error=str(e),
                )
                self.account_manager.record_error(account.username, str(e))
                stats["errors"].append(f"{account.username}: {e}")

            # Wait between accounts
            self.rate_limiter.wait_between_accounts()

        # Cleanup old stories
        try:
            deleted = self.story_service.cleanup_old_stories(self.settings.ig_cleanup_hours)
            stats["cleanup"]["stories_deleted"] = deleted
        except Exception as e:
            logger.error("Cleanup failed", error=str(e))
            stats["errors"].append(f"Cleanup failed: {e}")

        logger.info(
            "Processing cycle complete",
            cycle_id=cycle_id,
            accounts_processed=stats["accounts_processed"],
            stories_liked=stats["stories"]["liked"],
            posts_liked=stats["posts"]["liked"],
            errors=len(stats["errors"]),
        )

        return stats

    def keep_alive(self) -> bool:
        """Perform session keep-alive."""
        logger.debug("Performing keep-alive")
        return self.instagram_client.keep_alive()

    def get_status(self) -> dict:
        """Get current service status."""
        return {
            "cycle_count": self._cycle_count,
            "rate_limits": self.rate_limiter.get_status(),
        }
