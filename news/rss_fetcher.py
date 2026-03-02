"""
Fetches articles from RSS feeds using feedparser.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

import feedparser

from config.feeds import RSS_FEEDS
from news.models import Article

logger = logging.getLogger(__name__)


def _parse_date(entry: feedparser.FeedParserDict) -> datetime:
    """Best-effort datetime extraction from a feed entry."""
    for attr in ("published", "updated"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                return dt.astimezone(timezone.utc).replace(tzinfo=None)
            except Exception:
                pass
    return datetime.utcnow()


def _clean(text: Optional[str]) -> str:
    if not text:
        return ""
    # Strip basic HTML tags
    import re
    return re.sub(r"<[^>]+>", "", text).strip()


def fetch_from_feed(feed_config: dict) -> list[Article]:
    """Fetch articles from a single RSS feed config dict."""
    articles: list[Article] = []
    try:
        parsed = feedparser.parse(feed_config["url"])
        if parsed.bozo and not parsed.entries:
            logger.warning("Feed parse error for %s: %s", feed_config["name"], parsed.bozo_exception)
            return articles

        for entry in parsed.entries[:20]:  # cap at 20 per feed
            title = _clean(getattr(entry, "title", ""))
            url = getattr(entry, "link", "")
            summary = _clean(getattr(entry, "summary", ""))

            if not title or not url:
                continue

            articles.append(
                Article(
                    title=title,
                    url=url,
                    source=feed_config["name"],
                    published_at=_parse_date(entry),
                    summary=summary[:500],
                    category=feed_config["category"],
                    trust_score=feed_config["trust"],
                )
            )
    except Exception as exc:
        logger.error("Failed to fetch %s: %s", feed_config["name"], exc)
    return articles


def fetch_all_rss() -> list[Article]:
    """Fetch from every configured RSS feed."""
    all_articles: list[Article] = []
    for feed in RSS_FEEDS:
        fetched = fetch_from_feed(feed)
        logger.info("RSS %s → %d articles", feed["name"], len(fetched))
        all_articles.extend(fetched)
    return all_articles
