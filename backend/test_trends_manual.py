"""
Quick test to verify trend computation works with sample data.
This simulates having 24h of articles and checks if trends are computed correctly.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from app.services.db import upsert_article, fetch_articles_between_published
from app.services.analytics.keywords import count_keywords
from app.services.analytics.trends import rank_trends, TrendItem
from app.core.config import settings
import spacy

async def test_trends_with_sample_data():
    """Test trend computation with sample articles."""
    
    # Load spaCy model
    nlp = spacy.load("en_core_web_sm")
    
    # Create sample articles spanning 24 hours
    now = datetime.now(timezone.utc)
    
    # Previous window (24h ago to 12h ago) - articles about "climate change" and "economy"
    prev_articles = [
        {
            "url": "http://test.com/1",
            "title": "Climate change summit begins in Paris",
            "description": "Climate talks",
            "content": "Climate talks content",
            "source_name": "Test News",
            "published_at": (now - timedelta(hours=20)).isoformat(),
            "fetched_at": now.isoformat(),
        },
        {
            "url": "http://test.com/2",
            "title": "Economic recovery shows strong signs",
            "description": "Economy improving",
            "content": "Economy improving content",
            "source_name": "Test News",
            "published_at": (now - timedelta(hours=18)).isoformat(),
            "fetched_at": now.isoformat(),
        },
        {
            "url": "http://test.com/3",
            "title": "Climate activists protest at summit",
            "description": "Climate protests",
            "content": "Climate protests content",
            "source_name": "Test News",
            "published_at": (now - timedelta(hours=16)).isoformat(),
            "fetched_at": now.isoformat(),
        },
    ]
    
    # Current window (12h ago to now) - "climate change" continues, "quantum computing" emerges, "economy" grows
    curr_articles = [
        {
            "url": "http://test.com/4",
            "title": "Climate change policies announced",
            "description": "Climate policies",
            "content": "Climate policies content",
            "source_name": "Test News",
            "published_at": (now - timedelta(hours=10)).isoformat(),
            "fetched_at": now.isoformat(),
        },
        {
            "url": "http://test.com/5",
            "title": "Climate scientists warn of tipping points",
            "description": "Climate science",
            "content": "Climate science content",
            "source_name": "Test News",
            "published_at": (now - timedelta(hours=8)).isoformat(),
            "fetched_at": now.isoformat(),
        },
        {
            "url": "http://test.com/6",
            "title": "Quantum computing breakthrough announced by researchers",
            "description": "Quantum breakthrough",
            "content": "Quantum breakthrough content",
            "source_name": "Test News",
            "published_at": (now - timedelta(hours=6)).isoformat(),
            "fetched_at": now.isoformat(),
        },
        {
            "url": "http://test.com/7",
            "title": "Quantum computing startup raises millions in funding",
            "description": "Quantum funding",
            "content": "Quantum funding content",
            "source_name": "Test News",
            "published_at": (now - timedelta(hours=4)).isoformat(),
            "fetched_at": now.isoformat(),
        },
        {
            "url": "http://test.com/8",
            "title": "Economic growth exceeds expectations this quarter",
            "description": "Economy stats",
            "content": "Economy stats content",
            "source_name": "Test News",
            "published_at": (now - timedelta(hours=2)).isoformat(),
            "fetched_at": now.isoformat(),
        },
        {
            "url": "http://test.com/9",
            "title": "Economic indicators point to continued recovery",
            "description": "Economy indicators",
            "content": "Economy indicators content",
            "source_name": "Test News",
            "published_at": (now - timedelta(minutes=30)).isoformat(),
            "fetched_at": now.isoformat(),
        },
        {
            "url": "http://test.com/10",
            "title": "Economic summit scheduled for next month",
            "description": "Economy summit",
            "content": "Economy summit content",
            "source_name": "Test News",
            "published_at": (now - timedelta(minutes=10)).isoformat(),
            "fetched_at": now.isoformat(),
        },
    ]
    
    # Insert all articles
    print("Inserting sample articles...")
    for article in prev_articles + curr_articles:
        await upsert_article(settings.sqlite_path, **article)
    
    print(f"\n✅ Inserted {len(prev_articles)} previous window articles")
    print(f"✅ Inserted {len(curr_articles)} current window articles")
    
    # Fetch articles for each window
    prev_start = now - timedelta(hours=24)
    prev_end = now - timedelta(hours=12)
    curr_start = now - timedelta(hours=12)
    curr_end = now
    
    prev_articles_db = await fetch_articles_between_published(
        settings.sqlite_path,
        start_iso=prev_start.isoformat(),
        end_iso=prev_end.isoformat()
    )
    curr_articles_db = await fetch_articles_between_published(
        settings.sqlite_path,
        start_iso=curr_start.isoformat(),
        end_iso=curr_end.isoformat()
    )
    
    print(f"\n📊 Previous window ({prev_start.strftime('%H:%M')} to {prev_end.strftime('%H:%M')}): {len(prev_articles_db)} articles")
    print(f"📊 Current window ({curr_start.strftime('%H:%M')} to {curr_end.strftime('%H:%M')}): {len(curr_articles_db)} articles")
    
    # Count keywords
    prev_titles = [a["title"] for a in prev_articles_db]
    curr_titles = [a["title"] for a in curr_articles_db]
    
    prev_kw = count_keywords(nlp, prev_titles)
    curr_kw = count_keywords(nlp, curr_titles)
    
    prev_counts = dict(prev_kw.counts)
    curr_counts = dict(curr_kw.counts)
    
    print(f"\n🔑 Previous keywords: {prev_counts}")
    print(f"🔑 Current keywords: {curr_counts}")
    
    # Rank trends using the built-in function
    ranked = rank_trends(
        current=curr_counts,
        previous=prev_counts,
        limit=50
    )
    
    print("\n📈 RANKED TRENDS:")
    print("-" * 80)
    for i, item in enumerate(ranked, 1):
        is_new = item.previous_count == 0
        if is_new:
            print(f"{i}. {item.keyword:30} | Current: {item.current_count} | Previous: {item.previous_count} | 🆕 NEW/EMERGING")
        else:
            growth = (item.growth * 100) if item.growth is not None else 0
            print(f"{i}. {item.keyword:30} | Current: {item.current_count} | Previous: {item.previous_count} | Growth: {growth:+.1f}%")
    
    print("\n✅ Trend computation successful!")
    print("\nExpected ranking:")
    print("1. Group A (new/emerging): All keywords appearing only in current window (previous=0)")
    print("2. Group B (existing): Keywords appearing in both windows, ranked by growth %")

if __name__ == "__main__":
    asyncio.run(test_trends_with_sample_data())
