"""
VyapaarBandhu — Audit Log Model
Append-only, immutable. No UPDATE or DELETE ever.
Includes SHA-256 hash chain for legal defensibility.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Text, String
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    # Sequential ID for ordering — not UUID
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    actor_type: Mapped[str] = mapped_column(
        String(10), nullable=False,
        # CHECK IN ('ca','client','system','admin')
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(Text, nullable=False)
    # e.g. 'invoice.approved', 'gstin.autocorrected', 'client.consent_given'
    entity_type: Mapped[str | None] = mapped_column(String(30))  # invoice|client|summary
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    old_value: Mapped[dict | None] = mapped_column(JSONB)
    new_value: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(INET)
    correlation_id: Mapped[str | None] = mapped_column(Text)  # Request trace ID

    # ── SHA-256 Hash Chain ─────────────────────────────────────────────
    # Each row: prev_hash = SHA256(prev_row_id || prev_hash || event_data_json)
    # First row uses genesis hash. Chain verified by walking all rows.
    prev_hash: Mapped[str | None] = mapped_column(Text)
    row_hash: Mapped[str | None] = mapped_column(Text)

    # NOTE: PostgreSQL RULE prevents UPDATE/DELETE at DB level.
    # CREATE RULE no_update_audit AS ON UPDATE TO vyapaar.audit_log DO INSTEAD NOTHING;
    # CREATE RULE no_delete_audit AS ON DELETE TO vyapaar.audit_log DO INSTEAD NOTHING;
