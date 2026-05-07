import uuid

import pytest
from sqlalchemy import select

from models.layout import Layout


async def _create_store(client, headers, payload=None):
    payload = payload or {
        "name": "My Store",
        "width_m": 40,
        "height_m": 25,
        "store_type": "supermarket",
    }
    response = await client.post("/api/v1/stores", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


async def _create_layout(client, headers, store_id: str, name: str = "Layout"):
    response = await client.post(
        "/api/v1/layouts",
        json={"store_id": store_id, "name": name},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.anyio
async def test_create_store_success(client, auth_headers):
    response = await client.post(
        "/api/v1/stores",
        json={
            "name": "Eureka Store",
            "width_m": 30,
            "height_m": 20,
            "store_type": "convenience",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Eureka Store"
    assert body["store_type"] == "convenience"
    assert body["width_m"] == 30
    assert body["height_m"] == 20


@pytest.mark.anyio
async def test_create_store_missing_name_returns_422(client, auth_headers):
    response = await client.post(
        "/api/v1/stores",
        json={"width_m": 20, "height_m": 10, "store_type": "supermarket"},
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_store_invalid_store_type_returns_422(client, auth_headers):
    response = await client.post(
        "/api/v1/stores",
        json={
            "name": "Invalid",
            "width_m": 20,
            "height_m": 10,
            "store_type": "invalid",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_store_invalid_width_returns_422(client, auth_headers):
    response = await client.post(
        "/api/v1/stores",
        json={
            "name": "Invalid",
            "width_m": 0,
            "height_m": 10,
            "store_type": "supermarket",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_list_stores_returns_only_current_user(client, auth_headers, other_user_headers):
    store = await _create_store(
        client,
        auth_headers,
        {"name": "Mine", "width_m": 10, "height_m": 10, "store_type": "supermarket"},
    )
    await _create_store(
        client,
        other_user_headers,
        {"name": "Other", "width_m": 12, "height_m": 12, "store_type": "supermarket"},
    )

    response = await client.get("/api/v1/stores", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["data"][0]["id"] == store["id"]


@pytest.mark.anyio
async def test_list_stores_empty_for_new_user(client, auth_headers):
    response = await client.get("/api/v1/stores", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["data"] == []


@pytest.mark.anyio
async def test_get_store_hierarchy(client, auth_headers):
    await _create_store(
        client,
        auth_headers,
        {"name": "RF Indiranagar BLR 560038", "width_m": 10, "height_m": 10, "store_type": "supermarket"},
    )
    await _create_store(
        client,
        auth_headers,
        {"name": "RS Koramangala BLR 560034", "width_m": 10, "height_m": 10, "store_type": "supermarket"},
    )

    response = await client.get("/api/v1/stores/hierarchy", headers=auth_headers)

    assert response.status_code == 200
    hierarchy = response.json()
    assert "India" in hierarchy
    assert "Karnataka" in hierarchy["India"]
    assert "Bangalore" in hierarchy["India"]["Karnataka"]


@pytest.mark.anyio
async def test_import_stores_from_csv(client, auth_headers):
    csv_payload = (
        "store_name,city,state,store_type\\n"
        "RF Indiranagar BLR 560038,Bangalore,Karnataka,supermarket\\n"
    )
    files = {"file": ("stores.csv", csv_payload, "text/csv")}

    response = await client.post("/api/v1/stores/import", headers=auth_headers, files=files)

    assert response.status_code == 200
    summary = response.json()
    assert summary["import_type"] == "store"
    assert summary["success"] == 1

    stores_response = await client.get("/api/v1/stores", headers=auth_headers)
    assert stores_response.status_code == 200
    assert stores_response.json()["total"] == 1


@pytest.mark.anyio
async def test_get_store_for_owner(client, auth_headers):
    store = await _create_store(client, auth_headers)

    response = await client.get(f"/api/v1/stores/{store['id']}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == store["id"]


@pytest.mark.anyio
async def test_get_store_for_other_user_returns_404(client, auth_headers, other_user_headers):
    store = await _create_store(client, other_user_headers)

    response = await client.get(f"/api/v1/stores/{store['id']}", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_store_nonexistent_returns_404(client, auth_headers):
    response = await client.get(f"/api/v1/stores/{uuid.uuid4()}", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.anyio
async def test_update_store_partial(client, auth_headers):
    store = await _create_store(client, auth_headers)

    response = await client.put(
        f"/api/v1/stores/{store['id']}",
        json={"name": "Updated"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated"
    assert response.json()["width_m"] == store["width_m"]


@pytest.mark.anyio
async def test_update_store_for_other_user_returns_404(client, auth_headers, other_user_headers):
    store = await _create_store(client, other_user_headers)

    response = await client.put(
        f"/api/v1/stores/{store['id']}",
        json={"name": "Nope"},
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_store_returns_204(client, auth_headers):
    store = await _create_store(client, auth_headers)

    response = await client.delete(f"/api/v1/stores/{store['id']}", headers=auth_headers)

    assert response.status_code == 204


@pytest.mark.anyio
async def test_delete_store_for_other_user_returns_404(client, auth_headers, other_user_headers):
    store = await _create_store(client, other_user_headers)

    response = await client.delete(f"/api/v1/stores/{store['id']}", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_store_cascades_layouts(client, db_session, auth_headers):
    store = await _create_store(client, auth_headers)
    await _create_layout(client, auth_headers, store["id"], "Layout to delete")

    response = await client.delete(f"/api/v1/stores/{store['id']}", headers=auth_headers)
    assert response.status_code == 204

    result = await db_session.execute(select(Layout).where(Layout.store_id == store["id"]))
    assert result.scalars().first() is None
