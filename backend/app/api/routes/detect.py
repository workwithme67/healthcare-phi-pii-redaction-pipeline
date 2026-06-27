"""
HealthTech PHI/PII Redaction Pipeline
API Routes — Detection Engine

Endpoints
---------
POST /api/detect      → run regex detector, return entity list
POST /api/redact      → detect + replace entities with placeholders
GET  /api/statistics  → aggregate metrics from detection_logs table
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.detection_log import DetectionLog
from app.schemas.detection import (
    DetectRequest,
    DetectResponse,
    EntityResult,
    EntityTypeCount,
    RedactRequest,
    RedactResponse,
    StatisticsResponse,
)
from app.services.regex_detector import detector

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Detection Engine"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _log_detection(
    db: Session,
    *,
    operation: str,
    text_length: int,
    entity_count: int,
    entity_types: list[str],
    processing_time_ms: float,
) -> None:
    """Persist a detection event to the detection_logs table."""
    try:
        log = DetectionLog(
            operation=operation,
            text_length=text_length,
            entity_count=entity_count,
            entity_types=",".join(sorted(entity_types)) if entity_types else "",
            processing_time_ms=round(processing_time_ms, 3),
        )
        db.add(log)
        db.commit()
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to write detection log: %s", exc)
        db.rollback()


# ── POST /api/detect ──────────────────────────────────────────────────────────

@router.post(
    "/detect",
    response_model=DetectResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect PHI/PII entities",
    description=(
        "Run the regex-based PHI/PII detection engine over the submitted text. "
        "Returns a list of detected entities with type, value, position, and confidence."
    ),
)
def detect_entities(
    payload: DetectRequest,
    db: Session = Depends(get_db),
) -> DetectResponse:
    """POST /api/detect — detect PHI/PII entities using regex patterns."""
    logger.info("Detection request received: %d chars", len(payload.text))

    result = detector.detect(payload.text)

    entities_out: list[EntityResult] = [
        EntityResult(
            type=e.type,
            value=e.value,
            start=e.start,
            end=e.end,
            confidence=e.confidence,
        )
        for e in result.entities
    ]

    _log_detection(
        db,
        operation="detect",
        text_length=result.text_length,
        entity_count=result.entity_count,
        entity_types=result.entity_types,
        processing_time_ms=result.processing_time_ms,
    )

    logger.info(
        "Detection complete: %d entities in %.2f ms",
        result.entity_count,
        result.processing_time_ms,
    )

    return DetectResponse(
        success=True,
        entities=entities_out,
        entity_count=result.entity_count,
        processing_time_ms=result.processing_time_ms,
    )


# ── POST /api/redact ──────────────────────────────────────────────────────────

@router.post(
    "/redact",
    response_model=RedactResponse,
    status_code=status.HTTP_200_OK,
    summary="Redact PHI/PII entities",
    description=(
        "Detect PHI/PII entities and replace them with numbered placeholders "
        "such as [EMAIL_001], [PHONE_002], etc."
    ),
)
def redact_text(
    payload: RedactRequest,
    db: Session = Depends(get_db),
) -> RedactResponse:
    """POST /api/redact — detect and replace PHI/PII with placeholders."""
    logger.info("Redaction request received: %d chars", len(payload.text))

    redacted_text, entities = detector.redact(payload.text)
    processing_time_ms = detector.detect(payload.text).processing_time_ms  # rerun for timing

    entity_types = sorted({e.type for e in entities})
    entities_out: list[EntityResult] = [
        EntityResult(
            type=e.type,
            value=e.value,
            start=e.start,
            end=e.end,
            confidence=e.confidence,
        )
        for e in entities
    ]

    _log_detection(
        db,
        operation="redact",
        text_length=len(payload.text),
        entity_count=len(entities),
        entity_types=entity_types,
        processing_time_ms=processing_time_ms,
    )

    logger.info(
        "Redaction complete: %d entities replaced",
        len(entities),
    )

    return RedactResponse(
        success=True,
        redacted_text=redacted_text,
        entities=entities_out,
        entity_count=len(entities),
        processing_time_ms=processing_time_ms,
    )


# ── GET /api/statistics ───────────────────────────────────────────────────────

@router.get(
    "/statistics",
    response_model=StatisticsResponse,
    summary="Detection statistics",
    description="Aggregate metrics from all detection and redaction calls.",
)
def get_statistics(db: Session = Depends(get_db)) -> StatisticsResponse:
    """GET /api/statistics — return aggregated detection metrics."""

    # Total calls
    total_notes = db.query(DetectionLog).count()
    total_detect = db.query(DetectionLog).filter(DetectionLog.operation == "detect").count()
    total_redact = db.query(DetectionLog).filter(DetectionLog.operation == "redact").count()

    # Total entities
    total_entities_row = db.query(func.sum(DetectionLog.entity_count)).scalar()
    total_entities: int = int(total_entities_row or 0)

    # Average processing time
    avg_time_row = db.query(func.avg(DetectionLog.processing_time_ms)).scalar()
    avg_time: Optional[float] = round(float(avg_time_row), 3) if avg_time_row else None

    # Entity type breakdown — parse stored CSV strings
    type_counter: Counter = Counter()
    logs_with_types = (
        db.query(DetectionLog.entity_types, DetectionLog.entity_count)
        .filter(DetectionLog.entity_types != "", DetectionLog.entity_types.isnot(None))
        .all()
    )
    for row in logs_with_types:
        if row.entity_types:
            for t in row.entity_types.split(","):
                t = t.strip()
                if t:
                    type_counter[t] += 1

    entity_counts_by_type = [
        EntityTypeCount(type=k, count=v)
        for k, v in sorted(type_counter.items(), key=lambda x: -x[1])
    ]

    return StatisticsResponse(
        total_notes_processed=total_notes,
        total_entities_found=total_entities,
        entity_counts_by_type=entity_counts_by_type,
        average_detection_time_ms=avg_time,
        total_detect_calls=total_detect,
        total_redact_calls=total_redact,
    )
