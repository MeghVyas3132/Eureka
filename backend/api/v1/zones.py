import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from db.session import get_db
from models.layout import Layout
from models.store import Store
from models.user import User
from models.zone import Zone
from schemas.zone import ZoneCreate, ZoneResponse, ZoneUpdate

router = APIRouter(prefix="/api/v1/zones", tags=["zones"])


async def verify_zone_ownership(zone_id: uuid.UUID, current_user: User, db: AsyncSession) -> Zone:
    result = await db.execute(
        select(Zone)
        .join(Layout, Zone.layout_id == Layout.id)
        .join(Store, Layout.store_id == Store.id)
        .where(Zone.id == zone_id, Store.user_id == current_user.id)
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


@router.post("", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_zone(
    data: ZoneCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Layout)
        .join(Store, Layout.store_id == Store.id)
        .where(Layout.id == data.layout_id, Store.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Layout not found")

    zone = Zone(**data.model_dump())
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    return zone


@router.put("/{zone_id}", response_model=ZoneResponse)
async def update_zone(
    zone_id: uuid.UUID,
    data: ZoneUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    zone = await verify_zone_ownership(zone_id, current_user, db)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(zone, field, value)
    await db.commit()
    await db.refresh(zone)
    return zone


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(
    zone_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    zone = await verify_zone_ownership(zone_id, current_user, db)
    await db.delete(zone)
    await db.commit()
