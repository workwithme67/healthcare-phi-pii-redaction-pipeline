"""
HealthTech PHI/PII Redaction Pipeline
ORM Model — AI Detection Log (Day 4)

Stores per-request metadata from the AI-powered detection pipeline
(Presidio + spaCy) for auditing and the statistics dashboard.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AIDetectionLog(Base):
    """
    Immutable record of a single /api/detect-ai or /api/compare call.

    Columns
    -------
    id                 : Auto-incrementing primary key.
    session_id         : UUID grouping a user session.
    operation          : 'detect-ai' | 'compare'.
    detection_source   : Comma-separated sources used ('Presidio,spaCy,Regex').
    text_length        : Character length of the submitted text.
    entity_count       : Merged entity count returned to the caller.
    presidio_count     : Raw entity count from Presidio.
    spacy_count        : Raw entity count from spaCy.
    regex_count        : Raw entity count from Regex (compare only).
    entity_types       : Comma-separated list of detected type names.
    processing_time_ms : Total wall-clock time for the pipeline (ms).
    detected_at        : UTC timestamp of the request.
    """

    __tablename__ = "ai_detection_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(
        String(36), default=lambda: str(uuid.uuid4()), index=True, nullable=False
    )
    operation: Mapped[str] = mapped_column(
        String(32), default="detect-ai", nullable=False, index=True
    )
    detection_source: Mapped[str] = mapped_column(
        String(64), default="Presidio,spaCy", nullable=True,
        comment="Comma-separated detection sources"
    )
    text_length: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    entity_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
        comment="Final merged entity count"
    )
    presidio_count: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    spacy_count: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    regex_count: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    entity_types: Mapped[str] = mapped_column(
        Text, nullable=True, comment="Comma-separated entity type names"
    )
    processing_time_ms: Mapped[float] = mapped_column(Float, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )

    def __repr__(self) -> str:
        return (
            f"<AIDetectionLog id={self.id} op={self.operation!r} "
            f"merged={self.entity_count} presidio={self.presidio_count} "
            f"spacy={self.spacy_count} at={self.detected_at.isoformat()}>"
        )
