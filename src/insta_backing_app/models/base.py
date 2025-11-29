"""SQLAlchemy base model and database setup."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from insta_backing_app.config import get_settings


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


_engine = None
_SessionFactory = None


def get_engine():
    """Get or create database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {}
        if settings.database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(
            settings.database_url,
            connect_args=connect_args,
            echo=False,
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Get or create session factory."""
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionFactory


def init_db() -> None:
    """Initialize database and create tables."""
    from insta_backing_app.models.story import Story
    from insta_backing_app.models.post import Post
    from insta_backing_app.models.session import SessionData
    from insta_backing_app.models.rate_limit import RateLimitCounter
    from insta_backing_app.models.target_account import TargetAccount

    engine = get_engine()
    Base.metadata.create_all(engine)


def get_db_session() -> Session:
    """Get a new database session."""
    factory = get_session_factory()
    return factory()