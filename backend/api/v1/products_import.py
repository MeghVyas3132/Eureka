from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from db.session import get_db
from ingestion.file_detector import detect_and_validate_file
from ingestion.ingestion_service import run_product_import
from models.import_log import ImportLog
from models.user import User
from schemas.ingestion import ImportLogResponse, ImportSummaryResponse

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.post(
    "/import",
    response_model=ImportSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Import products from CSV, Excel, or PDF",
)
async def import_products(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_format, file_bytes = await detect_and_validate_file(file)

    try:
        summary = await run_product_import(
            file_bytes=file_bytes,
            file_format=file_format,
            original_filename=file.filename or "upload",
            file_size_bytes=len(file_bytes),
            user_id=current_user.id,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return summary


@router.get(
    "/import/history",
    response_model=list[ImportLogResponse],
    summary="Get product import history for current user",
)
async def get_product_import_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ImportLog)
        .where(ImportLog.imported_by == current_user.id, ImportLog.import_type == "product")
        .order_by(desc(ImportLog.imported_at))
        .limit(limit)
    )
    return result.scalars().all()
