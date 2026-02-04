"""
API routes for entity extraction and article clustering.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.services.db import get_all_articles
from app.services.entity_extractor import get_entity_extractor
from app.services.article_clusterer import get_article_clusterer
from app.core.config import settings


router = APIRouter()


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
