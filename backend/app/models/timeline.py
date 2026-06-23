"""
Updated timeline model — adds PlaybookExecuted event type.
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, Enum as SAEnum, ForeignKey,
    Integer, String, Text,
)
from sqlalchemy.orm import relationship

from app.database.db import Base


class EventType(str, enum.Enum):
    AlertCreated      = "AlertCreated"
    AlertEnriched     = "AlertEnriched"
    RiskCalculated    = "RiskCalculated"
    StatusUpdated     = "StatusUpdated"
    PlaybookExecuted  = "PlaybookExecuted"
    AlertDeleted      = "AlertDeleted"


class TimelineEvent(Base):
    """One timestamped event on an alert's lifecycle."""

    __tablename__ = "timeline_events"

    id: int = Column(Integer, primary_key=True, index=True, autoincrement=True)

    alert_db_id: int = Column(
        Integer,
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    alert_id: str = Column(String(50), nullable=False, index=True)

    event_type: str = Column(
        SAEnum(EventType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    description: str = Column(String(500), nullable=False)

    metadata_json: str = Column(Text, nullable=True)

    occurred_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    alert = relationship("Alert", back_populates="timeline_events")

    def __repr__(self) -> str:
        return (
            f"<TimelineEvent id={self.id} alert_id={self.alert_id!r} "
            f"type={self.event_type} at={self.occurred_at}>"
        )
