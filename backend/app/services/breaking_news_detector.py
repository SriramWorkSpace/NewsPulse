"""
Breaking news detection service using time-series analysis and ML signals.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Sequence
    from app.services.entity_extractor import EntityExtractor
    from app.services.article_clusterer import ArticleClusterer


class BreakingNewsDetector:
    """Detect breaking news using volume spikes, novel entities, and clustering."""

    def detect_volume_spike(
        self, recent_articles: Sequence[dict], baseline_articles: Sequence[dict]
    ) -> float:
        """
        Detect volume spike by comparing recent vs baseline article counts.

        Args:
            recent_articles: Articles from recent window (e.g., last hour)
            baseline_articles: Articles from baseline window (e.g., last 12 hours)

        Returns:
            Spike score (0-100)
        """
        recent_count = len(recent_articles)
        baseline_count = len(baseline_articles)

        if baseline_count == 0:
            # No baseline, can't detect spike
            return 0.0

        baseline_avg_per_hour = baseline_count / 12  # Assuming 12-hour baseline

        if baseline_avg_per_hour == 0:
            # Very low activity, any recent article is significant
            return min(recent_count * 20, 100)

        # Calculate spike ratio
        spike_ratio = recent_count / baseline_avg_per_hour

        # Convert to 0-100 score
        # 2.5x = 50, 5x = 100
        score = min((spike_ratio - 1) * 25, 100)

        return max(0, score)

    def detect_novel_entities(
        self,
        recent_articles: Sequence[dict],
        baseline_articles: Sequence[dict],
        entity_extractor: EntityExtractor,
    ) -> tuple[float, list[str]]:
        """
        Detect new entities that appear in recent articles but not in baseline.

        Args:
            recent_articles: Articles from recent window
            baseline_articles: Articles from baseline window
            entity_extractor: Entity extraction service

        Returns:
            Tuple of (novelty_score 0-100, list of novel entities)
        """
        if not recent_articles:
            return 0.0, []

        # Extract entities from both windows
        recent_entities = entity_extractor.extract_from_articles(recent_articles)
        baseline_entities = entity_extractor.extract_from_articles(baseline_articles)

        # Find novel entities (present in recent but not baseline)
        novel = []
        
        # Check important entity types (weighted by importance)
        weights = {"PERSON": 3, "ORG": 2, "GPE": 2, "EVENT": 4}
        
        total_novelty = 0
        for entity_type, weight in weights.items():
            recent_names = {name for name, _ in recent_entities.get(entity_type, [])}
            baseline_names = {name for name, _ in baseline_entities.get(entity_type, [])}
            
            new_names = recent_names - baseline_names
            
            for name in new_names:
                novel.append(name)
                total_novelty += weight

        # Normalize to 0-100 (10 novel entities with avg weight 3 = 100)
        score = min(total_novelty * 3.3, 100)

        return score, novel[:10]  # Return top 10 novel entities

    def detect_rapid_clustering(
        self,
        recent_articles: Sequence[dict],
        article_clusterer: ArticleClusterer,
        similarity_threshold: float = 0.7,
    ) -> float:
        """
        Detect if recent articles cluster tightly (covering same story).

        Args:
            recent_articles: Articles from recent window
            article_clusterer: Article clustering service
            similarity_threshold: Minimum similarity to consider articles clustered

        Returns:
            Clustering score (0-100)
        """
        if len(recent_articles) < 2:
            return 0.0

        # Get embeddings for recent articles
        texts = []
        for article in recent_articles:
            text_parts = []
            if article.get("title"):
                text_parts.append(article["title"])
            if article.get("description"):
                text_parts.append(article["description"])
            texts.append(" ".join(text_parts) if text_parts else "")

        embeddings = article_clusterer.get_embeddings(texts)

        if embeddings.size == 0:
            return 0.0

        # Calculate pairwise similarities
        from sklearn.metrics.pairwise import cosine_similarity

        similarities = cosine_similarity(embeddings)

        # Count how many articles are highly similar
        high_similarity_count = 0
        n = len(recent_articles)

        for i in range(n):
            for j in range(i + 1, n):
                if similarities[i][j] >= similarity_threshold:
                    high_similarity_count += 1

        max_pairs = (n * (n - 1)) / 2
        if max_pairs == 0:
            return 0.0

        # Calculate percentage of high-similarity pairs
        similarity_ratio = high_similarity_count / max_pairs

        # Convert to 0-100 score
        score = similarity_ratio * 100

        return score

    def calculate_breaking_score(
        self, volume_score: float, novelty_score: float, clustering_score: float
    ) -> int:
        """
        Calculate overall breaking news score from component scores.

        Args:
            volume_score: Volume spike score (0-100)
            novelty_score: Novel entities score (0-100)
            clustering_score: Clustering score (0-100)

        Returns:
            Combined score (0-100) as integer
        """
        # Weighted combination
        combined = (
            volume_score * 0.40 +  # 40% weight on volume
            novelty_score * 0.35 +  # 35% weight on novelty
            clustering_score * 0.25  # 25% weight on clustering
        )

        return int(round(combined))

    async def detect_breaking_news(
        self,
        sqlite_path: str,
        entity_extractor: EntityExtractor,
        article_clusterer: ArticleClusterer,
        threshold: int = 60,
    ) -> list[dict]:
        """
        Detect breaking news stories.

        Args:
            sqlite_path: Path to SQLite database
            entity_extractor: Entity extraction service
            article_clusterer: Article clustering service
            threshold: Minimum score to consider breaking (default 60)

        Returns:
            List of breaking news stories with metadata
        """
        from app.services.db import get_articles_in_timerange

        now = datetime.now(tz=UTC)
        
        # Recent window: last 1 hour
        recent_start = now - timedelta(hours=1)
        recent_articles = await get_articles_in_timerange(
            sqlite_path, recent_start.isoformat(), now.isoformat()
        )

        # Baseline window: 1-13 hours ago (12 hour window)
        baseline_start = now - timedelta(hours=13)
        baseline_end = now - timedelta(hours=1)
        baseline_articles = await get_articles_in_timerange(
            sqlite_path, baseline_start.isoformat(), baseline_end.isoformat()
        )

        if not recent_articles:
            return []

        # Calculate component scores
        volume_score = self.detect_volume_spike(recent_articles, baseline_articles)
        novelty_score, novel_entities = self.detect_novel_entities(
            recent_articles, baseline_articles, entity_extractor
        )
        clustering_score = self.detect_rapid_clustering(
            recent_articles, article_clusterer
        )

        # Calculate overall score
        overall_score = self.calculate_breaking_score(
            volume_score, novelty_score, clustering_score
        )

        # Only return if above threshold
        if overall_score < threshold:
            return []

        # Find most representative article (highest similarity to others)
        if len(recent_articles) == 1:
            representative = recent_articles[0]
        else:
            # Get embeddings and find centroid
            texts = []
            for article in recent_articles:
                text_parts = []
                if article.get("title"):
                    text_parts.append(article["title"])
                if article.get("description"):
                    text_parts.append(article["description"])
                texts.append(" ".join(text_parts) if text_parts else "")

            embeddings = article_clusterer.get_embeddings(texts)
            
            # Find article closest to centroid
            centroid = np.mean(embeddings, axis=0)
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = cosine_similarity([centroid], embeddings)[0]
            representative_idx = np.argmax(similarities)
            representative = recent_articles[representative_idx]

        # Build breaking news entry
        breaking_story = {
            "title": representative.get("title", "Breaking News"),
            "url": representative.get("url", ""),
            "source": representative.get("source_name", ""),
            "published_at": representative.get("published_at", ""),
            "score": overall_score,
            "article_count": len(recent_articles),
            "novel_entities": novel_entities,
            "related_urls": [a.get("url") for a in recent_articles[:5]],
            "detected_at": now.isoformat(),
            "signals": {
                "volume": int(volume_score),
                "novelty": int(novelty_score),
                "clustering": int(clustering_score),
            },
        }

        return [breaking_story]


# Singleton instance
_breaking_news_detector: BreakingNewsDetector | None = None


def get_breaking_news_detector() -> BreakingNewsDetector:
    """Get or create singleton BreakingNewsDetector instance."""
    global _breaking_news_detector
    if _breaking_news_detector is None:
        _breaking_news_detector = BreakingNewsDetector()
    return _breaking_news_detector
