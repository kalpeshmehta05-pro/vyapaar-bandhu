"""
VyapaarBandhu — Reminder Log Model
Idempotency table for WhatsApp deadline reminders.
UNIQUE constraint prevents duplicate reminders per client per period per type.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class ReminderLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "reminder_log"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vyapaar.clients.id"),
        nullable=False,
    )
    tax_period: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    reminder_type: Mapped[str] = mapped_column(
        String(10), nullable=False,
        # CHECK IN ('7_day','3_day','1_day','overdue')
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    wa_message_id: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint(
            "client_id", "tax_period", "reminder_type",
            name="uq_reminder_client_period_type",
        ),
    )
