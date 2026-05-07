from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=120)
    name: str = Field(..., min_length=1, max_length=255)
    brand: str | None = Field(None, max_length=255)
    category: str | None = Field(None, max_length=255)
    width_cm: float | None = Field(None, gt=0)
    height_cm: float | None = Field(None, gt=0)
    depth_cm: float | None = Field(None, gt=0)
    price: float | None = Field(None, ge=0)
    image_url: str | None = Field(None, max_length=500)


class ProductUpdate(BaseModel):
    sku: str | None = Field(None, min_length=1, max_length=120)
    name: str | None = Field(None, min_length=1, max_length=255)
    brand: str | None = Field(None, max_length=255)
    category: str | None = Field(None, max_length=255)
    width_cm: float | None = Field(None, gt=0)
    height_cm: float | None = Field(None, gt=0)
    depth_cm: float | None = Field(None, gt=0)
    price: float | None = Field(None, ge=0)
    image_url: str | None = Field(None, max_length=500)


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    sku: str
    name: str
    brand: str | None
    category: str | None
    width_cm: float | None
    height_cm: float | None
    depth_cm: float | None
    price: float | None
    image_url: str | None
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    data: list[ProductResponse]
    total: int
