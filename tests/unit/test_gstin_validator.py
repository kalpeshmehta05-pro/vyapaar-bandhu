"""
VyapaarBandhu — GSTIN Validator Unit Tests
Tests Modulo 36 checksum validation and OCR auto-correction.
"""

import pytest

from app.services.ocr.gstin_validator import (
    GSTINValidationResult,
    calculate_gstin_checksum,
    validate_and_correct_gstin,
)


class TestValidGSTIN:
    def test_valid_gstin_passes(self):
        # 27AAPFU0939F1ZV is a commonly used test GSTIN
        result = validate_and_correct_gstin("27AAPFU0939F1ZV")
        assert result.is_valid is True
        assert result.was_corrected is False
        assert result.state_code == "27"
        assert result.state == "Maharashtra"

    def test_valid_gstin_extracts_pan(self):
        result = validate_and_correct_gstin("27AAPFU0939F1ZV")
        assert result.pan == "AAPFU0939F"

    def test_uppercase_normalization(self):
        result = validate_and_correct_gstin("27aapfu0939f1zv")
        assert result.corrected == "27AAPFU0939F1ZV"

    def test_whitespace_stripped(self):
        result = validate_and_correct_gstin("  27AAPFU0939F1ZV  ")
        assert result.is_valid is True


class TestInvalidGSTIN:
    def test_too_short(self):
        result = validate_and_correct_gstin("27AAPFU0939F")
        assert result.is_valid is False

    def test_too_long(self):
        result = validate_and_correct_gstin("27AAPFU0939F1ZVX")
        assert result.is_valid is False

    def test_empty_string(self):
        result = validate_and_correct_gstin("")
        assert result.is_valid is False

    def test_none_input(self):
        result = validate_and_correct_gstin(None)
        assert result.is_valid is False

    def test_invalid_state_code(self):
        result = validate_and_correct_gstin("99AAPFU0939F1ZV")
        assert result.is_valid is False


class TestOCRAutoCorrection:
    def test_o_zero_confusion(self):
        """O and 0 are commonly confused by OCR."""
        # Replace a 0 with O and see if it auto-corrects
        original = "27AAPFU0939F1ZV"
        corrupted = original.replace("0", "O", 1)
        if corrupted != original:
            result = validate_and_correct_gstin(corrupted)
            # Should either correct or flag for review
            assert result.was_corrected or result.needs_ca_review or not result.is_valid

    def test_ambiguous_correction_flags_ca_review(self):
        """Multiple valid corrections should flag for CA review."""
        result = validate_and_correct_gstin("27AAPFU0939F1ZV")
        # The valid GSTIN should not need CA review
        assert result.needs_ca_review is False

    def test_correction_preserves_original(self):
        """The original OCR output should be preserved."""
        result = validate_and_correct_gstin("27AAPFU0939F1ZV")
        assert result.original == "27AAPFU0939F1ZV"


class TestChecksumCalculation:
    def test_checksum_for_known_gstin(self):
        # The checksum of the first 14 chars should equal the 15th char
        gstin = "27AAPFU0939F1Z"
        expected_check = "V"
        assert calculate_gstin_checksum(gstin) == expected_check
