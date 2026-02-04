from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.errors import UpstreamAPIError
from app.schemas.newsapi import NewsAPIResponse


class NewsAPIClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(base_url=settings.newsapi_base_url, timeout=20.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def top_headlines(
        self,
        *,
        country: str,
        language: str,
        page_size: int = 100,
        category: str | None = None,
        sources: str | None = None,
        page: int | None = None,
        q: str | None = None,
    ) -> NewsAPIResponse:
        params: dict[str, object] = {
            "apiKey": settings.news_api_key,
            "country": country,
            "language": language,
            "pageSize": page_size,
        }
        if category is not None:
            params["category"] = category
        if sources is not None:
            params["sources"] = sources
        if page is not None:
            params["page"] = page
        if q is not None:
            params["q"] = q

        resp = await self._client.get("/top-headlines", params=params)
        return await self._parse(resp)

    async def everything(
        self,
        *,
        q: str,
        page_size: int | None = None,
        page: int | None = None,
        language: str | None = None,
    ) -> NewsAPIResponse:
        params: dict[str, object] = {"apiKey": settings.news_api_key, "q": q}
        if page_size is not None:
            params["pageSize"] = page_size
        if page is not None:
            params["page"] = page
        if language is not None:
            params["language"] = language

        resp = await self._client.get("/everything", params=params)
        return await self._parse(resp)

    async def _parse(self, resp: httpx.Response) -> NewsAPIResponse:
        if resp.status_code == 200:
            return NewsAPIResponse.model_validate(resp.json())

        try:
            payload = resp.json()
        except Exception:
            raise UpstreamAPIError(resp.status_code, None, resp.text)

        raise UpstreamAPIError(
            resp.status_code,
            payload.get("code"),
            payload.get("message", "Upstream error"),
        )
