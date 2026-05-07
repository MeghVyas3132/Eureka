import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from db.session import get_db
from ingestion.file_detector import detect_and_validate_file
from ingestion.ingestion_service import run_store_import
from models.user import User
from schemas.ingestion import ImportSummaryResponse
from schemas.store import StoreCreate, StoreListResponse, StoreResponse, StoreUpdate
from services import store_service

router = APIRouter(prefix="/api/v1/stores", tags=["stores"])


@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
async def create_store(
    data: StoreCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await store_service.create_store(current_user.id, data, db)


@router.get("", response_model=StoreListResponse)
async def list_stores(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stores = await store_service.get_stores_for_user(current_user.id, db)
    return {"data": stores, "total": len(stores)}


@router.get("/hierarchy")
async def get_store_hierarchy(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await store_service.get_store_hierarchy_for_user(current_user.id, db)


@router.post(
    "/import",
    response_model=ImportSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Import store list from CSV, Excel, or PDF",
)
async def import_stores(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_format, file_bytes = await detect_and_validate_file(file)
    try:
        summary = await run_store_import(
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


@router.get("/{store_id}", response_model=StoreResponse)
async def get_store(
    store_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store = await store_service.get_store(store_id, current_user.id, db)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


@router.put("/{store_id}", response_model=StoreResponse)
async def update_store(
    store_id: uuid.UUID,
    data: StoreUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store = await store_service.get_store(store_id, current_user.id, db)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return await store_service.update_store(store, data, db)


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store(
    store_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store = await store_service.get_store(store_id, current_user.id, db)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    await store_service.delete_store(store, db)
