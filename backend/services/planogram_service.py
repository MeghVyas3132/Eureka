import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.planogram import Planogram
from models.planogram_version import PlanogramVersion

MAX_VERSIONS_PER_PLANOGRAM = 20


def _build_snapshot(planogram: Planogram) -> dict:
    return {
        "planogram_id": str(planogram.id),
        "store_id": str(planogram.store_id),
        "name": planogram.name,
        "generation_level": planogram.generation_level,
        "generation_method": planogram.generation_method,
        "shelf_count": planogram.shelf_count,
        "shelf_width_cm": planogram.shelf_width_cm,
        "shelf_height_cm": planogram.shelf_height_cm,
        "planogram_json": planogram.planogram_json,
        "is_user_edited": planogram.is_user_edited,
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
    }


async def save_planogram_snapshot(planogram_id: uuid.UUID, db: AsyncSession) -> PlanogramVersion:
    planogram = await db.get(Planogram, planogram_id)
    if not planogram:
        raise ValueError(f"Planogram {planogram_id} not found")

    snapshot = _build_snapshot(planogram)

    result = await db.execute(
        select(PlanogramVersion.version_number)
        .where(PlanogramVersion.planogram_id == planogram_id)
        .order_by(PlanogramVersion.version_number.desc())
        .limit(1)
    )
    last_version = result.scalar_one_or_none()
    next_version = (last_version or 0) + 1

    new_version = PlanogramVersion(
        planogram_id=planogram_id,
        version_number=next_version,
        snapshot_json=snapshot,
    )
    db.add(new_version)

    all_versions_result = await db.execute(
        select(PlanogramVersion.id)
        .where(PlanogramVersion.planogram_id == planogram_id)
        .order_by(PlanogramVersion.version_number.asc())
    )
    all_version_ids = all_versions_result.scalars().all()

    excess_count = len(all_version_ids) + 1 - MAX_VERSIONS_PER_PLANOGRAM
    if excess_count > 0:
        ids_to_delete = all_version_ids[:excess_count]
        await db.execute(delete(PlanogramVersion).where(PlanogramVersion.id.in_(ids_to_delete)))

    await db.commit()
    await db.refresh(new_version)
    return new_version


async def rollback_planogram(planogram_id: uuid.UUID, version_id: uuid.UUID, db: AsyncSession) -> Planogram:
    version = await db.get(PlanogramVersion, version_id)
    if not version or version.planogram_id != planogram_id:
        raise ValueError("Version not found or does not belong to this planogram")

    planogram = await db.get(Planogram, planogram_id)
    if not planogram:
        raise ValueError(f"Planogram {planogram_id} not found")

    snapshot = version.snapshot_json
    planogram.name = snapshot.get("name", planogram.name)
    planogram.generation_level = snapshot.get("generation_level", planogram.generation_level)
    planogram.generation_method = snapshot.get("generation_method", planogram.generation_method)
    planogram.shelf_count = snapshot.get("shelf_count", planogram.shelf_count)
    planogram.shelf_width_cm = snapshot.get("shelf_width_cm", planogram.shelf_width_cm)
    planogram.shelf_height_cm = snapshot.get("shelf_height_cm", planogram.shelf_height_cm)
    planogram.planogram_json = snapshot.get("planogram_json", planogram.planogram_json)
    planogram.is_user_edited = snapshot.get("is_user_edited", planogram.is_user_edited)
    planogram.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await save_planogram_snapshot(planogram_id, db)
    return planogram
