import uuid
from collections.abc import Sequence
from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.api_response import error_payload
from core.constants import (
    APPROVAL_APPROVED,
    ERROR_CODE_ACCOUNT_PENDING_APPROVAL,
    ROLE_ADMIN,
)
from core.security import decode_token, oauth2_scheme
from db.session import get_db
from models.user import User


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token)
    if payload.get("token_type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_payload("invalid_token_type", "Expected an access token."),
        )

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_payload("invalid_token", "Token subject is missing."),
        )

    try:
        user_id = uuid.UUID(subject)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_payload("invalid_token", "Token subject is invalid."),
        ) from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_payload("user_not_found", "Token user does not exist."),
        )
    if user.role != ROLE_ADMIN and user.approval_status != APPROVAL_APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_payload(
                ERROR_CODE_ACCOUNT_PENDING_APPROVAL,
                "Your account is not approved for access.",
            ),
        )

    return user


def require_role(allowed_roles: Sequence[str]) -> Callable[..., User]:
    async def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_payload(
                    "forbidden",
                    f"Required role: {', '.join(allowed_roles)}.",
                ),
            )
        return current_user

    return role_dependency
