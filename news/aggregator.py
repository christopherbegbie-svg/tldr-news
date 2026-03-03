"""
Aggregates RSS + NewsAPI articles, deduplicates, scores, and selects
the best story to post each cycle.
"""

from __future__ import annotations

import difflib
import logging
from typing import Optional

from database import store as db
from news.models import Article
from news.newsapi_fetcher import fetch_newsapi
from news.rss_fetcher import fetch_all_rss

logger = logging.getLogger(__name__)

# If two titles have similarity >= this threshold they are considered duplicates
SIMILARITY_THRESHOLD = 0.75


def _titles_similar(a: str, b: str) -> bool:
    ratio = difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
    return ratio >= SIMILARITY_THRESHOLD


def deduplicate(articles: list[Article]) -> list[Article]:
    """
    Remove duplicates in two passes:
    1. Cross-article fuzzy title dedup (keep highest-scoring version)
    2. DB check — skip anything already posted in the last 48 hours
    """
    recent = db.recent_hashes(hours=48)

    # Pass 1: fuzzy within this batch
    seen_titles: list[str] = []
    unique: list[Article] = []
    for article in sorted(articles, key=lambda a: a.score(), reverse=True):
        if article.content_hash in recent:
            continue
        if any(_titles_similar(article.title, t) for t in seen_titles):
            continue
        seen_titles.append(article.title)
        unique.append(article)

    return unique


MIN_SUMMARY_LENGTH = 150  # skip articles with near-empty excerpts


def fetch_all() -> list[Article]:
    """Pull from all sources and return deduplicated, scored articles."""
    rss = fetch_all_rss()
    api = fetch_newsapi()
    combined = rss + api
    logger.info("Total before dedup: %d articles", len(combined))
    # Drop articles with no useful excerpt — Claude can't summarise them
    combined = [a for a in combined if len(a.summary.strip()) >= MIN_SUMMARY_LENGTH]
    deduped = deduplicate(combined)
    logger.info("Total after dedup: %d articles", len(deduped))
    return deduped


def select_top(articles: list[Article], n: int = 1) -> list[Article]:
    """Return the top-N articles by score."""
    ranked = sorted(articles, key=lambda a: a.score(), reverse=True)
    return ranked[:n]
