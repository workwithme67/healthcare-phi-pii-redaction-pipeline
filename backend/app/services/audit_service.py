"""
HealthTech PHI/PII Redaction Pipeline
Service — Audit Log

Handles creating and querying audit log records.
All PHI-touching operations must call `log_action` to maintain
a HIPAA-compliant audit trail.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service class for audit log operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def log_action(
        self,
        *,
        action: str,
        actor: str = "anonymous",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status_code: Optional[int] = None,
        detail: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLog:
        """
        Write a new audit log entry to the database.

        Parameters
        ----------
        action       : Short action name, e.g. 'UPLOAD', 'REDACT', 'VIEW'.
        actor        : User identifier (username, service account, etc.).
        resource_type: Type of resource, e.g. 'redaction_job'.
        resource_id  : ID of the specific resource.
        ip_address   : Remote IP of the requestor.
        user_agent   : HTTP User-Agent string.
        status_code  : HTTP status code of the response.
        detail       : Optional additional detail or error message.
        request_id   : Correlation ID from the request context.

        Returns
        -------
        The persisted AuditLog ORM instance.
        """
        entry = AuditLog(
            action=action,
            actor=actor,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status_code=status_code,
            detail=detail,
            **({"request_id": request_id} if request_id else {}),
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        logger.info(
            "Audit log written",
            extra={"action": action, "actor": actor, "resource_id": resource_id},
        )
        return entry

    def get_logs(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        action_filter: Optional[str] = None,
    ) -> tuple[list[AuditLog], int]:
        """
        Return a paginated list of audit log entries.

        Returns
        -------
        (items, total_count)
        """
        query = self.db.query(AuditLog).order_by(AuditLog.created_at.desc())

        if action_filter:
            query = query.filter(AuditLog.action == action_filter.upper())

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total
