"""
VyapaarBandhu — Compliance Engine Unit Tests
Every GST rule has at least 3 test cases:
(1) clear eligible, (2) clear blocked, (3) edge case

Target: 100% coverage on compliance/engine.py
"""

from decimal import Decimal

import pytest

from app.services.compliance.engine import (
    ClientData,
    InvoiceData,
    evaluate_invoice_itc,
)


def _make_invoice(**kwargs) -> InvoiceData:
    defaults = {
        "seller_gstin": "27AAPFU0939F1ZV",
        "category": "office_supplies",
        "product_description": "Printer paper A4",
        "taxable_amount": Decimal("10000"),
        "cgst_amount": Decimal("900"),
        "sgst_amount": Decimal("900"),
        "igst_amount": Decimal("0"),
        "total_amount": Decimal("11800"),
    }
    defaults.update(kwargs)
    return InvoiceData(**defaults)


def _make_client(**kwargs) -> ClientData:
    defaults = {
        "gstin": "27YYYYY5678Y1Z3",
        "business_type": "trader",
        "primary_activity": None,
        "is_composition": False,
    }
    defaults.update(kwargs)
    return ClientData(**defaults)


class TestCompositionScheme:
    """GST Act Section 10(4) — Composition scheme taxpayers cannot claim ITC."""

    def test_composition_no_itc(self):
        result = evaluate_invoice_itc(
            _make_invoice(taxable_amount=Decimal("10000"), cgst_amount=Decimal("900")),
            _make_client(is_composition=True),
        )
        assert result.is_eligible is False
        assert result.blocked_reason == "composition_scheme"
        assert "10(4)" in result.blocked_reference

    def test_non_composition_eligible(self):
        result = evaluate_invoice_itc(
            _make_invoice(),
            _make_client(is_composition=False),
        )
        assert result.is_eligible is True

    def test_composition_ignores_category(self):
        """Even eligible categories are blocked for composition taxpayers."""
        result = evaluate_invoice_itc(
            _make_invoice(category="office_supplies"),
            _make_client(is_composition=True),
        )
        assert result.is_eligible is False
        assert result.blocked_reason == "composition_scheme"


class TestSection17_5_Blocked:
    """GST Act Section 17(5) — Blocked ITC categories."""

    def test_food_blocked_for_trader(self):
        result = evaluate_invoice_itc(
            _make_invoice(category="food_and_beverages"),
            _make_client(business_type="trader"),
        )
        assert result.is_eligible is False
        assert "17(5)" in (result.blocked_reference or "")

    def test_food_eligible_for_restaurant(self):
        result = evaluate_invoice_itc(
            _make_invoice(category="food_and_beverages"),
            _make_client(business_type="service_provider", primary_activity="restaurant"),
        )
        assert result.is_eligible is True
        assert result.ca_override_required is True  # Exception needs CA confirmation

    def test_personal_clothing_always_blocked(self):
        result = evaluate_invoice_itc(
            _make_invoice(category="personal_clothing"),
            _make_client(business_type="retailer"),
        )
        assert result.is_eligible is False

    def test_office_supplies_eligible(self):
        result = evaluate_invoice_itc(
            _make_invoice(category="office_supplies"),
            _make_client(business_type="trader"),
        )
        assert result.is_eligible is True

    def test_health_blocked_for_trader(self):
        result = evaluate_invoice_itc(
            _make_invoice(category="health_and_wellness"),
            _make_client(business_type="trader"),
        )
        assert result.is_eligible is False

    def test_health_eligible_for_hospital(self):
        result = evaluate_invoice_itc(
            _make_invoice(category="health_and_wellness"),
            _make_client(business_type="service_provider", primary_activity="hospital"),
        )
        assert result.is_eligible is True
        assert result.ca_override_required is True


