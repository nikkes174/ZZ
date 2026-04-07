from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class OrderItemPayload(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=255)
    price: int = Field(..., ge=0, le=1_000_000)
    quantity: int = Field(..., ge=1, le=100)


class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=120)
    customer_phone: str = Field(..., min_length=6, max_length=32)
    checkout_type: str = Field(..., min_length=4, max_length=20)
    payment_type: str = Field(..., min_length=4, max_length=20)
    delivery_address: Optional[str] = Field(default=None, max_length=255)
    entrance: Optional[str] = Field(default=None, max_length=64)
    comment: Optional[str] = Field(default=None, max_length=255)
    cutlery_count: int = Field(default=0, ge=0, le=50)
    bonus_spent: int = Field(default=0, ge=0, le=1_000_000)
    items: list[OrderItemPayload] = Field(..., min_length=1, max_length=100)

    @field_validator("checkout_type")
    @classmethod
    def validate_checkout_type(cls, value: str) -> str:
        if value not in {"pickup", "delivery"}:
            raise ValueError("Некорректный тип заказа.")
        return value

    @field_validator("payment_type")
    @classmethod
    def validate_payment_type(cls, value: str) -> str:
        if value not in {"cash", "card"}:
            raise ValueError("Некорректный способ оплаты.")
        return value


class OrderRead(BaseModel):
    id: int
    user_id: int
    customer_name: str
    customer_phone: str
    checkout_type: str
    payment_type: str
    delivery_address: Optional[str]
    entrance: Optional[str]
    comment: Optional[str]
    items: list[OrderItemPayload]
    items_count: int
    cutlery_count: int
    subtotal_amount: int
    bonus_spent: int
    total_amount: int
    bonus_awarded: int
    status: str
    created_at: datetime
    updated_at: datetime


class UserOrdersPage(BaseModel):
    items: list[OrderRead]
