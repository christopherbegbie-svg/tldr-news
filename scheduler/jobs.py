"""
Orchestrates the full TLDR posting pipeline and schedules it.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config.settings import get_settings
from database import migrations, store as db
from news import aggregator
from publisher import image_generator, instagram_publisher, web_publisher, x_publisher, x_mentions
from summarizer import claude_client

logger = logging.getLogger(__name__)


def run_posting_cycle(dry_run: Optional[bool] = None) -> None:
    """
    Full pipeline: fetch → score → deduplicate → summarize → post.
    """
    settings = get_settings()
    if dry_run is None:
        dry_run = settings.dry_run

    logger.info("=== TLDR posting cycle started (dry_run=%s) ===", dry_run)
    db.log_run("started")

    try:
        # 1. Fetch + deduplicate + score
        articles = aggregator.fetch_all()
        if not articles:
            logger.warning("No new articles found this cycle.")
            db.log_run("skipped", "No new articles")
            return

        # Every 3rd post, prefer a politics story
        post_count = int(db.kv_get("post_count") or "0")
        if post_count % 3 == 2:
            politics = [a for a in articles if a.category == "politics"]
            top = aggregator.select_top(politics if politics else articles, n=1)
            logger.info("Politics rotation (post #%d)", post_count)
        else:
            top = aggregator.select_top(articles, n=1)
        db.kv_set("post_count", str(post_count + 1))

        article = top[0]
        logger.info("Selected: [%s] %s", article.source, article.title)

        # 2. Summarize with Claude
        summary = claude_client.summarize(article)
        if summary is None:
            logger.warning("Summarization failed for '%s' — skipping cycle.", article.title)
            db.log_run("skipped", f"Summarization failed: {article.title[:80]}")
            return
        logger.info("Summarized headline: %s", summary["headline"])

        # 3. Generate image card
        image_path: Optional[Path] = None
        try:
            image_path = image_generator.create_card(article, summary)
        except Exception as exc:
            logger.error("Image generation failed: %s", exc)

        # 4. Post to X (attach image card to tweet 1)
        x_post_id: Optional[str] = None
        if settings.x_enabled or dry_run:
            x_post_id = x_publisher.post_thread(
                summary["x_thread"], dry_run=dry_run, image_path=image_path
            )

        # 5. Upload image permanently for website (before Instagram uses/deletes it)
        web_image_url: Optional[str] = None
        if image_path:
            web_image_url = instagram_publisher.upload_for_web(image_path)

        # 6. Post to Instagram (max 3 per UTC day)
        ig_post_id: Optional[str] = None
        today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ig_date = db.kv_get("ig_posts_date") or ""
        ig_count = int(db.kv_get("ig_posts_count") or "0")
        if ig_date != today_utc:
            ig_count = 0
            db.kv_set("ig_posts_date", today_utc)
            db.kv_set("ig_posts_count", "0")
        ig_allowed = ig_count < 3

        if image_path and (settings.instagram_enabled or dry_run) and ig_allowed:
            ig_post_id = instagram_publisher.post(
                image_path,
                summary["instagram_caption"],
                dry_run=dry_run,
            )
            if ig_post_id and not dry_run:
                db.kv_set("ig_posts_count", str(ig_count + 1))
            logger.info("Instagram post %d/3 today.", ig_count + 1)
        elif not ig_allowed:
            logger.info("Instagram daily limit reached (3/3) — skipping.")

        # 7. Publish to website
        web_publisher.publish_story(
            article,
            summary,
            image_url=web_image_url,
            adsense_id=settings.adsense_publisher_id,
        )
        logger.info("Web story published.")

        # 8. Record in DB (even in dry_run, so we don't re-select same story)
        if not dry_run:
            db.record_post(
                content_hash=article.content_hash,
                title=article.title,
                source=article.source,
                url=article.url,
                category=article.category,
                x_post_id=x_post_id,
                instagram_post_id=ig_post_id,
            )

        # 9. Clean up temp image
        if image_path and image_path.exists():
            try:
                os.unlink(image_path)
            except Exception:
                pass

        db.log_run("success", f"Posted: {article.title[:80]}")
        logger.info("=== Cycle complete ===")

    except Exception as exc:
        logger.exception("Cycle failed: %s", exc)
        db.log_run("error", str(exc))


def start_scheduler() -> None:
    """Start the APScheduler blocking scheduler on configured post times."""
    settings = get_settings()

    # Initialise DB
    migrations.init_db(settings.db_path)

    scheduler = BlockingScheduler(timezone="UTC")

    for time_str in settings.post_times_list:
        try:
            hour, minute = time_str.split(":")
            scheduler.add_job(
                run_posting_cycle,
                CronTrigger(hour=int(hour), minute=int(minute), timezone="UTC"),
                id=f"tldr_{time_str.replace(':', '')}",
                name=f"TLDR post at {time_str} UTC",
                misfire_grace_time=300,  # 5 min grace if system was sleeping
            )
            logger.info("Scheduled post at %s UTC", time_str)
        except ValueError:
            logger.error("Invalid time format in POST_TIMES: '%s'", time_str)

    # Check and reply to mentions every 30 minutes
    scheduler.add_job(
        x_mentions.check_and_reply_mentions,
        "interval",
        minutes=30,
        id="tldr_mentions",
        name="TLDR reply to mentions",
        misfire_grace_time=120,
    )
    logger.info("Mention replies scheduled every 30 minutes.")

    logger.info(
        "Scheduler started. Posting at: %s UTC",
        ", ".join(settings.post_times_list),
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
