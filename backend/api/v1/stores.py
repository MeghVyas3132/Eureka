import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from db.session import get_db
from models.user import User
from schemas.store import StoreCreate, StoreListResponse, StoreResponse, StoreUpdate
from services import store_service

router = APIRouter(prefix="/api/v1/stores", tags=["stores"])


@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
async def create_store(
    data: StoreCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await store_service.create_store(current_user.id, data, db)


@router.get("", response_model=StoreListResponse)
async def list_stores(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stores = await store_service.get_stores_for_user(current_user.id, db)
    return {"data": stores, "total": len(stores)}


@router.get("/{store_id}", response_model=StoreResponse)
async def get_store(
    store_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store = await store_service.get_store(store_id, current_user.id, db)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


@router.put("/{store_id}", response_model=StoreResponse)
async def update_store(
    store_id: uuid.UUID,
    data: StoreUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store = await store_service.get_store(store_id, current_user.id, db)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return await store_service.update_store(store, data, db)


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store(
    store_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store = await store_service.get_store(store_id, current_user.id, db)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    await store_service.delete_store(store, db)
