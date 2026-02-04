from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.errors import UpstreamAPIError
from app.services.newsapi_client import NewsAPIClient
from app.services.sentiment import SentimentModel


router = APIRouter()

# Load sentiment model once at module level
_sentiment_model = SentimentModel(
    model_path=str(Path(__file__).parent.parent.parent.parent / "models" / "sentiment.pkl"),
    vectorizer_path=str(Path(__file__).parent.parent.parent.parent / "models" / "vectorizer.pkl"),
)
try:
    _sentiment_model.load()
except Exception as e:
    print(f"Warning: Could not load sentiment model: {e}")
    _sentiment_model = None


@router.get("/search")
async def search(q: str, page: int | None = None, pageSize: int | None = None, language: str | None = None):
    client = NewsAPIClient()
    try:
        resp = await client.everything(q=q, page=page, page_size=pageSize, language=language)
        
        # Enrich articles with sentiment analysis
        enriched_articles = []
        for article in resp.articles:
            article_dict = article.model_dump()
            
            # Add sentiment if model is available and article has content
            if _sentiment_model and article.title:
                try:
                    text_to_analyze = article.title
                    if article.description:
                        text_to_analyze = f"{article.title}. {article.description}"
                    
                    sentiment = _sentiment_model.predict(text_to_analyze)
                    article_dict["sentiment"] = {
                        "label": sentiment.label,
                        "score": sentiment.score
                    }
                except Exception as e:
                    # Don't fail the whole request if sentiment fails
                    article_dict["sentiment"] = {"label": "unknown", "score": None}
            else:
                article_dict["sentiment"] = {"label": "unknown", "score": None}
            
            enriched_articles.append(article_dict)
        
        return {
            "meta": {
                "q": q,
                "page": page,
                "pageSize": pageSize,
                "language": language,
                "totalResults": resp.totalResults,
            },
            "articles": enriched_articles,
        }
    except UpstreamAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    finally:
        await client.close()
