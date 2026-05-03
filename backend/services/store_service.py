import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.store import Store
from schemas.store import StoreCreate, StoreUpdate


async def create_store(user_id: uuid.UUID, data: StoreCreate, db: AsyncSession) -> Store:
    payload = data.model_dump()
    if not payload.get("raw_name"):
        payload["raw_name"] = payload["name"]
    if not payload.get("display_name"):
        payload["display_name"] = payload["name"]
    if not payload.get("country"):
        payload["country"] = "India"
    if not payload.get("source"):
        payload["source"] = "manual"

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
    for field, value in payload.items():
        setattr(store, field, value)
    await db.commit()
    await db.refresh(store)
    return store


async def delete_store(store: Store, db: AsyncSession) -> None:
    await db.delete(store)
    await db.commit()
