"""
HealthTech PHI/PII Redaction Pipeline
API Route — AI-Powered Detection Engine (Day 4)

Endpoint
--------
POST /api/detect-ai
    Run Presidio + spaCy detection pipeline, merge results, and return
    a deduplicated entity list with source attribution.
"""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.ai_detection_log import AIDetectionLog
from app.schemas.detection import (
    AIDetectRequest,
    AIDetectResponse,
    AIEntityResult,
)
from app.services.entity_merger import EntityMerger
from app.services.presidio_service import presidio_service
from app.services.spacy_service import spacy_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Detection Engine"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _log_ai_detection(
    db: Session,
    *,
    operation: str,
    text_length: int,
    entity_count: int,
    presidio_count: int,
    spacy_count: int,
    entity_types: list[str],
    processing_time_ms: float,
) -> None:
    """Persist an AI detection event to the ai_detection_logs table."""
    try:
        log = AIDetectionLog(
            operation=operation,
            detection_source="Presidio,spaCy",
            text_length=text_length,
            entity_count=entity_count,
            presidio_count=presidio_count,
            spacy_count=spacy_count,
            entity_types=",".join(sorted(entity_types)) if entity_types else "",
            processing_time_ms=round(processing_time_ms, 3),
        )
        db.add(log)
        db.commit()
    except Exception as exc:
        logger.warning("Failed to write AI detection log: %s", exc)
        db.rollback()


# ── POST /api/detect-ai ───────────────────────────────────────────────────────

@router.post(
    "/detect-ai",
    response_model=AIDetectResponse,
    status_code=status.HTTP_200_OK,
    summary="AI-Powered PHI/PII Detection",
    description=(
        "Run the Microsoft Presidio + spaCy NER detection pipeline over the submitted text. "
        "Results from both engines are merged and deduplicated. "
        "Each entity includes the detection source ('Presidio' or 'spaCy')."
    ),
)
def detect_ai_entities(
    payload: AIDetectRequest,
    db: Session = Depends(get_db),
) -> AIDetectResponse:
    """POST /api/detect-ai — detect PHI/PII using Presidio + spaCy."""
    logger.info(
        "AI detection request: %d chars", len(payload.text)
    )

    t0 = time.perf_counter()

    # ── Run Presidio ──────────────────────────────────────────────────────────
    try:
        presidio_entities, presidio_ms = presidio_service.analyze(payload.text)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Presidio service unavailable: {exc}. "
                "Ensure presidio-analyzer, presidio-anonymizer, and spaCy are installed."
            ),
        ) from exc

    # ── Run spaCy ─────────────────────────────────────────────────────────────
    try:
        spacy_entities, spacy_ms = spacy_service.analyze(payload.text)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"spaCy service unavailable: {exc}.",
        ) from exc

    # ── Merge & deduplicate ───────────────────────────────────────────────────
    merged = EntityMerger.merge(presidio_entities, spacy_entities)

    total_ms = round((time.perf_counter() - t0) * 1000, 3)

    # ── Build response ────────────────────────────────────────────────────────
    entity_types = sorted({e.type for e in merged})

    entities_out: list[AIEntityResult] = [
        AIEntityResult(
            type=e.type,
            value=e.value,
            start=e.start,
            end=e.end,
            confidence=e.confidence,
            source=e.source,
            all_sources=e.all_sources,
        )
        for e in merged
    ]

    # ── Persist log ───────────────────────────────────────────────────────────
    _log_ai_detection(
        db,
        operation="detect-ai",
        text_length=len(payload.text),
        entity_count=len(merged),
        presidio_count=len(presidio_entities),
        spacy_count=len(spacy_entities),
        entity_types=entity_types,
        processing_time_ms=total_ms,
    )

    logger.info(
        "AI detection complete: presidio=%d spacy=%d merged=%d in %.2f ms",
        len(presidio_entities),
        len(spacy_entities),
        len(merged),
        total_ms,
    )

    return AIDetectResponse(
        success=True,
        entities=entities_out,
        entity_count=len(entities_out),
        presidio_count=len(presidio_entities),
        spacy_count=len(spacy_entities),
        processing_time_ms=total_ms,
    )
