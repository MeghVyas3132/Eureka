import uuid

import pytest


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _username_for_email(email: str) -> str:
    return email.split("@", 1)[0].replace("-", "_")


async def _register_and_login(client, email: str, password: str, role: str):
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Plan",
            "last_name": "Limit",
            "email": email,
            "username": _username_for_email(email),
            "company_name": "Limit Test",
            "phone_number": "1234567890",
            "password": password,
            "role": role,
        },
    )
    assert register_response.status_code == 201
    user_id = register_response.json()["data"]["user"]["id"]
    admin_token = await _login_seeded_admin(client)
    approval_response = await client.patch(
        f"/api/v1/admin/onboarding/requests/{user_id}",
        headers=_auth_header(admin_token),
        json={"status": "approved", "review_note": "Approved in test"},
    )
    assert approval_response.status_code == 200
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["data"]["tokens"]["access_token"]


async def _login_seeded_admin(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@aexiz.com", "password": "qwerty123"},
    )
    return response.json()["data"]["tokens"]["access_token"]


async def _create_store(client, token: str):
    response = await client.post(
        "/api/v1/stores",
        headers=_auth_header(token),
        json={
            "name": "Limit Store",
            "width_m": 20,
            "height_m": 15,
            "store_type": "supermarket",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.anyio
async def test_admin_can_list_plan_limits(client):
    token = await _login_seeded_admin(client)

    response = await client.get("/api/v1/admin/plan-limits", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 4


@pytest.mark.anyio
async def test_non_admin_cannot_list_plan_limits(client):
    email = f"user-{uuid.uuid4()}@example.com"
    token = await _register_and_login(client, email, "password123", "merchandiser")

    response = await client.get("/api/v1/admin/plan-limits", headers=_auth_header(token))

    assert response.status_code == 403
    assert response.json()["error"] == "forbidden"


@pytest.mark.anyio
async def test_quota_evaluator_blocks_and_allows_as_expected():
    from services.quota_service import evaluate_planogram_quota

    blocked = evaluate_planogram_quota(current_count=15, annual_planogram_limit=15, is_unlimited=False)
    allowed = evaluate_planogram_quota(current_count=14, annual_planogram_limit=15, is_unlimited=False)
    unlimited = evaluate_planogram_quota(current_count=500, annual_planogram_limit=None, is_unlimited=True)

    assert blocked["allowed"] is False
    assert blocked["error_code"] == "quota_exceeded"
    assert allowed["allowed"] is True
    assert allowed["remaining"] == 1
    assert unlimited["allowed"] is True
    assert unlimited["limit"] is None


@pytest.mark.anyio
async def test_layout_creation_uses_per_user_limit_override(client):
    admin_token = await _login_seeded_admin(client)
    email = f"quota-{uuid.uuid4()}@example.com"
    user_token = await _register_and_login(client, email, "password123", "merchandiser")

    users_response = await client.get("/api/v1/admin/users", headers=_auth_header(admin_token))
    user_record = next(record for record in users_response.json()["data"] if record["email"] == email)
    limit_response = await client.patch(
        f"/api/v1/admin/users/{user_record['id']}/plan-limit",
        headers=_auth_header(admin_token),
        json={"annual_planogram_limit": 1, "is_unlimited": False},
    )
    assert limit_response.status_code == 200

    store = await _create_store(client, user_token)
    first_layout = await client.post(
        "/api/v1/layouts",
        headers=_auth_header(user_token),
        json={"store_id": store["id"], "name": "Allowed"},
    )
    assert first_layout.status_code == 201

    blocked_layout = await client.post(
        "/api/v1/layouts",
        headers=_auth_header(user_token),
        json={"store_id": store["id"], "name": "Blocked"},
    )
    assert blocked_layout.status_code == 403
    assert blocked_layout.json()["error"] == "quota_exceeded"
