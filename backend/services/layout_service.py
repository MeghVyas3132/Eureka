import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.layout import Layout, LayoutVersion
from models.shelf import Shelf
from models.zone import Zone

MAX_VERSIONS_PER_LAYOUT = 20


async def build_snapshot(layout: Layout, db: AsyncSession) -> dict:
    result = await db.execute(
        select(Zone)
        .where(Zone.layout_id == layout.id)
        .options(selectinload(Zone.shelves))
    )
    zones = result.scalars().all()

    return {
        "layout_id": str(layout.id),
        "store_id": str(layout.store_id),
        "name": layout.name,
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
        "zones": [
            {
                "id": str(zone.id),
                "name": zone.name,
                "zone_type": zone.zone_type,
                "x": zone.x,
                "y": zone.y,
                "width": zone.width,
                "height": zone.height,
                "shelves": [
                    {
                        "id": str(shelf.id),
                        "x": shelf.x,
                        "y": shelf.y,
                        "width_cm": shelf.width_cm,
                        "height_cm": shelf.height_cm,
                        "num_rows": shelf.num_rows,
                        "placements": [],
                    }
                    for shelf in zone.shelves
                ],
            }
            for zone in zones
        ],
    }


async def save_layout_snapshot(layout_id: uuid.UUID, db: AsyncSession) -> LayoutVersion:
    layout = await db.get(Layout, layout_id)
    if not layout:
        raise ValueError(f"Layout {layout_id} not found")

    snapshot = await build_snapshot(layout, db)

    result = await db.execute(
        select(LayoutVersion.version_number)
        .where(LayoutVersion.layout_id == layout_id)
        .order_by(LayoutVersion.version_number.desc())
        .limit(1)
    )
    last_version = result.scalar_one_or_none()
    next_version = (last_version or 0) + 1

    new_version = LayoutVersion(
        layout_id=layout_id,
        version_number=next_version,
        snapshot_json=snapshot,
    )
    db.add(new_version)

    all_versions_result = await db.execute(
        select(LayoutVersion.id)
        .where(LayoutVersion.layout_id == layout_id)
        .order_by(LayoutVersion.version_number.asc())
    )
    all_version_ids = all_versions_result.scalars().all()

    excess_count = len(all_version_ids) + 1 - MAX_VERSIONS_PER_LAYOUT
    if excess_count > 0:
        ids_to_delete = all_version_ids[:excess_count]
        await db.execute(delete(LayoutVersion).where(LayoutVersion.id.in_(ids_to_delete)))

    await db.commit()
    await db.refresh(new_version)
    return new_version


async def rollback_layout(layout_id: uuid.UUID, version_id: uuid.UUID, db: AsyncSession) -> Layout:
    version = await db.get(LayoutVersion, version_id)
    if not version or version.layout_id != layout_id:
        raise ValueError("Version not found or does not belong to this layout")

    snapshot = version.snapshot_json

    await db.execute(delete(Zone).where(Zone.layout_id == layout_id))

    for zone_data in snapshot.get("zones", []):
        zone = Zone(
            id=uuid.UUID(zone_data["id"]),
            layout_id=layout_id,
            name=zone_data["name"],
            zone_type=zone_data["zone_type"],
            x=zone_data["x"],
            y=zone_data["y"],
            width=zone_data["width"],
            height=zone_data["height"],
        )
        db.add(zone)

        for shelf_data in zone_data.get("shelves", []):
            shelf = Shelf(
                id=uuid.UUID(shelf_data["id"]),
                zone_id=uuid.UUID(zone_data["id"]),
                x=shelf_data["x"],
                y=shelf_data["y"],
                width_cm=shelf_data["width_cm"],
                height_cm=shelf_data["height_cm"],
                num_rows=shelf_data["num_rows"],
            )
            db.add(shelf)

    layout = await db.get(Layout, layout_id)
    if layout is None:
        raise ValueError(f"Layout {layout_id} not found")
    layout.updated_at = datetime.now(timezone.utc)

    await db.commit()

    await save_layout_snapshot(layout_id, db)

    return layout