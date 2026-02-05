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


async def get_recent_articles(sqlite_path: str, hours: int = 24) -> list[dict]:
    """
    Get articles from the last N hours.

    Args:
        sqlite_path: Path to SQLite database
        hours: Number of hours to look back

    Returns:
        List of article dictionaries ordered by published_at DESC
    """
    from datetime import UTC, datetime, timedelta

    cutoff = (datetime.now(tz=UTC) - timedelta(hours=hours)).isoformat()

    async with aiosqlite.connect(sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            SELECT url, title, description, content, source_name, published_at
            FROM articles
            WHERE published_at >= ?
            ORDER BY published_at DESC
            """,
            (cutoff,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_articles_in_timerange(
    sqlite_path: str, start_iso: str, end_iso: str
) -> list[dict]:
    """
    Get articles within a specific time range.

    Args:
        sqlite_path: Path to SQLite database
        start_iso: Start time in ISO format
        end_iso: End time in ISO format

    Returns:
        List of article dictionaries
    """
    async with aiosqlite.connect(sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            SELECT url, title, description, content, source_name, published_at
            FROM articles
            WHERE published_at >= ? AND published_at < ?
            ORDER BY published_at DESC
            """,
            (start_iso, end_iso),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def count_articles_by_hour(sqlite_path: str, hours_ago: int = 24) -> dict[int, int]:
    """
    Count articles by hour for the last N hours.

    Args:
        sqlite_path: Path to SQLite database
        hours_ago: How many hours to look back

    Returns:
        Dictionary mapping hour offset (0=current hour, 1=last hour, etc.) to count
    """
    from datetime import UTC, datetime, timedelta

    now = datetime.now(tz=UTC)
    cutoff = now - timedelta(hours=hours_ago)

    async with aiosqlite.connect(sqlite_path) as db:
        cur = await db.execute(
            """
            SELECT published_at
            FROM articles
            WHERE published_at >= ?
            """,
            (cutoff.isoformat(),),
        )
        rows = await cur.fetchall()

        # Group by hour
        counts: dict[int, int] = {}
        for row in rows:
            published_dt = datetime.fromisoformat(row[0])
            hours_diff = int((now - published_dt).total_seconds() / 3600)
            if hours_diff >= 0 and hours_diff < hours_ago:
                counts[hours_diff] = counts.get(hours_diff, 0) + 1

        return counts

