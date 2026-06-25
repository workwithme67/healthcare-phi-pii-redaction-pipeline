"""
HealthTech PHI/PII Redaction Pipeline
API Route — Audit Logs

Read-only endpoints for querying the HIPAA-compliant audit trail.
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.audit import AuditLogListResponse
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


def _get_service(db: Session = Depends(get_db)) -> AuditService:
    return AuditService(db)


@router.get(
    "",
    response_model=AuditLogListResponse,
    summary="List audit log entries",
    description=(
        "Returns a paginated, newest-first list of all audit events. "
        "Filter by action type to narrow results."
    ),
)
def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    action: str | None = Query(default=None, description="Filter by action type."),
    service: AuditService = Depends(_get_service),
) -> AuditLogListResponse:
    items, total = service.get_logs(
        page=page, page_size=page_size, action_filter=action
    )
    return AuditLogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,  # type: ignore[arg-type]
    )
