"""
VyapaarBandhu — ITC Calculator Unit Tests
Decimal precision tests for tax amount calculations.
"""

from decimal import Decimal

import pytest

from app.services.compliance.itc_calculator import ITCAmounts, calculate_itc_amounts


class TestIntraStateITC:
    def test_basic_cgst_sgst(self):
        result = calculate_itc_amounts(
            cgst=Decimal("900"), sgst=Decimal("900"), igst=Decimal("0"),
            is_interstate=False,
        )
        assert result.cgst == Decimal("900.00")
        assert result.sgst == Decimal("900.00")
        assert result.igst == Decimal("0.00")
        assert result.total == Decimal("1800.00")

    def test_decimal_precision(self):
        result = calculate_itc_amounts(
            cgst=Decimal("450.555"), sgst=Decimal("450.555"), igst=None,
            is_interstate=False,
        )
        # ROUND_HALF_UP: 450.555 -> 450.56
        assert result.cgst == Decimal("450.56")
        assert result.sgst == Decimal("450.56")
        assert result.total == Decimal("901.12")

    def test_none_values_become_zero(self):
        result = calculate_itc_amounts(
            cgst=None, sgst=None, igst=None,
            is_interstate=False,
        )
        assert result.total == Decimal("0.00")


class TestInterStateITC:
    def test_basic_igst(self):
        result = calculate_itc_amounts(
            cgst=Decimal("0"), sgst=Decimal("0"), igst=Decimal("1800"),
            is_interstate=True,
        )
        assert result.igst == Decimal("1800.00")
        assert result.cgst == Decimal("0.00")
        assert result.sgst == Decimal("0.00")
        assert result.total == Decimal("1800.00")

    def test_igst_with_decimal(self):
        result = calculate_itc_amounts(
            cgst=Decimal("0"), sgst=Decimal("0"), igst=Decimal("6062.035"),
            is_interstate=True,
        )
        # ROUND_HALF_UP: 6062.035 -> 6062.04
        assert result.igst == Decimal("6062.04")
        assert result.total == Decimal("6062.04")

    def test_interstate_ignores_cgst_sgst(self):
        """Even if CGST/SGST are provided, interstate uses IGST only."""
        result = calculate_itc_amounts(
            cgst=Decimal("500"), sgst=Decimal("500"), igst=Decimal("1000"),
            is_interstate=True,
        )
        assert result.igst == Decimal("1000.00")
        assert result.cgst == Decimal("0.00")
        assert result.total == Decimal("1000.00")


class TestEdgeCases:
    def test_negative_values_become_zero(self):
        result = calculate_itc_amounts(
            cgst=Decimal("-100"), sgst=Decimal("200"), igst=Decimal("0"),
            is_interstate=False,
        )
        assert result.cgst == Decimal("0.00")
        assert result.sgst == Decimal("200.00")
        assert result.total == Decimal("200.00")

    def test_zero_amounts(self):
        result = calculate_itc_amounts(
            cgst=Decimal("0"), sgst=Decimal("0"), igst=Decimal("0"),
            is_interstate=False,
        )
        assert result.total == Decimal("0.00")

    def test_large_amounts(self):
        result = calculate_itc_amounts(
            cgst=Decimal("9999999999999.99"),
            sgst=Decimal("0.01"),
            igst=Decimal("0"),
            is_interstate=False,
        )
        assert result.total == Decimal("10000000000000.00")
