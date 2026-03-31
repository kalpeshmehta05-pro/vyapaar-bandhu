"""
VyapaarBandhu — FastAPI Dependency Injection
Async DB session + current CA authentication dependency.
"""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.models.ca_account import CAAccount

security = HTTPBearer()

# Type alias for convenience
AsyncDB = Annotated[AsyncSession, Depends(get_async_session)]


async def get_current_ca(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session),
) -> CAAccount:
    """
    Decode JWT access token and return the authenticated CA account.
    Raises 401 if token is invalid, expired, or CA is inactive.
    """
    from app.utils.crypto import decode_access_token

    token = credentials.credentials
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
