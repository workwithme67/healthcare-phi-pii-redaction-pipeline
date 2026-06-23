"""
Playbook Service
================
Orchestrates playbook selection, execution, result persistence,
timeline recording, and blocked-IP tracking.
"""

from __future__ import annotations

import json
import sys
import os
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.blocked_ip import BlockedIP
from app.models.playbook import PlaybookExecution, PlaybookStatus
from app.models.timeline import EventType
from app.services import timeline_service
from app.utils.helpers import get_logger

logger = get_logger(__name__)

# Add project root to path so playbooks package is importable
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _load_playbook(name: str):
    """Dynamically load a playbook module by name."""
    try:
        import importlib
        module = importlib.import_module(f"playbooks.{name}")
        return module
    except ModuleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playbook '{name}' not found. "
                   f"Available: block_ip, isolate_host, notify_soc, escalate.",
        )


def _get_alert_by_string_id(db: Session, alert_id: str) -> Alert:
    """Fetch alert by human-readable alert_id string."""
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' not found.",
        )
    return alert


def execute_playbook(
    db: Session,
    alert_id: str,
    playbook_name: str,
    target: Optional[str] = None,
    executed_by: str = "system",
    notes: Optional[str] = None,
) -> PlaybookExecution:
    """
    Resolve the alert, execute the named playbook, persist the result,
    and record a timeline event.

    Parameters
    ----------
    db            : SQLAlchemy session.
    alert_id      : Human-readable alert ID (e.g. ALERT-A3F80001).
    playbook_name : Name of playbook to run.
    target        : Optional override target (defaults to alert.source_ip).
    executed_by   : Username of the triggering user.
    notes         : Optional notes to attach to execution record.

    Returns
    -------
    PlaybookExecution : The persisted execution record.
    """
    # 1. Resolve alert
    alert = _get_alert_by_string_id(db, alert_id)
    effective_target = target or alert.source_ip

    # 2. Load and run playbook
    module = _load_playbook(playbook_name)
    try:
        if playbook_name == "block_ip":
            result: Dict[str, Any] = module.execute(
                ip_address=effective_target,
                alert_id=alert_id,
                reason=notes,
                executed_by=executed_by,
            )
        elif playbook_name == "notify_soc":
            result = module.execute(
                target=effective_target,
                alert_id=alert_id,
                alert_type=alert.alert_type,
                severity=alert.severity,
                reason=notes,
                executed_by=executed_by,
            )
        elif playbook_name == "escalate":
            result = module.execute(
                target=effective_target,
                alert_id=alert_id,
                alert_type=alert.alert_type,
                severity=alert.severity,
                risk_score=alert.risk_score,
                reason=notes,
                executed_by=executed_by,
            )
        else:
            result = module.execute(
                target=effective_target,
                alert_id=alert_id,
                reason=notes,
                executed_by=executed_by,
            )
        exec_status = PlaybookStatus.Success
    except Exception as exc:
        logger.error("Playbook [%s] failed: %s", playbook_name, exc)
        result = {"error": str(exc)}
        exec_status = PlaybookStatus.Failed

    # 3. Persist execution record
    execution = PlaybookExecution(
        alert_db_id=alert.id,
        alert_id=alert_id,
        playbook_name=playbook_name,
        action=result.get("action", playbook_name.upper()),
        target=effective_target,
        status=exec_status,
        result_message=result.get("message", ""),
        result_data=json.dumps(result, default=str),
        executed_by=executed_by,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    # 4. Record timeline event
    timeline_service.add_event(
        db=db,
        alert_db_id=alert.id,
        alert_id=alert_id,
        event_type=EventType.PlaybookExecuted,
        description=(
            f"Playbook '{playbook_name}' executed | "
            f"target={effective_target} status={exec_status.value}"
        ),
        metadata={
            "playbook": playbook_name,
            "target":   effective_target,
            "status":   exec_status.value,
            "action":   result.get("action"),
        },
    )

    # 5. Track blocked IP if this was a block_ip playbook
    if playbook_name == "block_ip" and exec_status == PlaybookStatus.Success:
        _track_blocked_ip(db, effective_target, alert_id, notes, executed_by)

    logger.info(
        "Playbook executed | name=%s alert=%s target=%s status=%s",
        playbook_name, alert_id, effective_target, exec_status.value,
    )
    return execution


def _track_blocked_ip(
    db: Session,
    ip: str,
    alert_id: str,
    reason: Optional[str],
    blocked_by: str,
) -> None:
    """Upsert a BlockedIP record."""
    existing = db.query(BlockedIP).filter(BlockedIP.ip_address == ip).first()
    if not existing:
        record = BlockedIP(
            ip_address=ip,
            alert_id=alert_id,
            reason=reason or "Blocked via SOAR playbook",
            blocked_by=blocked_by,
        )
        db.add(record)
        db.commit()


def get_executions(
    db: Session,
    alert_id: Optional[str] = None,
    limit: int = 50,
) -> List[PlaybookExecution]:
    """List playbook executions, optionally filtered by alert_id."""
    q = db.query(PlaybookExecution)
    if alert_id:
        q = q.filter(PlaybookExecution.alert_id == alert_id)
    return q.order_by(PlaybookExecution.executed_at.desc()).limit(limit).all()


def count_blocked_ips(db: Session) -> int:
    return db.query(BlockedIP).count()


def get_blocked_ips(db: Session, limit: int = 100) -> List[BlockedIP]:
    return db.query(BlockedIP).order_by(BlockedIP.blocked_at.desc()).limit(limit).all()
