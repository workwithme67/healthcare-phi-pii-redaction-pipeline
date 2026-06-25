"""
HealthTech PHI/PII Redaction Pipeline
Pydantic Schemas — Audit Log

Response schemas for audit log entries.
"""

from datetime import datetime
from typing import Optional

from app.schemas.base import AppBaseModel


class AuditLogResponse(AppBaseModel):
    """Audit log entry returned by the API."""

    id: int
    request_id: str
    action: str
    actor: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    status_code: Optional[int] = None
    detail: Optional[str] = None
    created_at: datetime


class AuditLogListResponse(AppBaseModel):
    """Paginated list of audit log entries."""

    total: int
    page: int
    page_size: int
    items: list[AuditLogResponse]
