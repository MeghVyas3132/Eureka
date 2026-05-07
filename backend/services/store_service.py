import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.store import Store
from schemas.store import StoreCreate, StoreUpdate
from services.store_intelligence import StoreIntelligenceEngine, build_store_hierarchy

DEFAULT_STORE_WIDTH_M = 30.0
DEFAULT_STORE_HEIGHT_M = 20.0


def _apply_store_intelligence(payload: dict, *, overwrite_existing: bool = False) -> dict:
    raw_name = str(payload.get("raw_name") or payload.get("name") or "").strip()
    if not raw_name:
        return payload

    parsed = StoreIntelligenceEngine().parse(raw_name)

    field_map = {
        "display_name": parsed.get("display_name"),
        "country": parsed.get("country"),
        "state": parsed.get("state"),
        "city": parsed.get("city"),
        "locality": parsed.get("locality"),
        "detected_chain": parsed.get("detected_chain"),
        "pin_code": parsed.get("pin_code"),
        "parse_confidence": parsed.get("parse_confidence"),
        "store_type": parsed.get("store_type"),
    }
    for key, value in field_map.items():
        if overwrite_existing or key not in payload or payload.get(key) in (None, ""):
            payload[key] = value

    return payload


async def create_store(user_id: uuid.UUID, data: StoreCreate, db: AsyncSession) -> Store:
    payload = data.model_dump(exclude_none=True)
    if not payload.get("raw_name"):
        payload["raw_name"] = payload["name"]
    payload = _apply_store_intelligence(payload)
    if not payload.get("display_name"):
        payload["display_name"] = payload.get("name")
    if not payload.get("country"):
        payload["country"] = "India"
    if not payload.get("source"):
        payload["source"] = "manual"
    if not payload.get("width_m"):
        payload["width_m"] = DEFAULT_STORE_WIDTH_M
    if not payload.get("height_m"):
        payload["height_m"] = DEFAULT_STORE_HEIGHT_M
    if not payload.get("store_type"):
        payload["store_type"] = "supermarket"

    store = Store(user_id=user_id, **payload)
    db.add(store)
    await db.commit()
    await db.refresh(store)
    return store


async def get_stores_for_user(user_id: uuid.UUID, db: AsyncSession) -> list[Store]:
    result = await db.execute(select(Store).where(Store.user_id == user_id))
    return result.scalars().all()


async def get_store(store_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Store | None:
    result = await db.execute(select(Store).where(Store.id == store_id, Store.user_id == user_id))
    return result.scalar_one_or_none()


async def update_store(store: Store, data: StoreUpdate, db: AsyncSession) -> Store:
    payload = data.model_dump(exclude_none=True)
    if "name" in payload and "display_name" not in payload:
        payload["display_name"] = payload["name"]
    if "name" in payload and "raw_name" not in payload:
        payload["raw_name"] = payload["name"]
    if "raw_name" in payload or "name" in payload:
        payload = _apply_store_intelligence(payload, overwrite_existing=False)
    for field, value in payload.items():
        setattr(store, field, value)
    await db.commit()
    await db.refresh(store)
    return store


async def delete_store(store: Store, db: AsyncSession) -> None:
    await db.delete(store)
    await db.commit()


async def get_store_hierarchy_for_user(user_id: uuid.UUID, db: AsyncSession) -> dict:
    stores = await get_stores_for_user(user_id, db)
    return build_store_hierarchy(stores)
