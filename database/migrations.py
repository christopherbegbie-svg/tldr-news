"""
Database schema setup. Run once at startup.
"""

import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS posted_stories (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash     TEXT    UNIQUE NOT NULL,
    title            TEXT,
    source           TEXT,
    url              TEXT,
    category         TEXT,
    posted_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    x_post_id        TEXT,
    instagram_post_id TEXT
);

CREATE TABLE IF NOT EXISTS run_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ran_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status     TEXT,
    message    TEXT
);

CREATE TABLE IF NOT EXISTS replied_mentions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    mention_id    TEXT UNIQUE NOT NULL,
    author_id     TEXT,
    author_name   TEXT,
    mention_text  TEXT,
    replied_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kv_store (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


def init_db(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()
