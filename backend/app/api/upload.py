"""
HealthTech PHI/PII Redaction Pipeline
API Routes — Uploads

Defines endpoints for raw clinical note uploads and file uploads (TXT/PDF),
listing uploads, retrieving upload details, and deleting uploads.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.upload import (
    UploadDetailResponse,
    UploadFileResponse,
    UploadTextRequest,
    UploadTextResponse,
)
from app.services.upload_service import UploadService

logger = logging.getLogger(__name__)

# Prefixed with /api (registered on the app directly)
router = APIRouter(prefix="/api", tags=["Clinical Uploads"])


@router.post(
    "/upload-text",
    response_model=UploadTextResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Raw Clinical Note",
    description="Accepts raw clinical transcription or note text, validates it, and stores it in SQLite.",
)
def upload_text(
    request: Request,
    payload: UploadTextRequest,
    db: Session = Depends(get_db),
) -> UploadTextResponse:
    """
    Endpoint to upload raw clinical text notes.
    """
    client_ip = request.client.host if request.client else "unknown"
    service = UploadService(db)
    
    # Process text upload through the service
    record = service.upload_text_note(payload.note, client_ip)
    
    return UploadTextResponse(
        success=True,
        message="Clinical note uploaded successfully",
        note_id=record.id,
    )


@router.post(
    "/upload-file",
    response_model=UploadFileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Clinical Note File",
    description="Accepts TXT or PDF file upload, validates file type and size (max 10MB), and stores it.",
)
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="The clinical note file (TXT or PDF)."),
    db: Session = Depends(get_db),
) -> UploadFileResponse:
    """
    Endpoint to upload clinical note files (TXT/PDF).
    """
    client_ip = request.client.host if request.client else "unknown"
    service = UploadService(db)
    
    # Process file upload through the service
    record = await service.upload_file_note(file, client_ip)
    
    return UploadFileResponse(
        id=record.id,
        filename=record.filename,
        uploaded_at=record.created_at,
        file_type=record.file_type,
        size_bytes=record.size_bytes,
        status=record.status,
    )


@router.get(
    "/uploads",
    response_model=List[UploadFileResponse],
    summary="List Uploaded Notes",
    description="Returns a list of all uploaded clinical notes and files.",
)
def list_uploads(db: Session = Depends(get_db)) -> List[UploadFileResponse]:
    """
    Endpoint to list all uploaded clinical notes and files.
    """
    service = UploadService(db)
    records = service.list_uploads()
    
    return [
        UploadFileResponse(
            id=record.id,
            filename=record.filename or "Direct Note Upload",
            uploaded_at=record.created_at,
            file_type=record.file_type,
            size_bytes=record.size_bytes,
            status=record.status,
        )
        for record in records
    ]


@router.get(
    "/uploads/{id}",
    response_model=UploadDetailResponse,
    summary="Get Uploaded Note Details",
    description="Retrieves the metadata and content of a specific uploaded clinical note by ID.",
)
def get_upload(
    id: str,
    db: Session = Depends(get_db),
) -> UploadDetailResponse:
    """
    Endpoint to retrieve specific upload details by ID.
    """
    service = UploadService(db)
    record = service.get_upload_details(id)
    
    return UploadDetailResponse(
        id=record.id,
        filename=record.filename,
        note_text=record.note_text,
        file_type=record.file_type,
        size_bytes=record.size_bytes,
        created_at=record.created_at,
        status=record.status,
    )


@router.delete(
    "/uploads/{id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Uploaded Note",
    description="Deletes a specific uploaded clinical note and its associated file on disk.",
)
def delete_upload(
    request: Request,
    id: str,
    db: Session = Depends(get_db),
):
    """
    Endpoint to delete a specific clinical note upload.
    """
    client_ip = request.client.host if request.client else "unknown"
    service = UploadService(db)
    service.delete_upload(id, client_ip)
    
    return {
        "success": True,
        "message": f"Clinical note with ID '{id}' deleted successfully.",
    }
