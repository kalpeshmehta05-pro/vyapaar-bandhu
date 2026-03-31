"""
VyapaarBandhu — ITC Amount Calculator
Decimal math with ROUND_HALF_UP. No floating point anywhere.

CRITICAL: This file must never import any ML/AI library.
Reference: GST Act Section 16 — Eligibility and conditions for ITC.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

ZERO = Decimal("0.00")


@dataclass
class ITCAmounts:
    cgst: Decimal = ZERO
    sgst: Decimal = ZERO
    igst: Decimal = ZERO
    total: Decimal = ZERO


def calculate_itc_amounts(
    cgst: Decimal | None,
    sgst: Decimal | None,
    igst: Decimal | None,
    is_interstate: bool,
) -> ITCAmounts:
    """
    Calculate ITC amounts from invoice tax components.

    For inter-state transactions: ITC = IGST amount
    For intra-state transactions: ITC = CGST + SGST amounts

    All amounts rounded to 2 decimal places with ROUND_HALF_UP.

    Reference: GST Act Section 16 + IGST Act Section 5
    """
    cgst_val = _to_decimal(cgst)
    sgst_val = _to_decimal(sgst)
    igst_val = _to_decimal(igst)

    if is_interstate:
        return ITCAmounts(
            cgst=ZERO,
            sgst=ZERO,
            igst=igst_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total=igst_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        )
    else:
        total = (cgst_val + sgst_val).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return ITCAmounts(
            cgst=cgst_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            sgst=sgst_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            igst=ZERO,
            total=total,
        )


def _to_decimal(value: Decimal | float | int | None) -> Decimal:
    """Safely convert to Decimal. None and negative values become 0."""
    if value is None:
        return ZERO
    d = Decimal(str(value))
    return max(d, ZERO)
