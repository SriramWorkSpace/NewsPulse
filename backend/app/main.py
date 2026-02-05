from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.search import router as search_router
from app.api.routes.summarize import router as summarize_router
from app.api.routes.trends import router as trends_router
from app.api.routes.ml import router as ml_router
from app.core.config import settings
from app.services.analytics.keywords import load_spacy_model
from app.services.poller import HeadlinePoller


nlp = load_spacy_model()


@asynccontextmanager
async def lifespan(app: FastAPI):
    poller = HeadlinePoller(sqlite_path=settings.sqlite_path)
    await poller.start()
    app.state.poller = poller
    yield
    await poller.stop()


app = FastAPI(title="NewsPulse API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your Vercel domain
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trends_router)
app.include_router(search_router)
app.include_router(summarize_router)
app.include_router(ml_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