class TestCapitalGoods:
    """Capital goods ITC depends on end-use — CA must confirm."""

    def test_capital_goods_requires_ca_confirmation(self):
        result = evaluate_invoice_itc(
            _make_invoice(category="capital_goods"),
            _make_client(business_type="manufacturer"),
        )
        assert result.is_eligible is True
        assert result.requires_ca_end_use_confirmation is True
        assert "end-use" in result.ca_review_note.lower()

    def test_capital_goods_blocked_for_composition(self):
        result = evaluate_invoice_itc(
            _make_invoice(category="capital_goods"),
            _make_client(is_composition=True),
        )
        assert result.is_eligible is False
        assert result.blocked_reason == "composition_scheme"


class TestIGSTvsCGSTSGST:
    """Inter-state vs intra-state transaction detection."""

    def test_inter_state_uses_igst(self):
        """Seller in Maharashtra (27), buyer in Gujarat (24)."""
        result = evaluate_invoice_itc(
            _make_invoice(
                seller_gstin="27XXXXX1234X1ZV",
                igst_amount=Decimal("1800"),
                cgst_amount=Decimal("0"),
                sgst_amount=Decimal("0"),
            ),
            _make_client(gstin="24YYYYY5678Y1Z3"),
        )
        assert result.transaction_type == "interstate"
        assert result.draft_igst_itc == Decimal("1800.00")
        assert result.draft_cgst_itc == Decimal("0.00")
        assert result.draft_sgst_itc == Decimal("0.00")

    def test_intra_state_uses_cgst_sgst(self):
        """Seller and buyer both in Gujarat (24)."""
        result = evaluate_invoice_itc(
            _make_invoice(
                seller_gstin="24XXXXX1234X1ZV",
                cgst_amount=Decimal("900"),
                sgst_amount=Decimal("900"),
                igst_amount=Decimal("0"),
            ),
            _make_client(gstin="24YYYYY5678Y1Z3"),
        )
        assert result.transaction_type == "intrastate"
        assert result.draft_cgst_itc == Decimal("900.00")
        assert result.draft_sgst_itc == Decimal("900.00")
        assert result.draft_igst_itc == Decimal("0.00")

    def test_missing_buyer_gstin_defaults_intrastate(self):
        """Conservative default when GSTIN is missing."""
        result = evaluate_invoice_itc(
            _make_invoice(cgst_amount=Decimal("500"), sgst_amount=Decimal("500")),
            _make_client(gstin=None),
        )
        assert result.transaction_type == "intrastate"

    def test_total_itc_calculation(self):
        result = evaluate_invoice_itc(
            _make_invoice(
                cgst_amount=Decimal("450.55"),
                sgst_amount=Decimal("450.55"),
                igst_amount=Decimal("0"),
            ),
            _make_client(),
        )
        assert result.draft_total_itc == Decimal("901.10")


class TestRCM:
    """Reverse Charge Mechanism detection."""

    def test_gta_detected_as_rcm(self):
        result = evaluate_invoice_itc(
            _make_invoice(
                product_description="Goods Transport Agency freight charges",
                total_amount=Decimal("5000"),
            ),
            _make_client(),
        )
        assert result.is_rcm is True
        assert result.rcm_category == "gta"

    def test_legal_services_rcm(self):
        result = evaluate_invoice_itc(
            _make_invoice(product_description="Legal service advocate fees"),
            _make_client(),
        )
        assert result.is_rcm is True
        assert result.rcm_category == "legal"

    def test_normal_purchase_not_rcm(self):
        result = evaluate_invoice_itc(
            _make_invoice(product_description="Dell laptop computer"),
            _make_client(),
        )
        assert result.is_rcm is False

    def test_unregistered_vendor_flags_ca_review(self):
        result = evaluate_invoice_itc(
            _make_invoice(seller_gstin=None, product_description="Office furniture"),
            _make_client(),
        )
        assert result.rcm_category == "unregistered_vendor"


class TestDraftLabeling:
    """Every evaluation must be labeled as draft."""

    def test_all_results_are_draft(self):
        result = evaluate_invoice_itc(_make_invoice(), _make_client())
        assert result.is_draft is True

    def test_blocked_result_is_draft(self):
        result = evaluate_invoice_itc(
            _make_invoice(category="personal_clothing"),
            _make_client(),
        )
        assert result.is_draft is True
