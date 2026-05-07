import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.api_response import error_payload
from core.constants import ERROR_CODE_QUOTA_EXCEEDED
from core.deps import get_current_user
from db.session import get_db
from models.planogram import Planogram
from models.planogram_version import PlanogramVersion
from models.product import Product
from models.sales_data import SalesData
from models.store import Store
from models.user import User
from schemas.planogram import (
    PlanogramCreate,
    PlanogramGenerateAllRequest,
    PlanogramGenerateAllResponse,
    PlanogramGenerateRequest,
    PlanogramListResponse,
    PlanogramResponse,
    PlanogramUpdate,
    PlanogramVersionListResponse,
)
from services.export_service import (
    render_planogram_to_jpeg,
    render_planogram_to_pptx,
)
from services.planogram_engine import PlanogramInput, generate as generate_planogram
from services import planogram_service
from services.plan_limit_service import get_effective_plan_limit_for_user
from services.quota_service import evaluate_planogram_quota

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


async def _load_sales_for_level(
    *,
    store: Store,
    user_id: uuid.UUID,
    generation_level: str,
    db: AsyncSession,
) -> list[SalesData]:
    if generation_level == "store":
        result = await db.execute(select(SalesData).where(SalesData.store_id == store.id))
        return result.scalars().all()

    if generation_level == "city":
        if not store.city:
            result = await db.execute(select(SalesData).where(SalesData.store_id == store.id))
            return result.scalars().all()
        store_ids_result = await db.execute(
            select(Store.id).where(Store.user_id == user_id, Store.city == store.city)
        )
        store_ids = store_ids_result.scalars().all()
        if not store_ids:
            return []
        result = await db.execute(select(SalesData).where(SalesData.store_id.in_(store_ids)))
        return result.scalars().all()

    if generation_level == "state":
        if not store.state:
            result = await db.execute(select(SalesData).where(SalesData.store_id == store.id))
            return result.scalars().all()
        store_ids_result = await db.execute(
            select(Store.id).where(Store.user_id == user_id, Store.state == store.state)
        )
        store_ids = store_ids_result.scalars().all()
        if not store_ids:
            return []
        result = await db.execute(select(SalesData).where(SalesData.store_id.in_(store_ids)))
        return result.scalars().all()

    result = await db.execute(select(SalesData).where(SalesData.store_id == store.id))
    return result.scalars().all()


async def _get_user_planogram_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count(Planogram.id))
        .join(Store, Planogram.store_id == Store.id)
        .where(Store.user_id == user_id)
    )
    return int(result.scalar_one() or 0)


async def _enforce_planogram_quota(db: AsyncSession, user: User, additional: int = 1) -> None:
    plan_limit = await get_effective_plan_limit_for_user(db, user)
    if plan_limit["is_unlimited"]:
        return
    current_count = await _get_user_planogram_count(db, user.id)
    quota = evaluate_planogram_quota(
        current_count=current_count + max(0, additional - 1),
        annual_planogram_limit=plan_limit["annual_planogram_limit"],
        is_unlimited=plan_limit["is_unlimited"],
    )
    if not quota["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_payload(
                ERROR_CODE_QUOTA_EXCEEDED,
                {
                    "message": "Annual planogram limit reached for this user.",
                    "limit": quota["limit"],
                    "remaining": quota["remaining"],
                },
            ),
        )


