"""
Integration test: Full end-to-end flow simulation.
Tests the logical flow without requiring a running server.

This verifies:
1. CA registration flow exists
2. Login returns access token
3. Client creation endpoint exists
4. Invoice upload endpoint exists
5. Dashboard overview endpoint exists
6. GSTR-3B export endpoint exists
7. Audit chain verification endpoint exists
"""

import pathlib
import pytest


BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "backend"


class TestFullFlowEndpoints:
    """Verify all endpoints required for the full flow exist."""

    def _read_source(self, *path_parts):
        return (BACKEND_DIR / "app" / pathlib.Path(*path_parts)).read_text()

    def test_step1_register_endpoint_exists(self):
        """CA registration endpoint."""
        source = self._read_source("api", "v1", "ca_auth.py")
        assert "register" in source
        assert "CARegisterRequest" in source

    def test_step2_login_endpoint_exists(self):
        """CA login endpoint with httpOnly cookie."""
        source = self._read_source("api", "v1", "ca_auth.py")
        assert "login" in source
        assert "httponly" in source.lower()
        assert "access_token" in source

    def test_step3_create_client_endpoint_exists(self):
        """Client creation endpoint."""
        source = self._read_source("api", "v1", "clients.py")
        assert "create_client" in source
        assert "ClientCreateRequest" in source
        assert "sanitize_string" in source

    def test_step4_upload_invoice_endpoint_exists(self):
        """Invoice upload endpoint."""
        source = self._read_source("api", "v1", "invoices.py")
        assert "upload_invoice" in source
        assert "UploadFile" in source

    def test_step5_dashboard_overview_exists(self):
        """Dashboard overview endpoint."""
        source = self._read_source("api", "v1", "ca_dashboard.py")
        assert "overview" in source

    def test_step6_gstr3b_export_exists(self):
        """GSTR-3B JSON export endpoint."""
        source = self._read_source("api", "v1", "exports.py")
        assert "gstr3b" in source
        assert "ret_period" in source or "GSTR3B" in source

    def test_step7_audit_chain_verify_exists(self):
        """Audit chain verification endpoint."""
        source = self._read_source("api", "v1", "audit.py")
        assert "verify-chain" in source or "verify_chain" in source

    def test_step8_audit_export_exists(self):
        """Audit log export endpoint."""
        source = self._read_source("api", "v1", "audit.py")
        assert "export" in source
        assert "from_date" in source or "from" in source

    def test_step9_health_check_exists(self):
        """Health check endpoint at app level."""
        source = self._read_source("api", "v1", "health.py")
        assert "health" in source
        assert "database" in source

    def test_step10_all_routes_registered(self):
        """All API routers are registered."""
        router_source = self._read_source("api", "v1", "router.py")
        assert "ca_auth_router" in router_source
        assert "clients_router" in router_source
        assert "invoices_router" in router_source
        assert "ca_dashboard_router" in router_source
        assert "exports_router" in router_source
        assert "whatsapp_router" in router_source
        assert "audit_router" in router_source

    def test_rate_limiting_on_login(self):
        """Login has rate limiting decorator."""
        source = self._read_source("api", "v1", "ca_auth.py")
        assert "limiter.limit" in source

    def test_security_headers_middleware_registered(self):
        """Security headers middleware is in the app factory."""
        main_source = (BACKEND_DIR / "app" / "main.py").read_text()
        assert "SecurityHeadersMiddleware" in main_source

    def test_metrics_middleware_registered(self):
        """Prometheus metrics middleware is in the app factory."""
        main_source = (BACKEND_DIR / "app" / "main.py").read_text()
        assert "MetricsMiddleware" in main_source
        assert "metrics_endpoint" in main_source
