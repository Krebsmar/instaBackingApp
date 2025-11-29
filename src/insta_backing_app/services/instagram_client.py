"""Instagram client wrapper using instagrapi."""

import json
from datetime import datetime, timezone
from typing import Any

from instagrapi import Client
from instagrapi.exceptions import (
    ChallengeRequired,
    LoginRequired,
    PleaseWaitFewMinutes,
    RateLimitError,
)
from instagrapi.types import Media, Story, UserShort

from insta_backing_app.config import get_settings
from insta_backing_app.logging_config import get_logger
from insta_backing_app.models import get_db_session
from insta_backing_app.repositories import SessionRepository
from insta_backing_app.services.rate_limiter import RateLimiter

logger = get_logger(__name__)


class InstagramClientError(Exception):
    """Base exception for Instagram client errors."""

    pass


class InstagramRateLimitError(InstagramClientError):
    """Rate limit exceeded."""

    pass


class InstagramChallengeError(InstagramClientError):
    """Challenge required (2FA, verification)."""

    pass


class InstagramLoginError(InstagramClientError):
    """Login failed."""

    pass


class InstagramClient:
    """Wrapper around instagrapi Client with session management."""

    def __init__(self, rate_limiter: RateLimiter):
        self.settings = get_settings()
        self.rate_limiter = rate_limiter
        self._client: Client | None = None
        self._user_id_cache: dict[str, str] = {}

    def _get_session_repo(self) -> SessionRepository:
        """Get session repository with fresh DB session."""
        return SessionRepository(get_db_session())

    def _create_client(self) -> Client:
        """Create a new instagrapi client."""
        client = Client()
        client.delay_range = [1, 3]
        return client

    def _load_session(self) -> bool:
        """Try to load existing session from database."""
        repo = self._get_session_repo()
        session_data = repo.get_by_username(self.settings.ig_username)

        if session_data is None:
            logger.debug("No existing session found")
            return False

        try:
            self._client = self._create_client()
            settings = json.loads(session_data.session_json)
            self._client.set_settings(settings)
            self._client.login(self.settings.ig_username, self.settings.ig_password)
            
            logger.info("Session loaded from database", username=self.settings.ig_username)
            repo.update_last_request(self.settings.ig_username)
            return True
        except LoginRequired:
            logger.warning("Stored session invalid, need fresh login")
            return False
        except Exception as e:
            logger.warning("Failed to load session", error=str(e))
            return False

    def _save_session(self) -> None:
        """Save current session to database."""
        if self._client is None:
            return

        try:
            repo = self._get_session_repo()
            settings_json = json.dumps(self._client.get_settings())
            repo.save(self.settings.ig_username, settings_json)
            logger.debug("Session saved to database")
        except Exception as e:
            logger.error("Failed to save session", error=str(e))

    def _fresh_login(self) -> None:
        """Perform a fresh login."""
        self._client = self._create_client()

        for attempt in range(1, self.settings.ig_max_login_attempts + 1):
            try:
                logger.info(
                    "Attempting login",
                    username=self.settings.ig_username,
                    attempt=attempt,
                )
                self._client.login(self.settings.ig_username, self.settings.ig_password)
                self._save_session()
                
                repo = self._get_session_repo()
                repo.update_last_login(self.settings.ig_username)
                
                logger.info("Login successful", username=self.settings.ig_username)
                return
            except ChallengeRequired as e:
                logger.error("Challenge required during login", error=str(e))
                raise InstagramChallengeError("Challenge required, manual intervention needed")
            except PleaseWaitFewMinutes:
                logger.warning("Rate limited during login", attempt=attempt)
                self.rate_limiter.apply_backoff()
            except Exception as e:
                logger.error("Login failed", attempt=attempt, error=str(e))
                if attempt == self.settings.ig_max_login_attempts:
                    raise InstagramLoginError(f"Login failed after {attempt} attempts: {e}")
                self.rate_limiter.apply_backoff()

    def ensure_logged_in(self) -> None:
        """Ensure client is logged in, loading session or performing fresh login."""
        if self._client is not None:
            return

        if not self._load_session():
            self._fresh_login()

    def _handle_api_error(self, e: Exception) -> None:
        """Handle API errors with appropriate responses."""
        if isinstance(e, RateLimitError | PleaseWaitFewMinutes):
            logger.warning("Instagram rate limit hit", error=str(e))
            raise InstagramRateLimitError(str(e))
        elif isinstance(e, ChallengeRequired):
            logger.error("Challenge required", error=str(e))
            raise InstagramChallengeError(str(e))
        elif isinstance(e, LoginRequired):
            logger.warning("Session expired, will retry login")
            self._client = None
            raise InstagramLoginError("Session expired")
        else:
            raise InstagramClientError(str(e))

    def get_user_id(self, username: str) -> str:
        """Get user ID from username (cached)."""
        if username in self._user_id_cache:
            return self._user_id_cache[username]

        self.ensure_logged_in()
        
        if not self.rate_limiter.can_make_request():
            raise InstagramRateLimitError("Request limit reached")

        try:
            self.rate_limiter.wait_between_requests()
            user_id = self._client.user_id_from_username(username)
            self._user_id_cache[username] = str(user_id)
            self.rate_limiter.record_request()
            self._save_session()
            
            logger.debug("Got user ID", username=username, user_id=user_id)
            return str(user_id)
        except Exception as e:
            self._handle_api_error(e)
            raise

    def get_user_stories(self, user_id: str) -> list[Story]:
        """Get stories for a user."""
        self.ensure_logged_in()
        
        if not self.rate_limiter.can_make_request():
            raise InstagramRateLimitError("Request limit reached")

        try:
            self.rate_limiter.wait_between_requests()
            stories = self._client.user_stories(user_id)
            self.rate_limiter.record_request()
            self._save_session()
            
            logger.debug("Got stories", user_id=user_id, count=len(stories))
            return stories
        except Exception as e:
            self._handle_api_error(e)
            raise

    def get_user_medias(self, user_id: str, amount: int = 20) -> list[Media]:
        """Get recent media (posts) for a user."""
        self.ensure_logged_in()
        
        if not self.rate_limiter.can_make_request():
            raise InstagramRateLimitError("Request limit reached")

        try:
            self.rate_limiter.wait_between_requests()
            medias = self._client.user_medias(user_id, amount=amount)
            self.rate_limiter.record_request()
            self._save_session()
            
            logger.debug("Got medias", user_id=user_id, count=len(medias))
            return medias
        except Exception as e:
            self._handle_api_error(e)
            raise

    def like_story(self, story_id: str, story_pk: str) -> bool:
        """Like a story."""
        self.ensure_logged_in()
        
        if not self.rate_limiter.can_like():
            raise InstagramRateLimitError("Like limit reached")

        try:
            self.rate_limiter.wait_between_likes()
            result = self._client.story_like(story_pk)
            self.rate_limiter.record_like()
            self.rate_limiter.record_request()
            self._save_session()
            
            logger.info("Story liked", story_pk=story_pk, success=result)
            return result
        except Exception as e:
            self._handle_api_error(e)
            raise

    def like_media(self, media_id: str) -> bool:
        """Like a media item (post)."""
        self.ensure_logged_in()
        
        if not self.rate_limiter.can_like():
            raise InstagramRateLimitError("Like limit reached")

        try:
            self.rate_limiter.wait_between_likes()
            result = self._client.media_like(media_id)
            self.rate_limiter.record_like()
            self.rate_limiter.record_request()
            self._save_session()
            
            logger.info("Media liked", media_id=media_id, success=result)
            return result
        except Exception as e:
            self._handle_api_error(e)
            raise

    def keep_alive(self) -> bool:
        """Perform a lightweight request to keep session alive."""
        self.ensure_logged_in()

        try:
            self.rate_limiter.wait_between_requests()
            # Use timeline to keep session active
            self._client.get_timeline_feed()
            self.rate_limiter.record_request()
            
            repo = self._get_session_repo()
            repo.update_last_request(self.settings.ig_username)
            self._save_session()
            
            logger.debug("Keep-alive successful")
            return True
        except Exception as e:
            logger.warning("Keep-alive failed", error=str(e))
            return False
