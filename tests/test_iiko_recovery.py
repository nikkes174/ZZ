from types import SimpleNamespace
from datetime import datetime, timezone

import pytest
import httpx

from backend.orders.iiko import IikoOrderError, IikoOrderGateway, IikoOrderItem
from backend.orders.schemas import OrderCreate, OrderItemPayload
from backend.orders.service import NormalizedOrderItem, OrderService, PreparedOrder
from backend.orders.branches import BranchCode


def pickup_payload():
    return OrderCreate(
        customer_name="Клиент",
        customer_phone="+79990000000",
        checkout_type="pickup",
        payment_type="card",
        items=[OrderItemPayload(id="1", title="Тест", price=500, quantity=1)],
        branch_code=BranchCode.MALYSHAVA,
    )


class GatewayClient:
    api_login = "token"

    def __init__(self, create_response):
        self.create_response = create_response
        self.create_payloads = []

    async def get_access_token(self):
        return "access"

    async def get_delivery_order_types(self, **_):
        return [{"organizationId": "org", "items": [{"id": "type", "orderServiceType": "DeliveryPickUp"}]}]

    async def create_delivery_order(self, *, token, payload):
        self.create_payloads.append(payload)
        return self.create_response

    async def confirm_delivery_order(self, **_):
        return {}


@pytest.mark.asyncio
async def test_timeout_error_keeps_iiko_ids_and_stable_request_id():
    client = GatewayClient(
        {
            "correlationId": "corr",
            "orderInfo": {
                "id": "ed80f47c-9878-422e-a9ae-d4c74a06ddc7",
                "posId": "276a9749-858e-4673-9fa9-196d21001e28",
                "creationStatus": "Error",
                "errorInfo": {
                    "code": "Common",
                    "message": "Creation timeout expired, order automatically transited to error creation status",
                },
            },
        }
    )
    gateway = IikoOrderGateway(client=client, organization_id="org")

    with pytest.raises(IikoOrderError) as exc_info:
        await gateway.submit_order(
            payload=pickup_payload(),
            items=[IikoOrderItem(product_id="product", title="Тест", price=500, quantity=1)],
            total_amount=500,
            terminal_group_id="terminal",
            external_number="zamzam-order-48",
            iiko_request_order_id="11111111-1111-1111-1111-111111111111",
        )

    error = exc_info.value
    assert error.retryable and error.ambiguous
    assert error.iiko_order_id == "ed80f47c-9878-422e-a9ae-d4c74a06ddc7"
    assert error.pos_order_id == "276a9749-858e-4673-9fa9-196d21001e28"
    assert client.create_payloads[0]["order"]["id"] == "11111111-1111-1111-1111-111111111111"
    assert client.create_payloads[0]["createOrderSettings"]["transportToFrontTimeout"] == 60


@pytest.mark.asyncio
async def test_success_persists_order_and_pos_ids():
    client = GatewayClient(
        {"correlationId": "corr", "orderInfo": {"id": "order-id", "posId": "pos-id", "creationStatus": "Success"}}
    )
    gateway = IikoOrderGateway(client=client, organization_id="org")

    result = await gateway.submit_order(
        payload=pickup_payload(),
        items=[IikoOrderItem(product_id="product", title="Тест", price=500, quantity=1)],
        total_amount=500,
        terminal_group_id="terminal",
        external_number="zamzam-order-48",
        iiko_request_order_id="request-id",
    )

    assert result == {
        "iiko_order_id": "order-id",
        "iiko_pos_order_id": "pos-id",
        "correlation_id": "corr",
        "creation_status": "Success",
    }
    assert len(client.create_payloads) == 1


