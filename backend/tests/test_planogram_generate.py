import pytest
import uuid

from models.product import Product
from models.sales_data import SalesData


async def _create_store(client, headers):
    response = await client.post(
        "/api/v1/stores",
        json={"name": "RF Indiranagar BLR 560038"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.anyio
async def test_generate_planogram_creates_auto_planogram(client, db_session, auth_headers):
    store = await _create_store(client, auth_headers)
    user_id = uuid.UUID(store["user_id"])
    store_id = uuid.UUID(store["id"])

    db_session.add_all(
        [
            Product(user_id=user_id, sku="SKU-001", name="Organic Milk 1L", category="Dairy", width_cm=8, height_cm=20),
            Product(user_id=user_id, sku="SKU-002", name="Orange Juice 500ml", category="Beverages", width_cm=7, height_cm=22),
            Product(user_id=user_id, sku="SKU-003", name="Salted Chips", category="Snacks", width_cm=15, height_cm=18),
        ]
    )
    db_session.add_all(
        [
            SalesData(
                store_id=store_id,
                sku="SKU-001",
                period_start="2026-01-01",
                period_end="2026-01-31",
                units_sold=120,
                revenue=980.0,
                ingestion_method="manual",
            ),
            SalesData(
                store_id=store_id,
                sku="SKU-002",
                period_start="2026-01-01",
                period_end="2026-01-31",
                units_sold=90,
                revenue=760.0,
                ingestion_method="manual",
            ),
        ]
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/planograms/generate",
        json={"store_id": store["id"], "generation_level": "store"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["generation_method"] == "auto"
    assert body["planogram_json"]["confidence"]["tier"] in {"high", "medium", "low"}
    assert body["planogram_json"]["shelf_config"]["shelf_count"] == 5


@pytest.mark.anyio
async def test_generate_planogram_requires_force_when_latest_auto_was_edited(client, db_session, auth_headers):
    store = await _create_store(client, auth_headers)
    user_id = uuid.UUID(store["user_id"])

    db_session.add(Product(user_id=user_id, sku="SKU-001", name="Organic Milk 1L", category="Dairy", width_cm=8, height_cm=20))
    await db_session.commit()

    first = await client.post(
        "/api/v1/planograms/generate",
        json={"store_id": store["id"], "generation_level": "store"},
        headers=auth_headers,
    )
    assert first.status_code == 201

    planogram_id = first.json()["id"]
    update = await client.put(
        f"/api/v1/planograms/{planogram_id}",
        json={"name": "Edited by user"},
        headers=auth_headers,
    )
    assert update.status_code == 200

    blocked = await client.post(
        "/api/v1/planograms/generate",
        json={"store_id": store["id"], "generation_level": "store"},
        headers=auth_headers,
    )
    assert blocked.status_code == 409

    forced = await client.post(
        "/api/v1/planograms/generate",
        json={"store_id": store["id"], "generation_level": "store", "force": True},
        headers=auth_headers,
    )
    assert forced.status_code == 201
