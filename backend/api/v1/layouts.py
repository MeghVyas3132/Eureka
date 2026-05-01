import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.deps import get_current_user
from db.session import get_db
from models.layout import Layout, LayoutVersion
from models.store import Store
from models.user import User
from models.zone import Zone
from schemas.layout import (
    LayoutCreate,
    LayoutListResponse,
    LayoutResponse,
    LayoutUpdate,
    LayoutVersionListResponse,
)
from services import layout_service

router = APIRouter(prefix="/api/v1/layouts", tags=["layouts"])


async def get_layout_with_auth(layout_id: uuid.UUID, current_user: User, db: AsyncSession) -> Layout:
    result = await db.execute(
        select(Layout)
        .join(Store, Layout.store_id == Store.id)
        .where(Layout.id == layout_id, Store.user_id == current_user.id)
        .options(
            selectinload(Layout.zones).selectinload(Zone.shelves),
            selectinload(Layout.versions),
        )
    )
    layout = result.scalar_one_or_none()
    if not layout:
        raise HTTPException(status_code=404, detail="Layout not found")
    return layout


@router.get("", response_model=LayoutListResponse)
async def list_layouts(
    store_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Layout)
        .join(Store, Layout.store_id == Store.id)
        .where(Layout.store_id == store_id, Store.user_id == current_user.id)
        .options(
            selectinload(Layout.zones).selectinload(Zone.shelves),
            selectinload(Layout.versions),
        )
        .order_by(Layout.created_at.desc())
    )
    layouts = result.scalars().unique().all()
    return {"data": layouts, "total": len(layouts)}


@router.post("", response_model=LayoutResponse, status_code=status.HTTP_201_CREATED)
async def create_layout(
    data: LayoutCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store_result = await db.execute(
        select(Store).where(Store.id == data.store_id, Store.user_id == current_user.id)
    )
    if not store_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Store not found")

    layout = Layout(store_id=data.store_id, name=data.name)
    db.add(layout)
    await db.commit()
    await db.refresh(layout)

    await layout_service.save_layout_snapshot(layout.id, db)

    return await get_layout_with_auth(layout.id, current_user, db)


@router.get("/{layout_id}", response_model=LayoutResponse)
async def get_layout(
    layout_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_layout_with_auth(layout_id, current_user, db)


@router.put("/{layout_id}", response_model=LayoutResponse)
async def save_layout(
    layout_id: uuid.UUID,
    data: LayoutUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    layout = await get_layout_with_auth(layout_id, current_user, db)

    if data.name is not None:
        layout.name = data.name
        await db.commit()

    await layout_service.save_layout_snapshot(layout_id, db)

    return await get_layout_with_auth(layout_id, current_user, db)


@router.get("/{layout_id}/versions", response_model=LayoutVersionListResponse)
async def list_versions(
    layout_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_layout_with_auth(layout_id, current_user, db)

    result = await db.execute(
        select(LayoutVersion)
        .where(LayoutVersion.layout_id == layout_id)
        .order_by(LayoutVersion.version_number.desc())
    )
    versions = result.scalars().all()
    return {"data": versions}


@router.post("/{layout_id}/rollback/{version_id}", response_model=LayoutResponse)
async def rollback_layout(
    layout_id: uuid.UUID,
    version_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_layout_with_auth(layout_id, current_user, db)
    try:
        await layout_service.rollback_layout(layout_id, version_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return await get_layout_with_auth(layout_id, current_user, db)