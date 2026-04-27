import uuid

import pytest


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _register_and_login(client, email: str, password: str, role: str):
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "role": role,
        },
    )
    assert register_response.status_code == 201

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    return login_response.json()["data"]["tokens"]["access_token"]


async def _login_seeded_admin(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@aexiz.com", "password": "qwerty123"},
    )
    assert response.status_code == 200
    return response.json()["data"]["tokens"]["access_token"]


@pytest.mark.anyio
async def test_layout_creation_is_blocked_when_tier_limit_reached(client):
    admin_token = await _login_seeded_admin(client)
    user_token = await _register_and_login(
        client,
        f"plus-{uuid.uuid4()}@example.com",
        "password123",
        "merchandiser",
    )

    patch_response = await client.patch(
        "/api/v1/admin/plan-limits/individual-plus",
        json={"annual_planogram_limit": 1, "is_unlimited": False},
        headers=_auth_header(admin_token),
    )
    assert patch_response.status_code == 200

    first_response = await client.post(
        "/api/v1/layouts",
        json={"name": "First Layout"},
        headers=_auth_header(user_token),
    )
    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/layouts",
        json={"name": "Second Layout"},
        headers=_auth_header(user_token),
    )
    assert second_response.status_code == 422
    assert second_response.json()["error"] == "quota_exceeded"


@pytest.mark.anyio
async def test_enterprise_layout_creation_not_blocked(client):
    token = await _register_and_login(
        client,
        f"ent-{uuid.uuid4()}@example.com",
        "password123",
        "enterprise",
    )

    first_response = await client.post(
        "/api/v1/layouts",
        json={"name": "Enterprise Layout 1"},
        headers=_auth_header(token),
    )
    second_response = await client.post(
        "/api/v1/layouts",
        json={"name": "Enterprise Layout 2"},
        headers=_auth_header(token),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
