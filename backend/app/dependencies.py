"""
VyapaarBandhu — FastAPI Dependency Injection
Async DB session + current CA authentication dependency.
"""

import uuid
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.models.ca_account import CAAccount

# auto_error=False so we can fall back to httpOnly cookie
security = HTTPBearer(auto_error=False)

# Type alias for convenience
AsyncDB = Annotated[AsyncSession, Depends(get_async_session)]


async def get_current_ca(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_async_session),
) -> CAAccount:
    """
    Decode JWT access token and return the authenticated CA account.
    Checks the Authorization header first, then falls back to the
    httpOnly access_token cookie. Raises 401 if no valid token found.
    """
    from app.utils.crypto import decode_access_token

    # Prefer Bearer header, fall back to httpOnly cookie
    token: Optional[str] = None
    if credentials:
        token = credentials.credentials
    else:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    ca_id = payload.get("sub")
    if not ca_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
        )

    try:
        ca_uuid = uuid.UUID(ca_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )

    result = await db.execute(select(CAAccount).where(CAAccount.id == ca_uuid))
    ca = result.scalar_one_or_none()

    if ca is None or not ca.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CA account not found or inactive",
        )

    return ca


# Type alias for authenticated CA
CurrentCA = Annotated[CAAccount, Depends(get_current_ca)]


def get_correlation_id(request: Request) -> str:
    """Extract correlation ID from request state."""
    return getattr(request.state, "correlation_id", "unknown")
