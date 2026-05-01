import uuid

import pytest


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_payload(email: str, username: str, role: str = "merchandiser") -> dict:
    return {
        "first_name": "Onboard",
        "last_name": "Candidate",
        "email": email,
        "username": username,
        "company_name": "Pilot Co",
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


@pytest.mark.anyio
async def test_admin_can_list_pending_requests_and_approve(client):
    payload = _register_payload(f"user-{uuid.uuid4()}@example.com", f"user_{uuid.uuid4().hex[:8]}")
    register_response = await client.post("/api/v1/auth/register", json=payload)
    user_id = register_response.json()["data"]["user"]["id"]

    admin_token = await _login_seeded_admin(client)
    pending_response = await client.get(
        "/api/v1/admin/onboarding/requests?status=pending",
        headers=_auth_header(admin_token),
    )
    assert pending_response.status_code == 200
    pending_rows = pending_response.json()["data"]
    pending_row = next(row for row in pending_rows if row["id"] == user_id)
    assert pending_row["approval_status"] == "pending"

    approval_response = await client.patch(
        f"/api/v1/admin/onboarding/requests/{user_id}",
        headers=_auth_header(admin_token),
        json={"status": "approved", "review_note": "Approved"},
    )
    assert approval_response.status_code == 200
    assert approval_response.json()["data"]["status"] == "approved"

    approved_response = await client.get(
        "/api/v1/admin/onboarding/requests?status=approved",
        headers=_auth_header(admin_token),
    )
    assert approved_response.status_code == 200
    approved_rows = approved_response.json()["data"]
    approved_row = next(row for row in approved_rows if row["id"] == user_id)
    assert approved_row["approval_status"] == "approved"
    assert approved_row["review_note"] == "Approved"


@pytest.mark.anyio
async def test_non_admin_cannot_access_onboarding_review_endpoints(client):
    payload = _register_payload(f"user-{uuid.uuid4()}@example.com", f"user_{uuid.uuid4().hex[:8]}")
    register_response = await client.post("/api/v1/auth/register", json=payload)
    user_id = register_response.json()["data"]["user"]["id"]

    admin_token = await _login_seeded_admin(client)
    await client.patch(
        f"/api/v1/admin/onboarding/requests/{user_id}",
        headers=_auth_header(admin_token),
        json={"status": "approved", "review_note": "Approved"},
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    user_token = login_response.json()["data"]["tokens"]["access_token"]

    list_response = await client.get(
        "/api/v1/admin/onboarding/requests?status=all",
        headers=_auth_header(user_token),
    )
    assert list_response.status_code == 403
    assert list_response.json()["error"] == "forbidden"
