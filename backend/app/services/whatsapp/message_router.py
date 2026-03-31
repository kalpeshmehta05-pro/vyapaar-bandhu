"""
VyapaarBandhu — WhatsApp Message Router
Routes inbound messages to handlers. Redis-backed state machine.
Idempotency via whatsapp_message_id. Consent check before processing.
"""

import json
import structlog
from datetime import datetime, timezone

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.client import Client
from app.models.invoice import Invoice
from app.services.whatsapp import client as wa_client
from app.services.whatsapp.message_templates import MESSAGES
from app.utils.phone import normalize_phone

logger = structlog.get_logger()

# ── Redis session management ──────────────────────────────────────────

_redis: aioredis.Redis | None = None


async def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def get_session(phone: str) -> dict | None:
    """Get conversation session from Redis."""
    r = await _get_redis()
    data = await r.get(f"wa_session:{phone}")
    return json.loads(data) if data else None


async def set_session(phone: str, session: dict) -> None:
    """Set conversation session in Redis with TTL."""
    r = await _get_redis()
    session["last_updated"] = datetime.now(timezone.utc).isoformat()
    await r.set(
        f"wa_session:{phone}",
        json.dumps(session),
        ex=settings.REDIS_SESSION_TTL,
    )


async def clear_session(phone: str) -> None:
    """Clear conversation session."""
    r = await _get_redis()
    await r.delete(f"wa_session:{phone}")


# ── Message Router ────────────────────────────────────────────────────

async def route_message(
    phone: str,
    message: dict,
    db: AsyncSession,
) -> None:
    """
    Route an inbound WhatsApp message to the appropriate handler.
    Enforces idempotency and consent checks.
    """
    message_id = message.get("id", "")
    message_type = message.get("type", "")
    normalized_phone = normalize_phone(phone)

    # ── Idempotency: skip if already processed ────────────────────
    if message_id:
        existing = await db.execute(
            select(Invoice).where(Invoice.whatsapp_message_id == message_id)
        )
        if existing.scalar_one_or_none():
            logger.debug("whatsapp.duplicate_message", message_id=message_id)
            return

    # ── Client lookup ─────────────────────────────────────────────
    result = await db.execute(
        select(Client).where(Client.whatsapp_phone == normalized_phone)
    )
    client = result.scalar_one_or_none()

    if not client:
        await wa_client.send_text(normalized_phone, MESSAGES["not_registered"])
        return

    if not client.is_active:
        return  # Silently ignore deactivated clients

    # ── Consent check ─────────────────────────────────────────────
    if client.consent_given_at is None:
        # Client hasn't given consent yet
        if message_type == "text":
            text = message.get("text", {}).get("body", "").strip().lower()
            if text in ("haan", "yes", "agree", "ha"):
                from app.utils.consent import record_consent
                await record_consent(db, client.id)
                await db.commit()
                await wa_client.send_text(normalized_phone, MESSAGES["consent_given"])
                return
            elif text in ("nahi", "no", "disagree"):
                await wa_client.send_text(normalized_phone, MESSAGES["consent_denied"])
                return

        # For any other message from unconsented client, re-send consent request
        from app.models.ca_account import CAAccount
        ca_result = await db.execute(select(CAAccount).where(CAAccount.id == client.ca_id))
        ca = ca_result.scalar_one_or_none()
        ca_name = ca.firm_name if ca else "your CA"
        await wa_client.send_text(
            normalized_phone,
            MESSAGES["consent_request"].format(ca_firm_name=ca_name),
        )
        return

    # ── Consent withdrawn check ───────────────────────────────────
    if client.consent_withdrawn_at is not None:
        return  # Silently ignore withdrawn clients

    # ── Mark as read ──────────────────────────────────────────────
    await wa_client.mark_as_read(message_id)

    # ── Route by message type ─────────────────────────────────────
    session = await get_session(normalized_phone) or {"state": "IDLE"}

    if message_type in ("image", "document"):
        await _handle_image(client, message, session, normalized_phone, db)

    elif message_type == "text":
        text = message.get("text", {}).get("body", "").strip().lower()
        await _handle_text(client, text, session, normalized_phone, message, db)

    else:
        await wa_client.send_text(normalized_phone, MESSAGES["unrecognised_command"])


# ── Image Handler ─────────────────────────────────────────────────────

async def _handle_image(
    client: Client,
    message: dict,
    session: dict,
    phone: str,
    db: AsyncSession,
) -> None:
    """Handle incoming invoice image — triggers Celery OCR task."""
    from app.tasks.ocr_task import process_invoice_ocr

    # Get media ID
    media = None
    if message.get("type") == "image":
        media = message.get("image", {})
    elif message.get("type") == "document":
        media = message.get("document", {})

    if not media or not media.get("id"):
        await wa_client.send_text(phone, MESSAGES["ocr_failed"])
        return

    media_id = media["id"]
    message_id = message.get("id", "")

    # Get current month invoice count
    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count(Invoice.id)).where(
            Invoice.client_id == client.id,
        )
    )
    invoice_count = count_result.scalar() or 0

    # Send acknowledgement
    await wa_client.send_text(
        phone,
        MESSAGES["received"].format(invoice_count=invoice_count + 1),
    )

    # Update session state
    await set_session(phone, {
        "state": "PROCESSING_IMAGE",
        "media_id": media_id,
        "message_id": message_id,
    })

    # Dispatch Celery OCR task
    process_invoice_ocr.delay(
        client_id=str(client.id),
        ca_id=str(client.ca_id),
        media_id=media_id,
        whatsapp_message_id=message_id,
        phone=phone,
    )


