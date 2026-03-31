"""
VyapaarBandhu — S3-Compatible Storage Client
Works with MinIO (dev) and Cloudflare R2 (prod).
Presigned URLs only — never public bucket access. Max 15-minute expiry.
"""

import asyncio
import io
import uuid
from datetime import datetime, timezone

import boto3
import structlog
from botocore.config import Config as BotoConfig
from PIL import Image

from app.config import settings

logger = structlog.get_logger()

# Lazy-init client
_s3_client = None


def _get_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
            config=BotoConfig(signature_version="s3v4"),
        )
    return _s3_client


async def upload_invoice_image(
    image_bytes: bytes,
    client_id: uuid.UUID,
    filename_hint: str = "invoice",
) -> str:
    """
    Upload invoice image to S3. Returns the S3 key.
    Key format: invoices/{client_id}/{timestamp}_{uuid}.{ext}
    """
    ext = _detect_extension(image_bytes)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    unique = uuid.uuid4().hex[:8]
    key = f"invoices/{client_id}/{timestamp}_{unique}.{ext}"

    client = _get_client()
    await asyncio.to_thread(
        client.put_object,
        Bucket=settings.S3_BUCKET_INVOICES,
        Key=key,
        Body=image_bytes,
        ContentType=f"image/{ext}",
        ServerSideEncryption="AES256",
    )

    logger.info("s3.upload", bucket=settings.S3_BUCKET_INVOICES, key=key, size=len(image_bytes))
    return key


async def upload_export(
    data: bytes,
    client_id: uuid.UUID,
    filename: str,
    content_type: str,
) -> str:
    """Upload export file (PDF, JSON) to S3. Returns the S3 key."""
    key = f"exports/{client_id}/{filename}"

    client = _get_client()
    await asyncio.to_thread(
        client.put_object,
        Bucket=settings.S3_BUCKET_EXPORTS,
        Key=key,
        Body=data,
        ContentType=content_type,
        ServerSideEncryption="AES256",
    )

    logger.info("s3.upload.export", bucket=settings.S3_BUCKET_EXPORTS, key=key)
    return key


async def download(bucket: str, key: str) -> bytes:
    """Download a file from S3. Returns bytes."""
    client = _get_client()
    response = await asyncio.to_thread(client.get_object, Bucket=bucket, Key=key)
    return response["Body"].read()


def generate_presigned_url(bucket: str, key: str, expiry: int | None = None) -> str:
    """
    Generate a presigned download URL.
    Max expiry: 15 minutes (settings.S3_PRESIGNED_URL_EXPIRY).
    NEVER return public URLs.
    """
    if expiry is None:
        expiry = settings.S3_PRESIGNED_URL_EXPIRY

    # Enforce max 15 minutes
    expiry = min(expiry, 900)

    client = _get_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expiry,
    )


async def upload_ca_logo(
    image_bytes: bytes,
    ca_id: uuid.UUID,
) -> tuple[str, str]:
    """
    Upload CA logo + generate 200x200 thumbnail.
    Returns (original_key, thumbnail_key).
    """
    ext = _detect_extension(image_bytes)
    base_key = f"logos/{ca_id}/logo.{ext}"
    thumb_key = f"logos/{ca_id}/logo_thumb.{ext}"

    # Upload original (max 2MB enforced at API layer)
    client = _get_client()
    await asyncio.to_thread(
        client.put_object,
        Bucket=settings.S3_BUCKET_EXPORTS,
        Key=base_key,
        Body=image_bytes,
        ContentType=f"image/{ext}",
    )

    # Generate 200x200 thumbnail
    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail((200, 200), Image.LANCZOS)
    thumb_buffer = io.BytesIO()
    img.save(thumb_buffer, format=ext.upper() if ext != "jpg" else "JPEG")
    thumb_bytes = thumb_buffer.getvalue()

    await asyncio.to_thread(
        client.put_object,
        Bucket=settings.S3_BUCKET_EXPORTS,
        Key=thumb_key,
        Body=thumb_bytes,
        ContentType=f"image/{ext}",
    )

    logger.info("s3.upload.logo", ca_id=str(ca_id), original=base_key, thumbnail=thumb_key)
    return base_key, thumb_key


def _detect_extension(image_bytes: bytes) -> str:
    """Detect image format from bytes (not filename — prevents MIME spoofing)."""
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if image_bytes[:2] == b"\xff\xd8":
        return "jpg"
    if image_bytes[:4] == b"GIF8":
        return "gif"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "webp"
    # SVG check (text-based)
    try:
        header = image_bytes[:200].decode("utf-8", errors="ignore").lower()
        if "<svg" in header:
            return "svg"
    except Exception:
        pass
    # Default to jpg
    return "jpg"
