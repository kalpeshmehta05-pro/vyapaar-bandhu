"""
VyapaarBandhu — Section 17(5) Blocked ITC Categories
Reference: GST Act Section 17(5) as amended

CRITICAL: This file must never import any ML/AI library.
Every rule is traceable to a specific GST Act section.
"""

from dataclasses import dataclass


@dataclass
class BlockedCategoryResult:
    is_blocked: bool
    reason: str = ""
    requires_ca_review: bool = False
    reference: str = ""
    can_ca_override: bool = False


# ── Always blocked — no exceptions ────────────────────────────────────

ALWAYS_BLOCKED = {
    "personal_clothing",         # 17(5)(b)(i)
    "club_membership",           # 17(5)(b)(ii)
    "personal_vehicle",          # 17(5)(a) — motor vehicles for personal use
    "works_contract_immovable",  # 17(5)(c)
    "gift_over_50k",             # 17(5)(h) — gifts above Rs.50,000
}

# ── Blocked with business-type exceptions ─────────────────────────────

BLOCKED_WITH_EXCEPTIONS: dict[str, dict] = {
    "motor_vehicles": {
        "blocked_for": ["trader", "manufacturer", "service_provider", "retailer"],
        "eligible_for_activity": [
            "motor_vehicle_dealer", "transportation", "driving_school",
            "vehicle_rental", "cab_service",
        ],
        "reference": "GST Act Section 17(5)(a)",
    },
    "food_and_beverages": {
        "blocked_for": ["trader", "service_provider", "retailer"],
        "eligible_for_activity": [
            "restaurant", "hotel", "catering", "food_manufacturer",
            "canteen", "outdoor_catering_provider",
        ],
        "reference": "GST Act Section 17(5)(b)(i)",
    },
    "health_and_wellness": {
        "blocked_for": ["trader", "manufacturer", "service_provider", "retailer"],
        "eligible_for_activity": [
            "hospital", "clinic", "pharmacy", "health_service_provider",
            "diagnostic_centre", "medical_equipment",
        ],
        "reference": "GST Act Section 17(5)(b)(iii)",
    },
    "outdoor_catering": {
        "blocked_for": ["trader", "manufacturer", "service_provider", "retailer"],
        "eligible_for_activity": [
            "restaurant", "hotel", "catering", "event_management",
        ],
        "reference": "GST Act Section 17(5)(b)(i)",
    },
    "rent_a_cab": {
        "blocked_for": ["trader", "manufacturer", "service_provider", "retailer"],
        "eligible_for_activity": [
            "transportation", "cab_service", "travel_agency",
        ],
        "reference": "GST Act Section 17(5)(a)(A)",
    },
    "life_insurance": {
        "blocked_for": ["trader", "manufacturer", "service_provider", "retailer"],
        "eligible_for_activity": [
            "insurance_company", "insurance_broker",
        ],
        "reference": "GST Act Section 17(5)(b)",
    },
    "health_insurance": {
        "blocked_for": ["trader", "manufacturer", "service_provider", "retailer"],
        "eligible_for_activity": [
            "insurance_company", "insurance_broker",
        ],
        "reference": "GST Act Section 17(5)(b)",
    },
    "construction": {
        "blocked_for": ["trader", "manufacturer", "service_provider", "retailer"],
        "eligible_for_activity": [
            "real_estate_developer", "construction_contractor",
        ],
        "reference": "GST Act Section 17(5)(c)(d)",
    },
}


def is_section_17_5_blocked(
    category: str,
    business_type: str,
    primary_activity: str | None,
) -> BlockedCategoryResult:
    """
    Determine if a purchase category is blocked under Section 17(5).

    Returns BlockedCategoryResult with:
    - is_blocked: whether ITC is blocked
    - requires_ca_review: whether CA must confirm (exception cases)
    - can_ca_override: whether CA can override (edge cases)
    - reference: GST Act section reference

    GST Act Section 17(5) — Blocked credits for specified goods/services.
    """
    category_lower = category.lower().strip() if category else ""

    # Check 1: Always blocked — no exceptions
    if category_lower in ALWAYS_BLOCKED:
        return BlockedCategoryResult(
            is_blocked=True,
            reason=f"Section 17(5) blocked category: {category_lower}",
            can_ca_override=False,
            reference="GST Act Section 17(5)",
        )

    # Check 2: Blocked with exceptions
    if category_lower in BLOCKED_WITH_EXCEPTIONS:
        rule = BLOCKED_WITH_EXCEPTIONS[category_lower]

        if business_type in rule["blocked_for"]:
            # Check if primary_activity provides an exception
            if primary_activity and any(
                act in primary_activity.lower()
                for act in rule["eligible_for_activity"]
            ):
                # Potential exception — CA must confirm
                return BlockedCategoryResult(
                    is_blocked=False,  # Tentatively eligible
                    reason=f"Potential Section 17(5) exception for {primary_activity} — CA must confirm",
                    requires_ca_review=True,
                    reference=rule["reference"],
                    can_ca_override=True,
                )

            # Blocked for this business type
            return BlockedCategoryResult(
                is_blocked=True,
                reason=f"{rule['reference']} — blocked for {business_type}",
                can_ca_override=True,  # CA can override with notes
                reference=rule["reference"],
            )

    # Not blocked
    return BlockedCategoryResult(is_blocked=False)
