from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the backend directory (one level up from this file)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_FILE), extra="ignore")

    news_api_key: str
    gemini_api_key: str

    # Polling / trends
    poll_country: str = "us"
    poll_language: str = "en"
    poll_interval_minutes: int = 30
    retention_hours: int = 48

    # Storage
    sqlite_path: str = "news.db"

    # External
    newsapi_base_url: str = "https://newsapi.org/v2"
    gemini_model: str = "gemini-2.5-flash"  # Latest stable model (verified working)
    gemini_timeout_seconds: float = 20.0


settings = Settings()  # singleton
