from __future__ import annotations

from sqlalchemy import text

from db import engine


async def ensure_order_bonus_columns() -> None:
    statements = [
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS subtotal_amount INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS bonus_spent INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(128)",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_orders_idempotency_key ON orders (idempotency_key) WHERE idempotency_key IS NOT NULL",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS iiko_order_id VARCHAR(64)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS iiko_correlation_id VARCHAR(64)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS iiko_creation_status VARCHAR(32)",
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
        "UPDATE orders SET status = 'Готовится' WHERE status = 'Подтвержден'",
    ]

    async with engine.begin() as conn:
        for statement in statements:
            await conn.execute(text(statement))
