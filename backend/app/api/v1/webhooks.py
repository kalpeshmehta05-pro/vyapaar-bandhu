"""
VyapaarBandhu — WhatsApp Webhook Handler
GET: Meta verification challenge
POST: Inbound messages with HMAC-SHA256 signature verification
"""

import hashlib
import hmac

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_async_session
from app.services.whatsapp.message_router import route_message

logger = structlog.get_logger()
router = APIRouter()


def verify_meta_signature(payload: bytes, signature_header: str, app_secret: str) -> bool:
    """
    Verify WhatsApp webhook HMAC-SHA256 signature.
    Constant-time comparison to prevent timing attacks.
    Reference: Meta WhatsApp Cloud API — Webhooks security
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected_sig = hmac.new(
        app_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    received_sig = signature_header[7:]  # strip "sha256="
    return hmac.compare_digest(expected_sig, received_sig)


# ── GET: Webhook Verification ─────────────────────────────────────────

@router.get("/whatsapp")
async def verify_webhook(request: Request):
    """
    Meta webhook verification challenge.
    Called once when registering the webhook URL.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.WA_VERIFY_TOKEN:
        logger.info("whatsapp.webhook.verified")
        return Response(content=challenge, media_type="text/plain")

    raise HTTPException(status_code=403, detail="Verification failed")


# ── POST: Inbound Messages ───────────────────────────────────────────

@router.post("/whatsapp")
async def receive_webhook(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Handle inbound WhatsApp messages.
    Verifies HMAC-SHA256 signature before processing.
    """
    body = await request.body()

    # ── Signature verification ────────────────────────────────────
    if settings.WA_APP_SECRET:
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not verify_meta_signature(body, signature, settings.WA_APP_SECRET):
            logger.warning("whatsapp.webhook.invalid_signature")
            raise HTTPException(status_code=403, detail="Invalid webhook signature")

    # ── Parse payload ─────────────────────────────────────────────
    try:
        data = await request.json()
    except Exception:
        return {"status": "ok"}  # Malformed — acknowledge to prevent retries

    # Extract messages from the webhook payload
    entries = data.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])

            for message in messages:
                phone = message.get("from", "")
                if phone:
                    try:
                        await route_message(phone, message, db)
                    except Exception as e:
                        logger.error(
                            "whatsapp.webhook.processing_error",
                            phone_masked=phone[:5] + "XXXXX",
                            error=str(e),
                        )

    return {"status": "ok"}
