from __future__ import annotations

from pydantic import BaseModel, Field


class NewsAPISource(BaseModel):
    id: str | None = None
    name: str


class NewsAPIArticle(BaseModel):
    source: NewsAPISource
    author: str | None = None
    title: str
    description: str | None = None
    url: str
    urlToImage: str | None = None
    publishedAt: str
    content: str | None = None


class NewsAPIResponse(BaseModel):
    status: str
    totalResults: int | None = None
    articles: list[NewsAPIArticle] = Field(default_factory=list)
