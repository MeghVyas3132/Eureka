from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.api_response import success_response
from db.session import get_db
from schemas.auth import AuthResponseData, LoginRequest, RefreshRequest, RegisterRequest, RegisterResponseData
from schemas.user import UserRead
from services.auth_service import authenticate_user, build_token_pair, refresh_session, register_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> dict:
    user = await register_user(db, payload)
    response_data = RegisterResponseData(user=UserRead.model_validate(user))
    return success_response(
        response_data.model_dump(mode="json"),
        "Registration submitted. You will be notified by email once approved by admin.",
    )


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> dict:
    user = await authenticate_user(db, payload)
    response_data = AuthResponseData(user=UserRead.model_validate(user), tokens=build_token_pair(user))
    return success_response(response_data.model_dump(mode="json"), "Login successful.")


@router.post("/refresh")
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> dict:
    user, token_pair = await refresh_session(db, payload.refresh_token)
    response_data = AuthResponseData(user=UserRead.model_validate(user), tokens=token_pair)
    return success_response(response_data.model_dump(mode="json"), "Token refreshed successfully.")
