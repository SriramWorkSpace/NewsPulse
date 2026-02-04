from __future__ import annotations

import aiosqlite


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS articles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  description TEXT,
  content TEXT,
  source_name TEXT,
  published_at TEXT NOT NULL,
  fetched_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_fetched_at ON articles(fetched_at);
"""


async def init_db(sqlite_path: str) -> None:
    async with aiosqlite.connect(sqlite_path) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def upsert_article(
    sqlite_path: str,
    *,
    url: str,
    title: str,
    description: str | None,
    content: str | None,
    source_name: str,
    published_at: str,
    fetched_at: str,
) -> None:
    async with aiosqlite.connect(sqlite_path) as db:
        await db.execute(
            """
            INSERT INTO articles(url, title, description, content, source_name, published_at, fetched_at)
            VALUES(?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
              title=excluded.title,
              description=excluded.description,
              content=excluded.content,
              source_name=excluded.source_name,
              published_at=excluded.published_at,
              fetched_at=excluded.fetched_at
            """,
            (url, title, description, content, source_name, published_at, fetched_at),
        )
        await db.commit()


async def delete_older_than(sqlite_path: str, *, cutoff_iso: str) -> int:
    async with aiosqlite.connect(sqlite_path) as db:
        cur = await db.execute("DELETE FROM articles WHERE fetched_at < ?", (cutoff_iso,))
        await db.commit()
        return cur.rowcount


async def fetch_articles_between_published(
    sqlite_path: str,
    *,
    start_iso: str,
    end_iso: str,
) -> list[dict]:
    async with aiosqlite.connect(sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            SELECT url, title, description, content, source_name, published_at
            FROM articles
            WHERE published_at >= ? AND published_at < ?
            """,
            (start_iso, end_iso),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_all_articles(sqlite_path: str) -> list[dict]:
    """Get all articles from the database."""
    async with aiosqlite.connect(sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            SELECT url, title, description, content, source_name, published_at
            FROM articles
            ORDER BY published_at DESC
            """
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]
