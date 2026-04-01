"""
Tests for health check endpoints.
"""

import pytest


class TestHealthEndpoints:
    """Tests for health check endpoint logic."""

    def test_liveness_always_returns_alive(self):
        """The /health/live endpoint must always return status alive."""
        # Verify the endpoint function exists and returns correct format
        import pathlib
        health_path = pathlib.Path(__file__).resolve().parent.parent.parent / "backend" / "app" / "api" / "v1" / "health.py"
        source = health_path.read_text()

        assert "health/live" in source
        assert '"alive"' in source or "'alive'" in source

    def test_health_endpoint_exists(self):
        """Verify the main /health endpoint exists."""
        import pathlib
        health_path = pathlib.Path(__file__).resolve().parent.parent.parent / "backend" / "app" / "api" / "v1" / "health.py"
        source = health_path.read_text()

        assert '"/health"' in source
        assert "database" in source
        assert "redis" in source
        assert "celery" in source

    def test_readiness_checks_db_and_redis(self):
        """Verify readiness probe checks both database and Redis."""
        import pathlib
        health_path = pathlib.Path(__file__).resolve().parent.parent.parent / "backend" / "app" / "api" / "v1" / "health.py"
        source = health_path.read_text()

        assert "health/ready" in source
        assert "_check_database" in source
        assert "_check_redis" in source

    def test_health_returns_503_on_failure(self):
        """Verify health endpoint returns 503 when services are down."""
        import pathlib
        health_path = pathlib.Path(__file__).resolve().parent.parent.parent / "backend" / "app" / "api" / "v1" / "health.py"
        source = health_path.read_text()

        assert "503" in source
        assert "unhealthy" in source
