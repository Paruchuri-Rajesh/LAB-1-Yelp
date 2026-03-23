import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from app.config import settings

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


async def save_profile_picture(file: UploadFile) -> str:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file.content_type}' not allowed. Use JPEG, PNG, or WebP.",
        )
    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
        )
    ext = "jpg"
    if file.filename and "." in file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    dest = Path(settings.UPLOAD_DIR) / "profile_pics" / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(contents)
    return f"profile_pics/{filename}"


async def save_upload(file: UploadFile, subdir: str) -> str:
    """Save an uploaded file under UPLOAD_DIR/<subdir>/ and return the relative path."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file.content_type}' not allowed. Use JPEG, PNG, or WebP.",
        )
    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
        )
    ext = "jpg"
    if file.filename and "." in file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    dest = Path(settings.UPLOAD_DIR) / subdir / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(contents)
    return f"{subdir}/{filename}"


def delete_file(relative_path: str | None):
    if relative_path:
        full = Path(settings.UPLOAD_DIR) / relative_path
        full.unlink(missing_ok=True)
