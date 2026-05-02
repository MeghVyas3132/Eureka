from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import DEFAULT_PLAN_LIMITS, VALID_TIERS
from models.plan_limit import PlanLimit
from models.user import User


async def ensure_default_plan_limits(db: AsyncSession) -> None:
    result = await db.execute(select(PlanLimit))
    if result.scalars().first() is not None:
        return

    db.add_all(
        [
            PlanLimit(
                tier=tier,
                annual_planogram_limit=DEFAULT_PLAN_LIMITS[tier],
                is_unlimited=DEFAULT_PLAN_LIMITS[tier] is None,
            )
            for tier in VALID_TIERS
        ],
    )
    await db.commit()


async def get_plan_limit_for_tier(db: AsyncSession, tier: str) -> PlanLimit | None:
    await ensure_default_plan_limits(db)
    result = await db.execute(select(PlanLimit).where(PlanLimit.tier == tier))
    return result.scalar_one_or_none()


async def get_plan_limits_by_tier(db: AsyncSession) -> dict[str, PlanLimit]:
    await ensure_default_plan_limits(db)
    result = await db.execute(select(PlanLimit))
    records = result.scalars().all()
    return {record.tier: record for record in records}


async def get_effective_plan_limit_for_user(db: AsyncSession, user: User) -> dict[str, Any]:
    plan_limits_by_tier = await get_plan_limits_by_tier(db)
    return resolve_user_plan_limit(
        subscription_tier=user.subscription_tier,
        annual_override=user.annual_planogram_limit_override,
        is_unlimited_override=user.is_unlimited_override,
        plan_limits_by_tier=plan_limits_by_tier,
    )


def resolve_user_plan_limit(
    *,
    subscription_tier: str,
    annual_override: int | None,
    is_unlimited_override: bool | None,
    plan_limits_by_tier: dict[str, PlanLimit],
) -> dict[str, Any]:
    if is_unlimited_override is True:
        return {
            "annual_planogram_limit": None,
            "is_unlimited": True,
            "source": "override",
        }

    if annual_override is not None:
        return {
            "annual_planogram_limit": annual_override,
            "is_unlimited": False,
            "source": "override",
        }

    plan_limit = plan_limits_by_tier.get(subscription_tier)
    if plan_limit is None:
        return {
            "annual_planogram_limit": None,
            "is_unlimited": True,
            "source": "tier",
        }

    return {
        "annual_planogram_limit": plan_limit.annual_planogram_limit,
        "is_unlimited": plan_limit.is_unlimited,
        "source": "tier",
    }
