"""Instagram client wrapper using instagrapi."""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar

from instagrapi import Client
from instagrapi.exceptions import (
    ChallengeRequired,
    LoginRequired,
    PleaseWaitFewMinutes,
    RateLimitError,
)
from instagrapi.types import Media, Story
from pydantic import ValidationError

from insta_backing_app.config import get_settings
from insta_backing_app.logging_config import get_logger
from insta_backing_app.models import get_db_session
from insta_backing_app.repositories import SessionRepository
from insta_backing_app.services.rate_limiter import RateLimiter

logger = get_logger(__name__)

T = TypeVar("T")


class InstagramClientError(Exception):
    pass


class InstagramRateLimitError(InstagramClientError):
    pass


class InstagramChallengeError(InstagramClientError):
    pass


class InstagramLoginError(InstagramClientError):
    pass


class InstagramClient:
    def __init__(self, rate_limiter: RateLimiter):
        self.settings = get_settings()
        self.rate_limiter = rate_limiter
        self._client: Client | None = None
        self._user_id_cache: dict[str, str] = {}
        self._graphql_failures: int = 0
        self._graphql_disabled_until: float = 0

    def _get_session_repo(self) -> SessionRepository:
        return SessionRepository(get_db_session())

    def _create_client(self) -> Client:
        client = Client()
        client.delay_range = [1, 3]
        # Completely disable instagrapi's verbose loggers (they spam HTML dumps)
        client.logger.disabled = True
        client.private_request_logger.disabled = True
        client.public_request_logger.disabled = True
        return client

    def _load_session(self) -> bool:
        repo = self._get_session_repo()
        session_data = repo.get_valid_session(self.settings.ig_username)

        if session_data is None:
            logger.debug("No valid session found in database")
            return False

        try:
            self._client = self._create_client()
            settings = json.loads(session_data.session_json)
            self._client.set_settings(settings)
            self._client.login(self.settings.ig_username, self.settings.ig_password)

            # Validate session with a test request
            if not self._validate_session():
                logger.warning("Loaded session invalid, performing fresh login")
                repo.invalidate(self.settings.ig_username)
                self._client = None
                return False

            logger.info("Session loaded and validated", username=self.settings.ig_username)
            return True
        except Exception as e:
            logger.warning("Failed to load session", error=str(e))
            repo.invalidate(self.settings.ig_username)
            self._client = None
            return False

    def _validate_session(self) -> bool:
        """Validate session by making a test request."""
        if self._client is None:
            return False
        try:
            self._client.get_timeline_feed()
            return True
        except (LoginRequired, KeyError):
            return False
        except Exception:
            # Other errors (rate limit, network) don't mean session is invalid
            return True

    def _save_session(self) -> None:
        if self._client is None:
            return
        try:
            repo = self._get_session_repo()
            settings_json = json.dumps(self._client.get_settings())
            repo.save(self.settings.ig_username, settings_json)
        except Exception as e:
            logger.warning("Failed to save session (non-critical)", error=str(e))

    def _fresh_login(self) -> None:
        self._client = self._create_client()

        for attempt in range(1, self.settings.ig_max_login_attempts + 1):
            try:
                logger.info("Attempting login", username=self.settings.ig_username, attempt=attempt)
                self._client.login(self.settings.ig_username, self.settings.ig_password)
                self._save_session()
                logger.info("Login successful", username=self.settings.ig_username)
                return
            except ChallengeRequired:
                self._invalidate_session()
                raise InstagramChallengeError("Challenge required")
            except PleaseWaitFewMinutes:
                self.rate_limiter.apply_backoff()
            except Exception as e:
                logger.error("Login failed", attempt=attempt, error=str(e))
                if attempt == self.settings.ig_max_login_attempts:
                    self._invalidate_session()
                    raise InstagramLoginError(f"Login failed after {attempt} attempts: {e}")
                self.rate_limiter.apply_backoff()

    def _invalidate_session(self) -> None:
        """Mark current session as invalid in database."""
        try:
            repo = self._get_session_repo()
            repo.invalidate(self.settings.ig_username)
        except Exception as e:
            logger.warning("Failed to invalidate session", error=str(e))

    def relogin(self) -> bool:
        """Force a fresh login, invalidating the current session."""
        logger.info("Performing relogin", username=self.settings.ig_username)
        self._client = None
        self._invalidate_session()
        try:
            self._fresh_login()
            return True
        except (InstagramLoginError, InstagramChallengeError) as e:
            logger.error("Relogin failed", error=str(e))
            return False

    def _with_relogin(self, operation: Callable[[], T]) -> T:
        """Execute operation with automatic relogin on session expiry."""
        try:
            return operation()
        except LoginRequired:
            logger.warning("Session expired, attempting relogin")
            if self.relogin():
                return operation()
            raise InstagramLoginError("Session expired and relogin failed")

    def ensure_logged_in(self) -> None:
        if self._client is not None:
            return
        if not self._load_session():
            self._fresh_login()

    def _handle_api_error(self, e: Exception) -> None:
        if isinstance(e, (RateLimitError, PleaseWaitFewMinutes)):
            raise InstagramRateLimitError(str(e))
        elif isinstance(e, ChallengeRequired):
            self._invalidate_session()
            raise InstagramChallengeError(str(e))
        elif isinstance(e, LoginRequired):
            self._client = None
            self._invalidate_session()
            raise InstagramLoginError("Session expired")
        else:
            raise InstagramClientError(str(e))

    def _handle_graphql_error(self) -> None:
        """Track GraphQL failures and disable if too many consecutive errors."""
        self._graphql_failures += 1
        if self._graphql_failures >= 3:
            self._graphql_disabled_until = time.time() + 3600  # 1 hour
            logger.debug("GraphQL disabled for 1 hour due to consecutive failures")

    def _reset_graphql_failures(self) -> None:
        """Reset GraphQL failure counter on success."""
        self._graphql_failures = 0

    def _is_graphql_available(self) -> bool:
        """Check if GraphQL API is currently available."""
        if time.time() > self._graphql_disabled_until:
            return True
        return False

    def get_user_id(self, username: str) -> str:
        if username in self._user_id_cache:
            return self._user_id_cache[username]

        self.ensure_logged_in()

        if not self.rate_limiter.can_make_request():
            raise InstagramRateLimitError("Request limit reached")

        self.rate_limiter.wait_between_requests()

        def _fetch() -> str:
            result = self._client.private_request(f"users/{username}/usernameinfo/")
            return str(result["user"]["pk"])

        user_id = self._with_relogin(_fetch)
        self._user_id_cache[username] = user_id
        self.rate_limiter.record_request()
        logger.info("Resolved user ID", username=username, user_id=user_id)
        return user_id

    def get_user_stories(self, user_id: str) -> list[Story]:
        self.ensure_logged_in()

        if not self.rate_limiter.can_make_request():
            raise InstagramRateLimitError("Request limit reached")

        self.rate_limiter.wait_between_requests()

        def _fetch() -> list[Story]:
            return self._client.user_stories(user_id)

        stories = self._with_relogin(_fetch)
        self.rate_limiter.record_request()
        return stories

    def _fetch_medias_raw(self, user_id: str, amount: int) -> list[dict[str, Any]]:
        """Fetch raw media data from private API without parsing."""
        medias = []
        end_cursor = None
        while len(medias) < amount:
            result = self._client.private_request(
                f"feed/user/{user_id}/",
                params={"max_id": end_cursor, "count": min(amount - len(medias), 12)},
            )
            items = result.get("items", [])
            if not items:
                break
            medias.extend(items)
            end_cursor = result.get("next_max_id")
            if not end_cursor:
                break
        return medias[:amount]

    def get_user_medias(self, user_id: str, amount: int = 20) -> list[Media]:
        self.ensure_logged_in()

        if not self.rate_limiter.can_make_request():
            raise InstagramRateLimitError("Request limit reached")

        self.rate_limiter.wait_between_requests()

        def _fetch() -> list[Media]:
            # Try GraphQL first if available, fall back to private API
            if self._is_graphql_available():
                try:
                    medias = self._client.user_medias(user_id, amount=amount)
                    self._reset_graphql_failures()
                    return medias
                except KeyError as e:
                    if "data" in str(e):
                        logger.debug("GraphQL response invalid, using private API")
                        self._handle_graphql_error()
                    else:
                        raise
                except ValidationError:
                    logger.debug("GraphQL parsing failed, using private API")
                    self._handle_graphql_error()

            # Use private API with graceful error handling
            try:
                return self._client.user_medias_v1(user_id, amount=amount)
            except ValidationError:
                # Pydantic can't parse some media types (Reels), fetch raw and parse individually
                logger.warning("Media parsing error, fetching individually", user_id=user_id)
                raw_items = self._fetch_medias_raw(user_id, amount)
                parsed_medias = []
                for item in raw_items:
                    try:
                        media = Media(**self._client._extract_media_v1(item))
                        parsed_medias.append(media)
                    except ValidationError:
                        # Skip unparseable items (Reels with missing fields)
                        media_type = item.get("media_type", "unknown")
                        product_type = item.get("product_type", "")
                        logger.debug("Skipping unparseable media", media_type=media_type, product_type=product_type)
                        continue
                return parsed_medias

        medias = self._with_relogin(_fetch)
        self.rate_limiter.record_request()
        return medias

    def like_story(self, story_id: str, story_pk: str) -> bool:
        self.ensure_logged_in()

        if not self.rate_limiter.can_like():
            raise InstagramRateLimitError("Like limit reached")

        self.rate_limiter.wait_between_likes()

        def _like() -> bool:
            return self._client.story_like(story_pk)

        result = self._with_relogin(_like)
        self.rate_limiter.record_like()
        self.rate_limiter.record_request()
        self._save_session()
        logger.info("Story liked", story_pk=story_pk)
        return result

    def like_media(self, media_id: str) -> bool:
        self.ensure_logged_in()

        if not self.rate_limiter.can_like():
            raise InstagramRateLimitError("Like limit reached")

        self.rate_limiter.wait_between_likes()

        def _like() -> bool:
            return self._client.media_like(media_id)

        result = self._with_relogin(_like)
        self.rate_limiter.record_like()
        self.rate_limiter.record_request()
        self._save_session()
        logger.info("Media liked", media_id=media_id)
        return result

    def keep_alive(self) -> bool:
        self.ensure_logged_in()
        try:
            def _ping() -> bool:
                self._client.get_timeline_feed()
                return True

            self._with_relogin(_ping)
            self._save_session()
            return True
        except InstagramLoginError:
            logger.error("Keep-alive failed: session expired and relogin failed")
            return False
        except Exception as e:
            logger.warning("Keep-alive failed", error=str(e))
            return False