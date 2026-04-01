"""
VyapaarBandhu -- Rate Limiting Middleware
Uses slowapi for per-IP and per-CA rate limiting.
"""

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi import Request
from starlette.responses import JSONResponse


def _get_ca_id_or_ip(request: Request) -> str:
    """
    Extract the CA ID from request state (set by auth dependency) or
    fall back to remote IP for unauthenticated endpoints.
    """
    # After auth dependency runs, ca_id may be stored in request state
    ca_id = getattr(request.state, "ca_id", None)
    if ca_id:
        return str(ca_id)
    return get_remote_address(request)


limiter = Limiter(key_func=get_remote_address)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom 429 response with retry information."""
    retry_after = getattr(exc, "retry_after", 60)
    return JSONResponse(
        status_code=429,
        content={"detail": f"Too many requests. Try again in {retry_after}s"},
        headers={"Retry-After": str(retry_after)},
    )


# Key functions for different rate limit strategies
def key_func_ip(request: Request) -> str:
    """Rate limit by IP address."""
    return get_remote_address(request)


def key_func_ca(request: Request) -> str:
    """Rate limit by CA ID (falls back to IP if unauthenticated)."""
    return _get_ca_id_or_ip(request)
