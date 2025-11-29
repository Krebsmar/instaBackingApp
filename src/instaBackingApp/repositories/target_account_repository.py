"""Repository for TargetAccount access."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from insta_backing_app.models.target_account import TargetAccount


class TargetAccountRepository:
    """Data access layer for TargetAccount entities."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> TargetAccount | None:
        """Get account by username."""
        return self.db.get(TargetAccount, username)

    def get_enabled(self) -> list[TargetAccount]:
        """Get all enabled accounts."""
        stmt = select(TargetAccount).where(TargetAccount.enabled == True)
        return list(self.db.execute(stmt).scalars().all())

    def get_all(self) -> list[TargetAccount]:
        """Get all accounts."""
        stmt = select(TargetAccount)
        return list(self.db.execute(stmt).scalars().all())

    def create_or_update(self, username: str, user_id: str | None = None) -> TargetAccount:
        """Create or update target account."""
        account = self.get_by_username(username)
        
        if account is None:
            account = TargetAccount(
                username=username,
                user_id=user_id,
                enabled=True,
            )
            self.db.add(account)
        elif user_id and not account.user_id:
            account.user_id = user_id
        
        self.db.commit()
        self.db.refresh(account)
        return account

    def update_last_story_check(self, username: str) -> None:
        """Update last story check timestamp."""
        account = self.get_by_username(username)
        if account:
            account.last_story_check = datetime.now(timezone.utc)
            self.db.commit()

    def update_last_post_check(self, username: str) -> None:
        """Update last post check timestamp."""
        account = self.get_by_username(username)
        if account:
            account.last_post_check = datetime.now(timezone.utc)
            self.db.commit()

    def record_error(self, username: str, error: str) -> None:
        """Record an error for the account."""
        account = self.get_by_username(username)
        if account:
            account.error_count += 1
            account.last_error = error
            self.db.commit()

    def clear_error(self, username: str) -> None:
        """Clear error state for the account."""
        account = self.get_by_username(username)
        if account:
            account.error_count = 0
            account.last_error = None
            self.db.commit()

    def disable(self, username: str) -> None:
        """Disable an account."""
        account = self.get_by_username(username)
        if account:
            account.enabled = False
            self.db.commit()

    def sync_from_config(self, usernames: list[str]) -> None:
        """Sync accounts from configuration."""
        existing = {a.username for a in self.get_all()}
        
        # Add new accounts
        for username in usernames:
            if username not in existing:
                self.create_or_update(username)
        
        # Disable removed accounts
        for username in existing:
            if username not in usernames:
                self.disable(username)