@pytest.mark.asyncio
async def test_in_progress_is_recovery_pending_candidate():
    client = GatewayClient({"orderInfo": {"id": "order-id", "posId": "pos-id", "creationStatus": "InProgress"}})
    gateway = IikoOrderGateway(client=client, organization_id="org")

    result = await gateway.submit_order(
        payload=pickup_payload(),
        items=[IikoOrderItem(product_id="product", title="Тест", price=500, quantity=1)],
        total_amount=500,
        terminal_group_id="terminal",
        iiko_request_order_id="request-id",
    )

    assert result["creation_status"] == "InProgress"
    assert len(client.create_payloads) == 1


class AttemptRepository:
    def __init__(self):
        self.updated = []

    async def claim_iiko_submission(self, *, order_id):
        return SimpleNamespace(id=order_id)

    async def ensure_iiko_request_order_id(self, *, order_id):
        return "11111111-1111-1111-1111-111111111111"

    async def update_iiko_attempt_result(self, **kwargs):
        self.updated.append(kwargs)
        now = datetime.now(timezone.utc)
        return SimpleNamespace(**{"id": kwargs["order_id"], "user_id": 1, "customer_name": "Клиент", "customer_phone": "+7999", "checkout_type": "pickup", "payment_type": "card", "delivery_address": None, "delivery_street": None, "delivery_house": None, "delivery_flat": None, "entrance": None, "comment": None, "items_json": '[{"id":"1","title":"Тест","price":500,"quantity":1}]', "items_count": 1, "cutlery_count": 0, "subtotal_amount": 500, "bonus_spent": 0, "total_amount": 500, "bonus_awarded": 0, "iiko_order_id": kwargs["iiko_order_id"], "iiko_correlation_id": kwargs["correlation_id"], "iiko_creation_status": kwargs["creation_status"], "status": "Готовится", "created_at": now, "updated_at": now, "branch_code": "malyshava", "iiko_terminal_group_id": "terminal"})


@pytest.mark.asyncio
async def test_ambiguous_submission_transitions_to_recovery_pending_without_dropping_ids():
    repository = AttemptRepository()

    class TimeoutGateway:
        async def submit_order(self, **_):
            raise IikoOrderError(
                "timeout",
                iiko_order_id="request-id",
                pos_order_id="pos-id",
                correlation_id="corr",
                creation_status="Error",
                error_code="Common",
                error_message="Creation timeout expired",
                retryable=True,
                ambiguous=True,
            )

    payload = pickup_payload()
    prepared = PreparedOrder(
        payload=payload,
        normalized_items=[NormalizedOrderItem(payload.items[0], "product")],
        subtotal_amount=500,
        total_amount=500,
        branch_code=BranchCode.MALYSHAVA,
        terminal_group_id="terminal",
    )
    service = OrderService(repository=repository, menu_item_repository=SimpleNamespace(), iiko_order_gateway=TimeoutGateway())

    result = await service.submit_claimed_order(order_id=48, prepared_order=prepared)

    assert result.iiko_creation_status == "RecoveryPending"
    assert repository.updated[0]["iiko_order_id"] == "request-id"
    assert repository.updated[0]["iiko_pos_order_id"] == "pos-id"


@pytest.mark.asyncio
async def test_recovery_success_uses_lookup_and_never_calls_create():
    updates = []

    class RecoveryRepository:
        async def update_iiko_attempt_result(self, **kwargs):
            updates.append(kwargs)

        async def reset_iiko_recovery_checks(self, **_):
            return None

    class RecoveryGateway:
        create_called = False

        async def recover_order(self, **_):
            return {"creation_status": "Success", "iiko_order_id": "request-id", "iiko_pos_order_id": "pos-id"}

    order = SimpleNamespace(
        id=48,
        iiko_recovery_checks=0,
        iiko_order_id="request-id",
        iiko_request_order_id="request-id",
        iiko_pos_order_id="pos-id",
        iiko_error_code="Common",
        iiko_error_message="Creation timeout expired",
    )
    gateway = RecoveryGateway()
    service = OrderService(repository=RecoveryRepository(), menu_item_repository=SimpleNamespace(), iiko_order_gateway=gateway)

    assert await service.recover_iiko_order(order) == "success"
    assert updates[0]["creation_status"] == "Success"
    assert not gateway.create_called


