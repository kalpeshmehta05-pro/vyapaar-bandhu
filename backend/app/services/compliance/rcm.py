"""
VyapaarBandhu — Reverse Charge Mechanism (RCM)
Under RCM, the buyer (not seller) pays GST directly to the government.

CRITICAL: This file must never import any ML/AI library.

RCM applies to:
- GTA (Goods Transport Agency) services — Notification 13/2017-CT(R)
- Legal services from individual advocates — Notification 13/2017-CT(R)
- Security services from non-body corporate — Notification 29/2018-CT(R)
- Import of services — IGST Act Section 5(3)
- Purchases from unregistered vendors above Rs.5000/day — Section 9(4)
  (Note: Section 9(4) was suspended then partially reinstated. Currently
   applies only to specified categories. CA must confirm applicability.)

RCM ITC is claimable only after tax is paid to the government.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

ZERO = Decimal("0.00")


@dataclass
class RCMEvaluation:
    is_rcm: bool = False
    rcm_category: str | None = None
    rcm_liability: Decimal = ZERO
    itc_claimable_after_payment: bool = False
    requires_ca_confirmation: bool = False
    reference: str = ""
    note: str = ""


# Keywords that indicate RCM-applicable services
RCM_KEYWORDS: dict[str, dict] = {
    "gta": {
        "keywords": [
            "goods transport", "gta", "freight", "transport agency",
            "lorry", "truck", "shipping", "cargo", "logistics",
        ],
        "category": "gta",
        "reference": "Notification 13/2017-CT(R) Entry 1",
        "note": "GTA services under RCM — buyer pays GST at 5%",
    },
    "legal": {
        "keywords": [
            "legal", "advocate", "lawyer", "attorney", "legal service",
            "litigation", "arbitration", "legal counsel",
        ],
        "category": "legal",
        "reference": "Notification 13/2017-CT(R) Entry 2",
        "note": "Legal services from individual advocate under RCM",
    },
    "security": {
        "keywords": [
            "security", "guard", "security service", "security agency",
            "watchman", "security guard",
        ],
        "category": "security",
        "reference": "Notification 29/2018-CT(R)",
        "note": "Security services from non-body corporate under RCM",
    },
    "import": {
        "keywords": [
            "import", "imported", "foreign", "overseas",
            "international service", "cross-border",
        ],
        "category": "import",
        "reference": "IGST Act Section 5(3)",
        "note": "Import of services — recipient pays IGST under RCM",
    },
    "sponsorship": {
        "keywords": [
            "sponsorship", "sponsor", "event sponsorship",
        ],
        "category": "sponsorship",
        "reference": "Notification 13/2017-CT(R) Entry 5",
        "note": "Sponsorship services under RCM",
    },
}


def evaluate_rcm(
    description: str | None,
    seller_gstin: str | None,
    total_amount: Decimal | None,
) -> RCMEvaluation:
    """
    Evaluate whether a purchase falls under Reverse Charge Mechanism.
    This is a DRAFT evaluation — CA must confirm before filing.

    Checks:
    1. Description keywords matching RCM service categories
    2. Unregistered vendor (no GSTIN) with amount considerations

    Returns RCMEvaluation with liability and CA review flags.
    """
    desc = (description or "").lower().strip()

    # Check 1: Keyword-based RCM detection
    for _key, rule in RCM_KEYWORDS.items():
        if any(kw in desc for kw in rule["keywords"]):
            amount = Decimal(str(total_amount)) if total_amount else ZERO
            return RCMEvaluation(
                is_rcm=True,
                rcm_category=rule["category"],
                rcm_liability=amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                itc_claimable_after_payment=True,
                requires_ca_confirmation=True,
                reference=rule["reference"],
                note=rule["note"],
            )

    # Check 2: Unregistered vendor (no GSTIN)
    # Section 9(4) — currently applies to limited categories
    # Flag for CA review if no seller GSTIN
    if not seller_gstin or seller_gstin.strip() == "":
        amount = Decimal(str(total_amount)) if total_amount else ZERO
        return RCMEvaluation(
            is_rcm=False,  # Not automatically RCM
            rcm_category="unregistered_vendor",
            requires_ca_confirmation=True,  # CA must check Section 9(4) applicability
            rcm_liability=ZERO,
            reference="GST Act Section 9(4)",
            note=(
                "Unregistered vendor — CA must verify if Section 9(4) RCM applies. "
                "Currently applicable only for specified categories."
            ),
        )

    return RCMEvaluation(is_rcm=False)
