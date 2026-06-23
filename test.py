from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import text

from backend.iiko_manager.client import IikoApiClient
from backend.orders.crud import SqlAlchemyOrderRepository
from backend.orders.iiko import IikoOrderGateway
from backend.orders.service import OrderService
from backend.redactor.crud import SqlAlchemyMenuItemRepository
from config import (
    API_IIKO,
    IIKO_BASE_URL,
    IIKO_ONLINE_PAYMENT_TYPE_ID,
    IIKO_ONLINE_PAYMENT_TYPE_KIND,
    IIKO_ORDER_SOURCE_KEY,
    IIKO_ORDER_TIMEOUT_SECONDS,
    IIKO_ORGANIZATION_ID,
    TERMINAL_ID_GROUP,
)
from db import AsyncSessionLocal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manually enqueue and/or send one existing order to iiko.",
    )
    parser.add_argument("order_id", type=int, help="orders.id to send to iiko")
    parser.add_argument(
        "--enqueue-only",
        action="store_true",
        help="Only create the delivery job; do not run the worker immediately.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow resending an order stuck outside LocalPending/Failed. Never resends if iiko_order_id already exists.",
    )
    return parser.parse_args()


def build_order_service(repository: SqlAlchemyOrderRepository, menu_repository: SqlAlchemyMenuItemRepository) -> OrderService:
    return OrderService(
        repository=repository,
        menu_item_repository=menu_repository,
        iiko_order_gateway=IikoOrderGateway(
            client=IikoApiClient(
                api_login=API_IIKO or "",
                base_url=IIKO_BASE_URL,
                timeout_seconds=IIKO_ORDER_TIMEOUT_SECONDS,
            ),
            organization_id=IIKO_ORGANIZATION_ID,
            terminal_group_id=TERMINAL_ID_GROUP,
            source_key=IIKO_ORDER_SOURCE_KEY,
            online_payment_type_id=IIKO_ONLINE_PAYMENT_TYPE_ID,
            online_payment_type_kind=IIKO_ONLINE_PAYMENT_TYPE_KIND,
        ),
    )


async def reset_for_manual_retry(repository: SqlAlchemyOrderRepository, order_id: int) -> None:
    await repository._session.execute(
        text(
            """
            UPDATE orders
            SET iiko_creation_status = 'Failed', updated_at = now()
            WHERE id = :order_id
              AND iiko_order_id IS NULL
            """
        ),
        {"order_id": order_id},
    )
    await repository._session.commit()


async def print_state(repository: SqlAlchemyOrderRepository, order_id: int, label: str) -> None:
    row = (
        await repository._session.execute(
            text(
                """
                SELECT
                    orders.id,
                    orders.iiko_order_id,
                    orders.iiko_correlation_id,
                    orders.iiko_creation_status,
                    jobs.id AS job_id,
                    jobs.status AS job_status,
                    jobs.attempts AS job_attempts,
                    jobs.error_message AS job_error
                FROM orders
                LEFT JOIN order_delivery_jobs AS jobs ON jobs.order_id = orders.id
                WHERE orders.id = :order_id
                """
            ),
            {"order_id": order_id},
        )
    ).mappings().one_or_none()
    if row is None:
        print(f"{label}: order {order_id} not found")
        return
    print(
        f"{label}: order_id={row['id']} "
        f"iiko_order_id={row['iiko_order_id'] or '-'} "
        f"iiko_status={row['iiko_creation_status'] or '-'} "
        f"job_id={row['job_id'] or '-'} "
        f"job_status={row['job_status'] or '-'} "
        f"job_attempts={row['job_attempts'] or 0} "
        f"job_error={(row['job_error'] or '-')[:300]}"
    )


async def main() -> int:
    args = parse_args()

    async with AsyncSessionLocal() as session:
        repository = SqlAlchemyOrderRepository(session)
        service = build_order_service(repository, SqlAlchemyMenuItemRepository(session))

        order = await repository.get_by_id(args.order_id)
        if order is None:
            print(f"Order {args.order_id} was not found.")
            return 1
        if order.iiko_order_id:
            print(f"Order {args.order_id} is already in iiko: {order.iiko_order_id}")
            await print_state(repository, args.order_id, "current")
            return 0

        await print_state(repository, args.order_id, "before")

        if order.iiko_creation_status not in {"LocalPending", "Failed"}:
            if not args.force:
                print(
                    "Order is not LocalPending/Failed. "
                    "Use --force only after checking that this order is not already in the iiko terminal."
                )
                return 2
            await reset_for_manual_retry(repository, args.order_id)

        await service.enqueue_iiko_submission_if_needed(order_id=args.order_id)
        await print_state(repository, args.order_id, "enqueued")

        if args.enqueue_only:
            print("Job was enqueued. Background worker will send it.")
            return 0

        result = await service.retry_pending_iiko_submissions(limit=10)
        print(
            "worker result: "
            f"enqueued={result.enqueued} checked={result.checked} "
            f"submitted={result.submitted} failed={result.failed}"
        )
        await print_state(repository, args.order_id, "after")
        return 0 if result.failed == 0 else 3


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
