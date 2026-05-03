import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StoreType = Literal["supermarket", "convenience", "specialty"]


class StoreCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    raw_name: str | None = Field(None, min_length=1, max_length=255)
    display_name: str | None = Field(None, min_length=1, max_length=255)
    country: str | None = Field(None, min_length=1, max_length=100)
    state: str | None = Field(None, min_length=1, max_length=100)
    city: str | None = Field(None, min_length=1, max_length=100)
    locality: str | None = Field(None, min_length=1, max_length=100)
    detected_chain: str | None = Field(None, min_length=1, max_length=120)
    pin_code: str | None = Field(None, min_length=1, max_length=20)
    parse_confidence: float | None = Field(None, ge=0, le=1)
    source: str | None = Field(None, min_length=1, max_length=50)
    width_m: float = Field(..., gt=0, le=1000, description="Store width in metres")
    height_m: float = Field(..., gt=0, le=1000, description="Store height in metres")
    store_type: StoreType


class StoreUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    raw_name: str | None = Field(None, min_length=1, max_length=255)
    display_name: str | None = Field(None, min_length=1, max_length=255)
    country: str | None = Field(None, min_length=1, max_length=100)
    state: str | None = Field(None, min_length=1, max_length=100)
    city: str | None = Field(None, min_length=1, max_length=100)
    locality: str | None = Field(None, min_length=1, max_length=100)
    detected_chain: str | None = Field(None, min_length=1, max_length=120)
    pin_code: str | None = Field(None, min_length=1, max_length=20)
    parse_confidence: float | None = Field(None, ge=0, le=1)
    source: str | None = Field(None, min_length=1, max_length=50)
    width_m: float | None = Field(None, gt=0, le=1000)
    height_m: float | None = Field(None, gt=0, le=1000)
    store_type: StoreType | None = None


class StoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    raw_name: str
    display_name: str
    country: str
    state: str | None
    city: str | None
    locality: str | None
    detected_chain: str | None
    pin_code: str | None
    parse_confidence: float | None
    source: str
    width_m: float
    height_m: float
    store_type: str
    created_at: datetime
    updated_at: datetime


class StoreListResponse(BaseModel):
    data: list[StoreResponse]
    total: int
