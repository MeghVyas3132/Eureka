import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.api_response import error_payload, success_response
from core.constants import (
    APPROVAL_STATUS_FILTER_TYPE,
    ROLE_ADMIN,
)
from core.deps import require_role
from db.session import get_db
from models.layout import Layout
from models.store import Store
from models.user import User
from schemas.admin_onboarding import OnboardingDecisionRequest, OnboardingDecisionResponseData
from schemas.user import AdminUserRead

router = APIRouter(prefix="/api/v1/admin/onboarding", tags=["admin-onboarding"])


def _user_with_layout_count_query():
    return (
        select(
            User.id,
            User.first_name,
            User.last_name,
            User.username,
            User.email,
            User.company_name,
            User.phone_number,
            User.role,
            User.subscription_tier,
            User.approval_status,
            User.reviewed_at,
            User.review_note,
            User.created_at,
            func.count(Layout.id).label("layout_count"),
        )
        .outerjoin(Store, Store.user_id == User.id)
        .outerjoin(Layout, Layout.store_id == Store.id)
        .group_by(User.id)
    )


@router.get("/requests")
async def list_onboarding_requests(
    status_filter: APPROVAL_STATUS_FILTER_TYPE = Query(default="pending", alias="status"),
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_role([ROLE_ADMIN])),
) -> dict:
    query = _user_with_layout_count_query().where(User.role != ROLE_ADMIN)
    if status_filter != "all":
        query = query.where(User.approval_status == status_filter)

    result = await db.execute(query.order_by(User.created_at.desc()))
    records = result.mappings().all()

    response_data: list[dict] = []
    for record in records:
        normalized = dict(record)
        normalized["layout_count"] = int(normalized["layout_count"] or 0)
        response_data.append(AdminUserRead.model_validate(normalized).model_dump(mode="json"))

    return success_response(response_data, "Onboarding requests fetched successfully.")


@router.patch("/requests/{user_id}")
async def review_onboarding_request(
    user_id: uuid.UUID,
    payload: OnboardingDecisionRequest,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_role([ROLE_ADMIN])),
) -> dict:
    if payload.status not in ("approved", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_payload("validation_error", "Status must be either 'approved' or 'rejected'."),
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("user_not_found", "User does not exist."),
        )
    if user.role == ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_payload("invalid_user", "Super admin accounts cannot be reviewed."),
        )

    user.approval_status = payload.status
    user.reviewed_at = datetime.now(timezone.utc)
    user.review_note = payload.review_note.strip() if payload.review_note else None
    await db.commit()

    response_data = OnboardingDecisionResponseData(user_id=user.id, status=user.approval_status)
    return success_response(response_data.model_dump(mode="json"), "Onboarding request updated successfully.")
