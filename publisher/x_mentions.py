"""
Fetches mentions of the TLDR account and replies to them using Claude.
Runs every 30 minutes via the scheduler.
"""

from __future__ import annotations

import logging
from typing import Optional

import anthropic

from config.settings import get_settings
from database import store as db
from summarizer.prompts import REPLY_SYSTEM_PROMPT, build_reply_prompt

logger = logging.getLogger(__name__)

# Don't reply to accounts with fewer followers than this (basic bot filter)
MIN_FOLLOWER_COUNT = 1

# Max replies per cycle (avoid burning credits if mentions spike)
MAX_REPLIES_PER_CYCLE = 10


def _get_client():
    try:
        import tweepy
    except ImportError:
        raise RuntimeError("tweepy not installed")

    settings = get_settings()
    return tweepy.Client(
        consumer_key=settings.x_api_key,
        consumer_secret=settings.x_api_secret,
        access_token=settings.x_access_token,
        access_token_secret=settings.x_access_secret,
        bearer_token=settings.x_bearer_token,
        wait_on_rate_limit=True,
    )


def _get_my_id(client) -> Optional[str]:
    cached = db.kv_get("x_user_id")
    if cached:
        return cached
    try:
        me = client.get_me()
        uid = str(me.data.id)
        db.kv_set("x_user_id", uid)
        return uid
    except Exception as exc:
        logger.error("Could not get X user ID: %s", exc)
        return None


def _is_spam(text: str) -> bool:
    spam_signals = ["follow back", "followback", "f4f", "dm me", "check my profile",
                    "click here", "free followers", "giveaway", "crypto", "nft"]
    lower = text.lower()
    return any(s in lower for s in spam_signals)


def _generate_reply(mention_text: str, post_topic: str) -> Optional[str]:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            system=REPLY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_reply_prompt(post_topic, mention_text)}],
        )
        reply = msg.content[0].text.strip()
        if reply.upper().startswith("SKIP") or not reply:
            return None
        # Hard cap at 270 chars to leave room for the @mention prefix X adds
        return reply[:270]
    except Exception as exc:
        logger.error("Claude reply generation failed: %s", exc)
        return None


def _get_post_topic(client, tweet_id: str) -> str:
    """Try to find what TLDR post was referenced. Falls back to generic."""
    try:
        tweet = client.get_tweet(
            tweet_id,
            tweet_fields=["referenced_tweets"],
            expansions=["referenced_tweets.id"],
        )
        if tweet.data and tweet.data.referenced_tweets:
            ref_id = str(tweet.data.referenced_tweets[0].id)
            # Check our DB for a post with this ID
            # (simple approach: just pull from the tweet text if available)
        return "global news"
    except Exception:
        return "global news"


def check_and_reply_mentions(dry_run: bool = False) -> int:
    """
    Fetch recent mentions and reply to ones we haven't answered yet.
    Returns number of replies sent.
    """
    settings = get_settings()
    if not settings.x_enabled:
        logger.warning("X not configured, skipping mention check.")
        return 0

    try:
        client = _get_client()
    except Exception as exc:
        logger.error("Could not create X client: %s", exc)
        return 0

    user_id = _get_my_id(client)
    if not user_id:
        return 0

    since_id = db.kv_get("mentions_since_id")
    replies_sent = 0

    try:
        kwargs = dict(
            id=user_id,
            max_results=20,
            tweet_fields=["author_id", "text", "referenced_tweets"],
            expansions=["author_id"],
            user_fields=["public_metrics"],
        )
        if since_id:
            kwargs["since_id"] = since_id

        response = client.get_users_mentions(**kwargs)

        if not response.data:
            logger.info("No new mentions.")
            return 0

        # Build author follower map
        author_followers: dict[str, int] = {}
        if response.includes and "users" in response.includes:
            for user in response.includes["users"]:
                metrics = getattr(user, "public_metrics", None)
                if metrics:
                    author_followers[str(user.id)] = metrics.get("followers_count", 0)

        # Process newest-first; track the highest ID seen
        newest_id = str(response.data[0].id)

        for tweet in response.data:
            mention_id = str(tweet.id)
            author_id = str(tweet.author_id)
            text = tweet.text or ""

            # Skip if already replied
            if db.has_replied(mention_id):
                continue

            # Skip spam
            if _is_spam(text):
                logger.info("Skipping spam mention %s", mention_id)
                db.record_reply(mention_id, author_id, "", text)
                continue

            # Skip low-follower accounts
            followers = author_followers.get(author_id, 0)
            if followers < MIN_FOLLOWER_COUNT:
                logger.info("Skipping low-follower mention %s (%d followers)", mention_id, followers)
                continue

            # Generate reply
            post_topic = _get_post_topic(client, mention_id)
            reply_text = _generate_reply(text, post_topic)

            if not reply_text:
                logger.info("Skipping mention %s (SKIP or empty reply)", mention_id)
                db.record_reply(mention_id, author_id, "", text)
                continue

            if dry_run:
                safe = lambda s: s.encode("ascii", errors="replace").decode("ascii")
                print(f"\n  [MENTION] {safe(text)}")
                print(f"  [REPLY]   {safe(reply_text)}\n")
                db.record_reply(mention_id, author_id, "", text)
                replies_sent += 1
            else:
                try:
                    client.create_tweet(
                        text=reply_text,
                        in_reply_to_tweet_id=mention_id,
                    )
                    logger.info("Replied to mention %s: %s", mention_id, reply_text[:60])
                    db.record_reply(mention_id, author_id, "", text)
                    replies_sent += 1
                except Exception as exc:
                    logger.error("Failed to reply to %s: %s", mention_id, exc)

            if replies_sent >= MAX_REPLIES_PER_CYCLE:
                break

        # Save watermark so next run only fetches new mentions
        db.kv_set("mentions_since_id", newest_id)
        logger.info("Mention check complete. Replied to %d mentions.", replies_sent)

    except Exception as exc:
        logger.error("Mention check failed: %s", exc)

    return replies_sent
