import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StoreType = Literal["supermarket", "convenience", "specialty"]


class StoreCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    width_m: float = Field(..., gt=0, le=1000, description="Store width in metres")
    height_m: float = Field(..., gt=0, le=1000, description="Store height in metres")
    store_type: StoreType


class StoreUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    width_m: float | None = Field(None, gt=0, le=1000)
    height_m: float | None = Field(None, gt=0, le=1000)
    store_type: StoreType | None = None


class StoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    width_m: float
    height_m: float
    store_type: str
    created_at: datetime
    updated_at: datetime


class StoreListResponse(BaseModel):
    data: list[StoreResponse]
    total: int
