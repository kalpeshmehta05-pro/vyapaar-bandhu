"""
VyapaarBandhu — Client Management CRUD
CA-scoped: a CA can only see/modify their own clients.
"""

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.dependencies import CurrentCA
from app.models.client import Client
from app.schemas.client import ClientCreateRequest, ClientResponse, ClientUpdateRequest
from app.services.compliance.gstin_state_mapper import get_state_from_gstin
from app.utils.audit import write_audit_log
from app.utils.phone import normalize_phone

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=list[ClientResponse])
async def list_clients(
    ca: CurrentCA,
    db: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 50,
):
    """List all clients for the authenticated CA."""
    result = await db.execute(
        select(Client)
        .where(Client.ca_id == ca.id, Client.is_active == True)
        .offset(skip)
        .limit(min(limit, 100))
        .order_by(Client.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=ClientResponse, status_code=201)
async def create_client(
    req: ClientCreateRequest,
    ca: CurrentCA,
    db: AsyncSession = Depends(get_async_session),
):
    """Add a new client. Triggers WhatsApp consent message (Phase 4)."""
    # Check CA client limit
    count_result = await db.execute(
        select(func.count(Client.id)).where(Client.ca_id == ca.id, Client.is_active == True)
    )
    current_count = count_result.scalar() or 0
    if current_count >= ca.max_clients:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Client limit reached ({ca.max_clients}). Upgrade your plan.",
        )

    phone = normalize_phone(req.whatsapp_phone)

    # Check duplicate phone for this CA
    existing = await db.execute(
        select(Client).where(Client.ca_id == ca.id, Client.whatsapp_phone == phone)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Client with this phone already exists")

    # Extract state code from GSTIN
    state_code = get_state_from_gstin(req.gstin) if req.gstin else None

    client = Client(
        ca_id=ca.id,
        whatsapp_phone=phone,
        business_name=req.business_name.strip(),
        owner_name=req.owner_name.strip(),
        gstin=req.gstin,
        business_type=req.business_type,
        primary_activity=req.primary_activity,
        state_code=state_code,
        is_composition=req.is_composition,
        # consent_given_at is NULL — WhatsApp consent flow handles this (Phase 4)
    )
    db.add(client)
    await db.flush()

    await write_audit_log(
        db,
        actor_type="ca",
        actor_id=ca.id,
        action="client.created",
        entity_type="client",
        entity_id=client.id,
        new_value={"business_name": client.business_name, "phone": phone},
    )
    await db.commit()

    logger.info("client.created", client_id=str(client.id), ca_id=str(ca.id))

    # TODO Phase 4: Send WhatsApp consent message to client.whatsapp_phone

    return client


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: uuid.UUID,
    ca: CurrentCA,
    db: AsyncSession = Depends(get_async_session),
):
    """Get a single client by ID. CA-scoped."""
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.ca_id == ca.id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: uuid.UUID,
    req: ClientUpdateRequest,
    ca: CurrentCA,
    db: AsyncSession = Depends(get_async_session),
):
    """Update client fields. CA-scoped."""
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.ca_id == ca.id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    update_data = req.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    old_values = {}
    for key, value in update_data.items():
        old_values[key] = getattr(client, key)
        setattr(client, key, value)

    await write_audit_log(
        db,
        actor_type="ca",
        actor_id=ca.id,
        action="client.updated",
        entity_type="client",
        entity_id=client.id,
        old_value=old_values,
        new_value=update_data,
    )
    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
async def deactivate_client(
    client_id: uuid.UUID,
    ca: CurrentCA,
    db: AsyncSession = Depends(get_async_session),
):
    """Soft-delete a client (deactivate). CA-scoped."""
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.ca_id == ca.id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    client.is_active = False

    await write_audit_log(
        db,
        actor_type="ca",
        actor_id=ca.id,
        action="client.deactivated",
        entity_type="client",
        entity_id=client.id,
    )
    await db.commit()
