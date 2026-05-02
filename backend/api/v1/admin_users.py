from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.api_response import success_response
from core.constants import ROLE_ADMIN
from core.deps import require_role
from db.session import get_db
from models.layout import Layout
from models.store import Store
from models.user import User
from schemas.user import AdminUserRead

router = APIRouter(prefix="/api/v1/admin/users", tags=["admin-users"])


@router.get("")
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_role([ROLE_ADMIN])),
) -> dict:
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
        response_data.append(AdminUserRead.model_validate(normalized).model_dump(mode="json"))

    return success_response(response_data, "Users fetched successfully.")
