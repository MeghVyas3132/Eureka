import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from db.session import get_db
from models.layout import Layout
from models.shelf import Shelf
from models.store import Store
from models.user import User
from models.zone import Zone
from schemas.shelf import ShelfCreate, ShelfResponse, ShelfUpdate

router = APIRouter(prefix="/api/v1/shelves", tags=["shelves"])


async def verify_shelf_ownership(shelf_id: uuid.UUID, current_user: User, db: AsyncSession) -> Shelf:
    result = await db.execute(
        select(Shelf)
        .join(Zone, Shelf.zone_id == Zone.id)
        .join(Layout, Zone.layout_id == Layout.id)
        .join(Store, Layout.store_id == Store.id)
        .where(Shelf.id == shelf_id, Store.user_id == current_user.id)
    )
    shelf = result.scalar_one_or_none()
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found")
    return shelf


@router.post("", response_model=ShelfResponse, status_code=status.HTTP_201_CREATED)
async def create_shelf(
    data: ShelfCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Zone)
        .join(Layout, Zone.layout_id == Layout.id)
        .join(Store, Layout.store_id == Store.id)
        .where(Zone.id == data.zone_id, Store.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Zone not found")

    shelf = Shelf(**data.model_dump())
    db.add(shelf)
    await db.commit()
    await db.refresh(shelf)
    return shelf


@router.put("/{shelf_id}", response_model=ShelfResponse)
async def update_shelf(
    shelf_id: uuid.UUID,
    data: ShelfUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    shelf = await verify_shelf_ownership(shelf_id, current_user, db)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(shelf, field, value)
    await db.commit()
    await db.refresh(shelf)
    return shelf


@router.delete("/{shelf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shelf(
    shelf_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    shelf = await verify_shelf_ownership(shelf_id, current_user, db)
    await db.delete(shelf)
    await db.commit()
