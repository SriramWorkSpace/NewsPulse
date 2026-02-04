from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib


@dataclass(frozen=True)
class SentimentResult:
    label: str
    score: float | None = None


class SentimentModel:
    def __init__(self, *, model_path: str, vectorizer_path: str) -> None:
        self._model_path = Path(model_path)
        self._vectorizer_path = Path(vectorizer_path)
        self._model = None
        self._vectorizer = None

    def load(self) -> None:
        if not self._model_path.exists() or not self._vectorizer_path.exists():
            raise FileNotFoundError(
                f"Missing sentiment artifacts: {self._model_path} / {self._vectorizer_path}"
            )
        self._vectorizer = joblib.load(self._vectorizer_path)
        self._model = joblib.load(self._model_path)

    def predict(self, text: str) -> SentimentResult:
        if self._model is None or self._vectorizer is None:
            raise RuntimeError("Sentiment model not loaded")

        X = self._vectorizer.transform([text])
        pred = self._model.predict(X)[0]

        score = None
        if hasattr(self._model, "predict_proba"):
            proba = self._model.predict_proba(X)[0]
            # best-effort: probability of predicted class
            try:
                idx = list(self._model.classes_).index(pred)
                score = float(proba[idx])
            except Exception:
                score = None

        return SentimentResult(label=str(pred), score=score)
