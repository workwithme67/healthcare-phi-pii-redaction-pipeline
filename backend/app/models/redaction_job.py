"""
HealthTech PHI/PII Redaction Pipeline
ORM Model — Redaction Job

Tracks a single clinical-note redaction request through its lifecycle.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobStatus(str, PyEnum):
    """Lifecycle states of a redaction job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEWED = "reviewed"


class RedactionJob(Base):
    """
    Represents a single clinical-note redaction request.

    Columns
    -------
    id              : Auto-incrementing primary key.
    job_id          : Globally unique UUID for external reference.
    filename        : Original file name uploaded by the user.
    original_text   : Raw text extracted from the uploaded document.
    redacted_text   : Output text after PHI/PII redaction (Day 2+).
    status          : Current job lifecycle status (see JobStatus).
    entity_count    : Number of PHI/PII entities detected (Day 2+).
    confidence_avg  : Average detection confidence score (Day 2+).
    error_message   : Error detail if the job failed.
    processing_time : Wall-clock time in seconds for the redaction step.
    created_at      : UTC timestamp when the job was created.
    updated_at      : UTC timestamp of the last status change.
    """

    __tablename__ = "redaction_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[str] = mapped_column(
        String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True, nullable=False
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=True)
    original_text: Mapped[str] = mapped_column(Text, nullable=True)
    redacted_text: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True
    )
    entity_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confidence_avg: Mapped[float] = mapped_column(Float, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    processing_time: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<RedactionJob job_id={self.job_id!r} status={self.status!r} "
            f"filename={self.filename!r}>"
        )
