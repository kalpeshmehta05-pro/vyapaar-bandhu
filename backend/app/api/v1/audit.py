"""
VyapaarBandhu -- Audit Log Export & Chain Verification Endpoints
Provides legally defensible audit trail export and integrity verification.
"""

from datetime import date, datetime, timezone, timedelta

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.dependencies import CurrentCA
from app.models.audit_log import AuditLog
from app.utils.audit import verify_audit_chain

logger = structlog.get_logger()
router = APIRouter()

MAX_DATE_RANGE_DAYS = 90


def _mask_uuid(uuid_val) -> str | None:
    """Mask a UUID for export: show first 8 chars, mask the rest."""
    if uuid_val is None:
        return None
    s = str(uuid_val)
    return s[:8] + "-****-****-****-************"


@router.get("/export")
async def export_audit_logs(
    ca: CurrentCA,
    db: AsyncSession = Depends(get_async_session),
    from_date: date = Query(..., alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: date = Query(..., alias="to", description="End date (YYYY-MM-DD)"),
):
    """
    Export audit log events for the authenticated CA within a date range.
    Max date range: 90 days.
    """
    if to_date < from_date:
        raise HTTPException(status_code=400, detail="to_date must be >= from_date")

    date_range = (to_date - from_date).days
    if date_range > MAX_DATE_RANGE_DAYS:
        raise HTTPException(
            status_code=400,
            detail=f"Date range exceeds maximum of {MAX_DATE_RANGE_DAYS} days",
        )

    from_dt = datetime.combine(from_date, datetime.min.time(), tzinfo=timezone.utc)
    to_dt = datetime.combine(to_date, datetime.max.time(), tzinfo=timezone.utc)

    result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.actor_id == ca.id,
            AuditLog.event_time >= from_dt,
            AuditLog.event_time <= to_dt,
        )
        .order_by(AuditLog.id.asc())
    )
    rows = result.scalars().all()

    return [
        {
            "id": row.id,
            "event_time": row.event_time.isoformat() if row.event_time else None,
            "action": row.action,
            "ca_id": _mask_uuid(row.actor_id),
            "entity_type": row.entity_type,
            "entity_id": str(row.entity_id) if row.entity_id else None,
            "row_hash": row.row_hash,
            "prev_hash": row.prev_hash,
        }
        for row in rows
    ]


@router.get("/verify-chain")
async def verify_chain(
    ca: CurrentCA,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Verify SHA-256 hash chain integrity for all audit logs.
    Returns validation result with count of checked entries.
    """
    result = await verify_audit_chain(db)

    return {
        "valid": result["valid"],
        "checked": result["total_rows"],
        "broken_at": None if result["valid"] else (
            # Look up the event_time for the broken row
            await _get_event_time(db, result["broken_at_id"])
        ),
    }


async def _get_event_time(db: AsyncSession, row_id: int | None) -> str | None:
    """Get the event_time for a specific audit log row."""
    if row_id is None:
        return None
    result = await db.execute(
        select(AuditLog.event_time).where(AuditLog.id == row_id)
    )
    row = result.first()
    if row and row.event_time:
        return row.event_time.isoformat()
    return None
