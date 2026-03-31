"""
VyapaarBandhu — CA Authentication Endpoints
RS256 JWT, refresh token rotation, httpOnly cookies.
"""

import uuid
from datetime import datetime, timedelta, timezone

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_async_session
from app.dependencies import CurrentCA
from app.models.ca_account import CAAccount
from app.models.refresh_token import RefreshToken
from app.schemas.ca import (
    CALoginRequest,
    CAProfileResponse,
    CAProfileUpdateRequest,
    CARegisterRequest,
    CATokenResponse,
)
from app.utils.audit import write_audit_log
from app.utils.crypto import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.utils.phone import normalize_phone

logger = structlog.get_logger()
router = APIRouter()

# ── Rate limit tracking (Redis-backed in production) ──────────────────
# TODO: Replace with Redis counter in Phase 8 hardening
_login_attempts: dict[str, list[float]] = {}


def _check_rate_limit(key: str, max_attempts: int, window_seconds: int) -> None:
    """Simple in-memory rate limiter. Replace with Redis in Phase 8."""
    import time
    now = time.time()
    attempts = _login_attempts.get(key, [])
    attempts = [t for t in attempts if now - t < window_seconds]
    if len(attempts) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many attempts. Try again in {window_seconds} seconds.",
        )
    attempts.append(now)
    _login_attempts[key] = attempts


# ── Register ──────────────────────────────────────────────────────────

@router.post("/register", response_model=CATokenResponse, status_code=201)
async def register(
    req: CARegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_session),
):
    """Register a new CA account."""
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(f"register:{client_ip}", max_attempts=3, window_seconds=3600)

    # Check existing email
    result = await db.execute(
        select(CAAccount).where(CAAccount.email == req.email.lower())
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check existing phone
    phone = normalize_phone(req.phone)
    result = await db.execute(
        select(CAAccount).where(CAAccount.phone == phone)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    ca = CAAccount(
        firm_name=req.firm_name.strip(),
        proprietor_name=req.proprietor_name.strip(),
        email=req.email.lower().strip(),
        phone=phone,
        password_hash=hash_password(req.password),
        membership_number=req.membership_number,
    )
    db.add(ca)
    await db.flush()

    # Create tokens
    access_token = create_access_token(ca.id, ca.email)
    refresh_raw = generate_refresh_token()
    refresh_hash = hash_token(refresh_raw)

    rt = RefreshToken(
        ca_id=ca.id,
        token_hash=refresh_hash,
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.REFRESH_TOKEN_EXPIRY),
        user_agent=request.headers.get("User-Agent"),
        ip_address=client_ip,
    )
    db.add(rt)

    await write_audit_log(
        db,
        actor_type="ca",
        actor_id=ca.id,
        action="ca.registered",
        entity_type="ca_account",
        entity_id=ca.id,
        ip_address=client_ip,
    )
    await db.commit()

    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_raw,
        httponly=True,
        secure=settings.APP_ENV != "development",
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRY,
        path="/api/v1/auth",
    )

    logger.info("ca.registered", ca_id=str(ca.id), email=ca.email)

    return CATokenResponse(
        access_token=access_token,
        ca_id=ca.id,
        firm_name=ca.firm_name,
        email=ca.email,
    )


# ── Login ─────────────────────────────────────────────────────────────

@router.post("/login", response_model=CATokenResponse)
async def login(
    req: CALoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_session),
):
    """Login with email + password. Returns access token + refresh cookie."""
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(f"login:{client_ip}", max_attempts=5, window_seconds=60)

    result = await db.execute(
        select(CAAccount).where(CAAccount.email == req.email.lower())
    )
    ca = result.scalar_one_or_none()

    if not ca or not verify_password(req.password, ca.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not ca.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    access_token = create_access_token(ca.id, ca.email)
    refresh_raw = generate_refresh_token()
    refresh_hash = hash_token(refresh_raw)

    rt = RefreshToken(
        ca_id=ca.id,
        token_hash=refresh_hash,
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.REFRESH_TOKEN_EXPIRY),
        user_agent=request.headers.get("User-Agent"),
        ip_address=client_ip,
    )
    db.add(rt)

    await write_audit_log(
        db,
        actor_type="ca",
        actor_id=ca.id,
        action="ca.login",
        entity_type="ca_account",
        entity_id=ca.id,
        ip_address=client_ip,
    )
    await db.commit()

    response.set_cookie(
        key="refresh_token",
        value=refresh_raw,
        httponly=True,
        secure=settings.APP_ENV != "development",
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRY,
        path="/api/v1/auth",
    )

    logger.info("ca.login", ca_id=str(ca.id))

    return CATokenResponse(
        access_token=access_token,
        ca_id=ca.id,
        firm_name=ca.firm_name,
        email=ca.email,
    )


