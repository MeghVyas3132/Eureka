from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SalesCreate(BaseModel):
    store_id: uuid.UUID
    sku: str = Field(..., min_length=1, max_length=120)
    period_start: str = Field(..., min_length=1, max_length=20)
    period_end: str = Field(..., min_length=1, max_length=20)
    units_sold: int | None = Field(None, ge=0)
    revenue: float = Field(..., ge=0)
    ingestion_method: str | None = Field(None, min_length=1, max_length=32)


class SalesUpdate(BaseModel):
    sku: str | None = Field(None, min_length=1, max_length=120)
    period_start: str | None = Field(None, min_length=1, max_length=20)
    period_end: str | None = Field(None, min_length=1, max_length=20)
    units_sold: int | None = Field(None, ge=0)
    revenue: float | None = Field(None, ge=0)
    ingestion_method: str | None = Field(None, min_length=1, max_length=32)


class SalesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    store_id: uuid.UUID
    sku: str
    period_start: str
    period_end: str
    units_sold: int | None
    revenue: float
    ingestion_method: str
    created_at: datetime


class SalesListResponse(BaseModel):
    data: list[SalesResponse]
    total: int
