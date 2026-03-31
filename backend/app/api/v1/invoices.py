"""
VyapaarBandhu — Invoice Endpoints
List, detail, approve, reject, override. CA-scoped with audit trail.
"""

import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.dependencies import CurrentCA
from app.models.invoice import Invoice
from app.models.classification_feedback import ClassificationFeedback
from app.schemas.invoice import (
    InvoiceApproveRequest,
    InvoiceOverrideRequest,
    InvoiceRejectRequest,
    InvoiceResponse,
)
from app.utils.audit import write_audit_log

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=list[InvoiceResponse])
async def list_invoices(
    ca: CurrentCA,
    db: AsyncSession = Depends(get_async_session),
    status: str | None = Query(None),
    client_id: uuid.UUID | None = Query(None),
    skip: int = 0,
    limit: int = 50,
):
    """List invoices with optional filters. CA-scoped."""
    query = select(Invoice).where(Invoice.ca_id == ca.id)

    if status:
        query = query.where(Invoice.status == status)
    if client_id:
        query = query.where(Invoice.client_id == client_id)

    query = query.offset(skip).limit(min(limit, 100)).order_by(Invoice.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    ca: CurrentCA,
    db: AsyncSession = Depends(get_async_session),
):
    """Get invoice detail with OCR confidence + flags. CA-scoped."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.ca_id == ca.id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.post("/{invoice_id}/approve", response_model=InvoiceResponse)
async def approve_invoice(
    invoice_id: uuid.UUID,
    req: InvoiceApproveRequest,
    ca: CurrentCA,
    db: AsyncSession = Depends(get_async_session),
):
    """CA approves invoice with optional category/ITC override."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.ca_id == ca.id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    old_status = invoice.status
    old_category = invoice.category
    old_itc = invoice.is_itc_eligible_draft

    invoice.status = "ca_approved"
    invoice.ca_reviewed_by = ca.id
    invoice.ca_reviewed_at = datetime.now(timezone.utc)

    if req.override_category:
        invoice.ca_override_category = req.override_category
        invoice.category = req.override_category
    if req.override_itc_eligible is not None:
        invoice.ca_override_itc_eligible = req.override_itc_eligible
        invoice.is_itc_eligible_draft = req.override_itc_eligible
    if req.notes:
        invoice.ca_override_notes = req.notes

    # Log classification feedback if category was overridden
    if req.override_category and old_category and req.override_category != old_category:
        feedback = ClassificationFeedback(
            invoice_id=invoice.id,
            original_category=old_category,
            corrected_category=req.override_category,
            original_method=invoice.classification_method or "unknown",
            ca_id=ca.id,
        )
        db.add(feedback)

    await write_audit_log(
        db,
        actor_type="ca",
        actor_id=ca.id,
        action="invoice.approved",
        entity_type="invoice",
        entity_id=invoice.id,
        old_value={"status": old_status, "category": old_category, "itc_eligible": old_itc},
        new_value={
            "status": "ca_approved",
            "category": invoice.category,
            "itc_eligible": invoice.is_itc_eligible_draft,
            "override_notes": req.notes,
        },
    )
    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.post("/{invoice_id}/reject", response_model=InvoiceResponse)
async def reject_invoice(
    invoice_id: uuid.UUID,
    req: InvoiceRejectRequest,
    ca: CurrentCA,
    db: AsyncSession = Depends(get_async_session),
):
    """CA rejects invoice. Reason required."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.ca_id == ca.id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    old_status = invoice.status
    invoice.status = "ca_rejected"
    invoice.ca_reviewed_by = ca.id
    invoice.ca_reviewed_at = datetime.now(timezone.utc)
    invoice.ca_override_notes = req.reason

    await write_audit_log(
        db,
        actor_type="ca",
        actor_id=ca.id,
        action="invoice.rejected",
        entity_type="invoice",
        entity_id=invoice.id,
        old_value={"status": old_status},
        new_value={"status": "ca_rejected", "reason": req.reason},
    )
    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.patch("/{invoice_id}/override", response_model=InvoiceResponse)
async def override_invoice(
    invoice_id: uuid.UUID,
    req: InvoiceOverrideRequest,
    ca: CurrentCA,
    db: AsyncSession = Depends(get_async_session),
):
    """CA overrides category + ITC eligibility. Logs to classification_feedback."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.ca_id == ca.id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    old_category = invoice.category
    old_itc = invoice.is_itc_eligible_draft

    invoice.status = "ca_overridden"
    invoice.ca_reviewed_by = ca.id
    invoice.ca_reviewed_at = datetime.now(timezone.utc)
    invoice.ca_override_category = req.category
    invoice.ca_override_itc_eligible = req.itc_eligible
    invoice.ca_override_notes = req.notes
    invoice.category = req.category
    invoice.is_itc_eligible_draft = req.itc_eligible
    invoice.classification_method = "ca_override"

    # Log for retraining pipeline
    if old_category and req.category != old_category:
        feedback = ClassificationFeedback(
            invoice_id=invoice.id,
            original_category=old_category,
            corrected_category=req.category,
            original_method=invoice.classification_method or "unknown",
            ca_id=ca.id,
        )
        db.add(feedback)

    await write_audit_log(
        db,
        actor_type="ca",
        actor_id=ca.id,
        action="invoice.overridden",
        entity_type="invoice",
        entity_id=invoice.id,
        old_value={"category": old_category, "itc_eligible": old_itc},
        new_value={
            "category": req.category,
            "itc_eligible": req.itc_eligible,
            "notes": req.notes,
        },
    )
    await db.commit()
    await db.refresh(invoice)
    return invoice
