import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.deps import get_current_user
from db.session import get_db
from models.planogram import Planogram
from models.planogram_version import PlanogramVersion
from models.store import Store
from models.user import User
from schemas.planogram import (
    PlanogramCreate,
    PlanogramListResponse,
    PlanogramResponse,
    PlanogramUpdate,
    PlanogramVersionListResponse,
)
from services import planogram_service

router = APIRouter(prefix="/api/v1/planograms", tags=["planograms"])


async def get_planogram_with_auth(
    planogram_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Planogram:
    result = await db.execute(
        select(Planogram)
        .join(Store, Planogram.store_id == Store.id)
        .where(Planogram.id == planogram_id, Store.user_id == current_user.id)
        .options(selectinload(Planogram.versions))
    )
    planogram = result.scalar_one_or_none()
    if not planogram:
        raise HTTPException(status_code=404, detail="Planogram not found")
    return planogram


@router.get("", response_model=PlanogramListResponse)
async def list_planograms(
    store_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Planogram)
        .join(Store, Planogram.store_id == Store.id)
        .where(Planogram.store_id == store_id, Store.user_id == current_user.id)
        .options(selectinload(Planogram.versions))
        .order_by(Planogram.created_at.desc())
    )
    planograms = result.scalars().unique().all()
    return {"data": planograms, "total": len(planograms)}


@router.post("", response_model=PlanogramResponse, status_code=status.HTTP_201_CREATED)
async def create_planogram(
    data: PlanogramCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store_result = await db.execute(
        select(Store).where(Store.id == data.store_id, Store.user_id == current_user.id)
    )
    if not store_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Store not found")

    planogram = Planogram(
        store_id=data.store_id,
        name=data.name,
        generation_level=data.generation_level,
        generation_method=data.generation_method,
        shelf_count=data.shelf_count,
        shelf_width_cm=data.shelf_width_cm,
        shelf_height_cm=data.shelf_height_cm,
        planogram_json=data.planogram_json,
    )
    db.add(planogram)
    await db.commit()
    await db.refresh(planogram)

    await planogram_service.save_planogram_snapshot(planogram.id, db)

    return await get_planogram_with_auth(planogram.id, current_user, db)


@router.get("/{planogram_id}", response_model=PlanogramResponse)
async def get_planogram(
    planogram_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_planogram_with_auth(planogram_id, current_user, db)


@router.put("/{planogram_id}", response_model=PlanogramResponse)
async def update_planogram(
    planogram_id: uuid.UUID,
    data: PlanogramUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    planogram = await get_planogram_with_auth(planogram_id, current_user, db)

    payload = data.model_dump(exclude_none=True)
    for field, value in payload.items():
        setattr(planogram, field, value)

    if payload:
        planogram.is_user_edited = True

    await db.commit()
    await planogram_service.save_planogram_snapshot(planogram_id, db)

    return await get_planogram_with_auth(planogram_id, current_user, db)


@router.delete("/{planogram_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_planogram(
    planogram_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    planogram = await get_planogram_with_auth(planogram_id, current_user, db)
    await db.delete(planogram)
    await db.commit()


@router.get("/{planogram_id}/versions", response_model=PlanogramVersionListResponse)
async def list_versions(
    planogram_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_planogram_with_auth(planogram_id, current_user, db)

    result = await db.execute(
        select(PlanogramVersion)
        .where(PlanogramVersion.planogram_id == planogram_id)
        .order_by(PlanogramVersion.version_number.desc())
    )
    versions = result.scalars().all()
    return {"data": versions}


@router.post("/{planogram_id}/rollback/{version_id}", response_model=PlanogramResponse)
async def rollback_planogram(
    planogram_id: uuid.UUID,
    version_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_planogram_with_auth(planogram_id, current_user, db)
    try:
        await planogram_service.rollback_planogram(planogram_id, version_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return await get_planogram_with_auth(planogram_id, current_user, db)
