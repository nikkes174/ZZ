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

    async def _post(self, path: str, json_payload: dict[str, Any], *, token: Optional[str]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}"} if token else None
        logger.debug("Sending iiko request. path=%s payload_keys=%s", path, sorted(json_payload.keys()))
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(f"{self.base_url}/{path}", json=json_payload, headers=headers)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = response.text.strip()
            raise IikoClientError(f"iiko request failed for {path}: {response.status_code} {detail}") from exc

        payload = response.json()
        if not isinstance(payload, dict):
            raise IikoClientError(f"iiko returned non-object payload for {path}.")
        logger.debug("iiko request finished successfully. path=%s status=%s", path, response.status_code)
        return payload
