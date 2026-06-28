"""
HealthTech PHI/PII Redaction Pipeline
Pydantic Schemas — Detection Engine

Request / response shapes for:
  /api/detect        (Day 3 — regex)
  /api/redact        (Day 3 — regex)
  /api/statistics    (Day 3 — aggregate metrics)
  /api/detect-ai     (Day 4 — Presidio + spaCy)
  /api/compare       (Day 4 — engine comparison)
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
    source: str = Field(default="Regex", description="Detection source (e.g. 'Regex').")


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


# ── Day 4: AI Detection ────────────────────────────────────────────────────────

class AIEntityResult(AppBaseModel):
    """A single PHI/PII entity from the AI pipeline (Presidio or spaCy)."""

    type: str = Field(..., description="Entity type label (e.g. PERSON, EMAIL_ADDRESS).")
    value: str = Field(..., description="Raw matched text span.")
    start: int = Field(..., ge=0, description="Start character offset.")
    end: int = Field(..., ge=0, description="End character offset (exclusive).")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence [0, 1].")
    source: str = Field(
        default="Presidio",
        description="Detection source: 'Presidio', 'spaCy', or 'Regex'.",
    )
    all_sources: list[str] = Field(
        default_factory=list,
        description="All sources that detected this entity (populated after merging).",
    )


class AIDetectRequest(AppBaseModel):
    """Payload for POST /api/detect-ai."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=500_000,
        description="Clinical note text to analyze with the AI engine.",
        examples=["Patient John Smith visited Apollo Hospital on 12/04/2026."],
    )

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must contain non-whitespace characters.")
        return v


class AIDetectResponse(AppBaseModel):
    """Response from POST /api/detect-ai."""

    success: bool = True
    entities: list[AIEntityResult] = Field(default_factory=list)
    entity_count: int = 0
    presidio_count: int = Field(0, description="Entities detected by Presidio alone.")
    spacy_count: int = Field(0, description="Entities detected by spaCy alone.")
    processing_time_ms: Optional[float] = None


# ── Day 4: Compare ─────────────────────────────────────────────────────────────

class CompareRequest(AppBaseModel):
    """Payload for POST /api/compare."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=500_000,
        description="Text to run all three detection engines on.",
    )

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must contain non-whitespace characters.")
        return v


class EngineStats(AppBaseModel):
    """Per-engine detection statistics."""

    engine: str
    entity_count: int
    processing_time_ms: float
    entity_types: list[str] = Field(default_factory=list)


class CompareResponse(AppBaseModel):
    """Response from POST /api/compare."""

    success: bool = True
    regex: int = Field(0, description="Entity count from Regex engine.")
    presidio: int = Field(0, description="Entity count from Presidio engine.")
    spacy: int = Field(0, description="Entity count from spaCy engine.")
    merged: int = Field(0, description="Entity count after merging and deduplication.")
    duplicates_removed: int = Field(0, description="Entities removed as duplicates.")
    processing_time: str = Field("", description="Total wall-clock time (e.g. '48ms').")
    processing_time_ms: float = Field(0.0, description="Total processing time in ms.")
    engine_stats: list[EngineStats] = Field(
        default_factory=list,
        description="Per-engine breakdown of counts and latency.",
    )
    merged_entities: list[AIEntityResult] = Field(
        default_factory=list,
        description="Final merged entity list.",
    )
