from __future__ import annotations

from pydantic import BaseModel, Field

from backend.user.schemas import UserRead


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class PasswordRecoveryRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)


class PasswordResetRequest(BaseModel):
    token: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    password: str = Field(..., min_length=6, max_length=128)


class AuthTokenRead(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int
    user: UserRead
