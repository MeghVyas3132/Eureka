from pathlib import Path
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from core.constants import APPROVAL_APPROVED, ROLE_MERCHANDISER, TIER_INDIVIDUAL_PLUS
from core.deps import get_current_user
from db.session import get_db
from main import app
from models.product import Product
from models.store import Store
from models.user import User

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _read_fixture(name: str) -> bytes:
    return (FIXTURES_DIR / name).read_bytes()


@pytest.fixture()
async def authed_client(db_session):
    user = User(
        email="ingestion@example.com",
        username=f"ingestion_{uuid.uuid4().hex[:6]}",
        hashed_password="hashed",
        role=ROLE_MERCHANDISER,
        subscription_tier=TIER_INDIVIDUAL_PLUS,
        approval_status=APPROVAL_APPROVED,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client, user

    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_products_import_success(authed_client):
    client, _ = authed_client

    response = await client.post(
        "/api/v1/products/import",
        files={"file": ("products_valid.csv", _read_fixture("products_valid.csv"), "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["success"] == 5


@pytest.mark.anyio
async def test_products_import_header_only_returns_422(authed_client):
    client, _ = authed_client

    response = await client.post(
        "/api/v1/products/import",
        files={"file": ("header_only.csv", _read_fixture("header_only.csv"), "text/csv")},
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_products_import_rejects_large_file(authed_client):
    client, _ = authed_client
    large_bytes = b"a" * (10 * 1024 * 1024 + 1)

    response = await client.post(
        "/api/v1/products/import",
        files={"file": ("large.csv", large_bytes, "text/csv")},
    )

    assert response.status_code == 413


@pytest.mark.anyio
async def test_sales_import_success(authed_client, db_session):
    client, user = authed_client

    store = Store(user_id=user.id, name="Store", width_m=10, height_m=10, store_type="supermarket")
    db_session.add(store)
    db_session.add(Product(user_id=user.id, sku="SKU-001", name="Product 1"))
    db_session.add(Product(user_id=user.id, sku="SKU-002", name="Product 2"))
    db_session.add(Product(user_id=user.id, sku="SKU-003", name="Product 3"))
    await db_session.commit()

    response = await client.post(
        f"/api/v1/sales/import?store_id={store.id}&period_start=2025-01-01&period_end=2025-01-31",
        files={"file": ("sales_valid.csv", _read_fixture("sales_valid.csv"), "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] == 3
    assert body["period_start"] == "2025-01-01"


@pytest.mark.anyio
async def test_sales_import_store_not_found(authed_client):
    client, _ = authed_client

    response = await client.post(
        f"/api/v1/sales/import?store_id={uuid.uuid4()}&period_start=2025-01-01&period_end=2025-01-31",
        files={"file": ("sales_valid.csv", _read_fixture("sales_valid.csv"), "text/csv")},
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_sales_import_period_range_invalid(authed_client, db_session):
    client, user = authed_client
    store = Store(user_id=user.id, name="Store", width_m=10, height_m=10, store_type="supermarket")
    db_session.add(store)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/sales/import?store_id={store.id}&period_start=2025-02-01&period_end=2025-01-01",
        files={"file": ("sales_valid.csv", _read_fixture("sales_valid.csv"), "text/csv")},
    )

    assert response.status_code == 422
