from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from db.session import get_db
from models.product import Product
from models.user import User
from schemas.product import ProductCreate, ProductListResponse, ProductResponse, ProductUpdate
from services.data_normalization import normalise_product

router = APIRouter(prefix="/api/v1/products", tags=["products"])


async def get_product_for_user(product_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Product | None:
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.user_id == user_id)
    )
    return result.scalar_one_or_none()


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payload = normalise_product(data.model_dump(exclude_none=True))

    product = Product(user_id=current_user.id, **payload)
    db.add(product)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Product SKU already exists for this user") from exc

    await db.refresh(product)
    return product


@router.get("", response_model=ProductListResponse)
async def list_products(
    filter: Literal["missing_dimensions", "missing_category"] | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Product).where(Product.user_id == current_user.id)

    if filter == "missing_dimensions":
        stmt = stmt.where(Product.width_cm.is_(None))
    elif filter == "missing_category":
        stmt = stmt.where(or_(Product.category.is_(None), Product.category == ""))

    result = await db.execute(stmt.order_by(Product.created_at.desc()))
    products = result.scalars().all()
    return {"data": products, "total": len(products)}


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await get_product_for_user(product_id, current_user.id, db)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    payload = data.model_dump(exclude_unset=True)
    if "sku" in payload and payload["sku"] is not None:
        payload["sku"] = str(payload["sku"]).strip().upper()
    if "name" in payload and payload["name"] is not None:
        name = str(payload["name"]).strip()
        payload["name"] = name.title() if name.isupper() else name
    if "brand" in payload and payload["brand"]:
        payload["brand"] = str(payload["brand"]).strip().title()
    if "category" in payload and payload["category"]:
        payload["category"] = str(payload["category"]).strip().title()

    for field, value in payload.items():
        setattr(product, field, value)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Product SKU already exists for this user") from exc

    await db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await get_product_for_user(product_id, current_user.id, db)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.delete(product)
    await db.commit()
