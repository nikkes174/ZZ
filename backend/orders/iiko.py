from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional

from backend.iiko_manager.client import IikoApiClient, IikoClientError
from backend.orders.schemas import OrderCreate


logger = logging.getLogger(__name__)
_HOUSE_RE = re.compile(r"(?:д\.?|дом)\s*([0-9A-Za-zА-Яа-я/-]+)", re.IGNORECASE)
_FLAT_RE = re.compile(r"(?:кв\.?|квартира)\s*([0-9A-Za-zА-Яа-я/-]+)", re.IGNORECASE)
_BUILDING_RE = re.compile(r"(?:к\.|корп\.?|корпус)\s*([0-9A-Za-zА-Яа-я/-]+)", re.IGNORECASE)
_HOUSE_NUMBER_RE = re.compile(r"\b([0-9]+[0-9A-Za-zА-Яа-я/-]*)\b")
_ADDRESS_PART_LABEL_RE = re.compile(
    r"^(?:ул\.?|улица|пр\.?|проспект|пер\.?|переулок|бульвар|б-р)\s+",
    re.IGNORECASE,
)


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
    terminal_group_id: Optional[str]
    source_key: str = "zamzam-site"

    async def submit_order(
        self,
        *,
        payload: OrderCreate,
        items: list[IikoOrderItem],
        total_amount: int,
    ) -> dict[str, str]:
        if not self.client.api_login:
            raise IikoOrderError("API_IIKO is not configured.")
        if not self.terminal_group_id:
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

        comment_parts = []
        if payload.comment:
            comment_parts.append(payload.comment.strip())
        if payload.entrance:
            comment_parts.append(f"Подъезд: {payload.entrance.strip()}")
        if payload.cutlery_count > 0:
            comment_parts.append(f"Приборы: {payload.cutlery_count}")

        order_payload: dict[str, object] = {
            "organizationId": organization_id,
            "terminalGroupId": self.terminal_group_id,
            "order": {
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
            },
        }
        if self.source_key:
            order_payload["order"]["sourceKey"] = self.source_key
        if comment_parts:
            order_payload["order"]["comment"] = " | ".join(comment_parts)
        if payments:
            order_payload["order"]["payments"] = payments
        if payload.checkout_type == "delivery" and payload.delivery_address:
            order_payload["order"]["deliveryPoint"] = self._build_delivery_point(
                address=payload.delivery_address,
                entrance=payload.entrance,
                comment=payload.comment,
            )

        try:
            response_payload = await self.client.create_delivery_order(token=token, payload=order_payload)
        except IikoClientError as exc:
            raise IikoOrderError(str(exc)) from exc

        order_info = response_payload.get("orderInfo") or {}
        creation_status = str(order_info.get("creationStatus") or "")
        if creation_status not in {"Success", "InProgress"}:
            error_info = order_info.get("errorInfo") or {}
            error_code = error_info.get("code")
            error_message = str(error_info.get("message") or error_info.get("description") or "Unknown iiko error.")
            raise IikoOrderError(self._to_user_message(error_code=error_code, error_message=error_message))

        logger.info(
            "iiko order accepted. creation_status=%s order_id=%s correlation_id=%s",
            creation_status,
            order_info.get("id"),
            response_payload.get("correlationId"),
        )
        return {
            "iiko_order_id": str(order_info.get("id") or ""),
            "correlation_id": str(response_payload.get("correlationId") or ""),
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
            return []
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

    def _build_delivery_point(self, *, address: str, entrance: Optional[str], comment: Optional[str]) -> dict[str, object]:
        normalized_address = address.strip()
        parsed_address = self._parse_delivery_address(normalized_address, entrance=entrance)
        comment_parts = []
        if entrance:
            comment_parts.append(f"Подъезд: {entrance.strip()}")
        if comment:
            comment_parts.append(comment.strip())
        comment_parts.append(f"Адрес: {normalized_address}")

        payload: dict[str, object] = {
            "address": parsed_address,
        }
        if comment_parts:
            payload["comment"] = " | ".join(comment_parts)
        return payload

    def _parse_delivery_address(self, address: str, entrance: Optional[str]) -> dict[str, object]:
        parts = [part.strip() for part in address.split(",") if part.strip()]
        house = self._extract_house(address)
        street = self._extract_street(parts=parts, house=house, fallback=address)
        parsed_address: dict[str, object] = {
            "street": {
                "name": street,
            },
            "house": house,
        }

        building = self._extract_optional_part(_BUILDING_RE, address)
        if building:
            parsed_address["building"] = building

        flat = self._extract_optional_part(_FLAT_RE, address)
        if flat:
            parsed_address["flat"] = flat

        if entrance and entrance.strip():
            parsed_address["entrance"] = entrance.strip()[:64]

        return parsed_address

    def _extract_street(self, *, parts: list[str], house: str, fallback: str) -> str:
        for part in parts:
            if house and house in part and any(char.isdigit() for char in part):
                continue
            if _FLAT_RE.search(part) or _BUILDING_RE.search(part):
                continue
            cleaned = _ADDRESS_PART_LABEL_RE.sub("", part).strip()
            if cleaned:
                return cleaned[:255]

        cleaned_fallback = fallback.replace(house, "").strip(" ,")
        return (cleaned_fallback or fallback)[:255]

    def _extract_optional_part(self, pattern: re.Pattern[str], address: str) -> Optional[str]:
        match = pattern.search(address)
        if not match:
            return None
        return match.group(1).strip()[:64]

    def _extract_house(self, address: str) -> str:
        match = _HOUSE_RE.search(address)
        if match:
            return match.group(1)

        parts = [part.strip() for part in address.split(",") if part.strip()]
        for part in reversed(parts):
            if _FLAT_RE.search(part) or _BUILDING_RE.search(part):
                continue
            if any(char.isdigit() for char in part):
                number_match = _HOUSE_NUMBER_RE.search(part)
                if number_match:
                    return number_match.group(1)[:64]
                return part[:64]
        return address[:64]

    def _to_user_message(self, *, error_code: object, error_message: str) -> str:
        if error_code == "TerminalGroupDisabled":
            return "iiko не принял заказ: группа терминалов отключена или не зарегистрирована."
        return f"iiko не принял заказ: {error_message}"
