"""
VyapaarBandhu — Cryptographic Utilities
JWT RS256 token generation/verification, password hashing, secure random tokens.

Key loading priority:
1. JWT_PRIVATE_KEY / JWT_PUBLIC_KEY env vars (raw PEM string — production via Secrets Manager)
2. JWT_PRIVATE_KEY_PATH / JWT_PUBLIC_KEY_PATH file paths (development via mounted volume)

NEVER generate keys at Docker build time — that invalidates all JWTs on every deploy.
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import structlog

from app.config import settings

logger = structlog.get_logger()

# ── Lazy-loaded RSA keys ──────────────────────────────────────────────────

_private_key: bytes | None = None
_public_key: bytes | None = None


def _load_private_key() -> bytes:
    """
    Load RSA private key. Priority:
    1. JWT_PRIVATE_KEY env var (raw PEM — for production)
    2. JWT_PRIVATE_KEY_PATH file (for development)
    """
    global _private_key
    if _private_key is not None:
        return _private_key

    # Priority 1: PEM content from settings (env var JWT_PRIVATE_KEY)
    if settings.JWT_PRIVATE_KEY:
        _private_key = settings.JWT_PRIVATE_KEY.encode()
        return _private_key

    # Priority 2: file path
    path = Path(settings.JWT_PRIVATE_KEY_PATH)
    if path.exists():
        _private_key = path.read_bytes()
        return _private_key

    raise FileNotFoundError(
        "JWT private key not found. Set JWT_PRIVATE_KEY env var (PEM string) "
        f"or create file at {path}. "
        "Run: openssl genrsa -out keys/private.pem 2048"
    )


def _load_public_key() -> bytes:
    """
    Load RSA public key. Priority:
    1. JWT_PUBLIC_KEY env var (raw PEM — for production)
    2. JWT_PUBLIC_KEY_PATH file (for development)
    """
    global _public_key
    if _public_key is not None:
        return _public_key

    # Priority 1: PEM content from settings (env var JWT_PUBLIC_KEY)
    if settings.JWT_PUBLIC_KEY:
        _public_key = settings.JWT_PUBLIC_KEY.encode()
        return _public_key

    # Priority 2: file path
    path = Path(settings.JWT_PUBLIC_KEY_PATH)
    if path.exists():
        _public_key = path.read_bytes()
        return _public_key

    raise FileNotFoundError(
        "JWT public key not found. Set JWT_PUBLIC_KEY env var (PEM string) "
        f"or create file at {path}. "
        "Run: openssl rsa -in keys/private.pem -pubout -out keys/public.pem"
    )


# ── JWT Access Tokens (RS256) ─────────────────────────────────────────────

def create_access_token(ca_id: uuid.UUID, email: str) -> str:
    """Create a short-lived RS256 JWT access token (15 minutes)."""
    import jwt

    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(ca_id),
        "email": email,
        "iat": now,
        "exp": now + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRY),
        "type": "access",
    }
    return jwt.encode(payload, _load_private_key(), algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Decode and verify an RS256 JWT access token. Returns None on failure."""
    import jwt

    try:
        payload = jwt.decode(
            token,
            _load_public_key(),
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("jwt.expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug("jwt.invalid", error=str(e))
        return None


# ── Refresh Tokens ────────────────────────────────────────────────────────

def generate_refresh_token() -> str:
    """Generate a cryptographically secure random refresh token."""
    return secrets.token_urlsafe(64)


# ── Password Hashing (bcrypt, 12 rounds) ──────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password with bcrypt. ~250ms at 12 rounds."""
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ── Token Hashing (for refresh token storage) ─────────────────────────────

def hash_token(token: str) -> str:
    """Hash a refresh token for database storage. SHA-256 is sufficient here."""
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()
