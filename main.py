#!/usr/bin/env python3
"""
TLDR News Auto-Poster
─────────────────────
Usage:
  python main.py               → Start scheduled daemon (posts at configured times)
  python main.py --dry-run     → Run one cycle now, print output, don't post
  python main.py --post-now    → Run one cycle now and actually post
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to sys.path so imports work from any cwd
sys.path.insert(0, str(Path(__file__).resolve().parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("tldr")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TLDR — Global news auto-poster for X and Instagram"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch, summarize, and print — do NOT post to social media",
    )
    mode.add_argument(
        "--post-now",
        action="store_true",
        help="Run one posting cycle immediately (actually posts)",
    )
    args = parser.parse_args()

    # Late imports so .env is loaded before settings are accessed
    from config.settings import get_settings
    from database import migrations

    settings = get_settings()
    migrations.init_db(settings.db_path)

    if args.dry_run:
        logger.info("Running in DRY RUN mode — no posts will be made.")
        from scheduler.jobs import run_posting_cycle
        run_posting_cycle(dry_run=True)

    elif args.post_now:
        logger.info("Running immediate posting cycle.")
        from scheduler.jobs import run_posting_cycle
        run_posting_cycle(dry_run=False)

    else:
        logger.info("Starting TLDR scheduler daemon.")
        from scheduler.jobs import start_scheduler
        start_scheduler()


if __name__ == "__main__":
    main()
