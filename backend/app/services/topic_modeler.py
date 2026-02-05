"""
Topic modeling service using BERTopic for automatic topic discovery.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

if TYPE_CHECKING:
    from collections.abc import Sequence


class TopicModeler:
    """Discover topics in articles using BERTopic."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """
        Initialize with a sentence transformer model.

        Args:
            model_name: Name of the sentence-transformers model to use
                       Should match the one used in ArticleClusterer for consistency
        """
        self.embedding_model = SentenceTransformer(model_name)
        self.topic_model = None

    def discover_topics(
        self,
        articles: Sequence[dict],
        embeddings: np.ndarray | None = None,
        nr_topics: int | str = "auto",
        min_topic_size: int = 3,
    ) -> dict:
        """
        Discover topics in a collection of articles.

        Args:
            articles: List of article dictionaries with 'title' and 'description'
            embeddings: Pre-computed embeddings (optional, will compute if None)
            nr_topics: Number of topics to extract ('auto' or specific number)
            min_topic_size: Minimum number of articles to form a topic

        Returns:
            Dictionary with discovered topics and metadata:
            {
                "topics": [
                    {
                        "topic_id": int,
                        "label": str,
                        "keywords": [str],
                        "article_count": int,
                        "sample_articles": [dict],
                    }
                ],
                "uncategorized_count": int,
                "total_articles": int
            }
        """
        if not articles or len(articles) < min_topic_size:
            return {
                "topics": [],
                "uncategorized_count": 0,
                "total_articles": len(articles),
            }

        # Prepare texts for topic modeling
        texts = []
        for article in articles:
            text_parts = []
            if article.get("title"):
                text_parts.append(article["title"])
            if article.get("description"):
                text_parts.append(article["description"])
            texts.append(" ".join(text_parts) if text_parts else "")

        # Get embeddings (compute if not provided)
        if embeddings is None:
            embeddings = self.embedding_model.encode(
                texts, show_progress_bar=False
            )

        # Initialize BERTopic with settings optimized for news articles
        self.topic_model = BERTopic(
            embedding_model=self.embedding_model,
            nr_topics=nr_topics,
            min_topic_size=min_topic_size,
            calculate_probabilities=False,  # Faster, we don't need probabilities
            verbose=False,
        )

        # Fit the model and get topic assignments
        try:
            topics, _ = self.topic_model.fit_transform(texts, embeddings)
        except Exception as e:
            # If BERTopic fails (e.g., not enough diversity), return empty
            return {
                "topics": [],
                "uncategorized_count": len(articles),
                "total_articles": len(articles),
            }

        # Get topic information
        topic_info = self.topic_model.get_topic_info()

        # Build response
        discovered_topics = []
        uncategorized_count = 0

        for _, row in topic_info.iterrows():
            topic_id = row["Topic"]
            
            # Topic -1 is outliers/uncategorized
            if topic_id == -1:
                uncategorized_count = row["Count"]
                continue

            # Get topic keywords
            topic_words = self.topic_model.get_topic(topic_id)
            if not topic_words:
                continue

            # Extract top 5 keywords
            keywords = [word for word, _ in topic_words[:5]]

            # Generate a readable label from top 3 keywords
            label = " • ".join(keywords[:3]).title()

            # Get sample articles for this topic
            article_indices = [i for i, t in enumerate(topics) if t == topic_id]
            sample_articles = []
            for idx in article_indices[:3]:  # Top 3 sample articles
                if idx < len(articles):
                    article = articles[idx]
                    sample_articles.append({
                        "title": article.get("title", ""),
                        "url": article.get("url", ""),
                        "source": article.get("source_name", ""),
                        "published_at": article.get("published_at", ""),
                    })

            discovered_topics.append({
                "topic_id": int(topic_id),
                "label": label,
                "keywords": keywords,
                "article_count": int(row["Count"]),
                "sample_articles": sample_articles,
            })

        # Sort by article count (most prominent topics first)
        discovered_topics.sort(key=lambda x: x["article_count"], reverse=True)

        return {
            "topics": discovered_topics,
            "uncategorized_count": uncategorized_count,
            "total_articles": len(articles),
        }

    def get_topic_info(self) -> dict | None:
        """
        Get information about the fitted topic model.

        Returns:
            Dictionary with topic model metadata or None if not fitted
        """
        if self.topic_model is None:
            return None

        topic_info = self.topic_model.get_topic_info()
        return {
            "num_topics": len(topic_info) - 1,  # Exclude -1 (outliers)
            "topics": topic_info.to_dict("records"),
        }


# Singleton instance
_topic_modeler: TopicModeler | None = None


def get_topic_modeler() -> TopicModeler:
    """Get or create singleton TopicModeler instance."""
    global _topic_modeler
    if _topic_modeler is None:
        _topic_modeler = TopicModeler()
    return _topic_modeler
