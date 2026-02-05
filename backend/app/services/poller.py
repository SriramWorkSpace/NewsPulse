from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.services.db import delete_older_than, init_db, upsert_article
from app.services.newsapi_client import NewsAPIClient
from app.services.ml_cache import init_ml_cache_tables
from app.services.ml_processor import run_ml_processing


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _cutoff_iso(hours: int) -> str:
    return (datetime.now(tz=UTC) - timedelta(hours=hours)).isoformat()


class HeadlinePoller:
    def __init__(self, *, sqlite_path: str) -> None:
        self._sqlite_path = sqlite_path
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._client = NewsAPIClient()

    async def start(self) -> None:
        await init_db(self._sqlite_path)
        await init_ml_cache_tables(self._sqlite_path)
        self._task = asyncio.create_task(self._run(), name="headline_poller")

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            await self._task
        await self._client.close()

    async def _poll_once(self) -> None:
        """Execute a single poll cycle."""
        fetched_at = _now_iso()
        try:
            resp = await self._client.top_headlines(
                country=settings.poll_country,
                language=settings.poll_language,
                page_size=100,
            )
            for a in resp.articles:
                await upsert_article(
                    self._sqlite_path,
                    url=a.url,
                    title=a.title,
                    description=a.description,
                    content=a.content,
                    source_name=a.source.name,
                    published_at=a.publishedAt,
                    fetched_at=fetched_at,
                )

            cutoff = _cutoff_iso(settings.retention_hours)
            await delete_older_than(self._sqlite_path, cutoff_iso=cutoff)
            
            # Run ML processing after successful poll
            print(f"📊 Poll complete - fetched {len(resp.articles)} articles", flush=True)
            await run_ml_processing(self._sqlite_path)
            
        except Exception as e:
            # v1: swallow poll errors to keep API serving; surfaced via logs
            print(f"⚠️ Poll error: {e}", flush=True)

    async def _run(self) -> None:
        interval = max(1, int(settings.poll_interval_minutes))
        
        # Run initial poll immediately on startup
        print("🚀 Running initial poll on startup...", flush=True)
        await self._poll_once()
        
        # Then continue with regular interval polling
        while not self._stop.is_set():
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=interval * 60)
            except TimeoutError:
                await self._poll_once()
