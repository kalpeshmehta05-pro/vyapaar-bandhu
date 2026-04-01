"""
Tests for security headers middleware.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.middleware.security_headers import SecurityHeadersMiddleware


class TestSecurityHeadersMiddleware:
    """Tests for SecurityHeadersMiddleware."""

    def test_headers_dict_contains_hsts(self):
        assert "Strict-Transport-Security" in SecurityHeadersMiddleware.HEADERS
        assert "31536000" in SecurityHeadersMiddleware.HEADERS["Strict-Transport-Security"]

    def test_headers_dict_contains_x_frame_options(self):
        assert SecurityHeadersMiddleware.HEADERS["X-Frame-Options"] == "DENY"

    def test_headers_dict_contains_content_type_options(self):
        assert SecurityHeadersMiddleware.HEADERS["X-Content-Type-Options"] == "nosniff"

    def test_headers_dict_contains_xss_protection(self):
        assert "1; mode=block" in SecurityHeadersMiddleware.HEADERS["X-XSS-Protection"]

    def test_headers_dict_contains_referrer_policy(self):
        assert SecurityHeadersMiddleware.HEADERS["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_headers_dict_contains_csp(self):
        csp = SecurityHeadersMiddleware.HEADERS["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "style-src 'self'" in csp

    def test_all_required_headers_present(self):
        required = [
            "Strict-Transport-Security",
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Content-Security-Policy",
        ]
        for header in required:
            assert header in SecurityHeadersMiddleware.HEADERS, f"Missing header: {header}"
