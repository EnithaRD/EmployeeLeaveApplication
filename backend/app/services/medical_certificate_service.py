import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


def _storage_dir() -> Path:
    storage_dir = Path(settings.MEDICAL_CERTIFICATE_STORAGE_DIR)
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


def resolve_certificate_path(stored_filename: str) -> Path:
    return _storage_dir() / stored_filename


def save_certificate(file: UploadFile) -> dict:
    content_type = (file.content_type or "").lower()
    extension = ALLOWED_CONTENT_TYPES.get(content_type)
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Allowed types: PDF, JPG, PNG.",
        )

    max_size = settings.MEDICAL_CERTIFICATE_MAX_SIZE_BYTES
    contents = file.file.read(max_size + 1)

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded medical certificate is empty.",
        )

    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Medical certificate exceeds the maximum allowed size of {max_size // (1024 * 1024)}MB.",
        )

    stored_filename = f"{uuid.uuid4().hex}{extension}"
    destination = _storage_dir() / stored_filename
    with open(destination, "wb") as out_file:
        out_file.write(contents)

    original_filename = os.path.basename(file.filename or "medical_certificate")

    return {
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "content_type": content_type,
        "file_size": len(contents),
    }
