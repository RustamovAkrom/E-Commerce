"""MinIO / S3-compatible object storage wrapper.

Thin, dependency-light wrapper around the MinIO client with upload validation
(MIME, extension, size) baked in to satisfy the file-upload security rules.
"""

from __future__ import annotations

import io
import os
import uuid
from functools import lru_cache

from minio import Minio

from src.config import settings
from src.core.exceptions import ValidationError

_EXT_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


@lru_cache
def get_minio_client() -> Minio:
    """Return a cached MinIO client."""
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


def ensure_bucket() -> None:
    """Create the configured bucket if it does not yet exist."""
    client = get_minio_client()
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)


def _safe_object_name(original_filename: str, content_type: str) -> str:
    """Generate a collision-free, traversal-safe object name."""
    ext = _EXT_BY_MIME.get(content_type, "")
    if not ext:
        # Fall back to the original extension, stripped of any path component.
        _, raw_ext = os.path.splitext(os.path.basename(original_filename))
        ext = raw_ext.lower()
    return f"{uuid.uuid4().hex}{ext}"


def validate_upload(content: bytes, content_type: str) -> None:
    """Validate size and MIME type before storing an upload."""
    if content_type not in settings.ALLOWED_UPLOAD_MIME:
        raise ValidationError(
            f"Unsupported file type '{content_type}'.",
            details={"allowed": settings.ALLOWED_UPLOAD_MIME},
        )
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise ValidationError(
            "File exceeds maximum allowed size.",
            details={"max_bytes": settings.MAX_UPLOAD_SIZE_BYTES},
        )


def upload_file(content: bytes, original_filename: str, content_type: str) -> str:
    """Validate and store a file, returning its public object key."""
    validate_upload(content, content_type)
    ensure_bucket()
    object_name = _safe_object_name(original_filename, content_type)
    client = get_minio_client()
    client.put_object(
        settings.MINIO_BUCKET,
        object_name,
        io.BytesIO(content),
        length=len(content),
        content_type=content_type,
    )
    return object_name


def public_url(object_name: str) -> str:
    """Build a public URL for a stored object."""
    scheme = "https" if settings.MINIO_SECURE else "http"
    return f"{scheme}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{object_name}"


def delete_file(object_name: str) -> None:
    get_minio_client().remove_object(settings.MINIO_BUCKET, object_name)
