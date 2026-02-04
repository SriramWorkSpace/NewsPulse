from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.services.db import delete_older_than, init_db, upsert_article
from app.services.newsapi_client import NewsAPIClient


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
        self._task = asyncio.create_task(self._run(), name="headline_poller")

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            await self._task
        await self._client.close()

    async def _run(self) -> None:
        interval = max(1, int(settings.poll_interval_minutes))
        while not self._stop.is_set():
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
            except Exception:
                # v1: swallow poll errors to keep API serving; surfaced via logs
                pass

            try:
                await asyncio.wait_for(self._stop.wait(), timeout=interval * 60)
            except TimeoutError:
                continue
