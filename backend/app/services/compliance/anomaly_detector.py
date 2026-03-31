"""
VyapaarBandhu — Invoice Amount Anomaly Detection
Flags invoices with amounts significantly above client historical average.
Does not block — flags for CA review.

CRITICAL: This file must never import any ML/AI library.
"""

import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.invoice import Invoice

ZERO = Decimal("0.00")


@dataclass
class AnomalyResult:
    is_anomalous: bool = False
    historical_avg: Decimal | None = None
    current_amount: Decimal = ZERO
    ratio: float = 0.0
    flag_message: str = ""


async def detect_amount_anomaly(
    client_id: uuid.UUID,
    invoice_amount: Decimal,
    db: AsyncSession,
) -> AnomalyResult:
    """
    Flag invoices with amounts significantly above client's historical average.
    Threshold: ANOMALY_THRESHOLD_MULTIPLIER (default 2.5x) of 3-month average.

    Does NOT block — flags for CA review only.
    """
    if invoice_amount is None or invoice_amount <= ZERO:
        return AnomalyResult(is_anomalous=False)

    historical_avg = await _get_client_invoice_average(client_id, months=3, db=db)

    if historical_avg is None or historical_avg <= ZERO:
        # No history — cannot detect anomaly
        return AnomalyResult(is_anomalous=False, current_amount=invoice_amount)

    threshold = historical_avg * Decimal(str(settings.ANOMALY_THRESHOLD_MULTIPLIER))

    if invoice_amount > threshold:
        ratio = float(invoice_amount / historical_avg)
        return AnomalyResult(
            is_anomalous=True,
            historical_avg=historical_avg,
            current_amount=invoice_amount,
            ratio=ratio,
            flag_message=f"Amount is {ratio:.1f}x above 3-month average of {historical_avg}",
        )

    return AnomalyResult(
        is_anomalous=False,
        historical_avg=historical_avg,
        current_amount=invoice_amount,
    )


async def _get_client_invoice_average(
    client_id: uuid.UUID,
    months: int,
    db: AsyncSession,
) -> Decimal | None:
    """Get average invoice total_amount for last N months, excluding outliers."""
    cutoff = date.today() - timedelta(days=months * 30)

    result = await db.execute(
        select(func.avg(Invoice.total_amount))
        .where(
            Invoice.client_id == client_id,
            Invoice.invoice_date >= cutoff,
            Invoice.total_amount.isnot(None),
            Invoice.status.notin_(["ca_rejected"]),
        )
    )
    avg = result.scalar()
    return Decimal(str(avg)) if avg else None
