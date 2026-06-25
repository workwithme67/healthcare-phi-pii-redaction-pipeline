"""
HealthTech PHI/PII Redaction Pipeline
Pydantic Schemas — Health Check
"""

from typing import Optional

from app.schemas.base import AppBaseModel


class HealthResponse(AppBaseModel):
    """Standard health-check response body."""

    status: str
    project: str
    version: str
    environment: str
    database: str
    uptime_seconds: Optional[float] = None
