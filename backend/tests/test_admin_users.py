import uuid

import pytest


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _username_for_email(email: str) -> str:
    return email.split("@", 1)[0].replace("-", "_")


async def _register_user(client, email: str, password: str, role: str):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Admin",
            "last_name": "TableUser",
            "email": email,
            "username": _username_for_email(email),
            "company_name": "Admin Table",
            "phone_number": "1234567890",
            "password": password,
            "role": role,
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["user"]


async def _login(client, email: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["data"]["tokens"]["access_token"]


async def _register_and_login(client, email: str, password: str, role: str) -> str:
    user = await _register_user(client, email, password, role)
    admin_token = await _login_seeded_admin(client)
    approval_response = await client.patch(
        f"/api/v1/admin/onboarding/requests/{user['id']}",
        headers=_auth_header(admin_token),
        json={"status": "approved", "review_note": "Approved in test"},
    )
    assert approval_response.status_code == 200
    return await _login(client, email, password)


async def _login_seeded_admin(client) -> str:
    return await _login(client, "admin@aexiz.com", "qwerty123")


@pytest.mark.anyio
async def test_admin_can_list_users_with_layout_counts(client):
    admin_token = await _login_seeded_admin(client)

    merch_email = f"merch-{uuid.uuid4()}@example.com"
    merch_password = "password123"
    merch_token = await _register_and_login(client, merch_email, merch_password, "merchandiser")

    enterprise_email = f"enterprise-{uuid.uuid4()}@example.com"
    await _register_user(client, enterprise_email, "password123", "enterprise")

    first_layout_response = await client.post(
        "/api/v1/layouts",
        json={"name": "Layout 1"},
        headers=_auth_header(merch_token),
    )
    second_layout_response = await client.post(
        "/api/v1/layouts",
        json={"name": "Layout 2"},
        headers=_auth_header(merch_token),
    )
    assert first_layout_response.status_code == 201
    assert second_layout_response.status_code == 201

    response = await client.get("/api/v1/admin/users", headers=_auth_header(admin_token))

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) >= 3

    merch_record = next(record for record in body["data"] if record["email"] == merch_email)
    assert merch_record["username"] == _username_for_email(merch_email)
    assert merch_record["first_name"] == "Admin"
    assert merch_record["last_name"] == "TableUser"
    assert merch_record["company_name"] == "Admin Table"
    assert merch_record["phone_number"] == "1234567890"
    assert merch_record["subscription_tier"] == "individual-plus"
    assert merch_record["approval_status"] == "approved"
    assert merch_record["layout_count"] == 2
    assert "password" not in merch_record
    assert "hashed_password" not in merch_record


@pytest.mark.anyio
async def test_non_admin_cannot_list_users(client):
    user_email = f"user-{uuid.uuid4()}@example.com"
    user_token = await _register_and_login(client, user_email, "password123", "merchandiser")

    response = await client.get("/api/v1/admin/users", headers=_auth_header(user_token))

    assert response.status_code == 403
    assert response.json()["error"] == "forbidden"
