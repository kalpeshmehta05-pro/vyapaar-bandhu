"""
VyapaarBandhu -- Prometheus Metrics Middleware
Exposes request counts, durations, and business metrics.
"""

import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


if PROMETHEUS_AVAILABLE:
    HTTP_REQUESTS_TOTAL = Counter(
        "vyapaar_http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status"],
    )

    HTTP_DURATION_SECONDS = Histogram(
        "vyapaar_http_duration_seconds",
        "HTTP request duration in seconds",
        ["method", "path"],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    )

    OCR_TASKS_TOTAL = Counter(
        "vyapaar_ocr_tasks_total",
        "Total OCR tasks processed",
        ["status"],
    )

    ACTIVE_CELERY_WORKERS = Gauge(
        "vyapaar_active_celery_workers",
        "Number of active Celery workers",
    )

    INVOICES_PROCESSED_TOTAL = Counter(
        "vyapaar_invoices_processed_total",
        "Total invoices processed",
    )


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record HTTP request metrics for Prometheus."""

    async def dispatch(self, request: Request, call_next):
        if not PROMETHEUS_AVAILABLE:
            return await call_next(request)

        start = time.monotonic()
        response: Response = await call_next(request)
        duration = time.monotonic() - start

        # Normalize path to avoid cardinality explosion
        path = request.url.path
        if "/clients/" in path or "/invoices/" in path:
            # Replace UUIDs with placeholder
            parts = path.split("/")
            normalized = []
            for part in parts:
                if len(part) == 36 and "-" in part:
                    normalized.append("{id}")
                else:
                    normalized.append(part)
            path = "/".join(normalized)

        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            path=path,
            status=response.status_code,
        ).inc()

        HTTP_DURATION_SECONDS.labels(
            method=request.method,
            path=path,
        ).observe(duration)

        return response


def metrics_endpoint():
    """Generate Prometheus metrics output."""
    if not PROMETHEUS_AVAILABLE:
        from starlette.responses import PlainTextResponse
        return PlainTextResponse("prometheus_client not installed", status_code=501)

    from starlette.responses import Response
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
