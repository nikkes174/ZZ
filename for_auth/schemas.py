from pydantic import BaseModel, Field


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int
    tg_id: int
    user_id: int
    is_admin: bool


class DevAdminAuthRequest(BaseModel):
    tg_id: int = Field(gt=0)


class DevUserAuthRequest(BaseModel):
    tg_id: int = Field(gt=0)
