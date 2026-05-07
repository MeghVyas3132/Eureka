from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from db.session import get_db
from ingestion.validators.base_validator import parse_date
from models.sales_data import SalesData
from models.store import Store
from models.user import User
from schemas.sales import SalesCreate, SalesListResponse, SalesResponse, SalesUpdate
from services.data_normalization import normalise_sales

router = APIRouter(prefix="/api/v1/sales", tags=["sales"])


async def get_store_for_user(store_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Store | None:
    result = await db.execute(
        select(Store).where(Store.id == store_id, Store.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_sales_for_user(sales_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> SalesData | None:
    result = await db.execute(
        select(SalesData)
        .join(Store, SalesData.store_id == Store.id)
        .where(SalesData.id == sales_id, Store.user_id == user_id)
    )
    return result.scalar_one_or_none()


def _normalize_periods(period_start: str, period_end: str) -> tuple[str, str]:
    parsed_start, start_err = parse_date(period_start, "period_start")
    if start_err or not parsed_start:
        raise ValueError(start_err or "period_start is required")

    parsed_end, end_err = parse_date(period_end, "period_end")
    if end_err or not parsed_end:
        raise ValueError(end_err or "period_end is required")

    if parsed_end < parsed_start:
        raise ValueError(f"period_end ({parsed_end}) must be >= period_start ({parsed_start})")

    return parsed_start, parsed_end


@router.post("", response_model=SalesResponse, status_code=status.HTTP_201_CREATED)
async def create_sales_entry(
    data: SalesCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store = await get_store_for_user(data.store_id, current_user.id, db)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    try:
        period_start, period_end = _normalize_periods(data.period_start, data.period_end)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    payload = data.model_dump(exclude_none=True)
    payload["sku"] = payload["sku"].strip().upper()
    payload["period_start"] = period_start
    payload["period_end"] = period_end
    payload["ingestion_method"] = payload.get("ingestion_method", "manual")
    payload = normalise_sales(payload)
    payload.pop("revenue_per_unit", None)

    existing_result = await db.execute(
        select(SalesData).where(
            SalesData.store_id == data.store_id,
            SalesData.sku == payload["sku"],
            SalesData.period_start == payload["period_start"],
            SalesData.period_end == payload["period_end"],
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        for key, value in payload.items():
            setattr(existing, key, value)
        sales_row = existing
    else:
        sales_row = SalesData(store_id=data.store_id, **payload)
        db.add(sales_row)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Sales entry already exists for this period") from exc

    await db.refresh(sales_row)
    return sales_row


@router.get("", response_model=SalesListResponse)
async def list_sales(
    store_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store = await get_store_for_user(store_id, current_user.id, db)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    result = await db.execute(
        select(SalesData)
        .where(SalesData.store_id == store_id)
        .order_by(SalesData.period_start.desc(), SalesData.created_at.desc())
    )
    rows = result.scalars().all()
    return {"data": rows, "total": len(rows)}


@router.put("/{sales_id}", response_model=SalesResponse)
async def update_sales_entry(
    sales_id: uuid.UUID,
    data: SalesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sales_row = await get_sales_for_user(sales_id, current_user.id, db)
    if not sales_row:
        raise HTTPException(status_code=404, detail="Sales entry not found")

    payload = data.model_dump(exclude_unset=True)

    next_period_start = payload.get("period_start", sales_row.period_start)
    next_period_end = payload.get("period_end", sales_row.period_end)
    try:
        parsed_start, parsed_end = _normalize_periods(next_period_start, next_period_end)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    payload["period_start"] = parsed_start
    payload["period_end"] = parsed_end

    if "sku" in payload and payload["sku"] is not None:
        payload["sku"] = str(payload["sku"]).strip().upper()

    normalized_payload = normalise_sales(
        {
            "sku": payload.get("sku", sales_row.sku),
            "period_start": payload["period_start"],
            "period_end": payload["period_end"],
            "units_sold": payload.get("units_sold", sales_row.units_sold),
            "revenue": payload.get("revenue", sales_row.revenue),
            "ingestion_method": payload.get("ingestion_method", sales_row.ingestion_method),
        }
    )
    normalized_payload.pop("revenue_per_unit", None)

    for field, value in normalized_payload.items():
        setattr(sales_row, field, value)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Sales entry already exists for this period") from exc

    await db.refresh(sales_row)
    return sales_row


@router.delete("/{sales_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sales_entry(
    sales_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sales_row = await get_sales_for_user(sales_id, current_user.id, db)
    if not sales_row:
        raise HTTPException(status_code=404, detail="Sales entry not found")

    await db.delete(sales_row)
    await db.commit()