class RecoveryRepository:
    def __init__(self, *, checks=0, increment_result=None, rotate_result=None):
        self.checks = checks
        self.increment_result = increment_result
        self.rotate_result = rotate_result
        self.updated = []
        self.rotated = False

    async def update_iiko_attempt_result(self, **kwargs):
        self.updated.append(kwargs)

    async def reset_iiko_recovery_checks(self, **_):
        self.checks = 0

    async def increment_iiko_recovery_checks(self, **_):
        self.checks += 1
        return self.increment_result if self.increment_result is not None else self.checks

    async def rotate_iiko_request_order_id_for_confirmed_retry(self, **_):
        self.rotated = True
        return self.rotate_result


def timeout_order(checks=0):
    return SimpleNamespace(
        id=48,
        iiko_recovery_checks=checks,
        iiko_order_id="order-id",
        iiko_request_order_id="request-id",
        iiko_pos_order_id="pos-id",
        iiko_error_code="Common",
        iiko_error_message="Creation timeout expired",
    )


@pytest.mark.asyncio
async def test_recovery_by_order_id_success_does_not_create():
    repository = RecoveryRepository()

    class Gateway:
        async def recover_order(self, **kwargs):
            assert kwargs["iiko_order_id"] == "order-id"
            return {"creation_status": "Success", "iiko_order_id": "order-id"}

    service = OrderService(repository=repository, menu_item_repository=SimpleNamespace(), iiko_order_gateway=Gateway())
    assert await service.recover_iiko_order(timeout_order()) == "success"
    assert repository.updated[0]["creation_status"] == "Success"
    assert not repository.rotated


@pytest.mark.asyncio
async def test_recovery_by_pos_id_recovers_real_pos_order():
    repository = RecoveryRepository()

    class Gateway:
        async def recover_order(self, **_):
            return {"creation_status": "Error", "pos_found": True, "status": "Closed", "iiko_pos_order_id": "pos-id"}

    service = OrderService(repository=repository, menu_item_repository=SimpleNamespace(), iiko_order_gateway=Gateway())
    assert await service.recover_iiko_order(timeout_order()) == "success"
    assert repository.updated[0]["creation_status"] == "Success"


@pytest.mark.asyncio
async def test_missing_pos_order_waits_and_increments_recovery_checks():
    repository = RecoveryRepository()

    class Gateway:
        async def recover_order(self, **_):
            return {"creation_status": "Error", "error_message": "Creation timeout expired", "pos_found": False}

    service = OrderService(repository=repository, menu_item_repository=SimpleNamespace(), iiko_order_gateway=Gateway())
    assert await service.recover_iiko_order(timeout_order()) == "wait"
    assert repository.checks == 1
    assert not repository.rotated


@pytest.mark.asyncio
async def test_confirmed_timeout_absence_rotates_request_uuid_after_grace_period():
    repository = RecoveryRepository(increment_result=3, rotate_result="new-request-id")

    class Gateway:
        async def recover_order(self, **_):
            return {"creation_status": "Error", "error_message": "Creation timeout expired", "pos_found": False}

    service = OrderService(repository=repository, menu_item_repository=SimpleNamespace(), iiko_order_gateway=Gateway())
    assert await service.recover_iiko_order(timeout_order(checks=2)) == "resubmit"
    assert repository.rotated


