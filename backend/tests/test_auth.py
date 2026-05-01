import uuid

import pytest


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_payload(email: str, username: str, role: str = "merchandiser") -> dict:
    return {
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "username": username,
        "company_name": "Acme Retail",
        "phone_number": "1234567890",
        "password": "password123",
        "role": role,
    }


async def _login_seeded_admin(client) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@aexiz.com", "password": "qwerty123"},
    )
    assert response.status_code == 200
    return response.json()["data"]["tokens"]["access_token"]


async def _approve_user(client, admin_token: str, user_id: str) -> None:
    response = await client.patch(
        f"/api/v1/admin/onboarding/requests/{user_id}",
        headers=_auth_header(admin_token),
        json={"status": "approved", "review_note": "Approved for onboarding"},
    )
    assert response.status_code == 200


@pytest.mark.anyio
async def test_register_success_creates_pending_request(client):
    payload = _register_payload("new-user@example.com", "new_user")

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["data"]["user"]["email"] == payload["email"]
    assert body["data"]["user"]["first_name"] == payload["first_name"]
    assert body["data"]["user"]["last_name"] == payload["last_name"]
    assert body["data"]["user"]["username"] == payload["username"]
    assert body["data"]["user"]["company_name"] == payload["company_name"]
    assert body["data"]["user"]["phone_number"] == payload["phone_number"]
    assert body["data"]["user"]["approval_status"] == "pending"
    assert body["data"]["requires_admin_approval"] is True


@pytest.mark.anyio
async def test_register_admin_is_not_allowed(client):
    payload = _register_payload("admin-user@example.com", "admin_candidate", role="admin")

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


@pytest.mark.anyio
async def test_register_duplicate_email_returns_conflict(client):
    payload = _register_payload("duplicate@example.com", "duplicate_user")

    first_response = await client.post("/api/v1/auth/register", json=payload)
    second_response = await client.post("/api/v1/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["error"] == "email_exists"


@pytest.mark.anyio
async def test_register_duplicate_username_returns_conflict(client):
    first_response = await client.post("/api/v1/auth/register", json=_register_payload("first@example.com", "shared_user"))
    second_response = await client.post("/api/v1/auth/register", json=_register_payload("second@example.com", "shared_user"))

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["error"] == "username_exists"


@pytest.mark.anyio
async def test_pending_user_cannot_login_until_approved(client):
    email = f"{uuid.uuid4()}@example.com"
    payload = _register_payload(email, f"user_{uuid.uuid4().hex[:8]}")
    await client.post("/api/v1/auth/register", json=payload)

    login_response = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})

    assert login_response.status_code == 403
    assert login_response.json()["error"] == "account_pending_approval"


@pytest.mark.anyio
async def test_approved_user_can_login(client):
    email = f"{uuid.uuid4()}@example.com"
    payload = _register_payload(email, f"user_{uuid.uuid4().hex[:8]}")
    register_response = await client.post("/api/v1/auth/register", json=payload)
    user_id = register_response.json()["data"]["user"]["id"]

    admin_token = await _login_seeded_admin(client)
    await _approve_user(client, admin_token, user_id)

    login_response = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})

    assert login_response.status_code == 200
    body = login_response.json()
    assert body["data"]["user"]["email"] == email
    assert body["data"]["tokens"]["access_token"]
    assert body["data"]["tokens"]["refresh_token"]


@pytest.mark.anyio
async def test_rejected_user_cannot_login(client):
    email = f"{uuid.uuid4()}@example.com"
    payload = _register_payload(email, f"user_{uuid.uuid4().hex[:8]}")
    register_response = await client.post("/api/v1/auth/register", json=payload)
    user_id = register_response.json()["data"]["user"]["id"]

    admin_token = await _login_seeded_admin(client)
    reject_response = await client.patch(
        f"/api/v1/admin/onboarding/requests/{user_id}",
        headers=_auth_header(admin_token),
        json={"status": "rejected", "review_note": "Invalid company details"},
    )
    assert reject_response.status_code == 200

    login_response = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})

    assert login_response.status_code == 403
    assert login_response.json()["error"] == "account_rejected"


@pytest.mark.anyio
async def test_seeded_admin_login_succeeds(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@aexiz.com", "password": "qwerty123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["user"]["role"] == "admin"
    assert body["data"]["user"]["approval_status"] == "approved"


@pytest.mark.anyio
async def test_login_invalid_credentials(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["error"] == "invalid_credentials"


@pytest.mark.anyio
async def test_refresh_returns_new_token_pair_for_approved_user(client):
    email = f"{uuid.uuid4()}@example.com"
    payload = _register_payload(email, f"user_{uuid.uuid4().hex[:8]}")
    register_response = await client.post("/api/v1/auth/register", json=payload)
    user_id = register_response.json()["data"]["user"]["id"]

    admin_token = await _login_seeded_admin(client)
    await _approve_user(client, admin_token, user_id)

    login_response = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    refresh_token = login_response.json()["data"]["tokens"]["refresh_token"]

    refresh_response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    assert refresh_response.status_code == 200
    body = refresh_response.json()
    assert body["data"]["tokens"]["access_token"]
    assert body["data"]["tokens"]["refresh_token"]
