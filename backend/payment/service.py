from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import uuid4

import httpx

from backend.orders.schemas import OrderCreate
from backend.payment.crud import SqlAlchemyPendingPaymentRepository
from backend.payment.schemas import PaymentInitRead
from config import PAYMENT_TEST_AMOUNT, WEBAPP_URL, YOOKASSA_SECRET_KEY, YOOKASSA_SHOP_ID


logger = logging.getLogger(__name__)


class PaymentError(Exception):
    pass


@dataclass
class YooKassaPaymentService:
    repository: SqlAlchemyPendingPaymentRepository

    def _ensure_configured(self) -> None:
        if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
            raise PaymentError("YooKassa credentials are not configured.")

    def _resolve_amount(self, amount: int) -> str:
        payment_amount = PAYMENT_TEST_AMOUNT if PAYMENT_TEST_AMOUNT > 0 else amount
        value = Decimal(str(payment_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return f"{value:.2f}"

    def _build_return_url(self) -> str:
        return (WEBAPP_URL or "http://127.0.0.1:8011").rstrip("/")

    async def create_payment(
        self,
        *,
        user_id: int,
        user_phone: str,
        payload: OrderCreate,
        amount: int,
    ) -> PaymentInitRead:
        self._ensure_configured()
        pending_payment = await self.repository.create_pending(
            user_id=user_id,
            amount=amount,
            payload_json=json.dumps(payload.model_dump(mode="json"), ensure_ascii=False),
        )
        request_payload = {
            "amount": {
                "value": self._resolve_amount(amount),
                "currency": "RUB",
            },
            "confirmation": {
                "type": "redirect",
                "return_url": self._build_return_url(),
            },
            "capture": True,
            "description": f"Zamzam заказ #{pending_payment.id}, телефон {user_phone}",
            "metadata": {
                "pending_payment_id": str(pending_payment.id),
                "user_id": str(user_id),
            },
        }

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    "https://api.yookassa.ru/v3/payments",
                    json=request_payload,
                    auth=(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY),
                    headers={"Idempotence-Key": str(uuid4())},
                )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip()
            logger.warning("YooKassa payment creation failed. status=%s detail=%s", exc.response.status_code, detail)
            await self.repository.mark_failed(
                pending_payment_id=pending_payment.id,
                status="create_failed",
                error_message=detail,
            )
            raise PaymentError(f"YooKassa payment creation failed: {detail}") from exc
        except httpx.HTTPError as exc:
            await self.repository.mark_failed(
                pending_payment_id=pending_payment.id,
                status="create_failed",
                error_message=str(exc),
            )
            raise PaymentError("YooKassa payment creation failed.") from exc

        response_payload = response.json()
        payment_id = str(response_payload.get("id") or "")
        status = str(response_payload.get("status") or "pending")
        confirmation = response_payload.get("confirmation") or {}
        confirmation_url = str(confirmation.get("confirmation_url") or "")
        if not payment_id or not confirmation_url:
            raise PaymentError("YooKassa payment response is incomplete.")

        await self.repository.attach_yookassa_payment(
            pending_payment_id=pending_payment.id,
            yookassa_payment_id=payment_id,
            confirmation_url=confirmation_url,
            status=status,
        )
        return PaymentInitRead(
            payment_id=payment_id,
            confirmation_url=confirmation_url,
            status=status,
        )

    async def fetch_payment(self, payment_id: str) -> dict[str, Any]:
        self._ensure_configured()
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(
                    f"https://api.yookassa.ru/v3/payments/{payment_id}",
                    auth=(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY),
                )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise PaymentError("YooKassa payment lookup failed.") from exc

        payload = response.json()
        if not isinstance(payload, dict):
            raise PaymentError("YooKassa payment lookup response is invalid.")
        return payload
