import pytest


async def _create_store(client, headers):
    response = await client.post(
        "/api/v1/stores",
        json={"name": "RF Indiranagar BLR 560038", "width_m": 30, "height_m": 20, "store_type": "supermarket"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.anyio
async def test_sales_crud_flow(client, auth_headers):
    store = await _create_store(client, auth_headers)

    create_response = await client.post(
        "/api/v1/sales",
        json={
            "store_id": store["id"],
            "sku": "sku-001",
            "units_sold": 120,
            "revenue": 980.5,
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["sku"] == "SKU-001"
    assert created["units_sold"] == 120

    list_response = await client.get(f"/api/v1/sales?store_id={store['id']}", headers=auth_headers)
    assert list_response.status_code == 200
    list_body = list_response.json()
    assert list_body["total"] == 1

    sales_id = created["id"]
    update_response = await client.put(
        f"/api/v1/sales/{sales_id}",
        json={"revenue": 1020.25, "units_sold": 150},
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["revenue"] == 1020.25
    assert updated["units_sold"] == 150

    delete_response = await client.delete(f"/api/v1/sales/{sales_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    list_after_delete = await client.get(f"/api/v1/sales?store_id={store['id']}", headers=auth_headers)
    assert list_after_delete.status_code == 200
    assert list_after_delete.json()["total"] == 0


@pytest.mark.anyio
async def test_sales_upsert_on_same_store_sku_period(client, auth_headers):
    store = await _create_store(client, auth_headers)

    first = await client.post(
        "/api/v1/sales",
        json={
            "store_id": store["id"],
            "sku": "SKU-XYZ",
            "units_sold": 10,
            "revenue": 100,
            "period_start": "2026-02-01",
            "period_end": "2026-02-28",
        },
        headers=auth_headers,
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/v1/sales",
        json={
            "store_id": store["id"],
            "sku": "SKU-XYZ",
            "units_sold": 15,
            "revenue": 180,
            "period_start": "2026-02-01",
            "period_end": "2026-02-28",
        },
        headers=auth_headers,
    )
    assert second.status_code == 201

    listed = await client.get(f"/api/v1/sales?store_id={store['id']}", headers=auth_headers)
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] == 1
    assert body["data"][0]["units_sold"] == 15
    assert body["data"][0]["revenue"] == 180
