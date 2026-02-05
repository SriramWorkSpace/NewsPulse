"""
ML Processor - Compute and cache ML results during polling cycles.

This service loads ML models temporarily, processes all articles,
saves results to cache, then unloads to free memory.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, UTC, timedelta
from typing import Any

from app.services.ml_cache import (
    save_embeddings,
    save_topics,
    save_clusters,
    save_breaking_news,
    cleanup_old_cache
)
from app.services.db import get_all_articles, get_recent_articles


class MLProcessor:
    """Process ML tasks during polling and cache results."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    async def process_all(self):
        """
        Run all ML processing tasks:
        1. Generate embeddings
        2. Discover topics
        3. Cluster articles
        4. Detect breaking news
        5. Cleanup old cache
        """
        print("🧠 Starting ML processing...", flush=True)
        
        try:
            # Get articles
            articles = await get_all_articles(self.db_path)
            
            if len(articles) < 5:
                print(f"⏭️  Skipping ML - need at least 5 articles (have {len(articles)})", flush=True)
                return
            
            # Step 1: Generate and save embeddings
            await self._process_embeddings(articles)
            
            # Step 2: Discover and save topics (needs 15+ articles)
            if len(articles) >= 15:
                await self._process_topics(articles)
            
            # Step 3: Cluster articles
            await self._process_clusters(articles)
            
            # Step 4: Detect breaking news
            await self._process_breaking_news()
            
            # Step 5: Cleanup old cache
            await cleanup_old_cache(self.db_path, retention_hours=48)
            
            print("✅ ML processing complete", flush=True)
            
        except Exception as e:
            print(f"❌ ML processing error: {e}", flush=True)
    
    async def _process_embeddings(self, articles: list[dict]):
        """Generate and cache embeddings for semantic similarity."""
        print(f"  📊 Computing embeddings for {len(articles)} articles...", flush=True)
        
        # Lazy import to avoid loading at startup
        from app.services.article_clusterer import get_article_clusterer
        
        clusterer = get_article_clusterer()
        
        # Prepare texts
        texts = []
        urls = []
        for article in articles:
            text = article.get('title', '')
            if article.get('description'):
                text = f"{text}. {article['description']}"
            texts.append(text)
            urls.append(article['url'])
        
        # Generate embeddings
        embeddings_array = clusterer.get_embeddings(texts)
        
        # Convert to dict {url: embedding}
        embeddings_dict = {url: emb.tolist() for url, emb in zip(urls, embeddings_array)}
        
        # Save to cache
        await save_embeddings(self.db_path, embeddings_dict)
        
        print(f"  ✓ Saved {len(embeddings_dict)} embeddings", flush=True)
        
        # Unload model to free memory
        del clusterer
    
    async def _process_topics(self, articles: list[dict]):
        """Discover topics using BERTopic and cache results."""
        print(f"  🗂️  Discovering topics from {len(articles)} articles...", flush=True)
        
        # Lazy import
        from app.services.topic_modeler import get_topic_modeler
        
        modeler = get_topic_modeler()
        
        # Discover topics
        result = modeler.discover_topics(articles, min_topic_size=3)
        
        if not result['topics']:
            print("  ⏭️  No topics discovered", flush=True)
            del modeler
            return
        
        # Build article assignments: {url: {topic_id, confidence}}
        article_assignments = {}
        for article in result.get('articles_by_topic', {}).get('articles', []):
            article_assignments[article['url']] = {
                'topic_id': article['topic_id'],
                'confidence': None  # BERTopic doesn't provide confidence by default
            }
        
        # Save to cache
        await save_topics(self.db_path, result['topics'], article_assignments)
        
        print(f"  ✓ Discovered {len(result['topics'])} topics", flush=True)
        
        # Unload model
        del modeler
    
    async def _process_clusters(self, articles: list[dict]):
        """Cluster articles and cache results."""
        print(f"  🔗 Clustering {len(articles)} articles...", flush=True)
        
        from app.services.article_clusterer import get_article_clusterer
        
        clusterer = get_article_clusterer()
        
        # Cluster articles
        result = clusterer.cluster_articles(articles, eps=0.3, min_samples=2)
        
        # Build clusters dict: {url: {cluster_id, cluster_size}}
        clusters_dict = {}
        for cluster in result['clusters']:
            cluster_id = cluster['cluster_id']
            cluster_size = cluster['size']
            for article in cluster['articles']:
                clusters_dict[article['url']] = {
                    'cluster_id': cluster_id,
                    'cluster_size': cluster_size
                }
        
        # Save to cache
        await save_clusters(self.db_path, clusters_dict)
        
        print(f"  ✓ Created {result['num_clusters']} clusters", flush=True)
        
        del clusterer
    
    async def _process_breaking_news(self):
        """Detect breaking news and cache the score."""
        print("  🚨 Detecting breaking news...", flush=True)
        
        from app.services.breaking_news_detector import get_breaking_news_detector
        from app.services.entity_extractor import get_entity_extractor
        from app.services.article_clusterer import get_article_clusterer
        
        detector = get_breaking_news_detector()
        
        # Get recent and baseline articles
        now = datetime.now(UTC)
        one_hour_ago = now - timedelta(hours=1)
        twelve_hours_ago = now - timedelta(hours=12)
        
        recent_articles = await get_recent_articles(self.db_path, hours=1)
        baseline_articles = await get_recent_articles(self.db_path, hours=12)
        
        if len(recent_articles) < 3:
            print("  ⏭️  Not enough recent articles for breaking news detection", flush=True)
            return
        
        # Calculate volume spike
        volume_score = detector.detect_volume_spike(recent_articles, baseline_articles)
        
        # Calculate novel entities
        extractor = get_entity_extractor()
        entity_score = detector.detect_novel_entities(
            recent_articles, baseline_articles, extractor
        )
        
        # Calculate rapid clustering
        clusterer = get_article_clusterer()
        clustering_score = detector.detect_rapid_clustering(recent_articles, clusterer)
        
        # Calculate final score
        final_score = (volume_score * 0.4) + (entity_score * 0.35) + (clustering_score * 0.25)
        
        signals = {
            "volume_spike": volume_score,
            "novel_entities": entity_score,
            "rapid_clustering": clustering_score,
            "recent_count": len(recent_articles),
            "baseline_count": len(baseline_articles)
        }
        
        # Save to cache
        await save_breaking_news(self.db_path, final_score, signals)
        
        status = "🚨 BREAKING" if final_score >= 60 else "📰 normal"
        print(f"  ✓ Breaking news score: {final_score:.1f} ({status})", flush=True)
        
        del detector, extractor, clusterer


async def run_ml_processing(db_path: str):
    """Run ML processing (called by HeadlinePoller after each poll)."""
    processor = MLProcessor(db_path)
    await processor.process_all()
