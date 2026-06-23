"""
Database configuration and session management.

Reads DATABASE_URL from app.config (which reads from .env).
SQLite for development; swap DATABASE_URL for PostgreSQL in production.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────
_connect_args = (
    {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args)

# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Declarative base ──────────────────────────────────────────────────────────
Base = declarative_base()


# ── Request-scoped DB dependency ──────────────────────────────────────────────
def get_db():
    """FastAPI dependency that yields a per-request SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
