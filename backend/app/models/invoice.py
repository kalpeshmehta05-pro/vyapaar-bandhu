"""
VyapaarBandhu — Invoice Model
Raw extracted data from OCR + classification + compliance evaluation.
Includes RCM fields and full CA workflow status.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Index, Numeric, String, Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# Valid invoice statuses
INVOICE_STATUSES = (
    "pending_client_confirmation",
    "pending_ca_review",
    "flagged_low_confidence",
    "flagged_classification",
    "flagged_anomaly",
    "ca_approved",
    "ca_rejected",
    "ca_overridden",
)


class Invoice(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "invoices"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vyapaar.clients.id", ondelete="RESTRICT"),
        nullable=False,
    )
    ca_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vyapaar.ca_accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # ── Source ─────────────────────────────────────────────────────────
    image_s3_key: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="whatsapp_photo",
        # CHECK IN ('whatsapp_photo','bank_pdf','manual_entry')
    )
    whatsapp_message_id: Mapped[str | None] = mapped_column(Text)  # Meta ID for dedup

    # ── Extracted fields (9 required) ──────────────────────────────────
    seller_gstin: Mapped[str | None] = mapped_column(String(15))
    seller_name: Mapped[str | None] = mapped_column(Text)
    invoice_number: Mapped[str | None] = mapped_column(Text)
    invoice_date: Mapped[date | None] = mapped_column(Date)
    taxable_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    cgst_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    sgst_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    igst_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    total_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    product_description: Mapped[str | None] = mapped_column(Text)

    # ── OCR metadata ───────────────────────────────────────────────────
    ocr_confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))  # 0.0000-1.0000
    ocr_provider: Mapped[str | None] = mapped_column(String(20))  # tesseract | easyocr
    gstin_was_autocorrected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    gstin_original_ocr: Mapped[str | None] = mapped_column(Text)

    # ── Classification ─────────────────────────────────────────────────
    category: Mapped[str | None] = mapped_column(Text)  # one of 7 categories
    classification_method: Mapped[str | None] = mapped_column(String(20))  # keyword|bart|indicbert|ca_override
    classification_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    is_itc_eligible_draft: Mapped[bool | None] = mapped_column(Boolean)  # DRAFT pending CA
    blocked_reason: Mapped[str | None] = mapped_column(Text)  # sec_17_5|composition|rcm|other

    # ── RCM (Reverse Charge Mechanism) ─────────────────────────────────
    is_rcm: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rcm_category: Mapped[str | None] = mapped_column(String(50))  # gta|legal|security|import|unregistered

    # ── CA workflow ────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(40), nullable=False, default="pending_client_confirmation",
    )
    ca_reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vyapaar.ca_accounts.id"),
    )
    ca_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ca_override_notes: Mapped[str | None] = mapped_column(Text)
    ca_override_category: Mapped[str | None] = mapped_column(Text)
    ca_override_itc_eligible: Mapped[bool | None] = mapped_column(Boolean)

    # ── Deduplication ──────────────────────────────────────────────────
    dedup_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    # SHA256(seller_gstin + invoice_number + client_id)

    # ── Timestamps ─────────────────────────────────────────────────────
    client_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ── Relationships ──────────────────────────────────────────────────
    client = relationship("Client", back_populates="invoices")
    ca = relationship("CAAccount", back_populates="invoices", foreign_keys=[ca_id])

    # ── Indexes ────────────────────────────────────────────────────────
    __table_args__ = (
        Index("idx_invoices_client_id", "client_id"),
        Index("idx_invoices_ca_id", "ca_id"),
        Index("idx_invoices_status", "status"),
        Index("idx_invoices_invoice_date", "invoice_date"),
        Index("idx_invoices_dedup_hash", "dedup_hash"),
    )
