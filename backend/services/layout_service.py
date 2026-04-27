from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.api_response import error_payload
from core.constants import ERROR_CODE_QUOTA_EXCEEDED
from models.layout import Layout
from models.user import User
from schemas.layout import LayoutCreateRequest
from services.plan_limit_service import get_plan_limit_for_tier
from services.quota_service import evaluate_planogram_quota


def _current_year_window() -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    year_start = datetime(now.year, 1, 1, tzinfo=timezone.utc)
    next_year_start = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    return year_start, next_year_start


async def create_layout_for_user(db: AsyncSession, user: User, payload: LayoutCreateRequest) -> Layout:
    year_start, next_year_start = _current_year_window()

    count_result = await db.execute(
        select(func.count(Layout.id)).where(
            Layout.user_id == user.id,
            Layout.created_at >= year_start,
            Layout.created_at < next_year_start,
        ),
    )
    current_count = int(count_result.scalar_one())

    plan_limit = await get_plan_limit_for_tier(db, user.subscription_tier)
    annual_limit = None if plan_limit is None else plan_limit.annual_planogram_limit
    is_unlimited = True if plan_limit is None else plan_limit.is_unlimited

    decision = evaluate_planogram_quota(
        current_count=current_count,
        annual_planogram_limit=annual_limit,
        is_unlimited=is_unlimited,
    )

    if not decision["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_payload(
                ERROR_CODE_QUOTA_EXCEEDED,
                {
                    "message": "Annual planogram limit reached for this account tier.",
                    "tier": user.subscription_tier,
                    "limit": decision["limit"],
                    "remaining": decision["remaining"],
                    "used": current_count,
                },
            ),
        )

    layout = Layout(user_id=user.id, name=payload.name.strip())
    db.add(layout)
    await db.commit()
    await db.refresh(layout)
    return layout
