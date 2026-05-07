import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from core.constants import APPROVAL_STATUS_TYPE, ROLE_TYPE, TIER_TYPE


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    company_name: str | None = None
    phone_number: str | None = None
    role: ROLE_TYPE
    subscription_tier: TIER_TYPE
    approval_status: APPROVAL_STATUS_TYPE
    created_at: datetime


class UserPlanLimitRead(BaseModel):
    annual_planogram_limit: int | None
    is_unlimited: bool
    source: Literal["tier", "override"]


class AdminUserRead(UserRead):
    planogram_count: int = Field(ge=0)
    reviewed_at: datetime | None = None
    review_note: str | None = None
    plan_limit: UserPlanLimitRead


class AdminUserPlanLimitUpdate(BaseModel):
    annual_planogram_limit: int | None = Field(default=None, ge=1)
    is_unlimited: bool | None = None
    use_tier_default: bool = False


class AdminUserPlanLimitResponse(BaseModel):
    user_id: uuid.UUID
    plan_limit: UserPlanLimitRead
