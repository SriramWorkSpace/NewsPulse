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
async def get_related_articles_by_url(url: str, top_k: int = 3, title: str = None):
    """
    Get articles related to a specific article by URL or title.
    
    Uses pre-computed embeddings from the ML cache for fast semantic similarity.

    Args:
        url: URL of the article to find relatives for
        top_k: Number of related articles to return
        title: Article title (fallback if URL not found)

    Returns:
        List of related articles with similarity scores
    """
    from app.services.ml_cache import get_embeddings
    import numpy as np
    
    # Get all articles and cached embeddings
    articles = await get_all_articles(settings.sqlite_path)
    embeddings_dict = await get_embeddings(settings.sqlite_path)
    
    if not embeddings_dict:
        return {
            "related": [],
            "message": "Embeddings are being computed. Check back in a few minutes."
        }
    
    # Find target article index
    article_index = None
    for idx, article in enumerate(articles):
        if article['url'] == url:
            article_index = idx
            break
    
    # If not found by URL, try title match
    if article_index is None and title:
        for idx, article in enumerate(articles):
            if article.get('title') == title:
                article_index = idx
                break
    
    if article_index is None:
        # Article not in our database - compute embedding for external article
        if not title:
            return {"related": [], "message": "Article not found and no title provided"}
        
        # Lazy load model just for this embedding
        from app.services.article_clusterer import get_article_clusterer
        clusterer = get_article_clusterer()
        title_embedding = clusterer.get_embeddings([title])[0]
        del clusterer
        
        # Compare with all cached embeddings
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Convert dict to arrays
        article_urls = []
        article_embeddings = []
        for art_url, emb in embeddings_dict.items():
            article_urls.append(art_url)
            article_embeddings.append(emb)
        
        article_embeddings = np.array(article_embeddings)
        similarities = cosine_similarity([title_embedding], article_embeddings)[0]
        
        # Get top_k most similar
        similar_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in similar_indices:
            if similarities[idx] > 0.2:
                # Find article by URL
                art_url = article_urls[idx]
                article = next((a for a in articles if a['url'] == art_url), None)
                if article:
                    results.append({
                        "similarity": float(similarities[idx]),
                        "title": article.get("title"),
                        "url": article.get("url"),
                        "source": article.get("source_name"),
                        "published_at": article.get("published_at"),
                    })
        
        return {"related": results}
    
    # Article found in our database - use cached embeddings
    target_url = articles[article_index]['url']
    target_embedding = embeddings_dict.get(target_url)
    
    if not target_embedding:
        return {"related": [], "message": "Embedding not found for this article"}
    
    # Compute similarities with all other articles
    from sklearn.metrics.pairwise import cosine_similarity
    
    similarities = []
    urls_list = []
    for art_url, emb in embeddings_dict.items():
        if art_url != target_url:  # Exclude self
            similarities.append(cosine_similarity([target_embedding], [emb])[0][0])
            urls_list.append(art_url)
    
    # Get top_k most similar
    similarities = np.array(similarities)
    top_indices = similarities.argsort()[-top_k:][::-1]
    
    results = []
    for idx in top_indices:
        if similarities[idx] > 0.4:  # Similarity threshold
            art_url = urls_list[idx]
            article = next((a for a in articles if a['url'] == art_url), None)
            if article:
                results.append({
                    "similarity": float(similarities[idx]),
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
    
    Clusters are pre-computed during the 30-minute polling cycle.

    Returns:
        Groups of related articles that discuss similar topics
    """
    from app.services.ml_cache import get_clusters
    
    # Get all articles and cached clusters
    articles = await get_all_articles(settings.sqlite_path)
    clusters_dict = await get_clusters(settings.sqlite_path)
    
    if not clusters_dict:
        return {
            "clusters": [],
            "message": "Clusters are being computed. Check back in a few minutes."
        }
    
    # Group articles by cluster_id
    clusters_map = {}
    for article in articles:
        url = article['url']
        cluster_info = clusters_dict.get(url)
        if cluster_info:
            cid = cluster_info['cluster_id']
            if cid not in clusters_map:
                clusters_map[cid] = []
            clusters_map[cid].append(article)
    
    # Format response (exclude noise cluster -1)
    formatted_clusters = []
    for cluster_id, cluster_articles in clusters_map.items():
        if cluster_id == -1:  # Skip noise
            continue
        
        formatted_clusters.append({
            "cluster_id": cluster_id,
            "article_count": len(cluster_articles),
            "articles": [
                {
                    "title": art.get("title"),
                    "url": art.get("url"),
                    "source": art.get("source_name"),
                }
                for art in cluster_articles
            ]
        })
    
    return {"clusters": formatted_clusters}


@router.get("/topics")
async def get_discovered_topics(lookback_hours: int = 24, min_articles: int = 3):
    """
    Get automatically discovered topics from recent articles using BERTopic.
    
    Topics are pre-computed during the 30-minute polling cycle and cached.

    Args:
        lookback_hours: Hours to look back for articles (default 24) [ignored, uses cache]
        min_articles: Minimum articles needed for topic discovery (default 3) [ignored, uses cache]

    Returns:
        Dictionary with discovered topics, keywords, and sample articles
    """
    from app.services.ml_cache import get_topics
    from app.services.db import get_recent_articles
    
    # Get cached topics
    cached_result = await get_topics(settings.sqlite_path)
    
    if cached_result:
        return cached_result
    
    # Fallback: No cached data yet (first run)
    articles = await get_recent_articles(settings.sqlite_path, hours=lookback_hours)
    return {
        "topics": [],
        "uncategorized_count": len(articles),
        "total_articles": len(articles),
        "message": f"Topics are being computed. Check back in a few minutes."
    }


@router.get("/breaking")
async def get_breaking_news(threshold: int = 60):
    """
    Get breaking news detected by analyzing article velocity and novelty.
    
    Breaking news detection is pre-computed during the 30-minute polling cycle.

    Uses multiple signals:
    - Volume spike: Sudden increase in article count
    - Novel entities: New people/orgs/locations appearing
    - Rapid clustering: Many similar articles published quickly

    Args:
        threshold: Minimum score to consider breaking news (0-100, default 60)

    Returns:
        Breaking news score, signals, and detection status
    """
    from app.services.ml_cache import get_breaking_news
    
    # Get cached breaking news result
    cached_result = await get_breaking_news(settings.sqlite_path)
    
    if cached_result:
        # Apply threshold filter
        if cached_result["score"] >= threshold:
            return {
                "is_breaking": True,
                "score": cached_result["score"],
                "signals": cached_result["signals"],
                "detected_at": cached_result["detected_at"]
            }
        else:
            return {
                "is_breaking": False,
                "score": cached_result["score"],
                "signals": cached_result["signals"],
                "message": f"Score {cached_result['score']:.1f} below threshold {threshold}"
            }
    
    # Fallback: No cached data yet
    return {
        "is_breaking": False,
        "score": 0,
        "signals": {},
        "message": "Breaking news detection is being computed. Check back in a few minutes."
    }