@pytest.mark.asyncio
async def test_duplicate_order_id_is_retryable_and_preserves_lookup_metadata():
    client = GatewayClient(
        {"orderInfo": {"id": "existing-id", "posId": "existing-pos", "creationStatus": "Error", "errorInfo": {"code": "DuplicatedOrderId", "message": "Order already exists"}}}
    )
    gateway = IikoOrderGateway(client=client, organization_id="org")

    with pytest.raises(IikoOrderError) as exc_info:
        await gateway.submit_order(
            payload=pickup_payload(),
            items=[IikoOrderItem(product_id="product", title="Тест", price=500, quantity=1)],
            total_amount=500,
            terminal_group_id="terminal",
            iiko_request_order_id="request-id",
        )

    assert exc_info.value.error_code == "DuplicatedOrderId"
    assert exc_info.value.retryable and exc_info.value.ambiguous


@pytest.mark.asyncio
async def test_manual_review_is_selected_after_max_recovery_checks():
    repository = RecoveryRepository()

    class Gateway:
        async def recover_order(self, **_):
            raise AssertionError("manual review must not perform another lookup")

    order = timeout_order(checks=10)
    service = OrderService(repository=repository, menu_item_repository=SimpleNamespace(), iiko_order_gateway=Gateway())
    assert await service.recover_iiko_order(order) == "manual_review"
    assert repository.updated[0]["creation_status"] == "ManualReview"


@pytest.mark.asyncio
async def test_product_excluded_from_menu_is_permanent():
    client = GatewayClient(
        {"orderInfo": {"creationStatus": "Error", "errorInfo": {"code": "ProductExludedFromMenu", "message": "excluded"}}}
    )
    gateway = IikoOrderGateway(client=client, organization_id="org")

    with pytest.raises(IikoOrderError) as exc_info:
        await gateway.submit_order(
            payload=pickup_payload(),
            items=[IikoOrderItem(product_id="product", title="Тест", price=500, quantity=1)],
            total_amount=500,
            terminal_group_id="terminal",
            iiko_request_order_id="request-id",
        )

    assert not exc_info.value.retryable
    assert not exc_info.value.ambiguous


class ErrorHttpClient:
    def __init__(self, error=None, status_code=None):
        self.error = error
        self.status_code = status_code

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def post(self, *_args, **_kwargs):
        request = httpx.Request("POST", "https://iiko.test")
        if self.error:
            raise self.error("network", request=request)
        response = httpx.Response(self.status_code, request=request, text="gateway error")
        return response


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [502, 503, 504])
async def test_gateway_5xx_errors_are_retryable_and_ambiguous(monkeypatch, status_code):
    monkeypatch.setattr(httpx, "AsyncClient", lambda **_: ErrorHttpClient(status_code=status_code))
    from backend.iiko_manager.client import IikoApiClient, IikoClientError

    with pytest.raises(IikoClientError) as exc_info:
        await IikoApiClient(api_login="api", base_url="https://iiko.test")._post("deliveries/create", {}, token="token")

    assert exc_info.value.retryable
    assert exc_info.value.ambiguous
    assert exc_info.value.status_code == status_code


@pytest.mark.asyncio
async def test_read_timeout_is_ambiguous(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", lambda **_: ErrorHttpClient(error=httpx.ReadTimeout))
    from backend.iiko_manager.client import IikoApiClient, IikoClientError

    with pytest.raises(IikoClientError) as exc_info:
        await IikoApiClient(api_login="api", base_url="https://iiko.test")._post("deliveries/create", {}, token="token")

    assert exc_info.value.retryable
    assert exc_info.value.ambiguous


@pytest.mark.asyncio
async def test_concurrent_request_uuid_calls_share_one_value():
    import asyncio

    class ConcurrentRepository:
        def __init__(self):
            self.value = None
            self.lock = asyncio.Lock()

        async def ensure_iiko_request_order_id(self, **_):
            async with self.lock:
                if self.value is None:
                    self.value = "stable-request-id"
                return self.value

    repository = ConcurrentRepository()
    values = await asyncio.gather(
        repository.ensure_iiko_request_order_id(order_id=48),
        repository.ensure_iiko_request_order_id(order_id=48),
    )
    assert values == ["stable-request-id", "stable-request-id"]
