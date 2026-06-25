"""
HealthTech PHI/PII Redaction Pipeline
Utility — Response Helpers

Consistent success / error response builders used across all routes.
"""

from typing import Any, Optional

from fastapi import status
from fastapi.responses import JSONResponse


def success_response(
    data: Any,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    """
    Wrap a payload in a standard success envelope.

    Example
    -------
    {
        "success": true,
        "message": "Job created.",
        "data": { ... }
    }
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data,
        },
    )


def error_response(
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    detail: Optional[str] = None,
) -> JSONResponse:
    """
    Build a standard error response envelope.

    Example
    -------
    {
        "success": false,
        "message": "Validation error.",
        "detail": "field X is required."
    }
    """
    body: dict[str, Any] = {
        "success": False,
        "message": message,
    }
    if detail:
        body["detail"] = detail

    return JSONResponse(status_code=status_code, content=body)
