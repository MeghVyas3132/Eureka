import uuid
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ingestion.file_detector import FileFormat
from ingestion.parsers.csv_parser import CSVParser
from ingestion.parsers.excel_parser import ExcelParser
from ingestion.parsers.pdf_parser import PDFParser
from ingestion.sku_deduplicator import SKUDeduplicator
from ingestion.storage_service import archive_file
from ingestion.validators.base_validator import RowError, parse_date
from ingestion.validators.product_validator import validate_product_rows
from ingestion.validators.sales_validator import validate_sales_rows
from ingestion.validators.store_validator import validate_store_rows
from models.import_log import ImportLog
from models.product import Product
from models.sales_data import SalesData
from models.store import Store
from schemas.ingestion import ImportSummaryResponse
from services.data_normalization import normalise_product, normalise_sales
from services.store_intelligence import StoreIntelligenceEngine

MAX_ERROR_DETAIL_ENTRIES = 100
MAX_UPLOAD_ROWS = 50_000
DEFAULT_STORE_WIDTH_M = 30.0
DEFAULT_STORE_HEIGHT_M = 20.0


def _get_parser(file_format: FileFormat):
    return {
        FileFormat.CSV: CSVParser(),
        FileFormat.EXCEL: ExcelParser(),
        FileFormat.PDF: PDFParser(),
    }[file_format]


def _build_error_detail(errors: Iterable[RowError]) -> list[dict]:
    return [{"row": err.row, "reason": err.reason} for err in errors]


def _resolve_status(success_count: int, error_count: int) -> str:
    if success_count == 0 and error_count > 0:
        return "failed"
    if success_count > 0 and error_count > 0:
        return "partial"
    return "completed"


async def _log_failed_import(
    *,
    import_id: uuid.UUID,
    import_type: str,
    file_format: str,
    original_filename: str,
    file_size_bytes: int,
    user_id: uuid.UUID,
    db: AsyncSession,
    store_id: uuid.UUID | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    error_message: str,
) -> None:
    log = ImportLog(
        id=import_id,
        user_id=user_id,
        store_id=store_id,
        import_type=import_type,
        file_format=file_format,
        original_filename=original_filename,
        file_size_bytes=file_size_bytes,
        total_rows=0,
        success_count=0,
        skipped_count=0,
        error_count=1,
        error_detail=[{"row": 0, "reason": error_message}],
        period_start=period_start,
        period_end=period_end,
        status="failed",
    )
    db.add(log)
    await db.commit()


