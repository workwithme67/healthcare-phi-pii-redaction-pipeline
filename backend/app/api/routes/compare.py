"""
HealthTech PHI/PII Redaction Pipeline
API Route — Detection Engine Comparison (Day 4)

Endpoint
--------
POST /api/compare
    Run all three detection engines (Regex, Presidio, spaCy) on the same
    text and return comparative statistics: entity counts, processing time,
    and the final merged entity list.

Response example
----------------
{
  "regex": 12,
  "presidio": 17,
  "spacy": 15,
  "merged": 20,
  "duplicates_removed": 24,
  "processing_time": "48ms",
  "processing_time_ms": 48.3,
  "engine_stats": [...],
  "merged_entities": [...]
}
"""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.ai_detection_log import AIDetectionLog
from app.schemas.detection import (
    AIEntityResult,
    CompareRequest,
    CompareResponse,
    EngineStats,
)
from app.services.entity_merger import EntityMerger
from app.services.presidio_service import presidio_service
from app.services.regex_detector import detector as regex_detector
from app.services.spacy_service import spacy_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Detection Comparison"])


# ── POST /api/compare ─────────────────────────────────────────────────────────

@router.post(
    "/compare",
    response_model=CompareResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare Detection Engines",
    description=(
        "Run all three detection engines (Regex, Presidio, spaCy) independently "
        "on the same text and return comparative statistics including entity counts, "
        "per-engine latency, and the final merged entity list."
    ),
)
def compare_detection_engines(
    payload: CompareRequest,
    db: Session = Depends(get_db),
) -> CompareResponse:
    """POST /api/compare — run all engines and return comparative stats."""
    logger.info(
        "Compare detection request: %d chars", len(payload.text)
    )

    t0 = time.perf_counter()
    text = payload.text

    # ── Regex Engine ──────────────────────────────────────────────────────────
    try:
        regex_result = regex_detector.detect(text)
        regex_entities = regex_result.entities
        regex_ms = regex_result.processing_time_ms
    except Exception as exc:
        logger.error("Regex engine failed: %s", exc)
        regex_entities = []
        regex_ms = 0.0

    # ── Presidio Engine ───────────────────────────────────────────────────────
    try:
        presidio_entities, presidio_ms = presidio_service.analyze(text)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Presidio service unavailable: {exc}. "
                "Ensure presidio-analyzer, presidio-anonymizer, and spaCy are installed."
            ),
        ) from exc
    except Exception as exc:
        logger.error("Presidio engine failed: %s", exc)
        presidio_entities = []
        presidio_ms = 0.0

    # ── spaCy Engine ──────────────────────────────────────────────────────────
    try:
        spacy_entities, spacy_ms = spacy_service.analyze(text)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"spaCy service unavailable: {exc}.",
        ) from exc
    except Exception as exc:
        logger.error("spaCy engine failed: %s", exc)
        spacy_entities = []
        spacy_ms = 0.0

    # ── Merge all three ───────────────────────────────────────────────────────
    merged = EntityMerger.merge(
        presidio_entities,
        spacy_entities,
        regex_entities=regex_entities,
    )

    total_ms = round((time.perf_counter() - t0) * 1000, 3)

    # ── Duplicate count ───────────────────────────────────────────────────────
    total_raw = len(regex_entities) + len(presidio_entities) + len(spacy_entities)
    duplicates_removed = max(0, total_raw - len(merged))

    # ── Engine stats ──────────────────────────────────────────────────────────
    engine_stats = [
        EngineStats(
            engine="Regex",
            entity_count=len(regex_entities),
            processing_time_ms=round(regex_ms, 3),
            entity_types=sorted({e.type for e in regex_entities}),
        ),
        EngineStats(
            engine="Presidio",
            entity_count=len(presidio_entities),
            processing_time_ms=round(presidio_ms, 3),
            entity_types=sorted({e.type for e in presidio_entities}),
        ),
        EngineStats(
            engine="spaCy",
            entity_count=len(spacy_entities),
            processing_time_ms=round(spacy_ms, 3),
            entity_types=sorted({e.type for e in spacy_entities}),
        ),
    ]

    # ── Build merged entity response ──────────────────────────────────────────
    merged_entities_out: list[AIEntityResult] = [
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

    # ── Human-readable time ───────────────────────────────────────────────────
    if total_ms < 1:
        time_str = "<1ms"
    elif total_ms < 1000:
        time_str = f"{round(total_ms)}ms"
    else:
        time_str = f"{total_ms / 1000:.2f}s"

    # ── Persist log ───────────────────────────────────────────────────────────
    try:
        log = AIDetectionLog(
            operation="compare",
            detection_source="Presidio,spaCy,Regex",
            text_length=len(text),
            entity_count=len(merged),
            presidio_count=len(presidio_entities),
            spacy_count=len(spacy_entities),
            regex_count=len(regex_entities),
            entity_types=",".join(sorted({e.type for e in merged})),
            processing_time_ms=total_ms,
        )
        db.add(log)
        db.commit()
    except Exception as exc:
        logger.warning("Failed to write compare log: %s", exc)
        db.rollback()

    logger.info(
        "Compare complete: regex=%d presidio=%d spacy=%d merged=%d dupes=%d in %.2f ms",
        len(regex_entities),
        len(presidio_entities),
        len(spacy_entities),
        len(merged),
        duplicates_removed,
        total_ms,
    )

    return CompareResponse(
        success=True,
        regex=len(regex_entities),
        presidio=len(presidio_entities),
        spacy=len(spacy_entities),
        merged=len(merged),
        duplicates_removed=duplicates_removed,
        processing_time=time_str,
        processing_time_ms=total_ms,
        engine_stats=engine_stats,
        merged_entities=merged_entities_out,
    )
