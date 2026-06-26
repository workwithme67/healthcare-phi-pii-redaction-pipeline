"""
HealthTech PHI/PII Redaction Pipeline
Pydantic Schemas — Uploads

Defines request and response models for the upload endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UploadTextRequest(BaseModel):
    """Request body schema for raw text uploads."""
    note: str = Field(
        ...,
        description="Raw clinical note or transcription text to upload.",
        examples=["Patient John Smith visited today for hypertension follow-up..."],
    )


class UploadTextResponse(BaseModel):
    """Response schema for raw text uploads."""
    success: bool = Field(True, description="Indicates if the upload was successful.")
    message: str = Field(..., description="Details about the upload status.")
    note_id: str = Field(..., description="Unique UUID generated for the uploaded note.")


class UploadFileResponse(BaseModel):
    """Response schema for file uploads (TXT/PDF)."""
    id: str = Field(..., description="Unique UUID generated for the uploaded file.")
    filename: str = Field(..., description="Sanitized name of the uploaded file.")
    uploaded_at: datetime = Field(..., description="Timestamp of when the upload occurred.")
    file_type: str = Field(..., description="Type of the file: 'TXT' or 'PDF'.")
    size_bytes: int = Field(0, description="Size of the note/file in bytes.")
    status: str = Field("Uploaded", description="Processing status.")


class UploadDetailResponse(BaseModel):
    """Detailed response schema for an uploaded note/file."""
    id: str = Field(..., description="Unique UUID of the upload.")
    filename: Optional[str] = Field(None, description="Original filename, if applicable.")
    note_text: Optional[str] = Field(None, description="Raw text content of the note.")
    file_type: str = Field(..., description="File type: 'TEXT', 'TXT', or 'PDF'.")
    size_bytes: int = Field(0, description="Size of the note/file in bytes.")
    created_at: datetime = Field(..., description="Timestamp when the record was created.")
    status: str = Field(..., description="Current processing status.")
