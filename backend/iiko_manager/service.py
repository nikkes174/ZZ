from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional, Tuple

from backend.iiko_manager.client import IikoApiClient
from backend.iiko_manager.repository import CatalogSyncItem, CatalogSyncResult, IikoCatalogRepository


class IikoCatalogSyncError(Exception):
    pass


logger = logging.getLogger(__name__)


@dataclass
class IikoCatalogSyncService:
    client: IikoApiClient
    repository: IikoCatalogRepository
    terminal_group_id: str
    organization_id: Optional[str] = None

    async def sync(self) -> CatalogSyncResult:
        logger.info("Catalog sync started. terminal_group_id=%s", self.terminal_group_id)
        token = await self.client.get_access_token()
        organization_id = await self._resolve_organization_id(token=token)
        nomenclature = await self.client.get_nomenclature(token=token, organization_id=organization_id)
        items = self._build_sync_items(nomenclature)
        synced_at = datetime.now(timezone.utc)
        logger.info("Prepared %s normalized iiko items for sync.", len(items))
        result = await self.repository.sync_items(
            items=items,
            synced_at=synced_at,
            terminal_group_id=self.terminal_group_id,
        )
        logger.info(
            "Catalog sync persisted successfully. created=%s updated=%s deactivated=%s",
            result.created,
            result.updated,
            result.deactivated,
        )
        return result

    async def _resolve_organization_id(self, *, token: str) -> str:
        if self.organization_id:
            logger.info("Using configured iiko organization id=%s", self.organization_id)
            return self.organization_id

        organizations = await self.client.get_organizations(token=token)
        if len(organizations) != 1:
            raise IikoCatalogSyncError(
                "IIKO_ORGANIZATION_ID is required when the iiko account contains more than one organization."
            )

        organization_id = organizations[0].get("id")
        if not organization_id:
            raise IikoCatalogSyncError("iiko organizations response did not include a valid organization id.")
        logger.info("Resolved iiko organization automatically. organization_id=%s", organization_id)
        return str(organization_id)

    def _build_sync_items(self, nomenclature: dict[str, Any]) -> list[CatalogSyncItem]:
        groups_by_id = {
            str(group.get("id")): group
            for group in nomenclature.get("groups", [])
            if isinstance(group, dict) and group.get("id")
        }

        normalized_items: list[CatalogSyncItem] = []
        products_without_price = 0
        deleted_products = 0
        seen_terminal_group_ids: set[str] = set()
        matched_by_current_price = 0
        for product in nomenclature.get("products", []):
            if not isinstance(product, dict):
                continue

            product_id = product.get("id")
            if not product_id:
                continue

            group_id = self._to_str_or_none(product.get("parentGroup") or product.get("groupId"))
            group = groups_by_id.get(group_id or "")
            parent_group_id = self._to_str_or_none(group.get("parentGroup")) if group else None
            title = self._resolve_title(product)
            category = self._resolve_category_name(group=group)
            description = self._resolve_description(product=product, category=category, title=title)
            seen_terminal_group_ids.update(self._collect_terminal_group_ids(product))
            price, price_source = self._extract_price(product)
            is_deleted = bool(product.get("isDeleted"))
            is_active = (not is_deleted) and price is not None
            if price is None:
                products_without_price += 1
            elif price_source == "currentPrice":
                matched_by_current_price += 1
            if is_deleted:
                deleted_products += 1

            normalized_items.append(
                CatalogSyncItem(
                    iiko_product_id=str(product_id),
                    iiko_group_id=group_id,
                    iiko_category_name=category,
                    iiko_parent_group_id=parent_group_id,
                    iiko_terminal_group_id=self.terminal_group_id,
                    title=title,
                    description=description,
                    category=category,
                    price_from_iiko=price,
                    is_active=is_active,
                    is_deleted_in_iiko=is_deleted,
                    sync_hash=self._build_sync_hash(
                        product_id=str(product_id),
                        group_id=group_id,
                        parent_group_id=parent_group_id,
                        title=title,
                        description=description,
                        category=category,
                        price=price,
                        is_active=is_active,
                        is_deleted=is_deleted,
                    ),
                )
            )

        logger.info(
            "Normalized iiko products. total=%s without_price=%s deleted=%s active=%s",
            len(normalized_items),
            products_without_price,
            deleted_products,
            sum(1 for item in normalized_items if item.is_active),
        )
        logger.info("Price extraction summary. matched_by_currentPrice=%s", matched_by_current_price)
        if products_without_price == len(normalized_items) and normalized_items:
            logger.warning(
                "No prices were matched for terminal group %s. Available terminalGroupId examples from iiko: %s",
                self.terminal_group_id,
                ", ".join(sorted(seen_terminal_group_ids)[:10]) or "none",
            )
        return normalized_items

    def _extract_price(self, product: dict[str, Any]) -> Tuple[Optional[int], Optional[str]]:
        for size_price in product.get("sizePrices", []):
            if not isinstance(size_price, dict):
                continue
            price_container = size_price.get("price") or {}
            current_prices = price_container.get("currentPrices") or []
            for price_item in current_prices:
                if not isinstance(price_item, dict):
                    continue
                if price_item.get("terminalGroupId") != self.terminal_group_id:
                    continue
                value = price_item.get("price")
                if value is None:
                    continue
                return int(value), "currentPrices"

            # В этой организации iiko отдает общую цену без terminalGroupId.
            current_price = price_container.get("currentPrice")
            if current_price is not None:
                return int(current_price), "currentPrice"
        return None, None

    def _collect_terminal_group_ids(self, product: dict[str, Any]) -> set[str]:
        terminal_group_ids: set[str] = set()
        for size_price in product.get("sizePrices", []):
            if not isinstance(size_price, dict):
                continue
            price_container = size_price.get("price") or {}
            current_prices = price_container.get("currentPrices") or []
            for price_item in current_prices:
                if not isinstance(price_item, dict):
                    continue
                terminal_group_id = self._to_str_or_none(price_item.get("terminalGroupId"))
                if terminal_group_id:
                    terminal_group_ids.add(terminal_group_id)
        return terminal_group_ids

    def _resolve_title(self, product: dict[str, Any]) -> str:
        title = str(product.get("name") or "").strip()
        if not title:
            raise IikoCatalogSyncError("iiko product without name was returned.")
        return title

    def _resolve_description(self, *, product: dict[str, Any], category: str, title: str) -> str:
        for key in ("description", "additionalInfo", "seoDescription"):
            value = product.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return f"{title} ({category})"

    def _resolve_category_name(self, *, group: Optional[dict[str, Any]]) -> str:
        if not group:
            return "Разное"

        name = str(group.get("name") or "").strip()
        return name or "Разное"

    def _build_sync_hash(
        self,
        *,
        product_id: str,
        group_id: Optional[str],
        parent_group_id: Optional[str],
        title: str,
        description: str,
        category: str,
        price: Optional[int],
        is_active: bool,
        is_deleted: bool,
    ) -> str:
        payload = {
            "category": category,
            "description": description,
            "group_id": group_id,
            "is_active": is_active,
            "is_deleted": is_deleted,
            "parent_group_id": parent_group_id,
            "price": price,
            "product_id": product_id,
            "title": title,
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _to_str_or_none(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
