from __future__ import annotations

from sqlalchemy import text

from config import TERMINAL_ID_GROUP_MALYSHAVA
from db import engine


async def ensure_order_bonus_columns() -> None:
    if not TERMINAL_ID_GROUP_MALYSHAVA:
        raise RuntimeError("TERMINAL_ID_GROUP_MALYSHAVA is required for orders branch migration.")

    statements = [
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS subtotal_amount INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS bonus_spent INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(128)",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_orders_idempotency_key ON orders (idempotency_key) WHERE idempotency_key IS NOT NULL",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS iiko_order_id VARCHAR(64)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS iiko_correlation_id VARCHAR(64)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS iiko_creation_status VARCHAR(32)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_street VARCHAR(255)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_house VARCHAR(64)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_flat VARCHAR(64)",
        """
        CREATE TABLE IF NOT EXISTS order_delivery_jobs (
            id SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
            job_type VARCHAR(32) NOT NULL DEFAULT 'send_to_iiko',
            status VARCHAR(32) NOT NULL DEFAULT 'pending',
            attempts INTEGER NOT NULL DEFAULT 0,
            next_run_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            locked_at TIMESTAMPTZ,
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_order_delivery_jobs_order_id ON order_delivery_jobs (order_id)",
        "CREATE INDEX IF NOT EXISTS ix_order_delivery_jobs_status_next_run_at ON order_delivery_jobs (status, next_run_at)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS branch_code VARCHAR(32)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS iiko_terminal_group_id VARCHAR(64)",
        "UPDATE orders SET branch_code = 'malyshava' WHERE branch_code IS NULL",
        """
        UPDATE orders
        SET iiko_terminal_group_id = :malyshava_terminal_group_id
        WHERE iiko_terminal_group_id IS NULL
        """,
        "ALTER TABLE orders ALTER COLUMN branch_code SET NOT NULL",
        "ALTER TABLE orders ALTER COLUMN iiko_terminal_group_id SET NOT NULL",
        "CREATE INDEX IF NOT EXISTS ix_orders_branch_code ON orders (branch_code)",
        "CREATE INDEX IF NOT EXISTS ix_orders_iiko_terminal_group_id ON orders (iiko_terminal_group_id)",
    ]

    params = {"malyshava_terminal_group_id": TERMINAL_ID_GROUP_MALYSHAVA}
    async with engine.begin() as conn:
        for statement in statements:
            await conn.execute(text(statement), params)
