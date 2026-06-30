"""
LLM Audit Log Model
====================
SQLAlchemy ORM model for storing LLM request/response audit logs.

Security note: Raw PHI is NEVER stored. Only pseudonymized session
IDs, token counts, latency, and provider metadata are persisted.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from app.database.db import Base


class LLMLog(Base):
    """Audit log entry for a single LLM API call."""

    __tablename__ = "llm_logs"

    id: int = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # ── Session / Tracing ─────────────────────────────────────────────────────
    session_id: str = Column(String(64), nullable=False, index=True)
    task_type: str = Column(
        String(50), nullable=False
    )  # summarize | diagnosis | treatment | explanation | process

    # ── Provider Info ─────────────────────────────────────────────────────────
    provider: str = Column(String(20), nullable=False)   # openai | ollama
    model: str = Column(String(100), nullable=False)

    # ── Token Usage ───────────────────────────────────────────────────────────
    prompt_tokens: int = Column(Integer, nullable=False, default=0)
    completion_tokens: int = Column(Integer, nullable=False, default=0)
    total_tokens: int = Column(Integer, nullable=False, default=0)

    # ── Performance ───────────────────────────────────────────────────────────
    latency_ms: float = Column(Float, nullable=False, default=0.0)

    # ── Security / Compliance ─────────────────────────────────────────────────
    phi_entities_count: int = Column(
        Integer, nullable=False, default=0,
        doc="Number of PHI/PII entities detected and pseudonymized"
    )
    has_phi_warning: bool = Column(
        Boolean, nullable=False, default=False,
        doc="True if PHI was found in the original input"
    )

    # ── Status ────────────────────────────────────────────────────────────────
    success: bool = Column(Boolean, nullable=False, default=True)
    error_message: Optional[str] = Column(Text, nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<LLMLog id={self.id} session={self.session_id!r} "
            f"provider={self.provider!r} task={self.task_type!r} "
            f"tokens={self.total_tokens} latency={self.latency_ms:.1f}ms>"
        )
