"""
SQLAlchemy ORM model for playbook executions.

Records every automated response action triggered against an alert.
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text

from app.database.db import Base


class PlaybookStatus(str, enum.Enum):
    Success = "Success"
    Failed  = "Failed"
    Skipped = "Skipped"


class PlaybookExecution(Base):
    """One playbook execution record tied to an alert."""

    __tablename__ = "playbook_executions"

    id: int = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # FK to alert (string id for easy querying)
    alert_db_id: int = Column(
        Integer,
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alert_id: str = Column(String(50), nullable=False, index=True)

    playbook_name: str = Column(String(100), nullable=False)
    action:        str = Column(String(100), nullable=False)
    target:        str = Column(String(255), nullable=True)   # IP, hostname, etc.

    status: str = Column(
        SAEnum(PlaybookStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=PlaybookStatus.Success,
    )

    result_message: str = Column(String(500), nullable=True)
    result_data:    str = Column(Text, nullable=True)   # JSON

    executed_by: str = Column(String(80), nullable=True, default="system")

    executed_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<PlaybookExecution id={self.id} playbook={self.playbook_name!r} "
            f"alert={self.alert_id!r} status={self.status}>"
        )
