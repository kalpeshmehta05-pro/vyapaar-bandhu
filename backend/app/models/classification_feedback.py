"""
VyapaarBandhu — Classification Feedback Model
CA overrides feed into the retraining pipeline for IndicBERT.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class ClassificationFeedback(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "classification_feedback"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vyapaar.invoices.id"),
        nullable=False,
    )
    original_category: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_category: Mapped[str] = mapped_column(Text, nullable=False)
    original_method: Mapped[str] = mapped_column(Text, nullable=False)
    ca_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vyapaar.ca_accounts.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
