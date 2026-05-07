import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ImportError(BaseModel):
    row: int
    reason: str


class PotentialDuplicate(BaseModel):
    row_a: int | None = None
    sku_a: str
    name_a: str
    row_b: int
    sku_b: str
    name_b: str
    similarity: float
    source: str


class ImportSummaryResponse(BaseModel):
    import_id: uuid.UUID
    import_type: str
    file_format: str
    original_filename: str
    imported_at: datetime
    total_rows: int
    success: int
    skipped: int
    errors: list[ImportError]
    status: str

    period_start: str | None = None
    period_end: str | None = None
    unmatched_skus: list[str] | None = None
    potential_duplicates: list[PotentialDuplicate] | None = None


class ImportLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    import_type: str
    file_format: str
    original_filename: str
    file_size_bytes: int
    total_rows: int
    success_count: int
    skipped_count: int
    error_count: int
    error_detail: list[ImportError] | None
    status: str
    imported_at: datetime
    period_start: str | None
    period_end: str | None
    unmatched_skus: list[str] | None
