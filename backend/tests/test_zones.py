import pytest
from sqlalchemy import select

from models.shelf import Shelf


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


async def _create_zone(client, headers, layout_id: str, payload=None):
    payload = payload or {
        "layout_id": layout_id,
        "name": "Zone",
        "zone_type": "aisle",
        "width": 5,
        "height": 4,
    }
    response = await client.post("/api/v1/zones", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


async def _create_shelf(client, headers, zone_id: str):
    response = await client.post(
        "/api/v1/shelves",
        json={"zone_id": zone_id, "width_cm": 120, "height_cm": 30, "num_rows": 2},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.anyio
async def test_create_zone_success(client, auth_headers):
    store = await _create_store(client, auth_headers)
    layout = await _create_layout(client, auth_headers, store["id"])

    zone = await _create_zone(client, auth_headers, layout["id"])
    assert zone["layout_id"] == layout["id"]
    assert zone["zone_type"] == "aisle"


@pytest.mark.anyio
async def test_create_zone_invalid_type_returns_422(client, auth_headers):
    store = await _create_store(client, auth_headers)
    layout = await _create_layout(client, auth_headers, store["id"])

    response = await client.post(
        "/api/v1/zones",
        json={
            "layout_id": layout["id"],
            "name": "Bad",
            "zone_type": "invalid",
            "width": 5,
            "height": 4,
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_zone_for_other_user_layout_returns_404(client, auth_headers, other_user_headers):
    store = await _create_store(client, other_user_headers)
    layout = await _create_layout(client, other_user_headers, store["id"])

    response = await client.post(
        "/api/v1/zones",
        json={
            "layout_id": layout["id"],
            "name": "Blocked",
            "zone_type": "aisle",
            "width": 5,
            "height": 4,
        },
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_update_zone_partial(client, auth_headers):
    store = await _create_store(client, auth_headers)
    layout = await _create_layout(client, auth_headers, store["id"])
    zone = await _create_zone(client, auth_headers, layout["id"])

    response = await client.put(
        f"/api/v1/zones/{zone['id']}",
        json={"name": "Updated", "x": 2.5},
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Updated"
    assert payload["x"] == 2.5


@pytest.mark.anyio
async def test_update_zone_for_other_user_returns_404(client, auth_headers, other_user_headers):
    store = await _create_store(client, other_user_headers)
    layout = await _create_layout(client, other_user_headers, store["id"])
    zone = await _create_zone(client, other_user_headers, layout["id"])

    response = await client.put(
        f"/api/v1/zones/{zone['id']}",
        json={"name": "Nope"},
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_zone_cascades_shelves(client, db_session, auth_headers):
    store = await _create_store(client, auth_headers)
    layout = await _create_layout(client, auth_headers, store["id"])
    zone = await _create_zone(client, auth_headers, layout["id"])
    await _create_shelf(client, auth_headers, zone["id"])

    response = await client.delete(f"/api/v1/zones/{zone['id']}", headers=auth_headers)

    assert response.status_code == 204
    result = await db_session.execute(select(Shelf).where(Shelf.zone_id == zone["id"]))
    assert result.scalars().first() is None


@pytest.mark.anyio
async def test_delete_zone_for_other_user_returns_404(client, auth_headers, other_user_headers):
    store = await _create_store(client, other_user_headers)
    layout = await _create_layout(client, other_user_headers, store["id"])
    zone = await _create_zone(client, other_user_headers, layout["id"])

    response = await client.delete(f"/api/v1/zones/{zone['id']}", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_layout_includes_zones(client, auth_headers):
    store = await _create_store(client, auth_headers)
    layout = await _create_layout(client, auth_headers, store["id"])
    zone_a = await _create_zone(client, auth_headers, layout["id"], {"layout_id": layout["id"], "name": "A", "zone_type": "aisle", "width": 4, "height": 3})
    zone_b = await _create_zone(client, auth_headers, layout["id"], {"layout_id": layout["id"], "name": "B", "zone_type": "checkout", "width": 6, "height": 2})

    response = await client.get(f"/api/v1/layouts/{layout['id']}", headers=auth_headers)

    assert response.status_code == 200
    zones = response.json()["zones"]
    zone_ids = {zone["id"] for zone in zones}
    assert zone_a["id"] in zone_ids
    assert zone_b["id"] in zone_ids
