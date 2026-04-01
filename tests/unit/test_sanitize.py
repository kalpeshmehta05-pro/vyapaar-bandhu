"""
Tests for input sanitization utility.
"""

import pytest

from app.utils.sanitize import sanitize_string


class TestSanitizeString:
    """Tests for sanitize_string()."""

    def test_strips_html_tags(self):
        result = sanitize_string("<b>Hello</b> World", 200)
        assert result == "Hello World"

    def test_strips_script_tags(self):
        result = sanitize_string("<script>alert('xss')</script>World", 200)
        assert "<script>" not in result
        assert "</script>" not in result

    def test_removes_null_bytes(self):
        result = sanitize_string("Hello\x00World", 200)
        assert result == "HelloWorld"

    def test_strips_whitespace(self):
        result = sanitize_string("  Hello World  ", 200)
        assert result == "Hello World"

    def test_enforces_max_length(self):
        result = sanitize_string("A" * 300, 200)
        assert len(result) == 200

    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError, match="empty after sanitization"):
            sanitize_string("   ", 200)

    def test_only_html_tags_raises_value_error(self):
        with pytest.raises(ValueError, match="empty after sanitization"):
            sanitize_string("<div></div>", 200)

    def test_only_null_bytes_raises_value_error(self):
        with pytest.raises(ValueError, match="empty after sanitization"):
            sanitize_string("\x00\x00\x00", 200)

    def test_non_string_raises_value_error(self):
        with pytest.raises(ValueError, match="Input must be a string"):
            sanitize_string(123, 200)  # type: ignore

    def test_normal_string_passes_through(self):
        result = sanitize_string("Mehta & Associates", 200)
        assert result == "Mehta & Associates"

    def test_mixed_html_and_text(self):
        result = sanitize_string('Client <img src="x" onerror="alert(1)"> Name', 200)
        assert result == "Client  Name"

    def test_truncation_with_trailing_whitespace(self):
        # After truncation at 10, trailing space should be stripped
        result = sanitize_string("Hello     World", 10)
        assert result == "Hello"
        assert len(result) <= 10
