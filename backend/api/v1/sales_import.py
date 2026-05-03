import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from db.session import get_db
from ingestion.file_detector import detect_and_validate_file
from ingestion.ingestion_service import run_sales_import
from models.import_log import ImportLog
from models.store import Store
from models.user import User
from schemas.ingestion import ImportLogResponse, ImportSummaryResponse

router = APIRouter(prefix="/api/v1/sales", tags=["sales"])


@router.post(
    "/import",
    response_model=ImportSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Import sales data from CSV, Excel, or PDF",
)
async def import_sales(
    file: UploadFile = File(...),
    store_id: uuid.UUID = Query(..., description="The store this sales data belongs to"),
    period_start: str | None = Query(
        None,
        description=(
            "Override period start for all rows. Format: YYYY-MM-DD. "
            "Takes precedence over per-row period_start column."
        ),
    ),
    period_end: str | None = Query(
        None,
        description="Override period end for all rows. Format: YYYY-MM-DD.",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store_result = await db.execute(
        select(Store).where(Store.id == store_id, Store.user_id == current_user.id)
    )
    if not store_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Store not found")

    file_format, file_bytes = await detect_and_validate_file(file)

    try:
        summary = await run_sales_import(
            file_bytes=file_bytes,
            file_format=file_format,
            original_filename=file.filename or "upload",
            file_size_bytes=len(file_bytes),
            user_id=current_user.id,
            store_id=store_id,
            period_start=period_start,
            period_end=period_end,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return summary


@router.get(
    "/import/history",
    response_model=list[ImportLogResponse],
    summary="Get sales import history for a store",
)
async def get_sales_import_history(
    store_id: uuid.UUID = Query(...),
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store_result = await db.execute(
        select(Store).where(Store.id == store_id, Store.user_id == current_user.id)
    )
    if not store_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Store not found")

    result = await db.execute(
        select(ImportLog)
        .where(ImportLog.store_id == store_id, ImportLog.import_type == "sales")
        .order_by(desc(ImportLog.imported_at))
        .limit(limit)
    )
    return result.scalars().all()