async def run_product_import(
    *,
    file_bytes: bytes,
    file_format: FileFormat,
    original_filename: str,
    file_size_bytes: int,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> ImportSummaryResponse:
    import_id = uuid.uuid4()

    parser = _get_parser(file_format)
    try:
        raw_rows = parser.parse(file_bytes)
    except ValueError as exc:
        await _log_failed_import(
            import_id=import_id,
            import_type="product",
            file_format=file_format.value,
            original_filename=original_filename,
            file_size_bytes=file_size_bytes,
            user_id=user_id,
            db=db,
            error_message=f"Parse error: {exc}",
        )
        raise ValueError(f"Parse error: {exc}") from exc

    if not raw_rows:
        await _log_failed_import(
            import_id=import_id,
            import_type="product",
            file_format=file_format.value,
            original_filename=original_filename,
            file_size_bytes=file_size_bytes,
            user_id=user_id,
            db=db,
            error_message="File contains no data rows after the header.",
        )
        raise ValueError("File contains no data rows after the header.")

    if len(raw_rows) > MAX_UPLOAD_ROWS:
        await _log_failed_import(
            import_id=import_id,
            import_type="product",
            file_format=file_format.value,
            original_filename=original_filename,
            file_size_bytes=file_size_bytes,
            user_id=user_id,
            db=db,
            error_message=f"File contains {len(raw_rows):,} rows. Maximum is 50,000 per upload.",
        )
        raise ValueError(f"File contains {len(raw_rows):,} rows. Maximum is 50,000 per upload.")

    result = validate_product_rows(raw_rows)

    existing_products_result = await db.execute(
        select(Product.sku, Product.name).where(Product.user_id == user_id)
    )
    existing_products = [
        {"sku": sku, "name": name}
        for sku, name in existing_products_result.fetchall()
        if sku and name
    ]
    potential_duplicates = SKUDeduplicator().find_duplicates(result.valid_rows, existing_products)

    success_count = 0
    if result.valid_rows:
        for row in result.valid_rows:
            row = normalise_product(row)
            update_fields = {k: v for k, v in row.items() if k != "sku"}
            stmt = (
                pg_insert(Product)
                .values(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    **row,
                )
                .on_conflict_do_update(
                    index_elements=["user_id", "sku"],
                    set_=update_fields,
                )
            )
            await db.execute(stmt)
            success_count += 1

    s3_key = await archive_file(file_bytes, "product", file_format.value, original_filename)

    error_detail = _build_error_detail(result.error_rows[:MAX_ERROR_DETAIL_ENTRIES])
    status = _resolve_status(success_count, len(result.error_rows))
    log = ImportLog(
        id=import_id,
        user_id=user_id,
        store_id=None,
        import_type="product",
        file_format=file_format.value,
        original_filename=original_filename,
        file_size_bytes=file_size_bytes,
        s3_key=s3_key,
        total_rows=len(raw_rows),
        success_count=success_count,
        skipped_count=result.skipped_count,
        error_count=len(result.error_rows),
        error_detail=error_detail if error_detail else None,
        status=status,
    )
    db.add(log)
    await db.commit()

    return ImportSummaryResponse(
        import_id=import_id,
        import_type="product",
        file_format=file_format.value,
        original_filename=original_filename,
        imported_at=log.imported_at,
        total_rows=len(raw_rows),
        success=success_count,
        skipped=result.skipped_count,
        errors=_build_error_detail(result.error_rows),
        status=status,
        potential_duplicates=potential_duplicates or None,
    )


async def run_sales_import(
    *,
    file_bytes: bytes,
    file_format: FileFormat,
    original_filename: str,
    file_size_bytes: int,
    user_id: uuid.UUID,
    store_id: uuid.UUID,
    period_start: str | None,
    period_end: str | None,
    db: AsyncSession,
) -> ImportSummaryResponse:
    import_id = uuid.uuid4()

    if period_start:
        parsed_start, err = parse_date(period_start, "period_start")
        if err:
            await _log_failed_import(
                import_id=import_id,
                import_type="sales",
                file_format=file_format.value,
                original_filename=original_filename,
                file_size_bytes=file_size_bytes,
                user_id=user_id,
                db=db,
                store_id=store_id,
                error_message=err,
            )
            raise ValueError(err)
        period_start = parsed_start

    if period_end:
        parsed_end, err = parse_date(period_end, "period_end")
        if err:
            await _log_failed_import(
                import_id=import_id,
                import_type="sales",
                file_format=file_format.value,
                original_filename=original_filename,
                file_size_bytes=file_size_bytes,
                user_id=user_id,
                db=db,
                store_id=store_id,
                error_message=err,
            )
            raise ValueError(err)
        period_end = parsed_end

    if period_start and period_end and period_end < period_start:
        message = f"period_end ({period_end}) must be >= period_start ({period_start})"
        await _log_failed_import(
            import_id=import_id,
            import_type="sales",
            file_format=file_format.value,
            original_filename=original_filename,
            file_size_bytes=file_size_bytes,
            user_id=user_id,
            db=db,
            store_id=store_id,
            period_start=period_start,
            period_end=period_end,
            error_message=message,
        )
        raise ValueError(message)

    parser = _get_parser(file_format)
    try:
        raw_rows = parser.parse(file_bytes)
    except ValueError as exc:
        await _log_failed_import(
            import_id=import_id,
            import_type="sales",
            file_format=file_format.value,
            original_filename=original_filename,
            file_size_bytes=file_size_bytes,
            user_id=user_id,
            db=db,
            store_id=store_id,
            period_start=period_start,
            period_end=period_end,
            error_message=f"Parse error: {exc}",
        )
        raise ValueError(f"Parse error: {exc}") from exc

    if not raw_rows:
        await _log_failed_import(
            import_id=import_id,
            import_type="sales",
            file_format=file_format.value,
            original_filename=original_filename,
            file_size_bytes=file_size_bytes,
            user_id=user_id,
            db=db,
            store_id=store_id,
            period_start=period_start,
            period_end=period_end,
            error_message="File contains no data rows.",
        )
        raise ValueError("File contains no data rows.")

    if len(raw_rows) > MAX_UPLOAD_ROWS:
        await _log_failed_import(
            import_id=import_id,
            import_type="sales",
            file_format=file_format.value,
            original_filename=original_filename,
            file_size_bytes=file_size_bytes,
            user_id=user_id,
            db=db,
            store_id=store_id,
            period_start=period_start,
            period_end=period_end,
            error_message=f"File contains {len(raw_rows):,} rows. Maximum is 50,000 per upload.",
        )
        raise ValueError(f"File contains {len(raw_rows):,} rows. Maximum is 50,000 per upload.")

    result = validate_sales_rows(raw_rows, period_start, period_end)

    known_skus_result = await db.execute(select(Product.sku).where(Product.user_id == user_id))
    known_skus = {row[0] for row in known_skus_result.fetchall()}

    unmatched_skus: list[str] = []
    for row in result.valid_rows:
        sku = row.get("sku")
        if sku and sku not in known_skus and sku not in unmatched_skus:
            unmatched_skus.append(sku)

    success_count = 0
    if result.valid_rows:
        for row in result.valid_rows:
            normalised_row = normalise_sales(row)
            row_for_db = {k: v for k, v in normalised_row.items() if k != "revenue_per_unit"}

            update_fields = {
                "revenue": row_for_db["revenue"],
                "ingestion_method": row_for_db.get("ingestion_method", "file_import"),
            }
            if "units_sold" in row_for_db:
                update_fields["units_sold"] = row_for_db["units_sold"]

            stmt = (
                pg_insert(SalesData)
                .values(
                    id=uuid.uuid4(),
                    store_id=store_id,
                    **row_for_db,
                )
                .on_conflict_do_update(
                    index_elements=["store_id", "sku", "period_start", "period_end"],
                    set_=update_fields,
                )
            )
            await db.execute(stmt)
            success_count += 1

    s3_key = await archive_file(file_bytes, "sales", file_format.value, original_filename)

    error_detail = _build_error_detail(result.error_rows[:MAX_ERROR_DETAIL_ENTRIES])
    status = _resolve_status(success_count, len(result.error_rows))
    log = ImportLog(
        id=import_id,
        user_id=user_id,
        store_id=store_id,
        import_type="sales",
        file_format=file_format.value,
        original_filename=original_filename,
        file_size_bytes=file_size_bytes,
        s3_key=s3_key,
        total_rows=len(raw_rows),
        success_count=success_count,
        skipped_count=result.skipped_count,
        error_count=len(result.error_rows),
        error_detail=error_detail if error_detail else None,
        period_start=period_start,
        period_end=period_end,
        unmatched_skus=unmatched_skus[:50] if unmatched_skus else None,
        status=status,
    )
    db.add(log)
    await db.commit()

    return ImportSummaryResponse(
        import_id=import_id,
        import_type="sales",
        file_format=file_format.value,
        original_filename=original_filename,
        imported_at=log.imported_at,
        total_rows=len(raw_rows),
        success=success_count,
        skipped=result.skipped_count,
        errors=_build_error_detail(result.error_rows),
        status=status,
        period_start=period_start,
        period_end=period_end,
        unmatched_skus=unmatched_skus,
    )


async def run_store_import(
    *,
    file_bytes: bytes,
    file_format: FileFormat,
    original_filename: str,
    file_size_bytes: int,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> ImportSummaryResponse:
    import_id = uuid.uuid4()

    parser = _get_parser(file_format)
    try:
        raw_rows = parser.parse(file_bytes)
    except ValueError as exc:
        await _log_failed_import(
            import_id=import_id,
            import_type="store",
            file_format=file_format.value,
            original_filename=original_filename,
            file_size_bytes=file_size_bytes,
            user_id=user_id,
            db=db,
            error_message=f"Parse error: {exc}",
        )
        raise ValueError(f"Parse error: {exc}") from exc

    if not raw_rows:
        await _log_failed_import(
            import_id=import_id,
            import_type="store",
            file_format=file_format.value,
            original_filename=original_filename,
            file_size_bytes=file_size_bytes,
            user_id=user_id,
            db=db,
            error_message="File contains no data rows after the header.",
        )
        raise ValueError("File contains no data rows after the header.")

    if len(raw_rows) > MAX_UPLOAD_ROWS:
        await _log_failed_import(
            import_id=import_id,
            import_type="store",
            file_format=file_format.value,
            original_filename=original_filename,
            file_size_bytes=file_size_bytes,
            user_id=user_id,
            db=db,
            error_message=f"File contains {len(raw_rows):,} rows. Maximum is 50,000 per upload.",
        )
        raise ValueError(f"File contains {len(raw_rows):,} rows. Maximum is 50,000 per upload.")

    result = validate_store_rows(raw_rows)
    parser_service = StoreIntelligenceEngine()

    success_count = 0
    for row in result.valid_rows:
        parsed = parser_service.parse(row.get("raw_name") or row.get("name") or "")
        payload = {
            "name": row.get("name") or parsed.get("display_name") or "Unnamed Store",
            "raw_name": row.get("raw_name") or row.get("name") or "",
            "display_name": parsed.get("display_name") or row.get("name") or "Unnamed Store",
            "country": parsed.get("country") or "India",
            "state": row.get("state") or parsed.get("state"),
            "city": row.get("city") or parsed.get("city"),
            "locality": parsed.get("locality"),
            "detected_chain": parsed.get("detected_chain"),
            "pin_code": parsed.get("pin_code"),
            "parse_confidence": parsed.get("parse_confidence"),
            "source": "file_import",
            "store_type": row.get("store_type") or parsed.get("store_type") or "supermarket",
            "width_m": DEFAULT_STORE_WIDTH_M,
            "height_m": DEFAULT_STORE_HEIGHT_M,
        }

        existing_result = await db.execute(
            select(Store).where(Store.user_id == user_id, Store.raw_name == payload["raw_name"])
        )
        existing_store = existing_result.scalar_one_or_none()
        if existing_store:
            for key, value in payload.items():
                setattr(existing_store, key, value)
        else:
            db.add(Store(user_id=user_id, **payload))
        success_count += 1

    s3_key = await archive_file(file_bytes, "store", file_format.value, original_filename)

    error_detail = _build_error_detail(result.error_rows[:MAX_ERROR_DETAIL_ENTRIES])
    status = _resolve_status(success_count, len(result.error_rows))
    log = ImportLog(
        id=import_id,
        user_id=user_id,
        store_id=None,
        import_type="store",
        file_format=file_format.value,
        original_filename=original_filename,
        file_size_bytes=file_size_bytes,
        s3_key=s3_key,
        total_rows=len(raw_rows),
        success_count=success_count,
        skipped_count=result.skipped_count,
        error_count=len(result.error_rows),
        error_detail=error_detail if error_detail else None,
        status=status,
    )
    db.add(log)
    await db.commit()

    return ImportSummaryResponse(
        import_id=import_id,
        import_type="store",
        file_format=file_format.value,
        original_filename=original_filename,
        imported_at=log.imported_at,
        total_rows=len(raw_rows),
        success=success_count,
        skipped=result.skipped_count,
        errors=_build_error_detail(result.error_rows),
        status=status,
    )
