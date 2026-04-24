import uuid

import pytest


@pytest.mark.anyio
async def test_register_success(client):
    payload = {
        "email": "new-user@example.com",
        "password": "password123",
        "role": "merchandiser",
    }

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["data"]["user"]["email"] == payload["email"]
    assert body["data"]["tokens"]["token_type"] == "bearer"
    assert body["data"]["tokens"]["access_token"]
    assert body["data"]["tokens"]["refresh_token"]


@pytest.mark.anyio
async def test_register_duplicate_email_returns_conflict(client):
    payload = {
        "email": "duplicate@example.com",
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
async def test_login_success(client):
    email = f"{uuid.uuid4()}@example.com"
    register_payload = {
        "email": email,
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
    assert body["data"]["tokens"]["access_token"]


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
        json={"email": email, "password": password, "role": "merchandiser"},
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
