from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

GenerationLevel = Literal["store", "city", "state"]
GenerationMethod = Literal["auto", "manual"]


class PlanogramCreate(BaseModel):
    store_id: uuid.UUID
    name: str = Field("Auto-Generated Planogram", min_length=1, max_length=255)
    generation_level: GenerationLevel = "store"
    generation_method: GenerationMethod = "auto"
    shelf_count: int = Field(5, ge=1, le=50)
    shelf_width_cm: float = Field(180.0, gt=0, le=2000)
    shelf_height_cm: float = Field(200.0, gt=0, le=500)
    planogram_json: dict = Field(default_factory=dict)


class PlanogramGenerateRequest(BaseModel):
    store_id: uuid.UUID
    generation_level: GenerationLevel = "store"
    shelf_count: int | None = Field(None, ge=1, le=50)
    shelf_width_cm: float | None = Field(None, gt=0, le=2000)
    shelf_height_cm: float | None = Field(None, gt=0, le=500)
    force: bool = False


class PlanogramGenerateAllRequest(BaseModel):
    level: Literal["city", "state"]
    shelf_count: int | None = Field(None, ge=1, le=50)
    shelf_width_cm: float | None = Field(None, gt=0, le=2000)
    shelf_height_cm: float | None = Field(None, gt=0, le=500)
    force: bool = False


class PlanogramGenerateAllResponse(BaseModel):
    generated_count: int
    skipped_edited_count: int
    planogram_ids: list[uuid.UUID]


class PlanogramUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    shelf_count: int | None = Field(None, ge=1, le=50)
    shelf_width_cm: float | None = Field(None, gt=0, le=2000)
    shelf_height_cm: float | None = Field(None, gt=0, le=500)
    planogram_json: dict | None = None


class PlanogramVersionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version_number: int
    created_at: datetime


class PlanogramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    store_id: uuid.UUID
    name: str
    generation_level: str
    generation_method: str
    shelf_count: int
    shelf_width_cm: float
    shelf_height_cm: float
    planogram_json: dict
    is_user_edited: bool
    last_auto_generated_at: datetime | None
    created_at: datetime
    updated_at: datetime
    versions: list[PlanogramVersionSummary] = Field(default_factory=list)


class PlanogramListResponse(BaseModel):
    data: list[PlanogramResponse]
    total: int


class PlanogramVersionListResponse(BaseModel):
    data: list[PlanogramVersionSummary]
