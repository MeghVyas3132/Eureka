import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from schemas.shelf import ShelfResponse

ZoneType = Literal["aisle", "entrance", "checkout", "department", "storage", "other"]


class ZoneCreate(BaseModel):
    layout_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=255)
    zone_type: ZoneType
    x: float = Field(0.0, ge=0)
    y: float = Field(0.0, ge=0)
    width: float = Field(..., gt=0)
    height: float = Field(..., gt=0)


class ZoneUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    zone_type: ZoneType | None = None
    x: float | None = Field(None, ge=0)
    y: float | None = Field(None, ge=0)
    width: float | None = Field(None, gt=0)
    height: float | None = Field(None, gt=0)


class ZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    layout_id: uuid.UUID
    name: str
    zone_type: str
    x: float
    y: float
    width: float
    height: float
    shelves: list[ShelfResponse] = Field(default_factory=list)
