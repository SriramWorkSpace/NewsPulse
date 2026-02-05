"""
ML Results Cache - Store pre-computed ML analysis results in SQLite.

This allows ML models to be loaded only during polling (every 30 min),
not on every API request, drastically reducing memory usage.
"""
from __future__ import annotations

import json
import aiosqlite
from typing import Any


async def init_ml_cache_tables(db_path: str):
    """Create tables for cached ML results."""
    async with aiosqlite.connect(db_path) as db:
        # Article embeddings (for semantic similarity)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS article_embeddings (
                url TEXT PRIMARY KEY,
                embedding TEXT NOT NULL,  -- JSON array of floats
                computed_at TEXT NOT NULL
            )
        """)
        
        # Topic assignments
        await db.execute("""
            CREATE TABLE IF NOT EXISTS article_topics (
                url TEXT PRIMARY KEY,
                topic_id INTEGER NOT NULL,
                topic_label TEXT,
                keywords TEXT,  -- JSON array
                confidence REAL,
                computed_at TEXT NOT NULL
            )
        """)
        
        # Cluster assignments
        await db.execute("""
            CREATE TABLE IF NOT EXISTS article_clusters (
                url TEXT PRIMARY KEY,
                cluster_id INTEGER NOT NULL,
                cluster_size INTEGER,
                computed_at TEXT NOT NULL
            )
        """)
        
        # Breaking news scores (cached globally)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS breaking_news_cache (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                score REAL NOT NULL,
                signals TEXT NOT NULL,  -- JSON object
                detected_at TEXT NOT NULL,
                computed_at TEXT NOT NULL
            )
        """)
        
        # Topic summary (global cache)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS topics_cache (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                topics TEXT NOT NULL,  -- JSON array of topic objects
                total_articles INTEGER,
                uncategorized_count INTEGER,
                computed_at TEXT NOT NULL
            )
        """)
        
        await db.commit()


async def save_embeddings(db_path: str, embeddings: dict[str, list[float]]):
    """Save article embeddings. embeddings = {url: [0.1, 0.2, ...]}"""
    from datetime import datetime, UTC
    
    async with aiosqlite.connect(db_path) as db:
        now = datetime.now(UTC).isoformat()
        await db.executemany(
            "INSERT OR REPLACE INTO article_embeddings (url, embedding, computed_at) VALUES (?, ?, ?)",
            [(url, json.dumps(emb), now) for url, emb in embeddings.items()]
        )
        await db.commit()


async def get_embeddings(db_path: str) -> dict[str, list[float]]:
    """Retrieve all cached embeddings."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT url, embedding FROM article_embeddings") as cursor:
            rows = await cursor.fetchall()
            return {url: json.loads(emb_json) for url, emb_json in rows}


async def save_topics(db_path: str, topics: list[dict[str, Any]], article_assignments: dict[str, dict]):
    """
    Save topic modeling results.
    
    Args:
        topics: List of topic objects with {topic_id, label, keywords, count}
        article_assignments: {url: {topic_id, confidence}}
    """
    from datetime import datetime, UTC
    now = datetime.now(UTC).isoformat()
    
    async with aiosqlite.connect(db_path) as db:
        # Save global topics summary
        await db.execute(
            "INSERT OR REPLACE INTO topics_cache (id, topics, total_articles, uncategorized_count, computed_at) VALUES (?, ?, ?, ?, ?)",
            (1, json.dumps(topics), len(article_assignments), 0, now)
        )
        
        # Save per-article topic assignments
        for url, assignment in article_assignments.items():
            topic_info = next((t for t in topics if t['topic_id'] == assignment['topic_id']), None)
            await db.execute(
                "INSERT OR REPLACE INTO article_topics (url, topic_id, topic_label, keywords, confidence, computed_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    url,
                    assignment['topic_id'],
                    topic_info['label'] if topic_info else None,
                    json.dumps(topic_info['keywords'][:5]) if topic_info else None,
                    assignment.get('confidence'),
                    now
                )
            )
        
        await db.commit()


async def get_topics(db_path: str) -> dict[str, Any] | None:
    """Retrieve cached topic modeling results."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT topics, total_articles, uncategorized_count FROM topics_cache WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "topics": json.loads(row[0]),
                    "total_articles": row[1],
                    "uncategorized_count": row[2]
                }
    return None


async def save_clusters(db_path: str, clusters: dict[str, dict]):
    """
    Save clustering results.
    
    Args:
        clusters: {url: {cluster_id, cluster_size}}
    """
    from datetime import datetime, UTC
    now = datetime.now(UTC).isoformat()
    
    async with aiosqlite.connect(db_path) as db:
        await db.executemany(
            "INSERT OR REPLACE INTO article_clusters (url, cluster_id, cluster_size, computed_at) VALUES (?, ?, ?, ?)",
            [(url, info['cluster_id'], info['cluster_size'], now) for url, info in clusters.items()]
        )
        await db.commit()


async def get_clusters(db_path: str) -> dict[str, dict]:
    """Retrieve all cached cluster assignments."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT url, cluster_id, cluster_size FROM article_clusters") as cursor:
            rows = await cursor.fetchall()
            return {url: {"cluster_id": cid, "cluster_size": size} for url, cid, size in rows}


async def save_breaking_news(db_path: str, score: float, signals: dict[str, Any]):
    """Save breaking news detection result."""
    from datetime import datetime, UTC
    now = datetime.now(UTC).isoformat()
    
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT OR REPLACE INTO breaking_news_cache (id, score, signals, detected_at, computed_at) VALUES (?, ?, ?, ?, ?)",
            (1, score, json.dumps(signals), now if score >= 60 else None, now)
        )
        await db.commit()


async def get_breaking_news(db_path: str) -> dict[str, Any] | None:
    """Retrieve cached breaking news result."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT score, signals, detected_at FROM breaking_news_cache WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "score": row[0],
                    "signals": json.loads(row[1]),
                    "is_breaking": row[0] >= 60,
                    "detected_at": row[2]
                }
    return None


async def cleanup_old_cache(db_path: str, retention_hours: int = 48):
    """Remove cached data for articles older than retention period."""
    from datetime import datetime, UTC, timedelta
    
    cutoff = (datetime.now(UTC) - timedelta(hours=retention_hours)).isoformat()
    
    async with aiosqlite.connect(db_path) as db:
        # Get valid article URLs
        async with db.execute("SELECT url FROM articles WHERE published_at > ?", (cutoff,)) as cursor:
            valid_urls = {row[0] for row in await cursor.fetchall()}
        
        # Delete cache entries for removed articles
        if valid_urls:
            placeholders = ','.join('?' * len(valid_urls))
            for table in ['article_embeddings', 'article_topics', 'article_clusters']:
                await db.execute(f"DELETE FROM {table} WHERE url NOT IN ({placeholders})", list(valid_urls))
        
        await db.commit()
