from __future__ import annotations

from sqlalchemy import text

from db import engine


async def ensure_order_bonus_columns() -> None:
    statements = [
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS subtotal_amount INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS bonus_spent INTEGER NOT NULL DEFAULT 0",
    ]

    async with engine.begin() as conn:
        for statement in statements:
            await conn.execute(text(statement))
