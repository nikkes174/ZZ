from __future__ import annotations

from pydantic import BaseModel, Field

from backend.user.schemas import UserRead


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class AuthTokenRead(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int
    user: UserRead
