from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserRegisterRequest(BaseModel):
    phone: str = Field(..., min_length=6, max_length=32)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=120)


class UserLoginRequest(BaseModel):
    phone: str = Field(..., min_length=6, max_length=32)
    password: str = Field(..., min_length=6, max_length=128)


class UserProfileUpdateRequest(BaseModel):
    phone: str = Field(..., min_length=6, max_length=32)


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
