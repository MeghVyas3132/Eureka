from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from core.constants import SIGNUP_ROLE_TYPE
from schemas.user import UserRead


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)
    role: SIGNUP_ROLE_TYPE = "merchandiser"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    token_type: Literal["bearer"] = "bearer"
    access_token: str
    refresh_token: str


class AuthResponseData(BaseModel):
    user: UserRead
    tokens: TokenPair
