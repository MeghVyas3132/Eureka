import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.api_response import error_payload
from core.constants import (
    APPROVAL_APPROVED,
    APPROVAL_PENDING,
    APPROVAL_REJECTED,
    ERROR_CODE_ACCOUNT_PENDING_APPROVAL,
    ERROR_CODE_ACCOUNT_REJECTED,
    ERROR_CODE_EMAIL_EXISTS,
    ERROR_CODE_INVALID_CREDENTIALS,
    ERROR_CODE_USERNAME_EXISTS,
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


def _normalize_username(raw_username: str) -> str:
    return raw_username.strip().lower()


def _normalize_name(raw_name: str) -> str:
    return raw_name.strip()


def _normalize_optional_text(raw_text: str | None) -> str | None:
    if raw_text is None:
        return None
    normalized = raw_text.strip()
    return normalized or None


def _username_with_suffix(base_username: str, suffix_index: int) -> str:
    normalized_base = base_username[:64] or "user"
    if suffix_index <= 1:
        return normalized_base

    suffix = f"_{suffix_index}"
    return f"{normalized_base[: max(1, 64 - len(suffix))]}{suffix}"


async def _username_exists(
    db: AsyncSession,
    username: str,
    *,
    exclude_user_id: uuid.UUID | None = None,
) -> bool:
    query = select(User.id).where(User.username == username)
    if exclude_user_id is not None:
        query = query.where(User.id != exclude_user_id)

    result = await db.execute(query)
    return result.scalar_one_or_none() is not None


async def _resolve_available_username(
    db: AsyncSession,
    base_username: str,
    *,
    exclude_user_id: uuid.UUID | None = None,
) -> str:
    normalized_base = _normalize_username(base_username) or "user"
    suffix_index = 1

    while True:
        candidate = _username_with_suffix(normalized_base, suffix_index)
        if not await _username_exists(db, candidate, exclude_user_id=exclude_user_id):
            return candidate
        suffix_index += 1


async def ensure_seed_admin_user(db: AsyncSession) -> None:
    result = await db.execute(select(User).where(User.email == SEED_ADMIN_EMAIL))
    user = result.scalar_one_or_none()

    should_persist_changes = False
    if user is None:
        seed_username = await _resolve_available_username(db, "admin")
        user = User(
            first_name="Super",
            last_name="Admin",
            email=SEED_ADMIN_EMAIL,
            username=seed_username,
            company_name="Eureka",
            phone_number=None,
            hashed_password=hash_password(SEED_ADMIN_PASSWORD),
            role=ROLE_ADMIN,
            subscription_tier=TIER_ADMIN,
            approval_status=APPROVAL_APPROVED,
            reviewed_at=datetime.now(timezone.utc),
            review_note="System-seeded super admin account.",
        )
        db.add(user)
        should_persist_changes = True
    else:
        current_username = _normalize_username(user.username or "")
        if not current_username:
            current_username = "admin"
        resolved_username = await _resolve_available_username(
            db,
            current_username,
            exclude_user_id=user.id,
        )
        if user.username != resolved_username:
            user.username = resolved_username
            should_persist_changes = True
        if user.first_name != "Super":
            user.first_name = "Super"
            should_persist_changes = True
        if user.last_name != "Admin":
            user.last_name = "Admin"
            should_persist_changes = True
        if user.company_name != "Eureka":
            user.company_name = "Eureka"
            should_persist_changes = True
        if user.approval_status != APPROVAL_APPROVED:
            user.approval_status = APPROVAL_APPROVED
            should_persist_changes = True
        if user.reviewed_at is None:
            user.reviewed_at = datetime.now(timezone.utc)
            should_persist_changes = True
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
    username = _normalize_username(payload.username)
    first_name = _normalize_name(payload.first_name)
    last_name = _normalize_name(payload.last_name)
    company_name = _normalize_optional_text(payload.company_name)
    phone_number = _normalize_optional_text(payload.phone_number)

    if not username:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_payload("validation_error", "Username is required."),
        )
    if not first_name or not last_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_payload("validation_error", "First name and last name are required."),
        )

    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_payload(ERROR_CODE_EMAIL_EXISTS, "Email is already registered."),
        )

    if await _username_exists(db, username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_payload(ERROR_CODE_USERNAME_EXISTS, "Username is already taken."),
        )

    subscription_tier = ROLE_TO_DEFAULT_TIER[payload.role]

    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        username=username,
        company_name=company_name,
        phone_number=phone_number,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        subscription_tier=subscription_tier,
        approval_status=APPROVAL_PENDING,
        reviewed_at=None,
        review_note=None,
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

    if user.role != ROLE_ADMIN and user.approval_status != APPROVAL_APPROVED:
        if user.approval_status == APPROVAL_REJECTED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_payload(
                    ERROR_CODE_ACCOUNT_REJECTED,
                    "Your signup request was rejected by admin. Please contact support.",
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_payload(
                ERROR_CODE_ACCOUNT_PENDING_APPROVAL,
                "Your signup request is pending admin approval.",
            ),
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
    if user.role != ROLE_ADMIN and user.approval_status != APPROVAL_APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_payload(
                ERROR_CODE_ACCOUNT_PENDING_APPROVAL,
                "Your account is not approved for access.",
            ),
        )

    return user, build_token_pair(user)
