from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import uuid4

import httpx

from backend.orders.schemas import OrderCreate
from backend.payment.crud import SqlAlchemyPendingPaymentRepository
from backend.payment.schemas import PaymentInitRead
from config import WEBAPP_URL, YOOKASSA_SECRET_KEY, YOOKASSA_SHOP_ID, YOOKASSA_VAT_CODE


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
        value = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return f"{value:.2f}"

    def _resolve_amount_from_cents(self, amount_cents: int) -> str:
        value = (Decimal(amount_cents) / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return f"{value:.2f}"

    def _build_return_url(self) -> str:
        return (WEBAPP_URL or "http://127.0.0.1:8011").rstrip("/")

    def _build_receipt_phone(self, *phones: str) -> str:
        for phone in phones:
            digits = re.sub(r"\D+", "", phone)
            if len(digits) == 10:
                digits = f"7{digits}"
            if len(digits) == 11 and digits.startswith("8"):
                digits = f"7{digits[1:]}"
            if 10 <= len(digits) <= 15:
                return digits
        return ""

    def _build_receipt_items(self, *, payload: OrderCreate, amount: int) -> list[dict[str, Any]]:
        subtotal_cents = sum(item.price * item.quantity * 100 for item in payload.items)
        payment_cents = amount * 100
        discount_cents = max(0, subtotal_cents - payment_cents)
        remaining_discount_cents = discount_cents
        receipt_items: list[dict[str, Any]] = []

        for index, item in enumerate(payload.items):
            line_total_cents = item.price * item.quantity * 100
            if index == len(payload.items) - 1:
                line_discount_cents = remaining_discount_cents
            elif subtotal_cents > 0:
                line_discount_cents = discount_cents * line_total_cents // subtotal_cents
                remaining_discount_cents -= line_discount_cents
            else:
                line_discount_cents = 0

            paid_line_cents = max(0, line_total_cents - line_discount_cents)
            if paid_line_cents <= 0:
                continue

            unit_cents = paid_line_cents // item.quantity
            remainder_units = paid_line_cents % item.quantity
            regular_units = item.quantity - remainder_units

            if regular_units > 0 and unit_cents > 0:
                receipt_items.append(
                    self._build_receipt_item(
                        title=item.title,
                        quantity=regular_units,
                        amount_cents=unit_cents,
                    )
                )
            if remainder_units > 0:
                receipt_items.append(
                    self._build_receipt_item(
                        title=item.title,
                        quantity=remainder_units,
                        amount_cents=unit_cents + 1,
                    )
                )

        return receipt_items

    def _build_receipt_item(self, *, title: str, quantity: int, amount_cents: int) -> dict[str, Any]:
        return {
            "description": title[:128],
            "quantity": f"{quantity:.2f}",
            "amount": {
                "value": self._resolve_amount_from_cents(amount_cents),
                "currency": "RUB",
            },
            "vat_code": YOOKASSA_VAT_CODE,
            "payment_mode": "full_payment",
            "payment_subject": "commodity",
        }

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
            "receipt": {
                "customer": {
                    "phone": self._build_receipt_phone(payload.customer_phone, user_phone),
                },
                "items": self._build_receipt_items(payload=payload, amount=amount),
            },
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
