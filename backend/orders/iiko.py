from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from backend.iiko_manager.client import IikoApiClient, IikoClientError
from backend.orders.schemas import OrderCreate


logger = logging.getLogger(__name__)
DEFAULT_DELIVERY_CITY = "Екатеринбург"


class IikoOrderError(Exception):
    pass


@dataclass(frozen=True)
class IikoOrderItem:
    product_id: str
    title: str
    price: int
    quantity: int


@dataclass
class IikoOrderGateway:
    client: IikoApiClient
    organization_id: Optional[str]
    source_key: str = "zamzam-site"
    online_payment_type_id: Optional[str] = None
    online_payment_type_kind: str = "Card"

    async def submit_order(
            self,
            *,
            payload: OrderCreate,
            items: list[IikoOrderItem],
            total_amount: int,
            terminal_group_id: str,
            external_number: Optional[str] = None,
    ) -> dict[str, str]:
        if not self.client.api_login:
            raise IikoOrderError("API_IIKO is not configured.")

        if not terminal_group_id:
            raise IikoOrderError("TERMINAL_ID_GROUP is not configured.")

        token = await self.client.get_access_token()
        organization_id = await self._resolve_organization_id(token=token)

        order_type_id = await self._resolve_order_type_id(
            token=token,
            checkout_type=payload.checkout_type,
            organization_id=organization_id,
        )

        payments = await self._build_payments(
            token=token,
            organization_id=organization_id,
            payment_type=payload.payment_type,
            total_amount=total_amount,
        )

        comment_parts: list[str] = []

        if payload.comment and payload.comment.strip():
            comment_parts.append(payload.comment.strip())

        if payload.cutlery_count > 0:
            comment_parts.append(f"Приборы: {payload.cutlery_count}")

        order_data: dict[str, object] = {
            "phone": payload.customer_phone,
            "customer": {
                "name": payload.customer_name,
            },
            "orderTypeId": order_type_id,
            "items": [
                {
                    "productId": item.product_id,
                    "type": "Product",
                    "amount": item.quantity,
                    "price": item.price,
                }
                for item in items
            ],
        }

        if self.source_key:
            order_data["sourceKey"] = self.source_key

        if external_number:
            order_data["externalNumber"] = external_number[:50]

        if comment_parts:
            order_data["comment"] = " | ".join(comment_parts)

        if payments:
            order_data["payments"] = payments

        if payload.checkout_type == "delivery":
            delivery_street = (payload.delivery_street or "").strip()
            delivery_house = (payload.delivery_house or "").strip()

            if not delivery_street:
                raise IikoOrderError("Не указана улица доставки.")

            if not delivery_house:
                raise IikoOrderError("Не указан номер дома.")

            delivery_info = self._build_delivery_info(
                street=delivery_street,
                house=delivery_house,
                flat=payload.delivery_flat,
                entrance=payload.entrance,
            )

            order_data["deliveryInfo"] = delivery_info

            logger.info(
                "Sending iiko delivery info. street=%s house=%s delivery_info=%s",
                delivery_street,
                delivery_house,
                delivery_info,
            )

        order_payload: dict[str, object] = {
            "organizationId": organization_id,
            "terminalGroupId": terminal_group_id,
            "order": order_data,
        }

        try:
            response_payload = await self.client.create_delivery_order(
                token=token,
                payload=order_payload,
            )
        except IikoClientError as exc:
            raise IikoOrderError(str(exc)) from exc

        raw_order_info = response_payload.get("orderInfo")
        order_info = raw_order_info if isinstance(raw_order_info, dict) else {}

        creation_status = str(order_info.get("creationStatus") or "")

        if creation_status not in {"Success", "InProgress"}:
            raw_error_info = order_info.get("errorInfo")
            error_info = raw_error_info if isinstance(raw_error_info, dict) else {}

            error_code = error_info.get("code")
            error_message = str(
                error_info.get("message")
                or error_info.get("description")
                or "Unknown iiko error."
            )

            raise IikoOrderError(
                self._to_user_message(
                    error_code=error_code,
                    error_message=error_message,
                )
            )

        iiko_order_id = str(order_info.get("id") or "")
        correlation_id = str(response_payload.get("correlationId") or "")

        logger.info(
            "iiko order accepted. creation_status=%s order_id=%s correlation_id=%s",
            creation_status,
            iiko_order_id,
            correlation_id,
        )

        if iiko_order_id:
            try:
                await self.client.confirm_delivery_order(
                    token=token,
                    organization_id=organization_id,
                    order_id=iiko_order_id,
                )
            except IikoClientError as exc:
                logger.warning(
                    "Could not confirm iiko delivery order. order_id=%s error=%s",
                    iiko_order_id,
                    exc,
                )

        return {
            "iiko_order_id": iiko_order_id,
            "correlation_id": correlation_id,
            "creation_status": creation_status,
        }
    async def _resolve_organization_id(self, *, token: str) -> str:
        if self.organization_id:
            return self.organization_id

        try:
            organizations = await self.client.get_organizations(token=token)
        except IikoClientError as exc:
            raise IikoOrderError(str(exc)) from exc

        if len(organizations) != 1:
            raise IikoOrderError("IIKO_ORGANIZATION_ID is required for order submission.")

        organization_id = organizations[0].get("id")
        if not organization_id:
            raise IikoOrderError("iiko did not return a valid organization id.")
        return str(organization_id)

    async def _resolve_order_type_id(self, *, token: str, checkout_type: str, organization_id: str) -> str:
        try:
            groups = await self.client.get_delivery_order_types(token=token, organization_ids=[organization_id])
        except IikoClientError as exc:
            raise IikoOrderError(str(exc)) from exc

        target_service_type = "DeliveryPickUp" if checkout_type == "pickup" else "DeliveryByCourier"
        for group in groups:
            if str(group.get("organizationId") or "") != organization_id:
                continue
            for item in group.get("items", []) or []:
                if item.get("isDeleted"):
                    continue
                if item.get("orderServiceType") == target_service_type and item.get("id"):
                    return str(item["id"])

        raise IikoOrderError(f"iiko order type for {checkout_type} was not found.")

    async def _build_payments(
        self,
        *,
        token: str,
        organization_id: str,
        payment_type: str,
        total_amount: int,
    ) -> list[dict[str, object]]:
        if payment_type != "cash":
            if not self.online_payment_type_id:
                logger.warning("Online iiko payment type is not configured. order will be sent without payments.")
                return []
            if total_amount <= 0:
                return []
            return [
                {
                    "paymentTypeKind": self.online_payment_type_kind,
                    "sum": float(total_amount),
                    "paymentTypeId": self.online_payment_type_id,
                    "isProcessedExternally": True,
                    "isFiscalizedExternally": True,
                    "isPrepay": True,
                }
            ]
        if total_amount <= 0:
            return []

        try:
            payment_types = await self.client.get_payment_types(token=token, organization_ids=[organization_id])
        except IikoClientError as exc:
            raise IikoOrderError(str(exc)) from exc

        for payment in payment_types:
            if payment.get("isDeleted"):
                continue
            if payment.get("paymentTypeKind") != "Cash":
                continue
            payment_type_id = payment.get("id")
            if not payment_type_id:
                continue
            return [
                {
                    "paymentTypeKind": "Cash",
                    "sum": float(total_amount),
                    "paymentTypeId": str(payment_type_id),
                    "isProcessedExternally": False,
                    "isFiscalizedExternally": False,
                    "isPrepay": False,
                }
            ]

        logger.warning("Cash payment type was not found in iiko. order will be sent without payments.")
        return []

    def _build_delivery_info(
        self,
        *,
        street: str,
        house: str,
        flat: Optional[str],
        entrance: Optional[str],
    ) -> dict[str, object]:
        normalized_street = street.strip()
        normalized_house = house.strip()

        line_parts = [
            f"город {DEFAULT_DELIVERY_CITY}",
            normalized_street,
            f"дом {normalized_house}",
        ]

        if flat and flat.strip():
            line_parts.append(f"квартира {flat.strip()}")

        if entrance and entrance.strip():
            line_parts.append(entrance.strip())

        return {
            "address": {
                "line1": ", ".join(line_parts),
                "type": "city",
            },
        }

    def _to_user_message(self, *, error_code: object, error_message: str) -> str:
        if error_code == "TerminalGroupDisabled":
            return "iiko не принял заказ: группа терминалов отключена или не зарегистрирована."
        return f"iiko не принял заказ: {error_message}"
