"""
SQLAlchemy ORM model for blocked IPs.

Tracks every IP that has been blocked via playbook execution.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database.db import Base


class BlockedIP(Base):
    """A record of a blocked IP address."""

    __tablename__ = "blocked_ips"

    id: int = Column(Integer, primary_key=True, index=True, autoincrement=True)

    ip_address: str = Column(String(45), unique=True, nullable=False, index=True)
    alert_id:   str = Column(String(50), nullable=True)   # originating alert

    reason:     str = Column(String(500), nullable=True)
    blocked_by: str = Column(String(80),  nullable=True, default="system")

    notes: str = Column(Text, nullable=True)

    blocked_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<BlockedIP ip={self.ip_address!r} alert={self.alert_id!r}>"