# ── Refresh ───────────────────────────────────────────────────────────

@router.post("/refresh", response_model=CATokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_session),
):
    """Rotate refresh token. Old token revoked, new one issued."""
    old_raw = request.cookies.get("refresh_token")
    if not old_raw:
        raise HTTPException(status_code=401, detail="No refresh token")

    old_hash = hash_token(old_raw)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == old_hash,
            RefreshToken.revoked_at.is_(None),
        )
    )
    old_rt = result.scalar_one_or_none()

    if not old_rt:
        raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")

    if old_rt.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # Revoke old token
    old_rt.revoked_at = datetime.now(timezone.utc)

    # Load CA
    ca_result = await db.execute(
        select(CAAccount).where(CAAccount.id == old_rt.ca_id)
    )
    ca = ca_result.scalar_one_or_none()
    if not ca or not ca.is_active:
        raise HTTPException(status_code=401, detail="CA account not found or inactive")

    # Issue new tokens
    access_token = create_access_token(ca.id, ca.email)
    new_raw = generate_refresh_token()
    new_hash = hash_token(new_raw)

    new_rt = RefreshToken(
        ca_id=ca.id,
        token_hash=new_hash,
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.REFRESH_TOKEN_EXPIRY),
        user_agent=request.headers.get("User-Agent"),
        ip_address=request.client.host if request.client else None,
    )
    db.add(new_rt)
    await db.commit()

    response.set_cookie(
        key="refresh_token",
        value=new_raw,
        httponly=True,
        secure=settings.APP_ENV != "development",
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRY,
        path="/api/v1/auth",
    )

    return CATokenResponse(
        access_token=access_token,
        ca_id=ca.id,
        firm_name=ca.firm_name,
        email=ca.email,
    )


# ── Logout ────────────────────────────────────────────────────────────

@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_session),
):
    """Revoke refresh token and clear cookie."""
    raw = request.cookies.get("refresh_token")
    if raw:
        token_hash = hash_token(raw)
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
        )
        rt = result.scalar_one_or_none()
        if rt:
            rt.revoked_at = datetime.now(timezone.utc)
            await db.commit()

    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth",
    )


# ── Profile ───────────────────────────────────────────────────────────

@router.get("/me", response_model=CAProfileResponse)
async def get_profile(ca: CurrentCA = Depends()):
    """Get current CA profile."""
    return ca


@router.patch("/me", response_model=CAProfileResponse)
async def update_profile(
    req: CAProfileUpdateRequest,
    ca: CurrentCA = Depends(),
    db: AsyncSession = Depends(get_async_session),
):
    """Update CA profile fields."""
    update_data = req.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    old_values = {}
    for key, value in update_data.items():
        old_values[key] = getattr(ca, key)
        setattr(ca, key, value)

    if "phone" in update_data:
        ca.phone = normalize_phone(ca.phone)
        # Check uniqueness — prevent IntegrityError on duplicate phone
        existing = await db.execute(
            select(CAAccount).where(
                CAAccount.phone == ca.phone, CAAccount.id != ca.id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Phone number already registered")

    await write_audit_log(
        db,
        actor_type="ca",
        actor_id=ca.id,
        action="ca.profile_updated",
        entity_type="ca_account",
        entity_id=ca.id,
        old_value=old_values,
        new_value=update_data,
    )
    await db.commit()
    await db.refresh(ca)
    return ca
