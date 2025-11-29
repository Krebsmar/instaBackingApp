"""Repository for SessionData access."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from insta_backing_app.models.session import SessionData


class SessionRepository:
    """Data access layer for SessionData entities."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> SessionData | None:
        """Get session by username."""
        stmt = select(SessionData).where(SessionData.username == username)
        return self.db.execute(stmt).scalar_one_or_none()

    def save(self, username: str, session_json: str, device_settings: str | None = None) -> SessionData:
        """Save or update session data."""
        session_data = self.get_by_username(username)
        now = datetime.now(timezone.utc)
        
        if session_data:
            session_data.session_json = session_json
            session_data.device_settings = device_settings
            session_data.last_request_at = now
        else:
            session_data = SessionData(
                username=username,
                session_json=session_json,
                device_settings=device_settings,
                last_login_at=now,
                last_request_at=now,
            )
            self.db.add(session_data)
        
        self.db.commit()
        self.db.refresh(session_data)
        return session_data

    def update_last_request(self, username: str) -> None:
        """Update last request timestamp."""
        session_data = self.get_by_username(username)
        if session_data:
            session_data.last_request_at = datetime.now(timezone.utc)
            self.db.commit()

    def update_last_login(self, username: str) -> None:
        """Update last login timestamp."""
        session_data = self.get_by_username(username)
        if session_data:
            session_data.last_login_at = datetime.now(timezone.utc)
            self.db.commit()

    def delete(self, username: str) -> None:
        """Delete session data."""
        session_data = self.get_by_username(username)
        if session_data:
            self.db.delete(session_data)
            self.db.commit()
