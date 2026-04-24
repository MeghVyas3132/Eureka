import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.api_response import error_payload
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from models.user import User
from schemas.auth import LoginRequest, RegisterRequest, TokenPair


async def register_user(db: AsyncSession, payload: RegisterRequest) -> User:
    email = payload.email.lower()
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_payload("email_exists", "Email is already registered."),
        )

    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, payload: LoginRequest) -> User:
    email = payload.email.lower()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_payload("invalid_credentials", "Email or password is incorrect."),
        )

    return user


def build_token_pair(user: User) -> TokenPair:
    user_id = str(user.id)
    return TokenPair(
        access_token=create_access_token(subject=user_id, role=user.role),
        refresh_token=create_refresh_token(subject=user_id, role=user.role),
    )


async def refresh_session(db: AsyncSession, refresh_token: str) -> tuple[User, TokenPair]:
    payload = decode_token(refresh_token)
    if payload.get("token_type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_payload("invalid_token_type", "Expected a refresh token."),
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

    return user, build_token_pair(user)
