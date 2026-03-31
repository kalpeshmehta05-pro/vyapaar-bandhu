"""
VyapaarBandhu — Client Pydantic Schemas
Request/response validation for client management.
"""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ClientCreateRequest(BaseModel):
    whatsapp_phone: str = Field(..., min_length=10, max_length=15)
    business_name: str = Field(..., min_length=2, max_length=200)
    owner_name: str = Field(..., min_length=2, max_length=200)
    gstin: str | None = Field(None, max_length=15)
    business_type: str = Field("trader")
    primary_activity: str | None = None
    is_composition: bool = False

    @field_validator("business_type")
    @classmethod
    def validate_business_type(cls, v: str) -> str:
        allowed = {"trader", "manufacturer", "service_provider", "retailer", "other"}
        if v not in allowed:
            raise ValueError(f"business_type must be one of {allowed}")
        return v

    @field_validator("gstin")
    @classmethod
    def validate_gstin_format(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.upper().strip()
        if len(v) != 15:
            raise ValueError("GSTIN must be exactly 15 characters")
        return v

    @field_validator("whatsapp_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"[^\d+]", "", v)
        if len(cleaned) < 10:
            raise ValueError("Phone number too short")
        return cleaned


class ClientResponse(BaseModel):
    id: uuid.UUID
    ca_id: uuid.UUID
    whatsapp_phone: str
    business_name: str
    owner_name: str
    gstin: str | None
    business_type: str
    primary_activity: str | None
    state_code: str | None
    is_composition: bool
    is_active: bool
    consent_given_at: datetime | None
    onboarded_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ClientUpdateRequest(BaseModel):
    business_name: str | None = None
    owner_name: str | None = None
    business_type: str | None = None
    primary_activity: str | None = None
    is_composition: bool | None = None
    is_active: bool | None = None