# ── Text Handler ──────────────────────────────────────────────────────

CONFIRM_WORDS = {"haan", "yes", "ok", "ha", "theek", "sahi"}
CANCEL_WORDS = {"cancel", "nahi", "no"}
EDIT_PREFIXES = ["edit date", "edit total", "edit gstin", "edit invoice_no",
                 "edit seller", "edit cgst", "edit sgst", "edit igst"]


async def _handle_text(
    client: Client,
    text: str,
    session: dict,
    phone: str,
    message: dict,
    db: AsyncSession,
) -> None:
    """Handle text commands based on conversation state."""
    state = session.get("state", "IDLE")

    # ── State: AWAITING_CONFIRMATION ──────────────────────────────
    if state == "AWAITING_CONFIRMATION":
        if text in CONFIRM_WORDS:
            await _handle_confirmation(client, session, phone, db)
            return
        elif text in CANCEL_WORDS:
            await clear_session(phone)
            await wa_client.send_text(phone, MESSAGES["cancelled"])
            return
        elif any(text.startswith(prefix) for prefix in EDIT_PREFIXES):
            # Parse edit command
            parts = text.split(" ", 2)
            if len(parts) >= 3:
                field = parts[1]
                value = parts[2]
                await _handle_edit(client, session, phone, field, value, db)
            else:
                await wa_client.send_text(
                    phone,
                    MESSAGES["edit_prompt"].format(field_name=parts[1] if len(parts) > 1 else "field"),
                )
            return

    # ── State: IDLE — handle commands ─────────────────────────────
    if text == "summary":
        await _handle_summary(client, phone, db)
    elif text == "help":
        await wa_client.send_text(phone, MESSAGES["help"])
    elif text in ("withdraw consent", "delete mera data"):
        from app.utils.consent import withdraw_consent
        result = await withdraw_consent(db, client.id)
        await db.commit()
        await wa_client.send_text(
            phone,
            MESSAGES["consent_withdrawn"].format(retention_years=7),
        )
    else:
        await wa_client.send_text(phone, MESSAGES["unrecognised_command"])


async def _handle_confirmation(
    client: Client,
    session: dict,
    phone: str,
    db: AsyncSession,
) -> None:
    """Handle user confirming extracted invoice data."""
    invoice_id = session.get("pending_invoice_id")
    if not invoice_id:
        await wa_client.send_text(phone, MESSAGES["unrecognised_command"])
        return

    import uuid
    result = await db.execute(
        select(Invoice).where(Invoice.id == uuid.UUID(invoice_id))
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        await clear_session(phone)
        return

    # Update status
    invoice.status = "pending_ca_review"
    invoice.client_confirmed_at = datetime.now(timezone.utc)

    from app.models.ca_account import CAAccount
    ca_result = await db.execute(select(CAAccount).where(CAAccount.id == client.ca_id))
    ca = ca_result.scalar_one_or_none()
    ca_name = ca.firm_name if ca else "your CA"

    from app.services.compliance.deadline_calculator import get_gstr3b_deadline
    tax_period = datetime.now(timezone.utc).strftime("%Y-%m")
    deadline = get_gstr3b_deadline(tax_period)

    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count(Invoice.id)).where(Invoice.client_id == client.id)
    )
    invoice_count = count_result.scalar() or 0

    draft_itc = (invoice.cgst_amount or 0) + (invoice.sgst_amount or 0) + (invoice.igst_amount or 0)

    await db.commit()
    await clear_session(phone)

    await wa_client.send_text(
        phone,
        MESSAGES["saved"].format(
            ca_firm_name=ca_name,
            draft_itc_total=f"{draft_itc:,.2f}",
            invoice_count=invoice_count,
            gstr3b_deadline=deadline.strftime("%d %b %Y"),
        ),
    )


async def _handle_edit(
    client: Client,
    session: dict,
    phone: str,
    field: str,
    value: str,
    db: AsyncSession,
) -> None:
    """Handle user editing an extracted field."""
    # Simplified — store edit in session for now
    edits = session.get("edits", {})
    edits[field] = value
    session["edits"] = edits
    await set_session(phone, session)

    await wa_client.send_text(
        phone,
        MESSAGES["edit_saved"].format(field_name=field, new_value=value),
    )


async def _handle_summary(
    client: Client,
    phone: str,
    db: AsyncSession,
) -> None:
    """Handle summary command."""
    from app.models.ca_account import CAAccount
    from app.services.compliance.deadline_calculator import get_filing_deadlines

    tax_period = datetime.now(timezone.utc).strftime("%Y-%m")

    ca_result = await db.execute(select(CAAccount).where(CAAccount.id == client.ca_id))
    ca = ca_result.scalar_one_or_none()
    ca_name = ca.firm_name if ca else "your CA"

    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count(Invoice.id)).where(
            Invoice.client_id == client.id,
        )
    )
    invoice_count = count_result.scalar() or 0

    deadlines = get_filing_deadlines(tax_period)

    await wa_client.send_text(
        phone,
        MESSAGES["summary"].format(
            tax_period=tax_period,
            invoice_count=invoice_count,
            draft_itc_total="0.00",
            approved_itc_total="0.00",
            pending_count=0,
            gstr1_deadline=deadlines["gstr1_deadline"].strftime("%d %b %Y"),
            gstr3b_deadline=deadlines["gstr3b_deadline"].strftime("%d %b %Y"),
            ca_firm_name=ca_name,
        ),
    )
