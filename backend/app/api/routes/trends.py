from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.services.analytics.keywords import count_keywords
from app.services.analytics.trends import rank_trends
from app.services.db import fetch_articles_between_published


router = APIRouter()


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


@router.get("/trends")
async def get_trends(limit: int = 50):
    """Compute trends from stored headlines.

    v1 locks: country=us, language=en polling only; keywords/phrases are trend units.
    """

    now = datetime.now(tz=UTC)
    start_24h = now - timedelta(hours=24)
    split_12h = now - timedelta(hours=12)

    # Use published_at for windowing
    previous_rows = await fetch_articles_between_published(
        settings.sqlite_path,
        start_iso=_iso(start_24h),
        end_iso=_iso(split_12h),
    )
    current_rows = await fetch_articles_between_published(
        settings.sqlite_path,
        start_iso=_iso(split_12h),
        end_iso=_iso(now),
    )

    # Keyword extraction uses title as primary; fallback to description.
    # (Summaries are separate; no scraping.)
    from app.main import nlp  # avoid circular init ordering issues

    prev_texts = [r["title"] for r in previous_rows if r.get("title")]
    cur_texts = [r["title"] for r in current_rows if r.get("title")]

    prev_counts = count_keywords(nlp, prev_texts).counts
    cur_counts = count_keywords(nlp, cur_texts).counts

    ranked = rank_trends(current=dict(cur_counts), previous=dict(prev_counts), limit=limit)

    return {
        "meta": {
            "country": settings.poll_country,
            "language": settings.poll_language,
            "windowHours": 24,
            "splitHours": 12,
            "retentionHours": settings.retention_hours,
            "fetchedAt": _iso(now),
        },
        "trending": [
            {
                "keyword": t.keyword,
                "currentCount": t.current_count,
                "previousCount": t.previous_count,
                "growth": t.growth,
                "isNew": t.previous_count == 0,
            }
            for t in ranked
        ],
    }
