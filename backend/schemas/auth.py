from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from core.constants import SIGNUP_ROLE_TYPE
from schemas.user import UserRead


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_]+$")
    company_name: str | None = Field(default=None, max_length=160)
    phone_number: str = Field(min_length=7, max_length=32, pattern=r"^[0-9+\-\s()]+$")
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


class RegisterResponseData(BaseModel):
    user: UserRead
    requires_admin_approval: bool = True
