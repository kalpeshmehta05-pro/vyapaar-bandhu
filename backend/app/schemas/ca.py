"""
VyapaarBandhu — CA Account Pydantic Schemas
Request/response validation for CA authentication and profile.
"""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.config import settings


class CARegisterRequest(BaseModel):
    firm_name: str = Field(..., min_length=2, max_length=200)
    proprietor_name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=12)
    membership_number: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < settings.MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {settings.MIN_PASSWORD_LENGTH} characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[^a-zA-Z0-9]", v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"[^\d+]", "", v)
        if len(cleaned) < 10:
            raise ValueError("Phone number too short")
        return cleaned


class CALoginRequest(BaseModel):
    email: EmailStr
    password: str


class CATokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    ca_id: uuid.UUID
    firm_name: str
    email: str


class CAProfileResponse(BaseModel):
    id: uuid.UUID
    firm_name: str
    proprietor_name: str
    email: str
    phone: str
    membership_number: str | None
    tier: str
    max_clients: int
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CAProfileUpdateRequest(BaseModel):
    firm_name: str | None = None
    proprietor_name: str | None = None
    phone: str | None = None
    membership_number: str | None = None
