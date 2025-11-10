"""Entry points for Poetry console scripts."""

import sys

from celery.__main__ import main as celery_main


def celery_worker() -> None:
    """Launch Celery worker with project settings."""
    sys.argv = ["celery", "-A", "config", "worker", "-l", "info"]
    celery_main()


def celery_beat() -> None:
    """Launch Celery beat with project settings."""
    sys.argv = ["celery", "-A", "config", "beat", "-l", "info"]
    celery_main()

