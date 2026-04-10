from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from config import API_IIKO, IIKO_BASE_URL, IIKO_ORGANIZATION_ID, TERMINAL_ID_GROUP


def _print_header(title: str) -> None:
    print(f"\n{'=' * 20} {title} {'=' * 20}")


async def get_token(client: httpx.AsyncClient) -> str:
    response = await client.post(
        f"{IIKO_BASE_URL}/access_token",
        json={"apiLogin": API_IIKO},
    )
    print("TOKEN STATUS:", response.status_code)
    response.raise_for_status()
    payload = response.json()
    token = payload.get("token")
    if not token:
        raise RuntimeError("iiko не вернул token")
    return str(token)


async def post_iiko(
    client: httpx.AsyncClient,
    token: str,
    path: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    response = await client.post(
        f"{IIKO_BASE_URL}/{path}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    print(f"{path.upper()} STATUS:", response.status_code)
    response.raise_for_status()
    return response.json()


async def get_organizations(client: httpx.AsyncClient, token: str) -> list[dict[str, Any]]:
    payload = await post_iiko(client, token, "organizations", {})
    return payload.get("organizations", [])


async def get_terminal_groups(
    client: httpx.AsyncClient,
    token: str,
    organization_ids: list[str],
) -> list[dict[str, Any]]:
    payload = await post_iiko(client, token, "terminal_groups", {"organizationIds": organization_ids})
    return payload.get("terminalGroups", [])


async def get_nomenclature(
    client: httpx.AsyncClient,
    token: str,
    organization_id: str,
) -> dict[str, Any]:
    return await post_iiko(client, token, "nomenclature", {"organizationId": organization_id})


def collect_terminal_group_ids(product: dict[str, Any]) -> list[str]:
    result: set[str] = set()
    for size_price in product.get("sizePrices", []):
        if not isinstance(size_price, dict):
            continue
        price_block = size_price.get("price") or {}
        for price_item in price_block.get("currentPrices", []) or []:
            if not isinstance(price_item, dict):
                continue
            terminal_group_id = price_item.get("terminalGroupId")
            if terminal_group_id:
                result.add(str(terminal_group_id))
    return sorted(result)


def extract_price(product: dict[str, Any], terminal_group_id: str) -> tuple[int | None, str | None]:
    for size_price in product.get("sizePrices", []):
        if not isinstance(size_price, dict):
            continue

        price_block = size_price.get("price") or {}
        for price_item in price_block.get("currentPrices", []) or []:
            if not isinstance(price_item, dict):
                continue
            if price_item.get("terminalGroupId") == terminal_group_id and price_item.get("price") is not None:
                return int(price_item["price"]), "currentPrices"

        current_price = price_block.get("currentPrice")
        if current_price is not None:
            return int(current_price), "currentPrice"
    return None, None


def print_organizations(organizations: list[dict[str, Any]]) -> None:
    _print_header("ORGANIZATIONS")
    for org in organizations:
        print(
            json.dumps(
                {
                    "id": org.get("id"),
                    "name": org.get("name"),
                    "code": org.get("code"),
                },
                ensure_ascii=False,
            )
        )


def print_terminal_groups(terminal_groups: list[dict[str, Any]]) -> None:
    _print_header("TERMINAL GROUPS")
    for group_block in terminal_groups:
        for item in group_block.get("items", []) or []:
            print(
                json.dumps(
                    {
                        "id": item.get("id"),
                        "name": item.get("name"),
                        "organizationId": item.get("organizationId"),
                    },
                    ensure_ascii=False,
                )
            )


def print_nomenclature_diagnostics(menu: dict[str, Any], terminal_group_id: str) -> None:
    products = menu.get("products", []) or []
    groups = menu.get("groups", []) or []

    _print_header("NOMENCLATURE SUMMARY")
    print("groups:", len(groups))
    print("products:", len(products))
    print("target terminal group:", terminal_group_id)

    with_price = 0
    deleted = 0
    seen_terminal_group_ids: set[str] = set()
    matched_by_current_price = 0

    for product in products:
        if not isinstance(product, dict):
            continue
        if product.get("isDeleted"):
            deleted += 1
        seen_terminal_group_ids.update(collect_terminal_group_ids(product))
        price, price_source = extract_price(product, terminal_group_id)
        if price is not None:
            with_price += 1
        if price_source == "currentPrice":
            matched_by_current_price += 1

    print("products with matched price:", with_price)
    print("deleted products:", deleted)
    print("matched by currentPrice:", matched_by_current_price)
    print("terminalGroupId in currentPrices:", sorted(seen_terminal_group_ids)[:20] or "none")

    _print_header("FIRST PRODUCTS DIAGNOSTICS")
    shown = 0
    for product in products:
        if not isinstance(product, dict):
            continue
        info = {
            "id": product.get("id"),
            "name": product.get("name"),
            "type": product.get("type"),
            "isDeleted": product.get("isDeleted"),
            "groupId": product.get("groupId"),
            "parentGroup": product.get("parentGroup"),
            "sizePrices_count": len(product.get("sizePrices", []) or []),
            "terminalGroupIds": collect_terminal_group_ids(product),
            "matched_price": extract_price(product, terminal_group_id)[0],
            "matched_price_source": extract_price(product, terminal_group_id)[1],
            "keys": sorted(product.keys()),
        }
        print(json.dumps(info, ensure_ascii=False, indent=2))

        if product.get("sizePrices"):
            print("sizePrices sample:")
            print(json.dumps(product.get("sizePrices"), ensure_ascii=False, indent=2)[:4000])
        else:
            print("sizePrices sample: []")

        shown += 1
        if shown >= 5:
            break


async def main() -> None:
    if not API_IIKO:
        raise RuntimeError("В .env не задан API_IIKO")

    if not TERMINAL_ID_GROUP:
        raise RuntimeError("В .env не задан TERMINAL_ID_GROUP")

    async with httpx.AsyncClient(timeout=30) as client:
        token = await get_token(client)

        organizations = await get_organizations(client, token)
        print_organizations(organizations)

        organization_id = IIKO_ORGANIZATION_ID or (organizations[0]["id"] if organizations else None)
        if not organization_id:
            raise RuntimeError("Не удалось определить organization_id")

        terminal_groups = await get_terminal_groups(client, token, [organization_id])
        print_terminal_groups(terminal_groups)

        menu = await get_nomenclature(client, token, organization_id)
        print_nomenclature_diagnostics(menu, TERMINAL_ID_GROUP)


if __name__ == "__main__":
    asyncio.run(main())
