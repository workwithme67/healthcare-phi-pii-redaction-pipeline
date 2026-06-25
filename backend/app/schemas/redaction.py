"""
HealthTech PHI/PII Redaction Pipeline
Pydantic Schemas — Redaction Job

Request / Response schemas for the redaction job API.
"""

from datetime import datetime
from typing import Optional

from pydantic import Field, field_validator

from app.models.redaction_job import JobStatus
from app.schemas.base import AppBaseModel, TimestampMixin


# ── Request Schemas ────────────────────────────────────────────────────────────

class RedactionJobCreate(AppBaseModel):
    """Payload for submitting a new redaction job."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=500_000,
        description="Clinical note text to be redacted.",
        examples=["Patient John Doe, DOB 01/15/1980, was admitted on 06/20/2024."],
    )
    filename: Optional[str] = Field(
        default=None,
        max_length=512,
        description="Original file name (if uploaded from a file).",
    )

    @field_validator("text")
    @classmethod
    def text_must_not_be_whitespace_only(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must contain non-whitespace characters.")
        return v


# ── Response Schemas ───────────────────────────────────────────────────────────

class RedactionJobResponse(TimestampMixin):
    """Full redaction job representation returned by the API."""

    id: int
    job_id: str
    filename: Optional[str] = None
    status: JobStatus
    entity_count: int = 0
    confidence_avg: Optional[float] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    # Note: original_text / redacted_text omitted for security;
    # expose via a dedicated /jobs/{job_id}/content endpoint.


class RedactionJobDetail(RedactionJobResponse):
    """Detailed job view that includes the text content."""

    original_text: Optional[str] = None
    redacted_text: Optional[str] = None


class RedactionJobListResponse(AppBaseModel):
    """Paginated list of redaction jobs."""

    total: int
    page: int
    page_size: int
    items: list[RedactionJobResponse]
