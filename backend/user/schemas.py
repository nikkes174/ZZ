from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AuthCodeRequest(BaseModel):
    phone: str = Field(..., min_length=6, max_length=32)


class AuthCodeResponse(BaseModel):
    phone: str
    message: str
    code: str = Field(..., min_length=4, max_length=6)
    expires_at: datetime


class AuthVerifyRequest(BaseModel):
    phone: str = Field(..., min_length=6, max_length=32)
    code: str = Field(..., min_length=4, max_length=6)
    full_name: Optional[str] = Field(default=None, max_length=120)


class UserRead(BaseModel):
    id: int
    phone: str
    full_name: Optional[str]
    bonus_balance: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserAuthRead(BaseModel):
    session_token: str
    user: UserRead


class UserDashboardRead(BaseModel):
    user: UserRead
    latest_order_status: Optional[str] = None
    active_orders_count: int = 0
