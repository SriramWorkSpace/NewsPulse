from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.core.errors import UpstreamAPIError
from app.services.gemini_client import GeminiClient


router = APIRouter()


class SummarizeRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    content: str | None = None


@router.post("/summarize")
async def summarize(req: SummarizeRequest):
    if not (req.title or req.description or req.content):
        raise HTTPException(status_code=400, detail={"status": "error", "code": "parametersMissing", "message": "Provide at least one of title/description/content"})

    client = GeminiClient()
    try:
        summary = await client.summarize(title=req.title, description=req.description, content=req.content)
        return {"summary": summary}
    except UpstreamAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    finally:
        await client.close()
