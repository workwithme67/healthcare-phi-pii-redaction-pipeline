"""
HealthTech PHI/PII Redaction Pipeline
API Route — Redaction Jobs

Provides CRUD endpoints for managing clinical-note redaction jobs.
PHI detection logic will be integrated here in Day 2+.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.redaction_job import JobStatus
from app.schemas.redaction import (
    RedactionJobCreate,
    RedactionJobDetail,
    RedactionJobListResponse,
    RedactionJobResponse,
)
from app.services.redaction_service import RedactionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["Redaction Jobs"])


def _get_service(db: Session = Depends(get_db)) -> RedactionService:
    return RedactionService(db)


# ── POST /jobs ────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=RedactionJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new redaction job",
    description=(
        "Upload clinical note text. The job is queued for PHI/PII detection "
        "(powered by Microsoft Presidio — Day 2+). Returns a job_id for status polling."
    ),
)
def create_job(
    payload: RedactionJobCreate,
    service: RedactionService = Depends(_get_service),
) -> RedactionJobResponse:
    job = service.create_job(payload)
    logger.info("New redaction job submitted", extra={"job_id": job.job_id})
    return job  # type: ignore[return-value]


# ── GET /jobs ─────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=RedactionJobListResponse,
    summary="List all redaction jobs",
)
def list_jobs(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page."),
    status_filter: Optional[JobStatus] = Query(
        default=None, alias="status", description="Filter by job status."
    ),
    service: RedactionService = Depends(_get_service),
) -> RedactionJobListResponse:
    items, total = service.get_jobs(
        page=page, page_size=page_size, status_filter=status_filter
    )
    return RedactionJobListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,  # type: ignore[arg-type]
    )


# ── GET /jobs/statistics ──────────────────────────────────────────────────────

@router.get(
    "/statistics",
    summary="Get redaction statistics",
    description="Returns aggregated counts and metrics for all redaction jobs.",
)
def get_statistics(
    service: RedactionService = Depends(_get_service),
) -> dict:
    return service.get_statistics()


# ── GET /jobs/{job_id} ────────────────────────────────────────────────────────

@router.get(
    "/{job_id}",
    response_model=RedactionJobDetail,
    summary="Get a specific redaction job",
)
def get_job(
    job_id: str,
    service: RedactionService = Depends(_get_service),
) -> RedactionJobDetail:
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Redaction job '{job_id}' not found.",
        )
    return job  # type: ignore[return-value]
