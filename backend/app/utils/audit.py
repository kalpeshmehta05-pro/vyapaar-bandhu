"""
VyapaarBandhu — Audit Log Writer
Append-only with SHA-256 hash chain for legal defensibility.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

logger = structlog.get_logger()

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


def _compute_row_hash(prev_id: int | None, prev_hash: str, event_data: dict) -> str:
    """SHA-256( prev_row_id || prev_hash || event_data_json )"""
    payload = f"{prev_id or 0}|{prev_hash}|{json.dumps(event_data, sort_keys=True, default=str)}"
    return hashlib.sha256(payload.encode()).hexdigest()


async def write_audit_log(
    db: AsyncSession,
    *,
    actor_type: str,
    action: str,
    actor_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    old_value: dict | None = None,
    new_value: dict | None = None,
    ip_address: str | None = None,
    correlation_id: str | None = None,
) -> AuditLog:
    """
    Write an immutable audit log entry with hash chain.
    This function must be called within an active DB transaction.
    """
    # Get the last row's hash for chain continuity
    # SELECT ... FOR UPDATE serializes concurrent writes to prevent race conditions
    result = await db.execute(
        select(AuditLog.id, AuditLog.row_hash)
        .order_by(AuditLog.id.desc())
        .limit(1)
        .with_for_update()
    )
    last_row = result.first()

    if last_row:
        prev_id, prev_hash = last_row.id, last_row.row_hash or GENESIS_HASH
    else:
        prev_id, prev_hash = None, GENESIS_HASH

    event_data = {
        "actor_type": actor_type,
        "action": action,
        "actor_id": str(actor_id) if actor_id else None,
        "entity_type": entity_type,
        "entity_id": str(entity_id) if entity_id else None,
        "old_value": old_value,
        "new_value": new_value,
    }

    row_hash = _compute_row_hash(prev_id, prev_hash, event_data)

    entry = AuditLog(
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        correlation_id=correlation_id,
        prev_hash=prev_hash,
        row_hash=row_hash,
    )
    db.add(entry)
    await db.flush()  # Get the ID assigned

    logger.info(
        "audit.log.written",
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        actor_type=actor_type,
    )

    return entry


async def verify_audit_chain(db: AsyncSession) -> dict:
    """
    Walk the entire audit log and verify hash chain integrity.
    Returns {valid: bool, last_verified_id: int, broken_at_id: int | None}.
    """
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.id.asc())
    )
    rows = result.scalars().all()

    if not rows:
        return {"valid": True, "last_verified_id": 0, "broken_at_id": None, "total_rows": 0}

    prev_id = None
    prev_hash = GENESIS_HASH

    for row in rows:
        event_data = {
            "actor_type": row.actor_type,
            "action": row.action,
            "actor_id": str(row.actor_id) if row.actor_id else None,
            "entity_type": row.entity_type,
            "entity_id": str(row.entity_id) if row.entity_id else None,
            "old_value": row.old_value,
            "new_value": row.new_value,
        }

        expected_hash = _compute_row_hash(prev_id, prev_hash, event_data)

        if row.row_hash != expected_hash or row.prev_hash != prev_hash:
            return {
                "valid": False,
                "last_verified_id": prev_id or 0,
                "broken_at_id": row.id,
                "total_rows": len(rows),
            }

        prev_id = row.id
        prev_hash = row.row_hash

    return {
        "valid": True,
        "last_verified_id": rows[-1].id,
        "broken_at_id": None,
        "total_rows": len(rows),
    }
