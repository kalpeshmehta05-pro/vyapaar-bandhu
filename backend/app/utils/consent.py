"""
VyapaarBandhu — DPDP Consent Enforcement
This module is the enforcement layer for DPDP Act 2023 consent.
The DPDP_COMPLIANCE.md documents the *policy*; this code *enforces* it.

Every code path that processes PII (WhatsApp message router, OCR task,
invoice creation) MUST call assert_client_consent() before proceeding.
Phase 4 developers: if you skip this, the system is non-compliant.
"""

import uuid
from datetime import datetime, timezone

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.invoice import Invoice
from app.config import settings

logger = structlog.get_logger()


class ConsentNotGivenError(Exception):
    """Raised when a client has not given DPDP consent."""
    pass


class ConsentWithdrawnError(Exception):
    """Raised when a client has withdrawn DPDP consent."""
    pass


async def assert_client_consent(
    db: AsyncSession,
    client_id: uuid.UUID,
) -> Client:
    """
    Assert that a client has given consent and not withdrawn it.
    This MUST be called before any data processing for the client.

    Raises:
        ConsentNotGivenError: if consent_given_at is NULL
        ConsentWithdrawnError: if consent_withdrawn_at is not NULL

    Returns:
        The Client object (for convenience in the calling code).
    """
    result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    if client.consent_given_at is None:
        logger.warning(
            "consent.not_given",
            client_id=str(client_id),
        )
        raise ConsentNotGivenError(
            f"Client {client_id} has not given DPDP consent. "
            "No data processing is permitted."
        )

    if client.consent_withdrawn_at is not None:
        logger.warning(
            "consent.withdrawn",
            client_id=str(client_id),
            withdrawn_at=client.consent_withdrawn_at.isoformat(),
        )
        raise ConsentWithdrawnError(
            f"Client {client_id} has withdrawn DPDP consent "
            f"at {client.consent_withdrawn_at}. "
            "No further data processing is permitted."
        )

    return client


async def assert_consent_by_phone(
    db: AsyncSession,
    whatsapp_phone: str,
) -> Client:
    """
    Assert consent by phone number (used in WhatsApp message router).
    Phone must be normalized to E.164 before calling.
    """
    result = await db.execute(
        select(Client).where(Client.whatsapp_phone == whatsapp_phone)
    )
    client = result.scalar_one_or_none()

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found for this phone number",
        )

    return await assert_client_consent(db, client.id)


async def record_consent(
    db: AsyncSession,
    client_id: uuid.UUID,
) -> None:
    """
    Record that a client has given consent via WhatsApp.
    Called when client replies 'haan'/'yes'/'agree' to the consent message.
    """
    now = datetime.now(timezone.utc)
    await db.execute(
        update(Client)
        .where(Client.id == client_id)
        .values(
            consent_given_at=now,
            consent_version=settings.CONSENT_VERSION,
            consent_withdrawn_at=None,  # Clear any previous withdrawal
        )
    )
    await db.flush()

    # Audit log
    from app.utils.audit import write_audit_log
    await write_audit_log(
        db,
        actor_type="client",
        actor_id=client_id,
        action="client.consent_given",
        entity_type="client",
        entity_id=client_id,
        new_value={"consent_version": settings.CONSENT_VERSION},
    )

    logger.info(
        "consent.recorded",
        client_id=str(client_id),
        consent_version=settings.CONSENT_VERSION,
    )


async def withdraw_consent(
    db: AsyncSession,
    client_id: uuid.UUID,
) -> dict:
    """
    Process a consent withdrawal request.
    Called when client replies 'nahi' / 'withdraw consent' on WhatsApp.

    Withdrawal cascade:
    1. Mark consent as withdrawn on the client record
    2. Deactivate the client (no further processing)
    3. Do NOT delete data immediately — GST Act Section 36 requires retention
    4. Log the withdrawal for audit trail
    5. Return summary of what happened

    Note: Actual data deletion happens via the nightly retention cron
    after the statutory retention period expires (images 3yr, data 7yr).
    This is documented in the consent message and privacy policy.
    """
    now = datetime.now(timezone.utc)

    # 1. Mark consent withdrawn + deactivate client
    result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    await db.execute(
        update(Client)
        .where(Client.id == client_id)
        .values(
            consent_withdrawn_at=now,
            is_active=False,
        )
    )

    # 2. Count affected invoices (for the audit record, not deletion)
    inv_result = await db.execute(
        select(Invoice).where(Invoice.client_id == client_id)
    )
    invoice_count = len(inv_result.scalars().all())

    # 3. Audit log
    from app.utils.audit import write_audit_log
    await write_audit_log(
        db,
        actor_type="client",
        actor_id=client_id,
        action="client.consent_withdrawn",
        entity_type="client",
        entity_id=client_id,
        old_value={
            "consent_given_at": client.consent_given_at.isoformat() if client.consent_given_at else None,
            "consent_version": client.consent_version,
        },
        new_value={
            "consent_withdrawn_at": now.isoformat(),
            "is_active": False,
            "invoices_affected": invoice_count,
            "data_retention_note": (
                "Data retained per GST Act Section 36. "
                f"Images deleted after {settings.RETENTION_IMAGES_YEARS} years. "
                f"Financial data deleted after {settings.RETENTION_DATA_YEARS} years."
            ),
        },
    )
    await db.flush()

    logger.info(
        "consent.withdrawn",
        client_id=str(client_id),
        invoices_affected=invoice_count,
    )

    return {
        "status": "consent_withdrawn",
        "client_id": str(client_id),
        "deactivated": True,
        "invoices_affected": invoice_count,
        "data_retention_note": (
            f"Aapka data GST Act ke under {settings.RETENTION_DATA_YEARS} saal tak "
            "stored rahega. Uske baad automatically delete ho jayega."
        ),
    }
