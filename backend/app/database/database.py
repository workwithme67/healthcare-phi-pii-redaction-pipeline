"""
HealthTech PHI/PII Redaction Pipeline
Database Initialisation

SQLite setup via SQLAlchemy.
Redis client preparation for future caching / pub-sub.
"""

import logging
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.settings import settings

logger = logging.getLogger(__name__)

# ── SQLAlchemy setup ──────────────────────────────────────────────────────────

# Ensure the data directory exists for SQLite
if settings.DATABASE_URL.startswith("sqlite"):
    _db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    Path(_db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


def init_db() -> None:
    """
    Create all tables defined in ORM models.
    Called once at application startup.
    """
    # Import models so SQLAlchemy registers them before create_all
    from app.models import audit_log, redaction_job  # noqa: F401
    from app.database import models as db_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created / verified.", extra={"url": settings.DATABASE_URL})


def get_db():
    """
    FastAPI dependency that yields a database session.
    Ensures the session is always closed after the request.

    Usage:
        def route(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Health-check helper — returns True if DB is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Database connection failed: %s", exc)
        return False
