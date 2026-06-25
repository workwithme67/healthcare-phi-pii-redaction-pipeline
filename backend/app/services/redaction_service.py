"""
HealthTech PHI/PII Redaction Pipeline
Service — Redaction Job

Orchestrates the lifecycle of a redaction job.
PHI detection logic will be wired here in Day 2+ via Microsoft Presidio / spaCy.
"""

import logging
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.redaction_job import JobStatus, RedactionJob
from app.schemas.redaction import RedactionJobCreate

logger = logging.getLogger(__name__)


class RedactionService:
    """Service class that manages RedactionJob lifecycle."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Create ─────────────────────────────────────────────────────────────────

    def create_job(self, payload: RedactionJobCreate) -> RedactionJob:
        """
        Persist a new redaction job in PENDING state.

        The actual PHI redaction will be triggered asynchronously in Day 2+.
        For now the job is stored and immediately marked as PENDING.
        """
        job = RedactionJob(
            job_id=str(uuid.uuid4()),
            filename=payload.filename,
            original_text=payload.text,
            status=JobStatus.PENDING,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        logger.info("Redaction job created", extra={"job_id": job.job_id})
        return job

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_job(self, job_id: str) -> Optional[RedactionJob]:
        """Retrieve a job by its UUID. Returns None if not found."""
        return (
            self.db.query(RedactionJob)
            .filter(RedactionJob.job_id == job_id)
            .first()
        )

    def get_jobs(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[JobStatus] = None,
    ) -> tuple[list[RedactionJob], int]:
        """
        Return a paginated list of redaction jobs, newest first.

        Returns
        -------
        (items, total_count)
        """
        query = self.db.query(RedactionJob).order_by(RedactionJob.created_at.desc())

        if status_filter:
            query = query.filter(RedactionJob.status == status_filter)

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_statistics(self) -> dict:
        """
        Return aggregated statistics for the dashboard.

        Returns
        -------
        Dictionary with counts by status and totals.
        """
        total = self.db.query(RedactionJob).count()
        by_status: dict[str, int] = {}

        for status in JobStatus:
            count = (
                self.db.query(RedactionJob)
                .filter(RedactionJob.status == status)
                .count()
            )
            by_status[status.value] = count

        return {
            "total_jobs": total,
            "by_status": by_status,
        }
