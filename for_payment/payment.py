import asyncio
import uuid
from decimal import Decimal, ROUND_HALF_UP

from yookassa import Configuration, Payment

from backend.config import TEST_AMOUNT, WEBAPP_URL, YOOKASSA_SECRET_KEY, YOOKASSA_SHOP_ID
from backend.exceptions import InfrastructureError


class PaymentUtils:
    def __init__(self) -> None:
        self.yookassa_id = YOOKASSA_SHOP_ID
        self.yookassa_key = YOOKASSA_SECRET_KEY
        if self.yookassa_id and self.yookassa_key:
            Configuration.account_id = self.yookassa_id
            Configuration.secret_key = self.yookassa_key

    def _ensure_configured(self) -> None:
        if not self.yookassa_id or not self.yookassa_key:
            raise InfrastructureError("YOOKASSA credentials are not configured")

    @staticmethod
    def _format_amount(amount: float) -> str:
        value = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return f"{value:.2f}"

    @staticmethod
    def _resolve_payment_amount(order_amount: float) -> float:
        if TEST_AMOUNT > 0:
            return TEST_AMOUNT
        return order_amount

    @staticmethod
    def _build_return_url() -> str:
        base_url = (WEBAPP_URL or "").rstrip("/")
        if not base_url:
            return "https://t.me"
        return base_url

    async def create_payment(
        self,
        *,
        order_id: int,
        user_id: int,
        amount: float,
        description: str,
    ) -> tuple[str, str]:
        self._ensure_configured()
        payload = {
            "amount": {"value": self._format_amount(self._resolve_payment_amount(amount)), "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": self._build_return_url()},
            "capture": True,
            "description": description,
            "metadata": {
                "order_id": str(order_id),
                "user_id": str(user_id),
            },
        }
        idempotence_key = str(uuid.uuid4())
        try:
            payment = await asyncio.to_thread(Payment.create, payload, idempotence_key)
        except Exception as exc:
            raise InfrastructureError("YooKassa payment creation failed") from exc

        confirmation = getattr(payment, "confirmation", None)
        confirmation_url = getattr(confirmation, "confirmation_url", "")
        if not payment.id or not confirmation_url:
            raise InfrastructureError("YooKassa payment response is incomplete")
        return payment.id, confirmation_url

    async def get_payment(self, payment_id: str):
        self._ensure_configured()
        try:
            return await asyncio.to_thread(Payment.find_one, payment_id)
        except Exception as exc:
            raise InfrastructureError("YooKassa payment lookup failed") from exc