async def _has_edited_latest_auto_planogram(store_id: uuid.UUID, db: AsyncSession) -> bool:
    result = await db.execute(
        select(Planogram)
        .where(Planogram.store_id == store_id, Planogram.generation_method == "auto")
        .order_by(Planogram.created_at.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()
    return bool(latest and latest.is_user_edited)


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


@router.post("/generate", response_model=PlanogramResponse, status_code=status.HTTP_201_CREATED)
async def generate_planogram_for_store(
    data: PlanogramGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store_result = await db.execute(
        select(Store).where(Store.id == data.store_id, Store.user_id == current_user.id)
    )
    store = store_result.scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    if await _has_edited_latest_auto_planogram(store.id, db) and not data.force:
        raise HTTPException(
            status_code=409,
            detail=(
                "Latest auto-generated planogram has user edits. "
                "Set force=true to explicitly generate a new auto planogram."
            ),
        )

    await _enforce_planogram_quota(db, current_user)

    products_result = await db.execute(select(Product).where(Product.user_id == current_user.id))
    products = products_result.scalars().all()

    sales = await _load_sales_for_level(
        store=store,
        user_id=current_user.id,
        generation_level=data.generation_level,
        db=db,
    )

    shelf_count = data.shelf_count or 5
    shelf_width_cm = data.shelf_width_cm or 180.0
    shelf_height_cm = data.shelf_height_cm or 200.0

    generation = generate_planogram(
        PlanogramInput(
            store_id=store.id,
            store=store,
            generation_level=data.generation_level,
            products=products,
            sales=sales,
            shelf_count=shelf_count,
            shelf_width_cm=shelf_width_cm,
            shelf_height_cm=shelf_height_cm,
        )
    )

    planogram = Planogram(
        store_id=store.id,
        name="Auto-Generated Planogram",
        generation_level=data.generation_level,
        generation_method="auto",
        shelf_count=shelf_count,
        shelf_width_cm=shelf_width_cm,
        shelf_height_cm=shelf_height_cm,
        planogram_json=generation.planogram_json,
        is_user_edited=False,
        last_auto_generated_at=datetime.now(timezone.utc),
    )
    db.add(planogram)
    await db.commit()
    await db.refresh(planogram)

    planogram_json = dict(planogram.planogram_json or {})
    planogram_json["planogram_id"] = str(planogram.id)
    planogram_json["store_id"] = str(store.id)
    planogram.planogram_json = planogram_json
    await db.commit()

    await planogram_service.save_planogram_snapshot(planogram.id, db)
    return await get_planogram_with_auth(planogram.id, current_user, db)


@router.post("/generate-all", response_model=PlanogramGenerateAllResponse)
async def generate_planograms_for_level(
    data: PlanogramGenerateAllRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stores_result = await db.execute(select(Store).where(Store.user_id == current_user.id))
    stores = stores_result.scalars().all()
    if not stores:
        return PlanogramGenerateAllResponse(generated_count=0, skipped_edited_count=0, planogram_ids=[])

    await _enforce_planogram_quota(db, current_user, additional=len(stores))

    products_result = await db.execute(select(Product).where(Product.user_id == current_user.id))
    products = products_result.scalars().all()

    groups: dict[str, list[Store]] = {}
    for store in stores:
        group_key = store.city if data.level == "city" else store.state
        group_key = str(group_key or f"unknown-{store.id}")
        groups.setdefault(group_key, []).append(store)

    shelf_count = data.shelf_count or 5
    shelf_width_cm = data.shelf_width_cm or 180.0
    shelf_height_cm = data.shelf_height_cm or 200.0

    generated_ids: list[uuid.UUID] = []
    skipped_edited_count = 0

    for grouped_stores in groups.values():
        store_ids = [store.id for store in grouped_stores]
        sales_result = await db.execute(select(SalesData).where(SalesData.store_id.in_(store_ids)))
        grouped_sales = sales_result.scalars().all()

        for store in grouped_stores:
            if await _has_edited_latest_auto_planogram(store.id, db) and not data.force:
                skipped_edited_count += 1
                continue

            generation = generate_planogram(
                PlanogramInput(
                    store_id=store.id,
                    store=store,
                    generation_level=data.level,
                    products=products,
                    sales=grouped_sales,
                    shelf_count=shelf_count,
                    shelf_width_cm=shelf_width_cm,
                    shelf_height_cm=shelf_height_cm,
                )
            )

            planogram = Planogram(
                store_id=store.id,
                name="Auto-Generated Planogram",
                generation_level=data.level,
                generation_method="auto",
                shelf_count=shelf_count,
                shelf_width_cm=shelf_width_cm,
                shelf_height_cm=shelf_height_cm,
                planogram_json=generation.planogram_json,
                is_user_edited=False,
                last_auto_generated_at=datetime.now(timezone.utc),
            )
            db.add(planogram)
            await db.flush()

            planogram_json = dict(planogram.planogram_json or {})
            planogram_json["planogram_id"] = str(planogram.id)
            planogram_json["store_id"] = str(store.id)
            planogram.planogram_json = planogram_json

            generated_ids.append(planogram.id)

    await db.commit()

    for planogram_id in generated_ids:
        await planogram_service.save_planogram_snapshot(planogram_id, db)

    return PlanogramGenerateAllResponse(
        generated_count=len(generated_ids),
        skipped_edited_count=skipped_edited_count,
        planogram_ids=generated_ids,
    )


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


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_")
    return cleaned or "planogram"


async def _load_planogram_with_store(
    planogram_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> tuple[Planogram, Store]:
    planogram = await get_planogram_with_auth(planogram_id, current_user, db)
    store_result = await db.execute(select(Store).where(Store.id == planogram.store_id))
    store = store_result.scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail="Planogram store not found")
    return planogram, store


@router.get("/{planogram_id}/export/jpeg")
async def export_planogram_jpeg(
    planogram_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    planogram, store = await _load_planogram_with_store(planogram_id, current_user, db)
    store_label = store.display_name or store.raw_name or "Store"
    image_bytes = render_planogram_to_jpeg(planogram.planogram_json or {}, store_name=store_label)

    today = datetime.now(timezone.utc).date().isoformat()
    filename = f"{_safe_filename(store_label)}_{today}_planogram.jpg"
    return Response(
        content=image_bytes,
        media_type="image/jpeg",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{planogram_id}/export/pptx")
async def export_planogram_pptx(
    planogram_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    planogram, store = await _load_planogram_with_store(planogram_id, current_user, db)
    store_label = store.display_name or store.raw_name or "Store"
    pptx_bytes = render_planogram_to_pptx(planogram.planogram_json or {}, store_name=store_label)

    today = datetime.now(timezone.utc).date().isoformat()
    filename = f"{_safe_filename(store_label)}_{today}_planogram.pptx"
    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
