"""Main entry point for instaBackingApp."""

import signal
import sys
from datetime import datetime, timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from insta_backing_app.config import get_settings
from insta_backing_app.logging_config import configure_logging, get_logger
from insta_backing_app.models import init_db
from insta_backing_app.services import ProcessingOrchestrator

logger = None
scheduler: BlockingScheduler | None = None
orchestrator: ProcessingOrchestrator | None = None


def signal_handler(signum: int, frame) -> None:
    """Handle shutdown signals gracefully."""
    global scheduler
    sig_name = signal.Signals(signum).name
    logger.info("Received signal, shutting down", signal=sig_name)
    
    if scheduler:
        scheduler.shutdown(wait=False)
    
    sys.exit(0)


def run_processing_cycle() -> None:
    """Job function for running the processing cycle."""
    global orchestrator
    if orchestrator:
        try:
            orchestrator.run_cycle()
        except Exception as e:
            logger.error("Unexpected error in processing cycle", error=str(e))


def run_keep_alive() -> None:
    """Job function for session keep-alive."""
    global orchestrator
    if orchestrator:
        try:
            orchestrator.keep_alive()
        except Exception as e:
            logger.warning("Keep-alive failed", error=str(e))


def main() -> None:
    """Main entry point."""
    global logger, scheduler, orchestrator

    # Configure logging first
    configure_logging()
    logger = get_logger(__name__)

    logger.info("Starting instaBackingApp")

    # Load settings
    try:
        settings = get_settings()
    except Exception as e:
        logger.error("Failed to load settings", error=str(e))
        sys.exit(1)

    logger.info(
        "Configuration loaded",
        target_accounts=len(settings.target_usernames_list),
        cycle_seconds=settings.ig_cycle_seconds,
        process_stories=settings.ig_process_stories,
        process_posts=settings.ig_process_posts,
    )

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        sys.exit(1)

    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Create orchestrator
    orchestrator = ProcessingOrchestrator()

    # Create scheduler
    scheduler = BlockingScheduler()

    # Add processing job
    scheduler.add_job(
        run_processing_cycle,
        trigger=IntervalTrigger(seconds=settings.ig_cycle_seconds),
        id="processing_cycle",
        name="Main Processing Cycle",
        next_run_time=datetime.now(timezone.utc),  # Run immediately
    )

    # Add keep-alive job
    scheduler.add_job(
        run_keep_alive,
        trigger=IntervalTrigger(seconds=settings.ig_session_keepalive_seconds),
        id="keep_alive",
        name="Session Keep-Alive",
    )

    logger.info(
        "Scheduler configured",
        cycle_interval_seconds=settings.ig_cycle_seconds,
        keepalive_interval_seconds=settings.ig_session_keepalive_seconds,
    )

    # Start scheduler
    try:
        logger.info("Starting scheduler")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down")
    finally:
        if scheduler.running:
            scheduler.shutdown()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main()
