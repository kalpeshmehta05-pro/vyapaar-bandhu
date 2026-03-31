"""
VyapaarBandhu — Client Model
Business clients managed by CAs. Includes DPDP consent fields.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Client(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "clients"

    ca_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vyapaar.ca_accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    whatsapp_phone: Mapped[str] = mapped_column(Text, nullable=False)  # E.164
    business_name: Mapped[str] = mapped_column(Text, nullable=False)
    owner_name: Mapped[str] = mapped_column(Text, nullable=False)
    gstin: Mapped[str | None] = mapped_column(String(15))  # 15-char GSTIN
    business_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="trader",
        # CHECK IN ('trader','manufacturer','service_provider','retailer','other')
    )
    primary_activity: Mapped[str | None] = mapped_column(Text)  # Free text for ITC edge cases
    state_code: Mapped[str | None] = mapped_column(String(2))  # From GSTIN[:2]
    is_composition: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    onboarded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(__import__("datetime").timezone.utc),
        nullable=False,
    )

    # ── DPDP Act 2023 — Consent Fields ─────────────────────────────────
    consent_given_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consent_version: Mapped[str | None] = mapped_column(Text)  # e.g. "v1.0"
    consent_withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ── Relationships ──────────────────────────────────────────────────
    ca = relationship("CAAccount", back_populates="clients")
    invoices = relationship("Invoice", back_populates="client", lazy="selectin")

    # ── Constraints and Indexes ────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint("ca_id", "whatsapp_phone", name="uq_clients_ca_phone"),
        Index("idx_clients_whatsapp_phone", "whatsapp_phone"),
        Index("idx_clients_ca_id", "ca_id"),
    )
