"""
VyapaarBandhu — FastAPI Application Factory
Async, structured logging, correlation ID injection, CORS with explicit origins.
"""

import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.middleware.rate_limiter import limiter, rate_limit_exceeded_handler
from app.middleware.security_headers import SecurityHeadersMiddleware

logger = structlog.get_logger()


# ── Correlation ID Middleware ──────────────────────────────────────────────

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Inject a correlation ID into every request for distributed tracing."""

    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        # Store in request state for downstream access
        request.state.correlation_id = correlation_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        response: Response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


# ── Request Logging Middleware ─────────────────────────────────────────────

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next):
        import time

        start = time.monotonic()
        response: Response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        logger.info(
            "http.request",
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response


# ── Structured Logging Configuration ──────────────────────────────────────

def configure_logging():
    """Configure structlog for JSON output. No print() allowed in production."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            structlog.get_level_from_name(settings.LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


# ── Lifespan ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    configure_logging()
    logger.info("app.startup", env=settings.APP_ENV, version=settings.APP_VERSION)
    yield
    logger.info("app.shutdown")


# ── App Factory ───────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="VyapaarBandhu",
        description="GST Document Management & Draft Preparation System for Indian SMEs",
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # ── Rate Limiter ──────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # ── Middleware (order matters — outermost first) ────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIDMiddleware)

    # ── Routes ─────────────────────────────────────────────────────────
    from app.api.v1.router import api_v1_router
    app.include_router(api_v1_router, prefix="/api/v1")

    # ── Health checks ──────────────────────────────────────────────────
    @app.get("/health/live", tags=["Health"])
    async def liveness():
        return {"status": "ok"}

    @app.get("/health/ready", tags=["Health"])
    async def readiness():
        # TODO: Check DB + Redis connectivity
        return {"status": "ok"}

    return app


app = create_app()
