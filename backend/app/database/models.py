"""
HealthTech PHI/PII Redaction Pipeline
ORM Model — Uploads

Stores metadata and raw content of uploaded clinical notes and files.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Upload(Base):
    """
    Stores clinical notes and uploaded files.

    Columns
    -------
    id          : Unique UUID identifier (Primary Key).
    filename    : Original name of the uploaded file (or None for raw text).
    note_text   : Raw clinical note content (or None for PDFs before parsing).
    file_type   : File type classification: 'TEXT', 'TXT', 'PDF'.
    size_bytes  : Size of the uploaded content in bytes.
    created_at  : Timestamp (UTC) when the note was uploaded.
    status      : Status of processing: 'Uploaded', 'Pending Processing', etc.
    """

    __tablename__ = "uploads"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=True)
    note_text: Mapped[str] = mapped_column(Text, nullable=True)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="Uploaded", nullable=False)

    def __repr__(self) -> str:
        return f"<Upload id={self.id} filename={self.filename!r} type={self.file_type!r} status={self.status!r}>"
