from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.errors import UpstreamAPIError


class GeminiClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=settings.gemini_timeout_seconds)

    async def close(self) -> None:
        await self._client.aclose()

    async def summarize(self, *, title: str | None, description: str | None, content: str | None) -> str:
        prompt_parts = ["Summarize this article:"]
        if title:
            prompt_parts.append(f"Title: {title}")
        if description:
            prompt_parts.append(f"Description: {description}")
        if content:
            prompt_parts.append(f"Content: {content}")

        prompt = "\n".join(prompt_parts)

        # Use Gemini REST API v1 with gemini-2.0-flash-exp
        url = (
            f"https://generativelanguage.googleapis.com/v1/models/{settings.gemini_model}:generateContent"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                    ],
                }
            ]
        }

        resp = await self._client.post(url, params={"key": settings.gemini_api_key}, json=payload)
        if resp.status_code != 200:
            try:
                data = resp.json()
            except Exception:
                raise UpstreamAPIError(resp.status_code, None, resp.text)
            raise UpstreamAPIError(resp.status_code, data.get("error", {}).get("status"), str(data))

        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            raise UpstreamAPIError(502, "geminiParseError", "Unexpected Gemini response format")
