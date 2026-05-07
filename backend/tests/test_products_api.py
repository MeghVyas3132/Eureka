import pytest


@pytest.mark.anyio
async def test_products_crud_flow(client, auth_headers):
    create_response = await client.post(
        "/api/v1/products",
        json={
            "sku": "sku-001",
            "name": "ORGANIC MILK 1L",
            "category": "dairy",
            "price": 149.0,
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["sku"] == "SKU-001"
    assert created["name"] == "Organic Milk 1L"
    assert created["category"] == "Dairy"

    list_response = await client.get("/api/v1/products", headers=auth_headers)
    assert list_response.status_code == 200
    list_body = list_response.json()
    assert list_body["total"] == 1

    product_id = created["id"]
    update_response = await client.put(
        f"/api/v1/products/{product_id}",
        json={"brand": "eureka foods", "name": "organic milk 1l"},
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["brand"] == "Eureka Foods"
    assert updated["name"] == "organic milk 1l"

    delete_response = await client.delete(f"/api/v1/products/{product_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    list_after_delete = await client.get("/api/v1/products", headers=auth_headers)
    assert list_after_delete.status_code == 200
    assert list_after_delete.json()["total"] == 0


@pytest.mark.anyio
async def test_products_filter_missing_dimensions(client, auth_headers):
    await client.post(
        "/api/v1/products",
        json={"sku": "SKU-A", "name": "No Dim Product"},
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/products",
        json={"sku": "SKU-B", "name": "With Dim Product", "width_cm": 10, "height_cm": 20, "depth_cm": 10},
        headers=auth_headers,
    )

    response = await client.get("/api/v1/products?filter=missing_dimensions", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["data"][0]["sku"] == "SKU-A"
