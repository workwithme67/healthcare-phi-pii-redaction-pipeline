"""
HealthTech PHI/PII Redaction Pipeline
API Router

Aggregates all route modules under the /api/v1 prefix.
"""

from fastapi import APIRouter

from app.api.routes import audit, health, redaction

# Root API router — all routes live under /api/v1
api_router = APIRouter(prefix="/api/v1")

# Health check mounted at /api/v1/app/health
api_router.include_router(health.router, prefix="/app")

# Redaction jobs → /api/v1/jobs
api_router.include_router(redaction.router)

# Audit logs → /api/v1/audit
api_router.include_router(audit.router)
