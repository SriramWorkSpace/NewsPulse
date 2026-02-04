"""
Entity extraction service using spaCy NER for tracking people, organizations, and locations.
"""
from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

import spacy

if TYPE_CHECKING:
    from collections.abc import Sequence


class EntityExtractor:
    """Extract named entities from text using spaCy."""

    def __init__(self) -> None:
        """Initialize with spaCy model."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise RuntimeError(
                "spaCy model 'en_core_web_sm' not found. "
                "Install it with: python -m spacy download en_core_web_sm"
            )

    def extract_entities(self, text: str) -> dict[str, list[str]]:
        """
        Extract named entities from text.

        Args:
            text: Input text to analyze

        Returns:
            Dictionary with entity types as keys and lists of entity strings as values
            Example: {"PERSON": ["Elon Musk"], "ORG": ["Tesla", "SpaceX"], "GPE": ["USA"]}
        """
        if not text:
            return {}

        doc = self.nlp(text)
        entities: dict[str, list[str]] = {}

        for ent in doc.ents:
            # Focus on key entity types
            if ent.label_ in ("PERSON", "ORG", "GPE", "EVENT", "PRODUCT"):
                if ent.label_ not in entities:
                    entities[ent.label_] = []
                # Clean and add entity text
                entity_text = ent.text.strip()
                if entity_text and len(entity_text) > 1:  # Filter out single characters
                    entities[ent.label_].append(entity_text)

        return entities

    def extract_from_articles(
        self, articles: Sequence[dict]
    ) -> dict[str, list[tuple[str, int]]]:
        """
        Extract and rank entities from multiple articles.

        Args:
            articles: List of article dictionaries with 'title' and 'description' fields

        Returns:
            Dictionary with entity types as keys and ranked (entity, count) tuples
            Example: {"PERSON": [("Elon Musk", 15), ("Jeff Bezos", 8)], ...}
        """
        entity_counters: dict[str, Counter] = {
            "PERSON": Counter(),
            "ORG": Counter(),
            "GPE": Counter(),
            "EVENT": Counter(),
            "PRODUCT": Counter(),
        }

        for article in articles:
            # Combine title and description for entity extraction
            text_parts = []
            if article.get("title"):
                text_parts.append(article["title"])
            if article.get("description"):
                text_parts.append(article["description"])

            text = " ".join(text_parts)
            if not text:
                continue

            entities = self.extract_entities(text)

            # Count occurrences
            for entity_type, entity_list in entities.items():
                for entity in entity_list:
                    entity_counters[entity_type][entity] += 1

        # Convert to sorted lists
        result = {}
        for entity_type, counter in entity_counters.items():
            # Get top entities sorted by frequency
            result[entity_type] = counter.most_common(20)

        return result


# Singleton instance
_entity_extractor: EntityExtractor | None = None


def get_entity_extractor() -> EntityExtractor:
    """Get or create the singleton entity extractor."""
    global _entity_extractor
    if _entity_extractor is None:
        _entity_extractor = EntityExtractor()
    return _entity_extractor
