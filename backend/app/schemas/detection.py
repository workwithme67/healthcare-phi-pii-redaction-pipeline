"""
HealthTech PHI/PII Redaction Pipeline
Pydantic Schemas — Detection Engine

Request / response shapes for /api/detect, /api/redact, /api/statistics.
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field, field_validator

from app.schemas.base import AppBaseModel


# ── Shared ─────────────────────────────────────────────────────────────────────

class EntityResult(AppBaseModel):
    """A single detected PHI/PII entity."""

    type: str = Field(..., description="Entity type label (e.g. EMAIL, PHONE).")
    value: str = Field(..., description="Raw matched text.")
    start: int = Field(..., ge=0, description="Start character offset in original text.")
    end: int = Field(..., ge=0, description="End character offset (exclusive).")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence [0, 1].")


# ── Detect ─────────────────────────────────────────────────────────────────────

class DetectRequest(AppBaseModel):
    """Payload for POST /api/detect."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=500_000,
        description="Clinical note or freeform text to scan for PHI/PII.",
        examples=["Patient John Smith can be contacted at 9876543210 and john@example.com."],
    )

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must contain non-whitespace characters.")
        return v


class DetectResponse(AppBaseModel):
    """Response from POST /api/detect."""

    success: bool = True
    entities: list[EntityResult] = Field(default_factory=list)
    entity_count: int = 0
    processing_time_ms: Optional[float] = None


# ── Redact ─────────────────────────────────────────────────────────────────────

class RedactRequest(AppBaseModel):
    """Payload for POST /api/redact."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=500_000,
        description="Clinical note text to redact.",
    )

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must contain non-whitespace characters.")
        return v


class RedactResponse(AppBaseModel):
    """Response from POST /api/redact."""

    success: bool = True
    redacted_text: str = Field(..., description="Text with PHI/PII replaced by placeholders.")
    entities: list[EntityResult] = Field(default_factory=list)
    entity_count: int = 0
    processing_time_ms: Optional[float] = None


# ── Statistics ─────────────────────────────────────────────────────────────────

class EntityTypeCount(AppBaseModel):
    """Count of a single entity type."""

    type: str
    count: int


class StatisticsResponse(AppBaseModel):
    """Response from GET /api/statistics."""

    total_notes_processed: int = Field(0, description="Total detect/redact calls logged.")
    total_entities_found: int = Field(0, description="Sum of all entities across all calls.")
    entity_counts_by_type: list[EntityTypeCount] = Field(
        default_factory=list,
        description="Per-type entity counts across all logged calls.",
    )
    average_detection_time_ms: Optional[float] = Field(
        None, description="Mean processing time in milliseconds."
    )
    total_detect_calls: int = 0
    total_redact_calls: int = 0
