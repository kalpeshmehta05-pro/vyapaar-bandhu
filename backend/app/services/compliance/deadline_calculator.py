"""
VyapaarBandhu — GST Filing Deadline Calculator
GSTR-1 and GSTR-3B deadlines per GSTN notifications.

CRITICAL: This file must never import any ML/AI library.
Monthly filing only for v1 (no quarterly — see plan Q1 decision).
"""

from datetime import date


# ── Deadline constants ────────────────────────────────────────────────
# These can change if GST Council issues new notifications.
# Keep in a single place for easy update.

GSTR1_DAY = 11    # GSTR-1 due on 11th of following month
GSTR3B_DAY = 20   # GSTR-3B due on 20th of following month (default)


def get_gstr1_deadline(tax_period: str) -> date:
    """
    GSTR-1 deadline: 11th of month following the tax period.
    For monthly filers (turnover > 5 Cr or opted monthly).

    Reference: GSTN notification for GSTR-1 due dates.
    """
    year, month = _parse_period(tax_period)
    next_year, next_month = _next_month(year, month)
    return date(next_year, next_month, GSTR1_DAY)


def get_gstr3b_deadline(tax_period: str, state_code: str | None = None) -> date:
    """
    GSTR-3B deadline: 20th of month following tax period (most states).
    22nd for Category 1 states (turnover <= 5 Cr, some states).
    24th for Category 2 states (turnover <= 5 Cr, other states).

    Default to 20th (conservative — earlier is safer).
    CA sets filing category at client onboarding (v1.1 roadmap).

    Reference: GSTN notification for GSTR-3B staggered deadlines.
    """
    year, month = _parse_period(tax_period)
    next_year, next_month = _next_month(year, month)
    return date(next_year, next_month, GSTR3B_DAY)


def get_filing_deadlines(tax_period: str, state_code: str | None = None) -> dict:
    """
    Get all filing deadlines for a tax period.
    Returns dict with deadlines and days remaining.
    """
    today = date.today()
    gstr1 = get_gstr1_deadline(tax_period)
    gstr3b = get_gstr3b_deadline(tax_period, state_code)

    return {
        "tax_period": tax_period,
        "gstr1_deadline": gstr1,
        "gstr3b_deadline": gstr3b,
        "days_to_gstr1": (gstr1 - today).days,
        "days_to_gstr3b": (gstr3b - today).days,
    }


def _parse_period(tax_period: str) -> tuple[int, int]:
    """Parse 'YYYY-MM' into (year, month)."""
    parts = tax_period.split("-")
    return int(parts[0]), int(parts[1])


def _next_month(year: int, month: int) -> tuple[int, int]:
    """Get the next month, rolling over at December."""
    if month == 12:
        return year + 1, 1
    return year, month + 1
