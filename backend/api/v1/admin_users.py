import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.api_response import error_payload, success_response
from core.constants import ROLE_ADMIN
from core.deps import require_role
from db.session import get_db
from models.layout import Layout
from models.store import Store
from models.user import User
from schemas.user import AdminUserPlanLimitResponse, AdminUserPlanLimitUpdate, AdminUserRead, UserPlanLimitRead
from services.plan_limit_service import get_plan_limits_by_tier, resolve_user_plan_limit

router = APIRouter(prefix="/api/v1/admin/users", tags=["admin-users"])


@router.get("")
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_role([ROLE_ADMIN])),
) -> dict:
    plan_limits_by_tier = await get_plan_limits_by_tier(db)
    query = (
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
            User.annual_planogram_limit_override,
            User.is_unlimited_override,
            User.approval_status,
            User.reviewed_at,
            User.review_note,
            User.created_at,
            func.count(Layout.id).label("layout_count"),
        )
        .outerjoin(Store, Store.user_id == User.id)
        .outerjoin(Layout, Layout.store_id == Store.id)
        .group_by(User.id)
        .order_by(User.created_at.desc())
    )
    result = await db.execute(query)
    records = result.mappings().all()

    response_data: list[dict] = []
    for record in records:
        normalized = dict(record)
        normalized["layout_count"] = int(normalized["layout_count"] or 0)
        normalized["plan_limit"] = resolve_user_plan_limit(
            subscription_tier=normalized["subscription_tier"],
            annual_override=normalized.get("annual_planogram_limit_override"),
            is_unlimited_override=normalized.get("is_unlimited_override"),
            plan_limits_by_tier=plan_limits_by_tier,
        )
        normalized.pop("annual_planogram_limit_override", None)
        normalized.pop("is_unlimited_override", None)
        response_data.append(AdminUserRead.model_validate(normalized).model_dump(mode="json"))

    return success_response(response_data, "Users fetched successfully.")


@router.patch("/{user_id}/plan-limit")
async def update_user_plan_limit(
    user_id: uuid.UUID,
    payload: AdminUserPlanLimitUpdate,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_role([ROLE_ADMIN])),
) -> dict:
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
            detail=error_payload("invalid_user", "Super admin accounts cannot be updated."),
        )

    if payload.use_tier_default:
        user.is_unlimited_override = None
        user.annual_planogram_limit_override = None
    elif payload.annual_planogram_limit is None and payload.is_unlimited is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_payload("validation_error", "Provide annual_planogram_limit or is_unlimited."),
        )
    else:
        if payload.is_unlimited:
            user.is_unlimited_override = True
            user.annual_planogram_limit_override = None
        else:
            if payload.annual_planogram_limit is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=error_payload(
                        "validation_error",
                        "annual_planogram_limit is required when is_unlimited is false.",
                    ),
                )
            user.is_unlimited_override = False
            user.annual_planogram_limit_override = payload.annual_planogram_limit

    await db.commit()
    await db.refresh(user)

    plan_limits_by_tier = await get_plan_limits_by_tier(db)
    plan_limit = resolve_user_plan_limit(
        subscription_tier=user.subscription_tier,
        annual_override=user.annual_planogram_limit_override,
        is_unlimited_override=user.is_unlimited_override,
        plan_limits_by_tier=plan_limits_by_tier,
    )
    response_data = AdminUserPlanLimitResponse(
        user_id=user.id,
        plan_limit=UserPlanLimitRead.model_validate(plan_limit),
    )
    return success_response(response_data.model_dump(mode="json"), "User plan limit updated successfully.")
