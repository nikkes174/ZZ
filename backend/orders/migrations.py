from __future__ import annotations

from sqlalchemy import text

from db import engine


async def ensure_order_bonus_columns() -> None:
    statements = [
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS subtotal_amount INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS bonus_spent INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS iiko_order_id VARCHAR(64)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS iiko_correlation_id VARCHAR(64)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS iiko_creation_status VARCHAR(32)",
        "UPDATE orders SET status = 'Готовится' WHERE status = 'Подтвержден'",
    ]

    async with engine.begin() as conn:
        for statement in statements:
            await conn.execute(text(statement))
