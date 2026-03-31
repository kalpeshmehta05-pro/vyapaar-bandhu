"""
VyapaarBandhu — CA Account Model
Mirrors vyapaar.ca_accounts table from Part 3 schema.
"""

import uuid

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CAAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ca_accounts"

    firm_name: Mapped[str] = mapped_column(Text, nullable=False)
    proprietor_name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(Text, unique=True, nullable=False)  # E.164
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    membership_number: Mapped[str | None] = mapped_column(Text, unique=True)  # ICAI
    gstin: Mapped[str | None] = mapped_column(Text)  # CA firm GSTIN
    logo_s3_key: Mapped[str | None] = mapped_column(Text)
    logo_thumbnail_s3_key: Mapped[str | None] = mapped_column(Text)  # 200x200
    icai_certificate_s3_key: Mapped[str | None] = mapped_column(Text)  # Q3 gate

    tier: Mapped[str] = mapped_column(
        String(20), nullable=False, default="starter",
        # CHECK (tier IN ('starter','professional','scale'))
    )
    max_clients: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    clients = relationship("Client", back_populates="ca", lazy="selectin")
    invoices = relationship("Invoice", back_populates="ca", foreign_keys="Invoice.ca_id", lazy="selectin")
