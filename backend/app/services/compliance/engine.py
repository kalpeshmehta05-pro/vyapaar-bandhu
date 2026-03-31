"""
VyapaarBandhu — GST Compliance Engine (Pure Python — No AI)
Main entry point for invoice ITC evaluation.

CRITICAL: This file must NEVER import any ML/AI library.
Every function must be traceable to a specific GST Act section.

GST Act references:
- ITC eligibility: Section 16
- Blocked credits: Section 17(5)
- Inter-state supply: IGST Act Section 5
- Composition scheme: Section 10(4)
- Reverse Charge: Section 9(3), 9(4)
"""

from dataclasses import dataclass, field
from decimal import Decimal

from app.services.compliance.blocked_categories import is_section_17_5_blocked
from app.services.compliance.gstin_state_mapper import is_interstate_transaction
from app.services.compliance.itc_calculator import calculate_itc_amounts
from app.services.compliance.rcm import evaluate_rcm

ZERO = Decimal("0.00")


@dataclass
class InvoiceData:
    """Input data for ITC evaluation. Populated from Invoice model."""
    seller_gstin: str | None = None
    category: str | None = None
    product_description: str | None = None
    taxable_amount: Decimal = ZERO
    cgst_amount: Decimal = ZERO
    sgst_amount: Decimal = ZERO
    igst_amount: Decimal = ZERO
    total_amount: Decimal = ZERO


@dataclass
class ClientData:
    """Input data for ITC evaluation. Populated from Client model."""
    gstin: str | None = None
    business_type: str = "trader"
    primary_activity: str | None = None
    is_composition: bool = False


@dataclass
class ITCEvaluation:
    """Output of invoice ITC evaluation. All figures are DRAFT pending CA approval."""
    is_draft: bool = True
    is_eligible: bool = False
    blocked_reason: str | None = None
    blocked_reference: str | None = None
    ca_override_required: bool = False
    requires_ca_end_use_confirmation: bool = False
    ca_review_note: str | None = None
    transaction_type: str | None = None  # "interstate" | "intrastate"
    draft_cgst_itc: Decimal = ZERO
    draft_sgst_itc: Decimal = ZERO
    draft_igst_itc: Decimal = ZERO
    draft_total_itc: Decimal = ZERO
    # RCM
    is_rcm: bool = False
    rcm_category: str | None = None
    rcm_liability: Decimal = ZERO
    rcm_note: str | None = None


def evaluate_invoice_itc(invoice: InvoiceData, client: ClientData) -> ITCEvaluation:
    """
    Evaluate ITC eligibility for a single invoice.
    Returns a DRAFT evaluation — to be confirmed by CA.

    This function is 100% deterministic Python. Zero AI involvement.
    """
    evaluation = ITCEvaluation(is_draft=True)

    # ── Check 1: Composition scheme — no ITC ──────────────────────
    # Reference: GST Act Section 10(4)
    if client.is_composition:
        evaluation.is_eligible = False
        evaluation.blocked_reason = "composition_scheme"
        evaluation.blocked_reference = "GST Act Section 10(4)"
        return evaluation

    # ── Check 2: RCM evaluation ───────────────────────────────────
    rcm = evaluate_rcm(
        description=invoice.product_description,
        seller_gstin=invoice.seller_gstin,
        total_amount=invoice.total_amount,
    )
    if rcm.is_rcm:
        evaluation.is_rcm = True
        evaluation.rcm_category = rcm.rcm_category
        evaluation.rcm_liability = rcm.rcm_liability
        evaluation.rcm_note = rcm.note
        evaluation.ca_override_required = True
        evaluation.ca_review_note = (
            f"RCM applicable: {rcm.note}. "
            "ITC claimable only after RCM tax is paid to government. "
            "CA must confirm RCM applicability and tax payment."
        )
    elif rcm.requires_ca_confirmation:
        evaluation.rcm_category = rcm.rcm_category
        evaluation.rcm_note = rcm.note
        evaluation.ca_review_note = rcm.note

    # ── Check 3: Section 17(5) blocked categories ─────────────────
    if invoice.category:
        blocked = is_section_17_5_blocked(
            category=invoice.category,
            business_type=client.business_type,
            primary_activity=client.primary_activity,
        )
        if blocked.is_blocked:
            evaluation.is_eligible = False
            evaluation.blocked_reason = blocked.reason
            evaluation.blocked_reference = blocked.reference
            evaluation.ca_override_required = blocked.can_ca_override
            return evaluation

        if blocked.requires_ca_review:
            evaluation.ca_override_required = True
            evaluation.ca_review_note = blocked.reason

    # ── Check 4: Capital goods — flag for CA end-use review ───────
    if invoice.category == "capital_goods":
        evaluation.requires_ca_end_use_confirmation = True
        evaluation.ca_review_note = (
            "Capital goods ITC eligibility depends on end-use. "
            "CA must confirm business use before approving."
        )

    # ── Check 5: Calculate ITC amounts ────────────────────────────
    is_interstate = is_interstate_transaction(
        seller_gstin=invoice.seller_gstin,
        buyer_gstin=client.gstin,
    )

    itc = calculate_itc_amounts(
        cgst=invoice.cgst_amount,
        sgst=invoice.sgst_amount,
        igst=invoice.igst_amount,
        is_interstate=is_interstate,
    )

    evaluation.is_eligible = True
    evaluation.draft_cgst_itc = itc.cgst
    evaluation.draft_sgst_itc = itc.sgst
    evaluation.draft_igst_itc = itc.igst
    evaluation.draft_total_itc = itc.total
    evaluation.transaction_type = "interstate" if is_interstate else "intrastate"

    return evaluation
