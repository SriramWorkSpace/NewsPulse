from __future__ import annotations

from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


# Minimal, non-copyrighted seed set.
# Replace with your offline training set later; v1 goal is a working .pkl artifact.
TRAIN = [
    ("Stocks soar on strong earnings report", "positive"),
    ("Company reports record profits and growth", "positive"),
    ("Team wins championship after dramatic final", "positive"),
    ("Breakthrough treatment shows promising results", "positive"),
    ("New policy receives widespread support", "positive"),
    ("Market crashes amid recession fears", "negative"),
    ("Layoffs announced as revenue falls sharply", "negative"),
    ("Severe storm causes widespread damage", "negative"),
    ("Data breach exposes millions of accounts", "negative"),
    ("Investigation reveals corruption allegations", "negative"),
    ("Central bank keeps rates unchanged", "neutral"),
    ("New smartphone model announced today", "neutral"),
    ("Government releases annual budget proposal", "neutral"),
    ("Conference scheduled for next month", "neutral"),
    ("Company appoints new CEO", "neutral"),
]


def main() -> None:
    texts = [t for t, _ in TRAIN]
    labels = [y for _, y in TRAIN]

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95)
    X = vectorizer.fit_transform(texts)

    clf = LogisticRegression(max_iter=1000, n_jobs=None)
    clf.fit(X, labels)

    out_dir = Path(__file__).resolve().parents[1] / "models"
    out_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(vectorizer, out_dir / "vectorizer.pkl")
    joblib.dump(clf, out_dir / "sentiment.pkl")

    print(f"Wrote: {out_dir / 'vectorizer.pkl'}")
    print(f"Wrote: {out_dir / 'sentiment.pkl'}")


if __name__ == "__main__":
    main()
