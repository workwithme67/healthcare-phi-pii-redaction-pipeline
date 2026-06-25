"""
HealthTech PHI/PII Redaction Pipeline
API Route — Health Check

Endpoint: GET /app/health
Returns the operational status of the application and its dependencies.
"""

import time
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.settings import Settings, get_settings
from app.database.database import check_db_connection, get_db
from app.schemas.health import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Record application start time for uptime calculation
_START_TIME: float = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description=(
        "Returns the operational status of the API and its dependencies. "
        "Use this endpoint for liveness and readiness probes in Kubernetes/Docker."
    ),
    tags=["Health"],
)
def health_check(
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> HealthResponse:
    """
    Perform a health check and return service status.

    Checks
    ------
    - Application is running
    - Database is reachable

    Returns
    -------
    HealthResponse with status information.
    """
    db_ok = check_db_connection()
    uptime = round(time.time() - _START_TIME, 2)

    logger.debug("Health check requested", extra={"db_ok": db_ok, "uptime": uptime})

    return HealthResponse(
        status="running",
        project=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        database="connected" if db_ok else "unreachable",
        uptime_seconds=uptime,
    )
