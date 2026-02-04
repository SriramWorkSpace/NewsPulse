from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import spacy


@dataclass(frozen=True)
class KeywordCounts:
    counts: Counter[str]


def load_spacy_model() -> "spacy.language.Language":
    # Requires user to install: python -m spacy download en_core_web_sm
    return spacy.load("en_core_web_sm", disable=["ner", "textcat"])


def extract_keywords(nlp: "spacy.language.Language", text: str) -> list[str]:
    doc = nlp(text)
    keywords: list[str] = []

    for chunk in doc.noun_chunks:
        lemmas = []
        for token in chunk:
            if token.is_stop or token.is_punct or token.like_num:
                continue
            lemma = token.lemma_.strip().lower()
            if not lemma or lemma == "-pron-":
                continue
            lemmas.append(lemma)

        if not lemmas:
            continue

        phrase = " ".join(lemmas)
        if len(phrase) < 3:
            continue
        keywords.append(phrase)

    return keywords


def count_keywords(nlp: "spacy.language.Language", texts: list[str]) -> KeywordCounts:
    counter: Counter[str] = Counter()
    for text in texts:
        for kw in extract_keywords(nlp, text):
            counter[kw] += 1
    return KeywordCounts(counter)
