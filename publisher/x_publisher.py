"""
Posts tweet threads to X (Twitter) using tweepy + Twitter API v2.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from config.settings import get_settings

logger = logging.getLogger(__name__)


def _get_client():
    """Build a tweepy.Client with OAuth 1.0a credentials."""
    try:
        import tweepy
    except ImportError:
        raise RuntimeError("tweepy not installed. Run: pip install tweepy")

    settings = get_settings()
    if not settings.x_enabled:
        raise RuntimeError(
            "X credentials not configured. Set X_API_KEY, X_API_SECRET, "
            "X_ACCESS_TOKEN, X_ACCESS_SECRET in .env"
        )

    return tweepy.Client(
        consumer_key=settings.x_api_key,
        consumer_secret=settings.x_api_secret,
        access_token=settings.x_access_token,
        access_token_secret=settings.x_access_secret,
        bearer_token=settings.x_bearer_token,
        wait_on_rate_limit=True,
    )


def post_thread(tweets: list[str], dry_run: bool = False) -> Optional[str]:
    """
    Post a list of tweet strings as a thread.
    Returns the URL of the first tweet, or None on failure.

    In dry_run mode, prints the tweets without posting.
    """
    if not tweets:
        logger.warning("post_thread called with empty list")
        return None

    if dry_run:
        safe = lambda s: s.encode("ascii", errors="replace").decode("ascii")
        print("\n-- X Thread (DRY RUN) -------------------------------------")
        for i, tweet in enumerate(tweets, 1):
            print(f"  [{i}] {safe(tweet)}")
        print("-----------------------------------------------------------\n")
        return "dry-run://x/thread"

    try:
        client = _get_client()
        first_id: Optional[str] = None
        reply_to: Optional[str] = None

        for i, text in enumerate(tweets):
            # Enforce 280-char hard limit just in case
            text = text[:280]
            kwargs: dict = {"text": text}
            if reply_to:
                kwargs["in_reply_to_tweet_id"] = reply_to

            response = client.create_tweet(**kwargs)
            tweet_id = str(response.data["id"])

            if i == 0:
                first_id = tweet_id
            reply_to = tweet_id

            logger.info("Posted tweet %d/%d (id=%s)", i + 1, len(tweets), tweet_id)
            if i < len(tweets) - 1:
                time.sleep(1)  # small delay between replies

        username = _get_username(client)
        url = f"https://twitter.com/{username}/status/{first_id}" if username else None
        logger.info("Thread posted: %s", url)
        return url

    except Exception as exc:
        logger.error("Failed to post X thread: %s", exc)
        return None


def _get_username(client) -> Optional[str]:
    try:
        me = client.get_me()
        return me.data.username
    except Exception:
        return None
