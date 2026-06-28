"""
HealthTech PHI/PII Redaction Pipeline
API Router

Aggregates all route modules under the /api/v1 prefix.
Also mounts the Day 3 detection engine under /api directly.
Day 4 adds AI detection (/api/detect-ai) and comparison (/api/compare).
"""

from fastapi import APIRouter

from app.api.routes import audit, detect, health, redaction
from app.api.routes import detect_ai, compare as compare_route

# Root API router — all routes live under /api/v1
api_router = APIRouter(prefix="/api/v1")

# Health check mounted at /api/v1/app/health
api_router.include_router(health.router, prefix="/app")

# Redaction jobs → /api/v1/jobs
api_router.include_router(redaction.router)

# Audit logs → /api/v1/audit
api_router.include_router(audit.router)

# ── Day 3: Detection Engine — mounted at /api (no v1 prefix per spec) ────────
detect_router = APIRouter(prefix="/api")
detect_router.include_router(detect.router)

# ── Day 4: AI Detection — mounted at /api (no v1 prefix per spec) ────────────
detect_router.include_router(detect_ai.router)
detect_router.include_router(compare_route.router)
