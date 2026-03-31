"""
VyapaarBandhu — Monthly ITC Summary Model
Materialised per client per tax period. Draft + confirmed figures.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MonthlySummary(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "monthly_summaries"

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
    tax_period: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM

    # ── Draft figures (before CA approval) ─────────────────────────────
    draft_total_taxable: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    draft_cgst_itc: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    draft_sgst_itc: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    draft_igst_itc: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    draft_total_itc: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)

    # ── Confirmed figures (after CA approval) ──────────────────────────
    confirmed_total_taxable: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    confirmed_cgst_itc: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    confirmed_sgst_itc: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    confirmed_igst_itc: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    confirmed_total_itc: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))

    # ── RCM totals ─────────────────────────────────────────────────────
    draft_rcm_liability: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    confirmed_rcm_liability: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))

    # ── Invoice counts ─────────────────────────────────────────────────
    invoice_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    approved_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    flagged_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Export keys ────────────────────────────────────────────────────
    gstr3b_json_s3_key: Mapped[str | None] = mapped_column(Text)
    filing_pdf_s3_key: Mapped[str | None] = mapped_column(Text)
    tally_xml_s3_key: Mapped[str | None] = mapped_column(Text)  # Roadmap Q3 2026

    is_filed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    filed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("client_id", "tax_period", name="uq_summary_client_period"),
    )
