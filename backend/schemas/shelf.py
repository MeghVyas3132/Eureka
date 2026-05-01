import uuid

from pydantic import BaseModel, ConfigDict, Field


class ShelfCreate(BaseModel):
    zone_id: uuid.UUID
    x: float = Field(0.0, ge=0)
    y: float = Field(0.0, ge=0)
    width_cm: float = Field(..., gt=0, le=2000)
    height_cm: float = Field(30.0, gt=0, le=500)
    num_rows: int = Field(1, ge=1, le=20)


class ShelfUpdate(BaseModel):
    x: float | None = Field(None, ge=0)
    y: float | None = Field(None, ge=0)
    width_cm: float | None = Field(None, gt=0, le=2000)
    height_cm: float | None = Field(None, gt=0, le=500)
    num_rows: int | None = Field(None, ge=1, le=20)


class ShelfResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    zone_id: uuid.UUID
    x: float
    y: float
    width_cm: float
    height_cm: float
    num_rows: int
