from importlib import import_module
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.orders.branches import BranchCode
from backend.orders.schemas import OrderCreate, OrderItemPayload
from backend.orders.service import IikoPayloadValidationError, OrderService


orders_router = import_module("backend.orders.router")


class FakeMenuRepository:
    async def get_many_by_ids(self, item_ids):
        return [
            SimpleNamespace(
                id=item_id,
                title="Тестовая позиция",
                site_title="Тестовая позиция",
                price=500,
                is_active=True,
                is_published=True,
                iiko_product_id=f"iiko-{item_id}",
            )
            for item_id in item_ids
        ]


def build_payload(**updates):
    values = {
        "customer_name": " Клиент ",
        "customer_phone": " +79990000000 ",
        "checkout_type": "delivery",
        "payment_type": "card",
        "delivery_street": " Малышева ",
        "delivery_house": " 10А ",
        "delivery_flat": None,
        "entrance": None,
        "comment": "  ",
        "items": [OrderItemPayload(id="1", title="Тест", price=500, quantity=1)],
        "branch_code": BranchCode.MALYSHAVA,
    }
    values.update(updates)
    return OrderCreate(**values)


def build_service(monkeypatch):
    monkeypatch.setattr("backend.orders.service.resolve_terminal_group_id", lambda _: "terminal-id")
    return OrderService(repository=SimpleNamespace(), menu_item_repository=FakeMenuRepository(), iiko_order_gateway=SimpleNamespace())


@pytest.mark.asyncio
async def test_valid_delivery_and_ten_character_house_are_accepted(monkeypatch):
    service = build_service(monkeypatch)
    prepared = await service.prepare_order(
        payload=build_payload(delivery_house="1234567890"),
        available_bonus_balance=0,
    )

    assert prepared.payload.delivery_street == "Малышева"
    assert prepared.payload.delivery_house == "1234567890"
    assert prepared.payload.comment is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("delivery_house", "12345678901", "Номер дома слишком длинный"),
        ("delivery_house", "---", "Проверьте номер дома."),
        ("delivery_street", "---", "Проверьте название улицы."),
        ("delivery_street", None, "Укажите улицу доставки."),
        ("delivery_house", None, "Укажите номер дома."),
    ],
)
async def test_invalid_delivery_address_is_rejected_before_preparation(monkeypatch, field, value, message):
    service = build_service(monkeypatch)

    with pytest.raises(IikoPayloadValidationError, match=message):
        await service.prepare_order(payload=build_payload(**{field: value}), available_bonus_balance=0)


@pytest.mark.asyncio
async def test_pickup_clears_delivery_fields(monkeypatch):
    service = build_service(monkeypatch)
    prepared = await service.prepare_order(
        payload=build_payload(
            checkout_type="pickup",
            delivery_street="Малышева",
            delivery_house="10А",
            delivery_flat="12",
            entrance="2",
        ),
        available_bonus_balance=0,
    )

    assert prepared.payload.delivery_address is None
    assert prepared.payload.delivery_street is None
    assert prepared.payload.delivery_house is None
    assert prepared.payload.delivery_flat is None
    assert prepared.payload.entrance is None


@pytest.mark.asyncio
async def test_retry_of_old_order_with_long_house_rejects_before_iiko_submission(monkeypatch):
    service = build_service(monkeypatch)
    old_order = SimpleNamespace(
        id=42,
        customer_name="Клиент",
        customer_phone="+79990000000",
        checkout_type="delivery",
        payment_type="card",
        delivery_address="Малышева, 12345678901",
        delivery_street="Малышева",
        delivery_house="12345678901",
        delivery_flat=None,
        entrance=None,
        comment=None,
        cutlery_count=0,
        bonus_spent=0,
        items_json='[{"id":"1","title":"Тест","price":500,"quantity":1}]',
        subtotal_amount=500,
        total_amount=500,
        branch_code="malyshava",
        iiko_terminal_group_id="terminal-id",
    )

    with pytest.raises(IikoPayloadValidationError, match="Номер дома слишком длинный"):
        await service._prepare_existing_order_for_iiko(old_order)


@pytest.mark.asyncio
async def test_retry_marks_locally_invalid_address_job_dead(monkeypatch):
    old_order = SimpleNamespace(
        id=42,
        customer_name="Клиент",
        customer_phone="+79990000000",
        checkout_type="delivery",
        payment_type="card",
        delivery_address="Малышева, 12345678901",
        delivery_street="Малышева",
        delivery_house="12345678901",
        delivery_flat=None,
        entrance=None,
        comment=None,
        cutlery_count=0,
        bonus_spent=0,
        items_json='[{"id":"1","title":"Тест","price":500,"quantity":1}]',
        subtotal_amount=500,
        total_amount=500,
        branch_code="malyshava",
        iiko_terminal_group_id="terminal-id",
        iiko_order_id=None,
        iiko_creation_status="LocalPending",
    )

    class RetryRepository:
        def __init__(self):
            self.dead = []

        async def enqueue_missing_paid_iiko_submission_jobs(self, **_):
            return 0

        async def claim_due_iiko_submission_jobs(self, **_):
            return [SimpleNamespace(id=7, order_id=42, attempts=1)]

        async def get_by_id(self, order_id):
            return old_order if order_id == 42 else None

        async def mark_iiko_submission_job_dead(self, **kwargs):
            self.dead.append(kwargs)

    repository = RetryRepository()
    service = OrderService(
        repository=repository,
        menu_item_repository=FakeMenuRepository(),
        iiko_order_gateway=SimpleNamespace(),
    )

    result = await service.retry_pending_iiko_submissions()

    assert result.failed == 1
    assert repository.dead == [{"job_id": 7, "error_message": "Номер дома слишком длинный. Укажите номер дома длиной не более 10 символов."}]


@pytest.mark.asyncio
async def test_invalid_house_does_not_create_yookassa_payment(monkeypatch):
    class FakePaymentService:
        called = False

        async def create_payment(self, **_):
            self.called = True
            raise AssertionError("YooKassa must not be called for an invalid address")

    class FakeRateLimiter:
        async def check(self, **_):
            return None

    monkeypatch.setattr(orders_router, "ensure_order_time_open", lambda: None)
    monkeypatch.setattr(orders_router, "rate_limiter", FakeRateLimiter())
    payment_service = FakePaymentService()
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/orders",
            "headers": [],
            "query_string": b"",
            "client": ("127.0.0.1", 8000),
            "scheme": "http",
            "server": ("testserver", 80),
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        await orders_router.create_order(
            payload=build_payload(delivery_house="12345678901"),
            request=request,
            user=SimpleNamespace(id=1, bonus_balance=0, phone="+79990000000"),
            order_service=build_service(monkeypatch),
            payment_service=payment_service,
            user_service=SimpleNamespace(),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Номер дома слишком длинный. Укажите номер дома длиной не более 10 символов."
    assert not payment_service.called
