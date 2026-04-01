"""
VyapaarBandhu -- Security Headers Middleware
Adds security headers to every HTTP response.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject security headers into every response."""

    HEADERS = {
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.twilio.com"
        ),
    }

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        for header, value in self.HEADERS.items():
            response.headers[header] = value
        return response
