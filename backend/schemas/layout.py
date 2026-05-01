from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from schemas.zone import ZoneResponse


class LayoutCreate(BaseModel):
    store_id: uuid.UUID
    name: str = Field("Untitled Layout", min_length=1, max_length=255)


class LayoutUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)


class LayoutVersionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version_number: int
    created_at: datetime


class LayoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    store_id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime
    zones: list[ZoneResponse] = Field(default_factory=list)
    versions: list[LayoutVersionSummary] = Field(default_factory=list)


class LayoutListResponse(BaseModel):
    data: list[LayoutResponse]
    total: int


class LayoutVersionListResponse(BaseModel):
    data: list[LayoutVersionSummary]