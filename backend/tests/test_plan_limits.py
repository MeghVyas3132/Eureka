import uuid

import pytest


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _username_for_email(email: str) -> str:
    return email.split("@", 1)[0].replace("-", "_")


def _register_payload(email: str, password: str, role: str) -> dict:
    return {
        "first_name": "Plan",
        "last_name": "Tester",
        "email": email,
        "username": _username_for_email(email),
        "company_name": "Plan Inc",
        "phone_number": "1234567890",
        "password": password,
        "role": role,
    }


async def _login_seeded_admin(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@aexiz.com", "password": "qwerty123"},
    )
    return response.json()["data"]["tokens"]["access_token"]


async def _register_and_login(client, email: str, password: str, role: str):
    register_response = await client.post(
        "/api/v1/auth/register",
        json=_register_payload(email, password, role),
    )
    user_id = register_response.json()["data"]["user"]["id"]
    admin_token = await _login_seeded_admin(client)
    approval_response = await client.patch(
        f"/api/v1/admin/onboarding/requests/{user_id}",
        json={"status": "approved", "review_note": "Approved for limits test"},
        headers=_auth_header(admin_token),
    )
    assert approval_response.status_code == 200
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return response.json()["data"]["tokens"]["access_token"]


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
