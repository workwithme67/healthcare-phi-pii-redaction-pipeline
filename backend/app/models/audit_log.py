"""
HealthTech PHI/PII Redaction Pipeline
ORM Model — Audit Log

Records every redaction request for HIPAA-compliant audit trails.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(Base):
    """
    Stores an immutable audit record for every API call that touches PHI.

    Columns
    -------
    id              : Auto-incrementing primary key.
    request_id      : UUID tied to the originating HTTP request.
    action          : One of: UPLOAD | REDACT | REVIEW | EXPORT | DELETE.
    actor           : Identifier of the user / service making the request.
    resource_type   : e.g. 'clinical_note', 'redaction_job'.
    resource_id     : The ID of the resource acted upon.
    ip_address      : Remote IP captured from the request.
    user_agent      : HTTP User-Agent header.
    status_code     : HTTP response code returned.
    detail          : Optional free-text detail or error message.
    created_at      : Timestamp (UTC) when the record was written.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[str] = mapped_column(
        String(36), default=lambda: str(uuid.uuid4()), index=True, nullable=False
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(256), nullable=False, default="anonymous")
    resource_type: Mapped[str] = mapped_column(String(128), nullable=True)
    resource_id: Mapped[str] = mapped_column(String(256), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(512), nullable=True)
    status_code: Mapped[int] = mapped_column(Integer, nullable=True)
    detail: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} action={self.action!r} actor={self.actor!r} "
            f"at={self.created_at.isoformat()}>"
        )
