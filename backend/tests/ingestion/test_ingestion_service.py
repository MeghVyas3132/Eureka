from pathlib import Path
import uuid

import pytest
from sqlalchemy import select

from core.constants import APPROVAL_APPROVED, ROLE_MERCHANDISER, TIER_INDIVIDUAL_PLUS
from ingestion.file_detector import FileFormat
from ingestion.ingestion_service import run_product_import, run_sales_import
from models.import_log import ImportLog
from models.product import Product
from models.sales_data import SalesData
from models.store import Store
from models.user import User

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _read_fixture(name: str) -> bytes:
    return (FIXTURES_DIR / name).read_bytes()


async def _create_user(db, email: str = "user@example.com") -> User:
    user = User(
        email=email,
        username=f"user_{uuid.uuid4().hex[:6]}",
        hashed_password="hashed",
        role=ROLE_MERCHANDISER,
        subscription_tier=TIER_INDIVIDUAL_PLUS,
        approval_status=APPROVAL_APPROVED,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _create_store(db, user_id: uuid.UUID) -> Store:
    store = Store(
        user_id=user_id,
        name="Test Store",
        width_m=10,
        height_m=10,
        store_type="supermarket",
    )
    db.add(store)
    await db.commit()
    await db.refresh(store)
    return store


@pytest.mark.anyio
async def test_product_import_creates_products(db_session, monkeypatch):
    async def _fake_archive(*_args, **_kwargs):
        return "test-key"

    monkeypatch.setattr("ingestion.ingestion_service.archive_file", _fake_archive)
    user = await _create_user(db_session)

    summary = await run_product_import(
        file_bytes=_read_fixture("products_valid.csv"),
        file_format=FileFormat.CSV,
        original_filename="products_valid.csv",
        file_size_bytes=123,
        user_id=user.id,
        db=db_session,
    )

    result = await db_session.execute(select(Product).where(Product.user_id == user.id))
    products = result.scalars().all()

    assert summary.success == 5
    assert len(products) == 5


@pytest.mark.anyio
async def test_product_import_upserts_duplicate_sku(db_session, monkeypatch):
    async def _fake_archive(*_args, **_kwargs):
        return "test-key"

    monkeypatch.setattr("ingestion.ingestion_service.archive_file", _fake_archive)
    user = await _create_user(db_session, email="dup@example.com")

    product = Product(user_id=user.id, sku="SKU-200", name="Original")
    db_session.add(product)
    await db_session.commit()

    await run_product_import(
        file_bytes=_read_fixture("products_duplicate_sku.csv"),
        file_format=FileFormat.CSV,
        original_filename="products_duplicate_sku.csv",
        file_size_bytes=123,
        user_id=user.id,
        db=db_session,
    )

    result = await db_session.execute(select(Product).where(Product.user_id == user.id))
    products = result.scalars().all()

    assert len(products) == 1
    assert products[0].name == "Updated Name"


@pytest.mark.anyio
async def test_sales_import_with_override(db_session, monkeypatch):
    async def _fake_archive(*_args, **_kwargs):
        return "test-key"

    monkeypatch.setattr("ingestion.ingestion_service.archive_file", _fake_archive)
    user = await _create_user(db_session, email="sales@example.com")
    store = await _create_store(db_session, user.id)

    for sku in ["SKU-001", "SKU-002", "SKU-003"]:
        db_session.add(Product(user_id=user.id, sku=sku, name=f"Product {sku}"))
    await db_session.commit()

    summary = await run_sales_import(
        file_bytes=_read_fixture("sales_valid.csv"),
        file_format=FileFormat.CSV,
        original_filename="sales_valid.csv",
        file_size_bytes=123,
        user_id=user.id,
        store_id=store.id,
        period_start="2025-01-01",
        period_end="2025-01-31",
        db=db_session,
    )

    result = await db_session.execute(select(SalesData).where(SalesData.store_id == store.id))
    sales_rows = result.scalars().all()

    assert summary.success == 3
    assert summary.period_start == "2025-01-01"
    assert len(sales_rows) == 3


@pytest.mark.anyio
async def test_sales_import_unmatched_skus_logged(db_session, monkeypatch):
    async def _fake_archive(*_args, **_kwargs):
        return "test-key"

    monkeypatch.setattr("ingestion.ingestion_service.archive_file", _fake_archive)
    user = await _create_user(db_session, email="unmatched@example.com")
    store = await _create_store(db_session, user.id)

    summary = await run_sales_import(
        file_bytes=_read_fixture("sales_unmatched_skus.csv"),
        file_format=FileFormat.CSV,
        original_filename="sales_unmatched_skus.csv",
        file_size_bytes=123,
        user_id=user.id,
        store_id=store.id,
        period_start="2025-01-01",
        period_end="2025-01-31",
        db=db_session,
    )

    assert summary.unmatched_skus == ["SKU-999", "SKU-998"]

    result = await db_session.execute(select(ImportLog).where(ImportLog.store_id == store.id))
    log = result.scalar_one()
    assert log.unmatched_skus == ["SKU-999", "SKU-998"]


@pytest.mark.anyio
async def test_failed_import_writes_log(db_session, monkeypatch):
    async def _fake_archive(*_args, **_kwargs):
        return "test-key"

    monkeypatch.setattr("ingestion.ingestion_service.archive_file", _fake_archive)
    user = await _create_user(db_session, email="fail@example.com")

    with pytest.raises(ValueError):
        await run_product_import(
            file_bytes=_read_fixture("header_only.csv"),
            file_format=FileFormat.CSV,
            original_filename="header_only.csv",
            file_size_bytes=123,
            user_id=user.id,
            db=db_session,
        )

    result = await db_session.execute(select(ImportLog).where(ImportLog.imported_by == user.id))
    log = result.scalar_one()

    assert log.status == "failed"
    assert log.error_count == 1
