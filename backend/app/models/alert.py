"""
SQLAlchemy ORM model for security alerts.

Fields
------
id              : Auto-incrementing integer primary key.
alert_id        : Human-readable unique ID (e.g. "ALERT-A3F80001").
alert_type      : Category of the alert (Brute Force, Port Scan, …).
source_ip       : IPv4 address that triggered the alert.
severity        : Low | Medium | High | Critical.
status          : Open | Investigating | Resolved.
description     : Optional free-text context.
risk_score      : Computed numeric risk score [0, 100].
threat_verdict  : Threat intelligence verdict — Clean | Suspicious | Malicious | Unknown.
enrichment_data : JSON string storing the full TI enrichment report.
created_at      : UTC timestamp of first ingestion.
updated_at      : UTC timestamp of last modification.

Relationships
-------------
timeline_events : List[TimelineEvent] — full lifecycle audit trail.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum as SAEnum, Float, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.db import Base


# ── Severity Enum ─────────────────────────────────────────────────────────────
class SeverityLevel(str, enum.Enum):
    Low      = "Low"
    Medium   = "Medium"
    High     = "High"
    Critical = "Critical"


# ── Status Enum ───────────────────────────────────────────────────────────────
class AlertStatus(str, enum.Enum):
    Open          = "Open"
    Investigating = "Investigating"
    Resolved      = "Resolved"


# ── ORM Model ─────────────────────────────────────────────────────────────────
class Alert(Base):
    """ORM representation of a security alert stored in the database."""

    __tablename__ = "alerts"

    id: int = Column(Integer, primary_key=True, index=True, autoincrement=True)

    alert_id: str = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: f"ALERT-{uuid.uuid4().hex[:8].upper()}",
    )

    alert_type: str = Column(String(100), nullable=False, index=True)
    source_ip:  str = Column(String(45),  nullable=False)

    severity: str = Column(
        SAEnum(SeverityLevel, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=SeverityLevel.Medium,
    )

    status: str = Column(
        SAEnum(AlertStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AlertStatus.Open,
    )

    description: str = Column(String(500), nullable=True)

    risk_score: float = Column(Float, nullable=True, default=0.0)

    # Threat intelligence outputs
    threat_verdict: str   = Column(String(20),  nullable=True, default="Unknown")
    enrichment_data: str  = Column(Text,         nullable=True)   # JSON string

    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    timeline_events = relationship(
        "TimelineEvent",
        back_populates="alert",
        cascade="all, delete-orphan",
        order_by="TimelineEvent.occurred_at",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Alert alert_id={self.alert_id!r} type={self.alert_type!r} "
            f"severity={self.severity} status={self.status} "
            f"score={self.risk_score} verdict={self.threat_verdict}>"
        )
