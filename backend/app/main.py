"""
HealthTech PHI/PII Redaction Pipeline
FastAPI Application Entry Point

This module creates and configures the FastAPI application instance.
It is the single entry point referenced by Uvicorn:

    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router, detect_router
from app.api.upload import router as upload_router
from app.config.logging_config import setup_logging
from app.config.settings import settings
from app.database.database import init_db
from app.middleware.logging_middleware import RequestLoggingMiddleware

# ── Logging must be set up before anything else ───────────────────────────────
setup_logging()
logger = logging.getLogger(__name__)


# ── Application Factory ────────────────────────────────────────────────────────

def create_application() -> FastAPI:
    """
    Application factory function.

    Separating creation from the module-level `app` variable makes the
    application easier to test (import without side-effects).
    """
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "HIPAA-compliant PHI/PII detection and redaction pipeline for "
            "Large Language Models. Built for HealthTech organisations that need "
            "to safely process clinical notes before sending them to LLM APIs."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=settings.ALLOWED_METHODS,
        allow_headers=settings.ALLOWED_HEADERS,
    )

    # ── Custom request-logging middleware ─────────────────────────────────────
    application.add_middleware(RequestLoggingMiddleware)

    # ── API Routes ────────────────────────────────────────────────────────────
    application.include_router(api_router)
    application.include_router(detect_router)      # Day 3: /api/detect, /api/redact, /api/statistics
    application.include_router(upload_router)

    # ── Root Redirect ─────────────────────────────────────────────────────────
    @application.get("/", include_in_schema=False)
    def root():
        return {
            "message": "HealthTech PHI/PII Redaction API",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/api/v1/app/health",
        }

    # ── Startup / Shutdown Events ─────────────────────────────────────────────
    @application.on_event("startup")
    async def on_startup() -> None:
        logger.info(
            "Starting %s v%s [%s]",
            settings.APP_NAME,
            settings.APP_VERSION,
            settings.APP_ENV,
        )
        init_db()
        # Ensure upload directory exists
        from pathlib import Path
        Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        logger.info("Application startup complete.")

    @application.on_event("shutdown")
    async def on_shutdown() -> None:
        logger.info("Application shutting down.")

    return application


# ── Module-level app instance (used by Uvicorn) ───────────────────────────────
app: FastAPI = create_application()
