"""
Supplemental news fetcher via NewsAPI.org.
Only runs if NEWSAPI_KEY is configured.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from config.settings import get_settings
from news.models import Article

logger = logging.getLogger(__name__)

NEWSAPI_CATEGORIES = ["general", "technology", "business", "science"]
SOURCE_TRUST = 0.75  # NewsAPI sources get a slightly lower default trust


def fetch_newsapi() -> list[Article]:
    settings = get_settings()
    if not settings.newsapi_enabled:
        return []

    try:
        from newsapi import NewsApiClient
    except ImportError:
        logger.warning("newsapi-python not installed; skipping NewsAPI fetch.")
        return []

    client = NewsApiClient(api_key=settings.newsapi_key)
    articles: list[Article] = []

    for category in NEWSAPI_CATEGORIES:
        try:
            resp = client.get_top_headlines(
                category=category,
                language="en",
                page_size=10,
            )
            for item in resp.get("articles", []):
                title = (item.get("title") or "").strip()
                url = item.get("url") or ""
                description = (item.get("description") or "").strip()
                source_name = (item.get("source") or {}).get("name", "NewsAPI")
                published_raw: Optional[str] = item.get("publishedAt")

                if not title or not url or title == "[Removed]":
                    continue

                try:
                    published_at = datetime.strptime(
                        published_raw, "%Y-%m-%dT%H:%M:%SZ"
                    ) if published_raw else datetime.utcnow()
                except ValueError:
                    published_at = datetime.utcnow()

                articles.append(
                    Article(
                        title=title,
                        url=url,
                        source=source_name,
                        published_at=published_at,
                        summary=description[:500],
                        category=category if category != "general" else "world",
                        trust_score=SOURCE_TRUST,
                    )
                )
        except Exception as exc:
            logger.error("NewsAPI fetch failed for category '%s': %s", category, exc)

    logger.info("NewsAPI → %d articles total", len(articles))
    return articles
