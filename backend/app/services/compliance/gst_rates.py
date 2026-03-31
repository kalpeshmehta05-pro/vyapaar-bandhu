"""
VyapaarBandhu — GST Rate Table
Versioned, not hardcoded. Loaded from config, not from AI.

CRITICAL: This file must never import any ML/AI library.

Rate source: CBIC GST rate schedule as of March 2026.
Update this when GST Council changes rates.
"""

from decimal import Decimal

# ── GST Rate Table (versioned) ────────────────────────────────────────
# Key: category or HSN prefix
# Value: GST rate as Decimal percentage

GST_RATES_VERSION = "2026-03"

GST_RATES: dict[str, Decimal] = {
    # Essentials (0%)
    "essential_food": Decimal("0"),
    "fresh_vegetables": Decimal("0"),
    "fresh_fruits": Decimal("0"),
    "milk": Decimal("0"),

    # Low rate (5%)
    "textile_below_1000": Decimal("5"),
    "restaurant_non_ac": Decimal("5"),
    "transport_gta": Decimal("5"),
    "sugar": Decimal("5"),
    "tea": Decimal("5"),

    # Standard low (12%)
    "garments_above_1000": Decimal("12"),
    "hotel_below_7500": Decimal("12"),
    "medicine": Decimal("12"),
    "processed_food": Decimal("12"),
    "furniture": Decimal("12"),

    # Standard (18%) — most common for business purchases
    "electronics_and_it": Decimal("18"),
    "office_supplies": Decimal("18"),
    "raw_materials": Decimal("18"),
    "software": Decimal("18"),
    "professional_services": Decimal("18"),
    "restaurant_ac": Decimal("18"),
    "hotel_above_7500": Decimal("18"),
    "capital_goods": Decimal("18"),
    "telecom": Decimal("18"),
    "financial_services": Decimal("18"),
    "construction": Decimal("18"),

    # High rate (28%)
    "automobile": Decimal("28"),
    "luxury_goods": Decimal("28"),
    "tobacco": Decimal("28"),
    "aerated_drinks": Decimal("28"),
    "cement": Decimal("28"),

    # Precious metals (3%)
    "gold": Decimal("3"),
    "silver": Decimal("3"),
    "precious_stones": Decimal("3"),

    # Default
    "default": Decimal("18"),
}


def get_gst_rate(category: str) -> Decimal:
    """Get GST rate for a category. Returns default (18%) if not found."""
    return GST_RATES.get(category.lower(), GST_RATES["default"])


def get_rates_version() -> str:
    """Get the current GST rates version identifier."""
    return GST_RATES_VERSION
