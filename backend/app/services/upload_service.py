"""
HealthTech PHI/PII Redaction Pipeline
Service — Upload Service

Handles the business logic for raw text uploads and file uploads (TXT/PDF).
Implements validation (size, empty text, character limits), filename sanitization,
directory traversal checks, disk storage, and database persistence.
"""

import os
import re
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.models import Upload
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

# Constants
MAX_TEXT_CHARS = 100000
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
SUPPORTED_EXTENSIONS = {".txt", ".pdf"}


class UploadService:
    """Service class managing clinical note and file uploads."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit_service = AuditService(db)
        # Ensure the uploads directory exists
        self.upload_dir = Path(settings.UPLOAD_DIR).resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitizes a filename to prevent directory traversal and invalid characters.
        
        Returns a clean filename with only safe characters.
        """
        # Get only the base name (no paths)
        base = os.path.basename(filename)
        # Separate name and extension
        name, ext = os.path.splitext(base)
        # Remove non-alphanumeric or underscore/dash from name
        clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
        # Lowercase and sanitize extension
        clean_ext = ext.lower()
        if clean_ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file extension '{clean_ext}'. Only TXT and PDF are allowed.",
            )
        
        # Ensure name isn't empty or starting with dots
        if not clean_name:
            clean_name = f"upload_{uuid.uuid4().hex[:8]}"
            
        return f"{clean_name}{clean_ext}"

    def _verify_safe_path(self, filename: str) -> Path:
        """
        Resolves the file path and verifies that it resides strictly within UPLOAD_DIR
        to prevent directory traversal attacks.
        """
        target_path = (self.upload_dir / filename).resolve()
        # Ensure it is a subpath of upload_dir
        if not target_path.is_relative_to(self.upload_dir):
            logger.error(
                "Directory traversal attempt detected! Filename: %s, Target Path: %s",
                filename,
                target_path,
            )
            raise HTTPException(
                status_code=400,
                detail="Invalid file path. Path traversal is not permitted.",
            )
        return target_path

    def upload_text_note(self, note_text: str, client_ip: str) -> Upload:
        """
        Validates, logs, and stores a raw text clinical note in SQLite.
        """
        # Validate note text
        stripped_text = note_text.strip()
        if not stripped_text:
            logger.warning("Upload rejected: Raw text note is empty.")
            raise HTTPException(status_code=400, detail="Clinical note cannot be empty.")

        if len(stripped_text) > MAX_TEXT_CHARS:
            logger.warning(
                "Upload rejected: Note size (%d chars) exceeds limit (%d chars).",
                len(stripped_text),
                MAX_TEXT_CHARS,
            )
            raise HTTPException(
                status_code=400,
                detail=f"Clinical note exceeds maximum limit of {MAX_TEXT_CHARS} characters.",
            )

        # Create upload record
        note_id = str(uuid.uuid4())
        upload_record = Upload(
            id=note_id,
            filename="Direct Note Upload",
            note_text=stripped_text,
            file_type="TEXT",
            size_bytes=len(stripped_text.encode("utf-8")),
            status="Uploaded",
        )

        try:
            self.db.add(upload_record)
            self.db.commit()
            self.db.refresh(upload_record)

            # Audit logging in SQLite
            self.audit_service.log_action(
                action="UPLOAD",
                actor="anonymous",
                resource_type="clinical_note",
                resource_id=note_id,
                ip_address=client_ip,
                status_code=200,
                detail=f"Successfully uploaded raw clinical note. Size: {len(stripped_text)} chars.",
            )

            logger.info("Clinical note uploaded successfully. ID: %s", note_id)
            return upload_record

        except Exception as exc:
            self.db.rollback()
            logger.exception("Failed to save text note upload to database.")
            # Log failed action
            self.audit_service.log_action(
                action="UPLOAD_FAILED",
                actor="anonymous",
                resource_type="clinical_note",
                ip_address=client_ip,
                status_code=500,
                detail=f"Failed to upload raw text note: {str(exc)}",
            )
            raise HTTPException(
                status_code=500, detail="Failed to save clinical note to the database."
            ) from exc

    async def upload_file_note(self, file: UploadFile, client_ip: str) -> Upload:
        """
        Validates, logs, stores a file (TXT/PDF) on disk, and saves metadata in SQLite.
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected / filename is empty.")

        # Sanitize filename
        sanitized_filename = self._sanitize_filename(file.filename)
        
        # Verify path safety to prevent directory traversal
        target_path = self._verify_safe_path(sanitized_filename)

        # Validate file extension
        ext = Path(sanitized_filename).suffix.lower()
        file_type_mapping = {".txt": "TXT", ".pdf": "PDF"}
        file_type = file_type_mapping.get(ext)
        if not file_type:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{ext}'. Only TXT and PDF are supported.",
            )

        # Read and validate size (maximum 10MB)
        try:
            content = await file.read()
            file_size = len(content)
            if file_size == 0:
                raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            
            if file_size > MAX_FILE_SIZE:
                logger.warning(
                    "File upload rejected: File size (%d bytes) exceeds 10MB limit.", file_size
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"File size exceeds maximum limit of 10MB (file is {file_size / (1024 * 1024):.2f}MB).",
                )
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Error reading uploaded file content.")
            raise HTTPException(status_code=500, detail="Failed to read uploaded file.") from exc

        # For text files, also validate character limit and empty content
        note_text: Optional[str] = None
        if file_type == "TXT":
            try:
                note_text = content.decode("utf-8")
                stripped_text = note_text.strip()
                if not stripped_text:
                    raise HTTPException(status_code=400, detail="Uploaded text file is empty.")
                if len(stripped_text) > MAX_TEXT_CHARS:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Text file content exceeds maximum limit of {MAX_TEXT_CHARS} characters.",
                    )
            except UnicodeDecodeError as exc:
                logger.warning("TXT file decoding failed. Re-trying with utf-8-sig or latin-1.")
                try:
                    note_text = content.decode("latin-1")
                except Exception as latin_exc:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid text encoding. The TXT file must be UTF-8 encoded.",
                    ) from latin_exc

        # Write to disk
        # If a file with the same name exists, generate a unique filename to prevent overwriting
        if target_path.exists():
            stem = Path(sanitized_filename).stem
            sanitized_filename = f"{stem}_{uuid.uuid4().hex[:8]}{ext}"
            target_path = self._verify_safe_path(sanitized_filename)

        try:
            with open(target_path, "wb") as f:
                f.write(content)
            logger.info("Saved file successfully to disk: %s", target_path)
        except Exception as exc:
            logger.exception("Failed to write file to disk.")
            raise HTTPException(
                status_code=500, detail="Failed to store the file on the server disk."
            ) from exc

        # Create database record
        note_id = str(uuid.uuid4())
        upload_record = Upload(
            id=note_id,
            filename=sanitized_filename,
            note_text=note_text,  # text content for TXT, None for PDF (store only, no parsing yet)
            file_type=file_type,
            size_bytes=file_size,
            status="Uploaded",
        )

        try:
            self.db.add(upload_record)
            self.db.commit()
            self.db.refresh(upload_record)

            # Audit logging in SQLite
            self.audit_service.log_action(
                action="UPLOAD",
                actor="anonymous",
                resource_type="clinical_note",
                resource_id=note_id,
                ip_address=client_ip,
                status_code=200,
                detail=f"Successfully uploaded file '{sanitized_filename}' ({file_type}). Size: {file_size} bytes.",
            )

            logger.info(
                "File note uploaded successfully. ID: %s, Filename: %s",
                note_id,
                sanitized_filename,
            )
            return upload_record

        except Exception as exc:
            self.db.rollback()
            # Clean up the file on disk if DB insert fails
            if target_path.exists():
                try:
                    os.remove(target_path)
                except Exception as rm_exc:
                    logger.error("Failed to clean up file %s on DB failure: %s", target_path, rm_exc)
            
            logger.exception("Failed to save file metadata to database.")
            self.audit_service.log_action(
                action="UPLOAD_FAILED",
                actor="anonymous",
                resource_type="clinical_note",
                ip_address=client_ip,
                status_code=500,
                detail=f"Failed to upload file '{sanitized_filename}': {str(exc)}",
            )
            raise HTTPException(
                status_code=500, detail="Failed to save file upload metadata to the database."
            ) from exc

    def list_uploads(self) -> List[Upload]:
        """
        Returns all uploaded notes/files sorted by upload time (newest first).
        """
        return self.db.query(Upload).order_by(Upload.created_at.desc()).all()

    def get_upload_details(self, upload_id: str) -> Upload:
        """
        Retrieves a single upload record by ID.
        """
        record = self.db.query(Upload).filter(Upload.id == upload_id).first()
        if not record:
            raise HTTPException(
                status_code=404, detail=f"Clinical note upload with ID '{upload_id}' not found."
            )
        return record

    def delete_upload(self, upload_id: str, client_ip: str) -> None:
        """
        Deletes a clinical note upload from SQLite and deletes its file from disk (if applicable).
        """
        record = self.db.query(Upload).filter(Upload.id == upload_id).first()
        if not record:
            raise HTTPException(
                status_code=404, detail=f"Clinical note upload with ID '{upload_id}' not found."
            )

        filename = record.filename
        file_type = record.file_type

        # If it's a file saved on disk (not direct text and has a file path), delete it
        if file_type in {"TXT", "PDF"} and filename and filename != "Direct Note Upload":
            try:
                target_path = self._verify_safe_path(filename)
                if target_path.exists():
                    os.remove(target_path)
                    logger.info("Deleted file from disk: %s", target_path)
            except Exception as exc:
                logger.error("Failed to delete file '%s' from disk: %s", filename, exc)
                # We still proceed to delete from DB, but log a warning

        try:
            self.db.delete(record)
            self.db.commit()

            # Audit logging
            self.audit_service.log_action(
                action="DELETE",
                actor="anonymous",
                resource_type="clinical_note",
                resource_id=upload_id,
                ip_address=client_ip,
                status_code=200,
                detail=f"Deleted clinical note upload '{filename or upload_id}'.",
            )
            logger.info("Deleted upload record: %s", upload_id)

        except Exception as exc:
            self.db.rollback()
            logger.exception("Failed to delete upload record from database: %s", upload_id)
            raise HTTPException(
                status_code=500, detail="Failed to delete clinical note from the database."
            ) from exc
