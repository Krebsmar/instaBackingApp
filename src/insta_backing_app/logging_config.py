"""Structured logging configuration using structlog."""

import logging
import sys
from typing import Any

import structlog
from structlog.typing import Processor

from insta_backing_app.config import get_settings


def _drop_exc_info(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Remove exc_info from log events to prevent stacktrace spam."""
    event_dict.pop("exc_info", None)
    return event_dict


def configure_logging() -> None:
    """Configure structured logging based on settings."""
    settings = get_settings()

    # Determine processors based on format
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
        _drop_exc_info,  # Remove exc_info to prevent stacktrace spam
    ]

    if settings.log_format == "json":
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level)

    # Silence noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    # Completely disable instagrapi and pydantic loggers (they spam HTML dumps and validation errors)
    for logger_name in ["instagrapi", "pydantic", "private_request", "public_request"]:
        noisy_logger = logging.getLogger(logger_name)
        noisy_logger.disabled = True


def get_logger(name: str) -> Any:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
