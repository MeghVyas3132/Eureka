from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.api_response import success_response
from core.constants import ROLE_ADMIN
from core.deps import require_role
from db.session import get_db
from models.planogram import Planogram
from models.store import Store
from models.user import User
from services.plan_limit_service import get_plan_limits_by_tier, resolve_user_plan_limit

router = APIRouter(prefix="/api/v1/admin/stats", tags=["admin-stats"])


@router.get("")
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_role([ROLE_ADMIN])),
) -> dict:
    """Aggregate metrics for the super-admin dashboard."""
    plan_limits_by_tier = await get_plan_limits_by_tier(db)

    user_count = int(
        (await db.execute(select(func.count(User.id)).where(User.role != ROLE_ADMIN))).scalar_one() or 0
    )
    approved_user_count = int(
        (
            await db.execute(
                select(func.count(User.id)).where(
                    User.role != ROLE_ADMIN, User.approval_status == "approved"
                )
            )
        ).scalar_one()
        or 0
    )
    pending_user_count = int(
        (
            await db.execute(
                select(func.count(User.id)).where(
                    User.role != ROLE_ADMIN, User.approval_status == "pending"
                )
            )
        ).scalar_one()
        or 0
    )
    store_count = int(
        (await db.execute(select(func.count(Store.id)))).scalar_one() or 0
    )
    total_planograms = int(
        (await db.execute(select(func.count(Planogram.id)))).scalar_one() or 0
    )

    # Sum of resolved annual limits across non-admin users (excluding unlimited).
    user_rows = (
        await db.execute(
            select(
                User.subscription_tier,
                User.annual_planogram_limit_override,
                User.is_unlimited_override,
            ).where(User.role != ROLE_ADMIN)
        )
    ).all()

    total_quota = 0
    has_unlimited = False
    for tier, override, is_unlimited in user_rows:
        plan_limit = resolve_user_plan_limit(
            subscription_tier=tier,
            annual_override=override,
            is_unlimited_override=is_unlimited,
            plan_limits_by_tier=plan_limits_by_tier,
        )
        if plan_limit["is_unlimited"]:
            has_unlimited = True
            continue
        if plan_limit["annual_planogram_limit"] is not None:
            total_quota += int(plan_limit["annual_planogram_limit"])

    payload = {
        "users": {
            "total": user_count,
            "approved": approved_user_count,
            "pending": pending_user_count,
        },
        "stores": {"total": store_count},
        "planograms": {
            "total": total_planograms,
            "total_quota": total_quota,
            "has_unlimited_users": has_unlimited,
            "utilisation_pct": round((total_planograms / total_quota) * 100, 1)
            if total_quota > 0
            else None,
        },
    }
    return success_response(payload, "Admin stats fetched successfully.")
