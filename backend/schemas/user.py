import uuid
from datetime import datetime

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


class AdminUserRead(UserRead):
    layout_count: int = Field(ge=0)
    reviewed_at: datetime | None = None
    review_note: str | None = None
