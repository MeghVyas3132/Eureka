import uuid

import pytest


@pytest.mark.anyio
async def test_register_success(client):
    payload = {
        "email": "new-user@example.com",
        "username": "new_user",
        "password": "password123",
        "role": "merchandiser",
    }

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["data"]["user"]["email"] == payload["email"]
    assert body["data"]["user"]["username"] == payload["username"]
    assert body["data"]["user"]["role"] == "merchandiser"
    assert body["data"]["user"]["subscription_tier"] == "individual-plus"
    assert body["data"]["tokens"]["token_type"] == "bearer"
    assert body["data"]["tokens"]["access_token"]
    assert body["data"]["tokens"]["refresh_token"]


@pytest.mark.anyio
async def test_register_admin_is_not_allowed(client):
    payload = {
        "email": "admin-user@example.com",
        "username": "admin_candidate",
        "password": "password123",
        "role": "admin",
    }

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"


@pytest.mark.anyio
async def test_register_duplicate_email_returns_conflict(client):
    payload = {
        "email": "duplicate@example.com",
        "username": "duplicate_user",
        "password": "password123",
        "role": "merchandiser",
    }

    first_response = await client.post("/api/v1/auth/register", json=payload)
    second_response = await client.post("/api/v1/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    body = second_response.json()
    assert body["error"] == "email_exists"


@pytest.mark.anyio
async def test_register_duplicate_username_returns_conflict(client):
    first_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "first@example.com",
            "username": "shared_user",
            "password": "password123",
            "role": "merchandiser",
        },
    )
    second_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "second@example.com",
            "username": "shared_user",
            "password": "password123",
            "role": "enterprise",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    body = second_response.json()
    assert body["error"] == "username_exists"


@pytest.mark.anyio
async def test_login_success(client):
    email = f"{uuid.uuid4()}@example.com"
    register_payload = {
        "email": email,
        "username": f"user_{uuid.uuid4().hex[:8]}",
        "password": "password123",
        "role": "merchandiser",
    }
    await client.post("/api/v1/auth/register", json=register_payload)

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )

    assert login_response.status_code == 200
    body = login_response.json()
    assert body["data"]["user"]["email"] == email
    assert body["data"]["user"]["username"] == register_payload["username"]
    assert body["data"]["user"]["subscription_tier"] == "individual-plus"
    assert body["data"]["tokens"]["access_token"]


@pytest.mark.anyio
async def test_seeded_admin_login_succeeds(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@aexiz.com", "password": "qwerty123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["user"]["role"] == "admin"
    assert body["data"]["user"]["username"] == "admin"
    assert body["data"]["user"]["subscription_tier"] == "admin"


@pytest.mark.anyio
async def test_login_invalid_credentials(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["error"] == "invalid_credentials"


@pytest.mark.anyio
async def test_refresh_returns_new_token_pair(client):
    email = f"{uuid.uuid4()}@example.com"
    password = "password123"

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "password": password,
            "role": "merchandiser",
        },
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    refresh_token = login_response.json()["data"]["tokens"]["refresh_token"]

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 200
    body = refresh_response.json()
    assert body["data"]["tokens"]["access_token"]
    assert body["data"]["tokens"]["refresh_token"]
