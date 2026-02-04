"""
Article clustering service using sentence embeddings and similarity grouping.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

if TYPE_CHECKING:
    from collections.abc import Sequence


class ArticleClusterer:
    """Cluster articles by semantic similarity using embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """
        Initialize with a sentence transformer model.

        Args:
            model_name: Name of the sentence-transformers model to use
                       'all-MiniLM-L6-v2' is fast and good quality (384 dimensions)
        """
        self.model = SentenceTransformer(model_name)

    def get_embeddings(self, texts: list[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            Numpy array of embeddings (n_texts, embedding_dim)
        """
        if not texts:
            return np.array([])

        return self.model.encode(texts, show_progress_bar=False)

    def cluster_articles(
        self, articles: Sequence[dict], eps: float = 0.3, min_samples: int = 2
    ) -> dict[int, list[int]]:
        """
        Cluster articles by semantic similarity using DBSCAN.

        Args:
            articles: List of article dictionaries with 'title' and 'description'
            eps: Maximum distance between two samples for clustering (lower = tighter clusters)
            min_samples: Minimum number of articles to form a cluster

        Returns:
            Dictionary mapping cluster_id -> list of article indices
            Cluster ID -1 means noise (not clustered)
        """
        if not articles:
            return {}

        # Combine title and description for embedding
        texts = []
        for article in articles:
            text_parts = []
            if article.get("title"):
                text_parts.append(article["title"])
            if article.get("description"):
                text_parts.append(article["description"])
            texts.append(" ".join(text_parts) if text_parts else "")

        # Get embeddings
        embeddings = self.get_embeddings(texts)

        if embeddings.size == 0:
            return {}

        # Cluster using DBSCAN (works well for varying cluster sizes)
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine")
        labels = clustering.fit_predict(embeddings)

        # Group article indices by cluster
        clusters: dict[int, list[int]] = {}
        for idx, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(idx)

        return clusters

    def find_related_articles(
        self, article_idx: int, articles: Sequence[dict], top_k: int = 5, threshold: float = 0.5
    ) -> list[tuple[int, float]]:
        """
        Find articles most similar to a given article.

        Args:
            article_idx: Index of the article to find relatives for
            articles: List of all articles
            top_k: Number of related articles to return
            threshold: Minimum similarity score (0-1)

        Returns:
            List of (article_index, similarity_score) tuples, sorted by similarity
        """
        if not articles or article_idx >= len(articles):
            return []

        # Prepare texts
        texts = []
        for article in articles:
            text_parts = []
            if article.get("title"):
                text_parts.append(article["title"])
            if article.get("description"):
                text_parts.append(article["description"])
            texts.append(" ".join(text_parts) if text_parts else "")

        # Get embeddings
        embeddings = self.get_embeddings(texts)

        if embeddings.size == 0:
            return []

        # Calculate similarity to target article
        target_embedding = embeddings[article_idx].reshape(1, -1)
        similarities = cosine_similarity(target_embedding, embeddings)[0]

        # Get top-k most similar (excluding the article itself)
        similar_indices = np.argsort(similarities)[::-1]
        results = []

        for idx in similar_indices:
            if idx == article_idx:  # Skip self
                continue
            if similarities[idx] < threshold:  # Below threshold
                break
            results.append((int(idx), float(similarities[idx])))
            if len(results) >= top_k:
                break

        return results


# Singleton instance
_article_clusterer: ArticleClusterer | None = None


def get_article_clusterer() -> ArticleClusterer:
    """Get or create the singleton article clusterer."""
    global _article_clusterer
    if _article_clusterer is None:
        _article_clusterer = ArticleClusterer()
    return _article_clusterer
