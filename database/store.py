"""
Persistence layer — tracks posted stories to prevent duplicates.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import get_settings


def _conn() -> sqlite3.Connection:
    settings = get_settings()
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def is_duplicate(content_hash: str) -> bool:
    """Return True if this story has already been posted."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT id FROM posted_stories WHERE content_hash = ?",
            (content_hash,),
        ).fetchone()
    return row is not None


def record_post(
    content_hash: str,
    title: str,
    source: str,
    url: str,
    category: str,
    x_post_id: Optional[str] = None,
    instagram_post_id: Optional[str] = None,
) -> None:
    """Mark a story as posted."""
    with _conn() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO posted_stories
                (content_hash, title, source, url, category, x_post_id, instagram_post_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (content_hash, title, source, url, category, x_post_id, instagram_post_id),
        )
        conn.commit()


def log_run(status: str, message: str = "") -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO run_log (status, message) VALUES (?, ?)",
            (status, message),
        )
        conn.commit()


def recent_hashes(hours: int = 48) -> set[str]:
    """Return content hashes posted in the last N hours (for fuzzy dedup)."""
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT content_hash FROM posted_stories
            WHERE posted_at >= datetime('now', ? || ' hours')
            """,
            (f"-{hours}",),
        ).fetchall()
    return {r["content_hash"] for r in rows}


# ── Mention reply tracking ─────────────────────────────────────────────────────

def has_replied(mention_id: str) -> bool:
    with _conn() as conn:
        row = conn.execute(
            "SELECT id FROM replied_mentions WHERE mention_id = ?",
            (mention_id,),
        ).fetchone()
    return row is not None


def record_reply(mention_id: str, author_id: str, author_name: str, mention_text: str) -> None:
    with _conn() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO replied_mentions
               (mention_id, author_id, author_name, mention_text)
               VALUES (?, ?, ?, ?)""",
            (mention_id, author_id, author_name, mention_text),
        )
        conn.commit()


# ── Key-value store (for since_id etc.) ───────────────────────────────────────

def kv_get(key: str) -> Optional[str]:
    with _conn() as conn:
        row = conn.execute("SELECT value FROM kv_store WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def kv_set(key: str, value: str) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()
