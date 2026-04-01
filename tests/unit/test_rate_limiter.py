"""
Tests for rate limiter configuration.
"""

import pytest
from unittest.mock import MagicMock

from starlette.responses import JSONResponse

from app.middleware.rate_limiter import (
    limiter,
    rate_limit_exceeded_handler,
    key_func_ip,
    key_func_ca,
)


class TestRateLimiter:
    """Tests for rate limiter module."""

    def test_limiter_instance_exists(self):
        assert limiter is not None

    def test_rate_limit_exceeded_handler_returns_429(self):
        mock_request = MagicMock()
        mock_exc = MagicMock()
        mock_exc.retry_after = 30

        response = rate_limit_exceeded_handler(mock_request, mock_exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 429

    def test_rate_limit_exceeded_handler_includes_retry_after(self):
        mock_request = MagicMock()
        mock_exc = MagicMock()
        mock_exc.retry_after = 45

        response = rate_limit_exceeded_handler(mock_request, mock_exc)

        assert response.headers.get("Retry-After") == "45"

    def test_key_func_ip_returns_remote_address(self):
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.100"
        result = key_func_ip(mock_request)
        assert result == "192.168.1.100"

    def test_key_func_ca_returns_ca_id_when_available(self):
        mock_request = MagicMock()
        mock_request.state.ca_id = "test-ca-uuid"
        result = key_func_ca(mock_request)
        assert result == "test-ca-uuid"

    def test_key_func_ca_falls_back_to_ip(self):
        mock_request = MagicMock()
        mock_request.state = MagicMock(spec=[])  # No ca_id attribute
        mock_request.client.host = "10.0.0.1"
        result = key_func_ca(mock_request)
        assert result == "10.0.0.1"
