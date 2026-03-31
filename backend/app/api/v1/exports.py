"""
VyapaarBandhu — Export Endpoints
PDF filing summary, GSTR-3B JSON, Tally XML (stub).
"""

import uuid
from decimal import Decimal

import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.dependencies import CurrentCA
from app.models.client import Client
from app.models.invoice import Invoice
from app.models.ca_account import CAAccount
from app.services.exports.pdf_generator import generate_filing_pdf
from app.services.exports.gstr3b_json import generate_gstr3b_json

logger = structlog.get_logger()
router = APIRouter()


@router.get("/{client_id}/pdf/{period}")
async def download_pdf(
    client_id: uuid.UUID,
    period: str,
    ca: CurrentCA,
    db: AsyncSession = Depends(get_async_session),
):
    """Generate and download filing summary PDF for a client+period."""
    client = await _get_client_or_404(client_id, ca.id, db)

    # Get approved invoices for this period
    invoices = await _get_period_invoices(client_id, period, db)

    # Calculate totals from confirmed invoices
    cgst = sum(float(i.cgst_amount or 0) for i in invoices if i.status == "ca_approved")
    sgst = sum(float(i.sgst_amount or 0) for i in invoices if i.status == "ca_approved")
    igst = sum(float(i.igst_amount or 0) for i in invoices if i.status == "ca_approved")
    total = cgst + sgst + igst
    pending = sum(1 for i in invoices if i.status not in ("ca_approved", "ca_rejected"))

    pdf_bytes = await generate_filing_pdf(
        ca_firm_name=ca.firm_name,
        ca_proprietor_name=ca.proprietor_name,
        client_name=client.business_name,
        client_gstin=client.gstin,
        tax_period=period,
        invoices=invoices,
        confirmed_cgst_itc=f"{cgst:,.2f}",
        confirmed_sgst_itc=f"{sgst:,.2f}",
        confirmed_igst_itc=f"{igst:,.2f}",
        confirmed_total_itc=f"{total:,.2f}",
        pending_count=pending,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=filing_summary_{period}_{client.business_name}.pdf"
        },
    )


@router.get("/{client_id}/gstr3b/{period}")
async def download_gstr3b(
    client_id: uuid.UUID,
    period: str,
    ca: CurrentCA,
    db: AsyncSession = Depends(get_async_session),
):
    """Generate GSTR-3B JSON for a client+period. Only CA-confirmed figures."""
    client = await _get_client_or_404(client_id, ca.id, db)
    invoices = await _get_period_invoices(client_id, period, db)

    # Only CA-approved invoices go into GSTR-3B
    approved = [i for i in invoices if i.status == "ca_approved"]
    cgst = sum(float(i.cgst_amount or 0) for i in approved)
    sgst = sum(float(i.sgst_amount or 0) for i in approved)
    igst = sum(float(i.igst_amount or 0) for i in approved)
    rcm = sum(float(i.total_amount or 0) for i in approved if i.is_rcm)

    gstr3b = generate_gstr3b_json(
        gstin=client.gstin or "",
        tax_period=period,
        confirmed_cgst_itc=f"{cgst:.2f}",
        confirmed_sgst_itc=f"{sgst:.2f}",
        confirmed_igst_itc=f"{igst:.2f}",
        confirmed_rcm_liability=f"{rcm:.2f}",
    )

    return JSONResponse(content=gstr3b)


@router.get("/{client_id}/tally/{period}")
async def download_tally(
    client_id: uuid.UUID,
    period: str,
    ca: CurrentCA,
):
    """TallyPrime XML export — roadmap Q3 2026."""
    raise HTTPException(
        status_code=501,
        detail="TallyPrime XML export is on the roadmap for Q3 2026.",
    )


async def _get_client_or_404(
    client_id: uuid.UUID, ca_id: uuid.UUID, db: AsyncSession
) -> Client:
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.ca_id == ca_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


async def _get_period_invoices(
    client_id: uuid.UUID, period: str, db: AsyncSession
) -> list[Invoice]:
    """Get invoices for a client in a specific tax period (YYYY-MM)."""
    from datetime import date
    parts = period.split("-")
    year, month = int(parts[0]), int(parts[1])
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    result = await db.execute(
        select(Invoice).where(
            Invoice.client_id == client_id,
            Invoice.invoice_date >= start,
            Invoice.invoice_date < end,
        ).order_by(Invoice.invoice_date)
    )
    return result.scalars().all()
