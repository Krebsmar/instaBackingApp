"""Service for managing target accounts."""

from datetime import datetime, timezone

from insta_backing_app.config import get_settings
from insta_backing_app.logging_config import get_logger
from insta_backing_app.models import TargetAccount, get_db_session
from insta_backing_app.repositories import TargetAccountRepository
from insta_backing_app.services.instagram_client import InstagramClient

logger = get_logger(__name__)


class AccountManager:
    """Service for managing target Instagram accounts."""

    def __init__(self, instagram_client: InstagramClient):
        self.client = instagram_client
        self.settings = get_settings()

    def _get_repo(self) -> TargetAccountRepository:
        """Get repository with fresh DB session."""
        return TargetAccountRepository(get_db_session())

    def sync_accounts(self) -> list[TargetAccount]:
        """Sync accounts from config and return enabled accounts."""
        repo = self._get_repo()
        target_usernames = self.settings.target_usernames_list
        
        logger.info("Syncing target accounts", count=len(target_usernames))
        
        # Sync from config
        repo.sync_from_config(target_usernames)
        
        # Resolve user IDs for new accounts
        for username in target_usernames:
            account = repo.get_by_username(username)
            if account and not account.user_id:
                try:
                    user_id = self.client.get_user_id(username)
                    repo.create_or_update(username, user_id)
                    logger.info("Resolved user ID", username=username, user_id=user_id)
                except Exception as e:
                    logger.error("Failed to resolve user ID", username=username, error=str(e))
                    repo.record_error(username, str(e))
        
        return repo.get_enabled()

    def get_enabled_accounts(self) -> list[TargetAccount]:
        """Get all enabled target accounts."""
        repo = self._get_repo()
        return repo.get_enabled()

    def record_success(self, username: str) -> None:
        """Record successful processing."""
        repo = self._get_repo()
        repo.clear_error(username)

    def record_error(self, username: str, error: str) -> None:
        """Record processing error."""
        repo = self._get_repo()
        repo.record_error(username, error)

    def update_story_check(self, username: str) -> None:
        """Update last story check timestamp."""
        repo = self._get_repo()
        repo.update_last_story_check(username)

    def update_post_check(self, username: str) -> None:
        """Update last post check timestamp."""
        repo = self._get_repo()
        repo.update_last_post_check(username)