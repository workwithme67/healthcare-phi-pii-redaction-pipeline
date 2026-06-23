"""
Timeline Service
================
Manages alert lifecycle events in the timeline_events table.

Every mutating alert operation should call add_event() so analysts
have a complete, chronological audit trail per incident.

Usage
-----
  from app.services import timeline_service
  from app.models.timeline import EventType

  timeline_service.add_event(
      db=db,
      alert_db_id=alert.id,
      alert_id=alert.alert_id,
      event_type=EventType.AlertCreated,
      description="Alert ingested via POST /alerts",
  )
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.timeline import EventType, TimelineEvent
from app.utils.helpers import get_logger

logger = get_logger(__name__)


# ── Write ─────────────────────────────────────────────────────────────────────

def add_event(
    db: Session,
    alert_db_id: int,
    alert_id: str,
    event_type: EventType,
    description: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> TimelineEvent:
    """
    Append a new timeline event for an alert.

    Parameters
    ----------
    db          : Active SQLAlchemy session.
    alert_db_id : Integer PK of the parent Alert row.
    alert_id    : Human-readable alert identifier (e.g. ALERT-A3F80001).
    event_type  : One of the EventType enum values.
    description : Short human-readable description of the event.
    metadata    : Optional dict of extra context (will be stored as JSON).

    Returns
    -------
    TimelineEvent : The newly created and committed ORM instance.
    """
    meta_json = json.dumps(metadata, default=str) if metadata else None

    event = TimelineEvent(
        alert_db_id=alert_db_id,
        alert_id=alert_id,
        event_type=event_type,
        description=description,
        metadata_json=meta_json,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    logger.info(
        "Timeline | %s | alert_id=%s desc=%r",
        event_type.value, alert_id, description,
    )
    return event


# ── Read ──────────────────────────────────────────────────────────────────────

def get_timeline(db: Session, alert_db_id: int) -> List[TimelineEvent]:
    """
    Retrieve all timeline events for a given alert, ordered oldest→newest.

    Parameters
    ----------
    db          : Active SQLAlchemy session.
    alert_db_id : Integer PK of the parent Alert.

    Returns
    -------
    List[TimelineEvent] : Events in chronological order.
    """
    return (
        db.query(TimelineEvent)
        .filter(TimelineEvent.alert_db_id == alert_db_id)
        .order_by(TimelineEvent.occurred_at.asc())
        .all()
    )


def get_timeline_by_alert_id(db: Session, alert_id: str) -> List[TimelineEvent]:
    """
    Retrieve timeline events by the human-readable alert_id string.

    Parameters
    ----------
    db       : Active SQLAlchemy session.
    alert_id : e.g. "ALERT-A3F80001".
    """
    return (
        db.query(TimelineEvent)
        .filter(TimelineEvent.alert_id == alert_id)
        .order_by(TimelineEvent.occurred_at.asc())
        .all()
    )
