import pytest


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


async def _create_zone(client, headers, layout_id: str):
    response = await client.post(
        "/api/v1/zones",
        json={
            "layout_id": layout_id,
            "name": "Zone",
            "zone_type": "aisle",
            "width": 5,
            "height": 4,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


async def _create_shelf(client, headers, zone_id: str, payload=None):
    payload = payload or {
        "zone_id": zone_id,
        "width_cm": 120,
        "height_cm": 30,
        "num_rows": 2,
    }
    response = await client.post("/api/v1/shelves", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


@pytest.mark.anyio
async def test_create_shelf_success(client, auth_headers):
    store = await _create_store(client, auth_headers)
    layout = await _create_layout(client, auth_headers, store["id"])
    zone = await _create_zone(client, auth_headers, layout["id"])

    shelf = await _create_shelf(client, auth_headers, zone["id"])
    assert shelf["zone_id"] == zone["id"]


@pytest.mark.anyio
async def test_create_shelf_for_other_user_zone_returns_404(client, auth_headers, other_user_headers):
    store = await _create_store(client, other_user_headers)
    layout = await _create_layout(client, other_user_headers, store["id"])
    zone = await _create_zone(client, other_user_headers, layout["id"])

    response = await client.post(
        "/api/v1/shelves",
        json={"zone_id": zone["id"], "width_cm": 120, "height_cm": 30, "num_rows": 2},
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_create_shelf_invalid_rows_returns_422(client, auth_headers):
    store = await _create_store(client, auth_headers)
    layout = await _create_layout(client, auth_headers, store["id"])
    zone = await _create_zone(client, auth_headers, layout["id"])

    response = await client.post(
        "/api/v1/shelves",
        json={"zone_id": zone["id"], "width_cm": 120, "height_cm": 30, "num_rows": 25},
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_shelf_invalid_width_returns_422(client, auth_headers):
    store = await _create_store(client, auth_headers)
    layout = await _create_layout(client, auth_headers, store["id"])
    zone = await _create_zone(client, auth_headers, layout["id"])

    response = await client.post(
        "/api/v1/shelves",
        json={"zone_id": zone["id"], "width_cm": 0, "height_cm": 30, "num_rows": 1},
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_shelf_success(client, auth_headers):
    store = await _create_store(client, auth_headers)
    layout = await _create_layout(client, auth_headers, store["id"])
    zone = await _create_zone(client, auth_headers, layout["id"])
    shelf = await _create_shelf(client, auth_headers, zone["id"])

    response = await client.put(
        f"/api/v1/shelves/{shelf['id']}",
        json={"width_cm": 140},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["width_cm"] == 140


@pytest.mark.anyio
async def test_update_shelf_for_other_user_returns_404(client, auth_headers, other_user_headers):
    store = await _create_store(client, other_user_headers)
    layout = await _create_layout(client, other_user_headers, store["id"])
    zone = await _create_zone(client, other_user_headers, layout["id"])
    shelf = await _create_shelf(client, other_user_headers, zone["id"])

    response = await client.put(
        f"/api/v1/shelves/{shelf['id']}",
        json={"width_cm": 140},
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_shelf_returns_204(client, auth_headers):
    store = await _create_store(client, auth_headers)
    layout = await _create_layout(client, auth_headers, store["id"])
    zone = await _create_zone(client, auth_headers, layout["id"])
    shelf = await _create_shelf(client, auth_headers, zone["id"])

    response = await client.delete(f"/api/v1/shelves/{shelf['id']}", headers=auth_headers)

    assert response.status_code == 204


@pytest.mark.anyio
async def test_delete_shelf_for_other_user_returns_404(client, auth_headers, other_user_headers):
    store = await _create_store(client, other_user_headers)
    layout = await _create_layout(client, other_user_headers, store["id"])
    zone = await _create_zone(client, other_user_headers, layout["id"])
    shelf = await _create_shelf(client, other_user_headers, zone["id"])

    response = await client.delete(f"/api/v1/shelves/{shelf['id']}", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.anyio
async def test_layout_returns_shelves_nested(client, auth_headers):
    store = await _create_store(client, auth_headers)
    layout = await _create_layout(client, auth_headers, store["id"])
    zone = await _create_zone(client, auth_headers, layout["id"])
    shelf = await _create_shelf(client, auth_headers, zone["id"])

    response = await client.get(f"/api/v1/layouts/{layout['id']}", headers=auth_headers)

    assert response.status_code == 200
    zones = response.json()["zones"]
    assert zones[0]["id"] == zone["id"]
    assert zones[0]["shelves"][0]["id"] == shelf["id"]
