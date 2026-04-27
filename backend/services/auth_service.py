import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.api_response import error_payload
from core.constants import (
    ERROR_CODE_EMAIL_EXISTS,
    ERROR_CODE_INVALID_CREDENTIALS,
    ROLE_ADMIN,
    ROLE_TO_DEFAULT_TIER,
    SEED_ADMIN_EMAIL,
    SEED_ADMIN_PASSWORD,
    TIER_ADMIN,
)
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from models.user import User
from schemas.auth import LoginRequest, RegisterRequest, TokenPair


def _is_seed_password_valid(user: User) -> bool:
    try:
        return verify_password(SEED_ADMIN_PASSWORD, user.hashed_password)
    except Exception:
        return False


async def ensure_seed_admin_user(db: AsyncSession) -> None:
    result = await db.execute(select(User).where(User.email == SEED_ADMIN_EMAIL))
    user = result.scalar_one_or_none()

    should_persist_changes = False
    if user is None:
        user = User(
            email=SEED_ADMIN_EMAIL,
            hashed_password=hash_password(SEED_ADMIN_PASSWORD),
            role=ROLE_ADMIN,
            subscription_tier=TIER_ADMIN,
        )
        db.add(user)
        should_persist_changes = True
    else:
        if user.role != ROLE_ADMIN:
            user.role = ROLE_ADMIN
            should_persist_changes = True
        if user.subscription_tier != TIER_ADMIN:
            user.subscription_tier = TIER_ADMIN
            should_persist_changes = True
        if not _is_seed_password_valid(user):
            user.hashed_password = hash_password(SEED_ADMIN_PASSWORD)
            should_persist_changes = True

    if not should_persist_changes:
        return

    try:
        await db.commit()
    except IntegrityError:
        # Handles concurrent requests attempting to seed at the same time.
        await db.rollback()


async def register_user(db: AsyncSession, payload: RegisterRequest) -> User:
    await ensure_seed_admin_user(db)

    email = payload.email.lower()
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_payload(ERROR_CODE_EMAIL_EXISTS, "Email is already registered."),
        )

    subscription_tier = ROLE_TO_DEFAULT_TIER[payload.role]

    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        subscription_tier=subscription_tier,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, payload: LoginRequest) -> User:
    await ensure_seed_admin_user(db)

    email = payload.email.lower()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_payload(ERROR_CODE_INVALID_CREDENTIALS, "Email or password is incorrect."),
        )

    return user


def build_token_pair(user: User) -> TokenPair:
    user_id = str(user.id)
    return TokenPair(
        access_token=create_access_token(
            subject=user_id,
            role=user.role,
            subscription_tier=user.subscription_tier,
        ),
        refresh_token=create_refresh_token(
            subject=user_id,
            role=user.role,
            subscription_tier=user.subscription_tier,
        ),
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
