from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class PaymentInitRead(BaseModel):
    payment_id: str = ""
    confirmation_url: Optional[str] = None
    status: str
    order_id: Optional[int] = None
    total_amount: Optional[int] = None
    bonus_spent: Optional[int] = None
    bonus_awarded: Optional[int] = None
    bonus_balance: Optional[int] = None
