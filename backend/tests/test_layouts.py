import pytest
from sqlalchemy import select

from models.layout import LayoutVersion


async def _create_store(client, headers, payload=None):
    payload = payload or {
        "name": "Main Store",
        "width_m": 20,
        "height_m": 15,
        "store_type": "supermarket",
    }
    response = await client.post("/api/v1/stores", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


async def _create_layout(client, headers, store_id: str, name: str = "Layout A"):
    response = await client.post(
        "/api/v1/layouts",
        json={"store_id": store_id, "name": name},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.anyio
async def test_create_layout_and_initial_version(client, db_session, auth_headers):
    store = await _create_store(client, auth_headers)
    layout = await _create_layout(client, auth_headers, store["id"], "New Layout")

    assert layout["store_id"] == store["id"]
    assert layout["name"] == "New Layout"

    version_result = await db_session.execute(
        select(LayoutVersion).where(LayoutVersion.layout_id == layout["id"])
    )
    versions = version_result.scalars().all()
    assert len(versions) == 1
    assert versions[0].version_number == 1


@pytest.mark.anyio
async def test_create_layout_for_other_users_store_returns_404(client, auth_headers, other_user_headers):
    store = await _create_store(client, other_user_headers)

    response = await client.post(
        "/api/v1/layouts",
        json={"store_id": store["id"], "name": "Blocked"},
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_layout_includes_zones_and_versions(client, auth_headers):
    store = await _create_store(client, auth_headers)
    layout = await _create_layout(client, auth_headers, store["id"], "Layout Detail")

    response = await client.get(f"/api/v1/layouts/{layout['id']}", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["zones"] == []
    assert len(payload["versions"]) == 1
    assert "snapshot_json" not in payload["versions"][0]


@pytest.mark.anyio
async def test_get_layout_for_other_user_returns_404(client, auth_headers, other_user_headers):
    store = await _create_store(client, other_user_headers)
    layout = await _create_layout(client, other_user_headers, store["id"], "Hidden")

    response = await client.get(f"/api/v1/layouts/{layout['id']}", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.anyio
async def test_save_layout_updates_name_and_creates_version(client, db_session, auth_headers):
    store = await _create_store(client, auth_headers)
    layout = await _create_layout(client, auth_headers, store["id"], "Original")

    response = await client.put(
        f"/api/v1/layouts/{layout['id']}",
        json={"name": "Updated"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated"

    version_result = await db_session.execute(
        select(LayoutVersion).where(LayoutVersion.layout_id == layout["id"])
    )
    versions = version_result.scalars().all()
    assert len(versions) == 2


@pytest.mark.anyio
async def test_version_pruning_keeps_last_20(client, db_session, auth_headers):
    store = await _create_store(client, auth_headers)
    layout = await _create_layout(client, auth_headers, store["id"], "Prune")

    for index in range(21):
        response = await client.put(
            f"/api/v1/layouts/{layout['id']}",
            json={"name": f"Prune {index}"},
            headers=auth_headers,
        )
        assert response.status_code == 200

    version_result = await db_session.execute(
        select(LayoutVersion).where(LayoutVersion.layout_id == layout["id"])
    )
    versions = version_result.scalars().all()
    assert len(versions) == 20


@pytest.mark.anyio
async def test_version_list_ordered_desc_and_summary_only(client, auth_headers):
    store = await _create_store(client, auth_headers)
    layout = await _create_layout(client, auth_headers, store["id"], "History")

    await client.put(
        f"/api/v1/layouts/{layout['id']}",
        json={"name": "History 2"},
        headers=auth_headers,
    )

    response = await client.get(f"/api/v1/layouts/{layout['id']}/versions", headers=auth_headers)
    assert response.status_code == 200
    versions = response.json()["data"]

    version_numbers = [item["version_number"] for item in versions]
    assert version_numbers == sorted(version_numbers, reverse=True)
    assert "snapshot_json" not in versions[0]


@pytest.mark.anyio
async def test_rollback_restores_zones_and_versions(client, db_session, auth_headers):
    store = await _create_store(client, auth_headers)
    layout = await _create_layout(client, auth_headers, store["id"], "Rollback")

    zone_response = await client.post(
        "/api/v1/zones",
        json={
            "layout_id": layout["id"],
            "name": "Zone 1",
            "zone_type": "aisle",
            "width": 5,
            "height": 4,
        },
        headers=auth_headers,
    )
    assert zone_response.status_code == 201
    zone_id = zone_response.json()["id"]

    save_response = await client.put(
        f"/api/v1/layouts/{layout['id']}",
        json={"name": "Rollback v2"},
        headers=auth_headers,
    )
    assert save_response.status_code == 200

    delete_response = await client.delete(f"/api/v1/zones/{zone_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    versions_response = await client.get(
        f"/api/v1/layouts/{layout['id']}/versions",
        headers=auth_headers,
    )
    versions = versions_response.json()["data"]
    target_version = next(item for item in versions if item["version_number"] == 2)

    rollback_response = await client.post(
        f"/api/v1/layouts/{layout['id']}/rollback/{target_version['id']}",
        headers=auth_headers,
    )
    assert rollback_response.status_code == 200

    refreshed_layout = await client.get(
        f"/api/v1/layouts/{layout['id']}",
        headers=auth_headers,
    )
    assert refreshed_layout.status_code == 200
    assert len(refreshed_layout.json()["zones"]) == 1

    version_result = await db_session.execute(
        select(LayoutVersion).where(LayoutVersion.layout_id == layout["id"])
    )
    versions_after = version_result.scalars().all()
    assert len(versions_after) == 3


@pytest.mark.anyio
async def test_rollback_with_wrong_version_returns_404(client, auth_headers):
    store_a = await _create_store(client, auth_headers, {"name": "Store A", "width_m": 10, "height_m": 10, "store_type": "supermarket"})
    store_b = await _create_store(client, auth_headers, {"name": "Store B", "width_m": 12, "height_m": 12, "store_type": "supermarket"})

    layout_a = await _create_layout(client, auth_headers, store_a["id"], "Layout A")
    layout_b = await _create_layout(client, auth_headers, store_b["id"], "Layout B")

    versions_response = await client.get(
        f"/api/v1/layouts/{layout_a['id']}/versions",
        headers=auth_headers,
    )
    version_id = versions_response.json()["data"][0]["id"]

    rollback_response = await client.post(
        f"/api/v1/layouts/{layout_b['id']}/rollback/{version_id}",
        headers=auth_headers,
    )

    assert rollback_response.status_code == 404
