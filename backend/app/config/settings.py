"""
HealthTech PHI/PII Redaction Pipeline
Configuration Settings

Uses Pydantic Settings for environment variable management.
Supports .env files for local development.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration class using Pydantic Settings.
    Values are loaded from environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "HealthTech PHI/PII Redaction Pipeline"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"          # development | staging | production
    DEBUG: bool = True

    # ── Server ───────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1                      # increase for production

    # ── CORS ─────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",          # Vite dev server
        "http://localhost:3000",
        "http://frontend:5173",           # Docker service name
    ]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./data/redaction.db"

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 10

    # ── AI / LLM Integrations (Future Day 2+) ────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    # ── Microsoft Presidio (Future Day 2+) ───────────────────────────────────
    PRESIDIO_ANALYZER_URL: str = "http://localhost:5002"
    PRESIDIO_ANONYMIZER_URL: str = "http://localhost:5003"

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"              # json | text

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-long-random-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    Use as a FastAPI dependency: Depends(get_settings)
    """
    return Settings()


# Module-level singleton for non-DI usage
settings: Settings = get_settings()
