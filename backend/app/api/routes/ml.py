"""
API routes for entity extraction and article clustering.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from fastapi import APIRouter

from app.services.db import get_all_articles, get_recent_articles
from app.services.entity_extractor import get_entity_extractor
from app.services.article_clusterer import get_article_clusterer
from app.services.topic_modeler import get_topic_modeler
from app.services.breaking_news_detector import get_breaking_news_detector
from app.core.config import settings


router = APIRouter()

# Simple caches (TTL-based)
_topics_cache = {"data": None, "timestamp": None}
_breaking_cache = {"data": None, "timestamp": None}


@router.get("/entities")
async def get_trending_entities():
    """
    Get trending named entities from recent articles.

    Returns trending people, organizations, locations, events, and products
    extracted from articles in the database.
    """
    # Get recent articles from database
    articles = await get_all_articles(settings.sqlite_path)

    if not articles:
        return {
            "PERSON": [],
            "ORG": [],
            "GPE": [],
            "EVENT": [],
            "PRODUCT": []
        }

    # Extract entities
    extractor = get_entity_extractor()
    entities = extractor.extract_from_articles(articles)

    return entities


@router.get("/related/{article_index}")
async def get_related_articles(article_index: int, top_k: int = 5):
    """
    Get articles related to a specific article by semantic similarity.

    Args:
        article_index: Index of the article in the current result set
        top_k: Number of related articles to return

    Returns:
        List of related article indices with similarity scores
    """
    # Get recent articles
    articles = await get_all_articles(settings.sqlite_path)

    if not articles or article_index >= len(articles):
        return {"related": []}

    # Find related articles
    clusterer = get_article_clusterer()
    related = clusterer.find_related_articles(
        article_index, articles, top_k=top_k, threshold=0.5
    )

    # Return articles with their similarity scores
    results = []
    for idx, score in related:
        if idx < len(articles):
            article = articles[idx]
            results.append({
                "index": idx,
                "similarity": score,
                "title": article.get("title"),
                "url": article.get("url"),
                "source": article.get("source_name"),
            })

    return {"related": results}


@router.get("/related-by-url")
async def get_related_articles_by_url(url: str, top_k: int = 3):
    """
    Get articles related to a specific article by URL.

    Args:
        url: URL of the article to find relatives for
        top_k: Number of related articles to return

    Returns:
        List of related articles with similarity scores
    """
    # Get recent articles
    articles = await get_all_articles(settings.sqlite_path)

    if not articles:
        return {"related": []}

    # Find the article index by URL
    article_index = None
    for idx, article in enumerate(articles):
        if article.get("url") == url:
            article_index = idx
            break

    if article_index is None:
        return {"related": []}

    # Find related articles
    clusterer = get_article_clusterer()
    related = clusterer.find_related_articles(
        article_index, articles, top_k=top_k, threshold=0.4
    )

    # Return articles with their similarity scores
    results = []
    for idx, score in related:
        if idx < len(articles):
            article = articles[idx]
            results.append({
                "similarity": score,
                "title": article.get("title"),
                "url": article.get("url"),
                "source": article.get("source_name"),
                "published_at": article.get("published_at"),
            })

    return {"related": results}


@router.get("/clusters")
async def get_article_clusters():
    """
    Get article clusters grouped by semantic similarity.

    Returns groups of related articles that discuss similar topics.
    """
    # Get recent articles
    articles = await get_all_articles(settings.sqlite_path)

    if not articles:
        return {"clusters": []}

    # Cluster articles
    clusterer = get_article_clusterer()
    clusters = clusterer.cluster_articles(articles, eps=0.3, min_samples=2)

    # Format response (exclude noise cluster -1)
    formatted_clusters = []
    for cluster_id, article_indices in clusters.items():
        if cluster_id == -1:  # Skip noise
            continue

        cluster_articles = []
        for idx in article_indices:
            if idx < len(articles):
                article = articles[idx]
                cluster_articles.append({
                    "index": idx,
                    "title": article.get("title"),
                    "url": article.get("url"),
                    "source": article.get("source_name"),
                })

        if cluster_articles:  # Only include non-empty clusters
            formatted_clusters.append({
                "cluster_id": cluster_id,
                "article_count": len(cluster_articles),
                "articles": cluster_articles
            })

    return {"clusters": formatted_clusters}


@router.get("/topics")
async def get_discovered_topics(lookback_hours: int = 24, min_articles: int = 15):
    """
    Get automatically discovered topics from recent articles using BERTopic.

    Args:
        lookback_hours: Hours to look back for articles (default 24)
        min_articles: Minimum articles needed for topic discovery (default 15)

    Returns:
        Dictionary with discovered topics, keywords, and sample articles
    """
    # Check cache (30 min TTL)
    now = datetime.now()
    if _topics_cache["data"] is not None and _topics_cache["timestamp"] is not None:
        cache_age = (now - _topics_cache["timestamp"]).total_seconds()
        if cache_age < 1800:  # 30 minutes
            return _topics_cache["data"]

    # Get recent articles
    articles = await get_recent_articles(settings.sqlite_path, hours=lookback_hours)

    # Early return if not enough articles
    if len(articles) < min_articles:
        result = {
            "topics": [],
            "uncategorized_count": len(articles),
            "total_articles": len(articles),
            "message": f"Need at least {min_articles} articles for topic discovery (found {len(articles)})"
        }
        return result

    # Get topic modeler
    modeler = get_topic_modeler()
    
    # Get clusterer for embeddings (reuse existing infrastructure)
    clusterer = get_article_clusterer()
    
    # Prepare texts and get embeddings
    texts = []
    for article in articles:
        text_parts = []
        if article.get("title"):
            text_parts.append(article["title"])
        if article.get("description"):
            text_parts.append(article["description"])
        texts.append(" ".join(text_parts) if text_parts else "")
    
    embeddings = clusterer.get_embeddings(texts)

    # Discover topics
    try:
        result = modeler.discover_topics(
            articles,
            embeddings=embeddings,
            nr_topics="auto",  # Let BERTopic decide optimal number
            min_topic_size=3,
        )
        
        # Cache the result
        _topics_cache["data"] = result
        _topics_cache["timestamp"] = now
        
        return result
    except Exception as e:
        # If topic discovery fails, return graceful error
        return {
            "topics": [],
            "uncategorized_count": len(articles),
            "total_articles": len(articles),
            "error": f"Topic discovery failed: {str(e)}"
        }


@router.get("/breaking")
async def get_breaking_news(threshold: int = 60):
    """
    Get breaking news detected by analyzing article velocity and novelty.

    Uses multiple signals:
    - Volume spike: Sudden increase in article count
    - Novel entities: New people/orgs/locations appearing
    - Rapid clustering: Many similar articles published quickly

    Args:
        threshold: Minimum score to consider breaking news (0-100, default 60)

    Returns:
        List of breaking news stories with scores and metadata
    """
    # Check cache (15 min TTL for breaking news)
    now = datetime.now()
    if _breaking_cache["data"] is not None and _breaking_cache["timestamp"] is not None:
        cache_age = (now - _breaking_cache["timestamp"]).total_seconds()
        if cache_age < 900:  # 15 minutes
            cached_data = _breaking_cache["data"]
            # Filter by threshold (may have changed)
            filtered = [
                story for story in cached_data
                if story.get("score", 0) >= threshold
            ]
            return {"breaking": filtered}

    # Get detector
    detector = get_breaking_news_detector()
    
    # Get other services
    entity_extractor = get_entity_extractor()
    article_clusterer = get_article_clusterer()

    # Detect breaking news
    try:
        breaking_stories = await detector.detect_breaking_news(
            settings.sqlite_path,
            entity_extractor,
            article_clusterer,
            threshold=threshold,
        )

        # Cache the result
        _breaking_cache["data"] = breaking_stories
        _breaking_cache["timestamp"] = now

        return {"breaking": breaking_stories}
    except Exception as e:
        # Graceful error handling
        return {
            "breaking": [],
            "error": f"Breaking news detection failed: {str(e)}"
        }


