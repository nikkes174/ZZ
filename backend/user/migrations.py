from __future__ import annotations

from sqlalchemy import text

from db import engine


async def ensure_user_auth_columns() -> None:
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)",
    ]

    async with engine.begin() as conn:
        for statement in statements:
            await conn.execute(text(statement))
