import uuid

from pydantic import BaseModel, Field

from core.constants import APPROVAL_STATUS_FILTER_TYPE, APPROVAL_STATUS_TYPE


class OnboardingRequestListQuery(BaseModel):
    status: APPROVAL_STATUS_FILTER_TYPE = "pending"


class OnboardingDecisionRequest(BaseModel):
    status: APPROVAL_STATUS_TYPE
    review_note: str | None = Field(default=None, max_length=255)


class OnboardingDecisionResponseData(BaseModel):
    user_id: uuid.UUID
    status: APPROVAL_STATUS_TYPE
