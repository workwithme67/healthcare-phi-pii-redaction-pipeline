"""
HealthTech PHI/PII Redaction Pipeline
Middleware — Request Logging

Logs every incoming request and outgoing response with timing information.
Attaches a unique X-Request-ID header to each request for distributed tracing.
"""

import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that:
    1. Generates a unique request ID (UUID4) if not already present.
    2. Logs request method, path, and client IP on receipt.
    3. Times the request processing.
    4. Logs the response status code and elapsed time on completion.
    5. Injects X-Request-ID into the response headers.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Generate / retrieve request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        start_time = time.perf_counter()

        logger.info(
            "→ %s %s",
            request.method,
            request.url.path,
            extra={
                "request_id": request_id,
                "client_ip": request.client.host if request.client else "unknown",
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
            },
        )

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            logger.exception(
                "Unhandled exception during request %s %s",
                request.method,
                request.url.path,
                extra={"request_id": request_id},
            )
            raise exc

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.info(
            "← %s %s | %d | %.2f ms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "elapsed_ms": elapsed_ms,
            },
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Processing-Time-Ms"] = str(elapsed_ms)

        return response
