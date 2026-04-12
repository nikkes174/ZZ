from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx
import logging


class IikoClientError(Exception):
    pass


logger = logging.getLogger(__name__)


@dataclass
class IikoApiClient:
    api_login: str
    base_url: str
    timeout_seconds: int = 20

    async def get_access_token(self) -> str:
        logger.info("Requesting iiko access token.")
        payload = await self._post("access_token", {"apiLogin": self.api_login}, token=None)
        token = payload.get("token")
        if not token:
            raise IikoClientError("iiko did not return an access token.")
        logger.info("iiko access token received successfully.")
        return str(token)

    async def get_organizations(self, *, token: str) -> list[dict[str, Any]]:
        logger.info("Requesting iiko organizations.")
        payload = await self._post("organizations", {}, token=token)
        organizations = payload.get("organizations")
        if not isinstance(organizations, list):
            raise IikoClientError("iiko organizations response is invalid.")
        logger.info("iiko organizations received. count=%s", len(organizations))
        return organizations

    async def get_nomenclature(self, *, token: str, organization_id: str) -> dict[str, Any]:
        logger.info("Requesting iiko nomenclature. organization_id=%s", organization_id)
        payload = await self._post("nomenclature", {"organizationId": organization_id}, token=token)
        if not isinstance(payload, dict):
            raise IikoClientError("iiko nomenclature response is invalid.")
        logger.info(
            "iiko nomenclature received. groups=%s products=%s",
            len(payload.get("groups", [])),
            len(payload.get("products", [])),
        )
        return payload

    async def get_delivery_order_types(self, *, token: str, organization_ids: list[str]) -> list[dict[str, Any]]:
        logger.info("Requesting iiko delivery order types. organization_ids=%s", organization_ids)
        payload = await self._post("deliveries/order_types", {"organizationIds": organization_ids}, token=token)
        order_types = payload.get("orderTypes")
        if not isinstance(order_types, list):
            raise IikoClientError("iiko delivery order types response is invalid.")
        logger.info("iiko delivery order types received. groups=%s", len(order_types))
        return order_types

    async def get_payment_types(self, *, token: str, organization_ids: list[str]) -> list[dict[str, Any]]:
        logger.info("Requesting iiko payment types. organization_ids=%s", organization_ids)
        payload = await self._post("payment_types", {"organizationIds": organization_ids}, token=token)
        payment_types = payload.get("paymentTypes")
        if not isinstance(payment_types, list):
            raise IikoClientError("iiko payment types response is invalid.")
        logger.info("iiko payment types received. count=%s", len(payment_types))
        return payment_types

    async def create_delivery_order(self, *, token: str, payload: dict[str, Any]) -> dict[str, Any]:
        logger.info(
            "Sending delivery order to iiko. organization_id=%s terminal_group_id=%s",
            payload.get("organizationId"),
            payload.get("terminalGroupId"),
        )
        response_payload = await self._post("deliveries/create", payload, token=token)
        if not isinstance(response_payload, dict):
            raise IikoClientError("iiko delivery create response is invalid.")
        return response_payload

    async def get_delivery_orders_by_ids(
        self,
        *,
        token: str,
        organization_id: str,
        order_ids: list[str],
    ) -> list[dict[str, Any]]:
        logger.info("Requesting iiko delivery orders by ids. count=%s", len(order_ids))
        payload = await self._post(
            "deliveries/by_id",
            {
                "organizationId": organization_id,
                "orderIds": order_ids,
            },
            token=token,
        )
        orders = payload.get("orders")
        if not isinstance(orders, list):
            raise IikoClientError("iiko deliveries by id response is invalid.")
        logger.info("iiko delivery orders received. count=%s", len(orders))
        return orders

    async def _post(self, path: str, json_payload: dict[str, Any], *, token: Optional[str]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}"} if token else None
        logger.debug("Sending iiko request. path=%s payload_keys=%s", path, sorted(json_payload.keys()))
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(f"{self.base_url}/{path}", json=json_payload, headers=headers)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = response.text.strip()
            logger.warning(
                "iiko request failed. path=%s status=%s detail=%s",
                path,
                response.status_code,
                detail,
            )
            raise IikoClientError(f"iiko request failed for {path}: {response.status_code} {detail}") from exc

        payload = response.json()
        if not isinstance(payload, dict):
            raise IikoClientError(f"iiko returned non-object payload for {path}.")
        logger.debug("iiko request finished successfully. path=%s status=%s", path, response.status_code)
        return payload
