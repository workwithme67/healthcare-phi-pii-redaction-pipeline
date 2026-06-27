"""
HealthTech PHI/PII Redaction Pipeline
ORM Model — Detection Log

Stores per-request detection metadata for the statistics dashboard.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DetectionLog(Base):
    """
    Immutable record of a single /api/detect or /api/redact call.

    Columns
    -------
    id                 : Auto-incrementing primary key.
    session_id         : UUID grouping a user session.
    operation          : 'detect' or 'redact'.
    text_length        : Character length of the submitted text.
    entity_count       : Number of entities found.
    entity_types       : Comma-separated list of detected type names.
    processing_time_ms : Wall-clock time for the detection run (ms).
    detected_at        : UTC timestamp of the request.
    """

    __tablename__ = "detection_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(
        String(36), default=lambda: str(uuid.uuid4()), index=True, nullable=False
    )
    operation: Mapped[str] = mapped_column(
        String(16), default="detect", nullable=False, index=True
    )
    text_length: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    entity_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    entity_types: Mapped[str] = mapped_column(
        Text, nullable=True, comment="Comma-separated entity type names"
    )
    processing_time_ms: Mapped[float] = mapped_column(Float, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )

    def __repr__(self) -> str:
        return (
            f"<DetectionLog id={self.id} op={self.operation!r} "
            f"entities={self.entity_count} at={self.detected_at.isoformat()}>"
        )
