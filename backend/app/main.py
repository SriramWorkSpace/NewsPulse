from __future__ import annotations
import sys

print("=== MAIN.PY STARTING ===", file=sys.stderr, flush=True)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

print("FastAPI imported", file=sys.stderr, flush=True)

from app.api.routes.search import router as search_router
print("search_router imported", file=sys.stderr, flush=True)
from app.api.routes.summarize import router as summarize_router
print("summarize_router imported", file=sys.stderr, flush=True)
from app.api.routes.trends import router as trends_router
print("trends_router imported", file=sys.stderr, flush=True)
from app.api.routes.ml import router as ml_router
print("ml_router imported", file=sys.stderr, flush=True)
from app.core.config import settings
print("settings imported", file=sys.stderr, flush=True)
from app.services.analytics.keywords import load_spacy_model
print("load_spacy_model imported", file=sys.stderr, flush=True)
from app.services.poller import HeadlinePoller
print("HeadlinePoller imported", file=sys.stderr, flush=True)

print("Loading spaCy model...", file=sys.stderr, flush=True)
nlp = load_spacy_model()
print("spaCy model loaded", file=sys.stderr, flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Lifespan starting...", file=sys.stderr, flush=True)
    poller = HeadlinePoller(sqlite_path=settings.sqlite_path)
    await poller.start()
    app.state.poller = poller
    print("Poller started, yielding...", file=sys.stderr, flush=True)
    yield
    await poller.stop()


print("Creating FastAPI app...", file=sys.stderr, flush=True)
app = FastAPI(title="NewsPulse API", version="0.1.0", lifespan=lifespan)
print("FastAPI app created", file=sys.stderr, flush=True)

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
