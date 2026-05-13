from __future__ import annotations

import re

from sqlalchemy import bindparam, text

from config import ADMIN_PHONES
from db import engine


def _normalize_admin_phone(phone: str) -> str | None:
    digits = re.sub(r"\D+", "", phone)
    if len(digits) == 11 and digits.startswith("8"):
        digits = f"7{digits[1:]}"
    if len(digits) != 11 or not digits.startswith("7"):
        return None
    return f"+{digits}"


def get_admin_phones() -> set[str]:
    return {
        normalized
        for phone in ADMIN_PHONES
        if (normalized := _normalize_admin_phone(phone))
    }


def is_admin_phone(phone: str) -> bool:
    return _normalize_admin_phone(phone) in get_admin_phones()


async def ensure_user_auth_columns() -> None:
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)",
        """
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token VARCHAR(6) NOT NULL UNIQUE,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            used BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_user_id ON password_reset_tokens (user_id)",
        "CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_token ON password_reset_tokens (token)",
        "CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_expires_at ON password_reset_tokens (expires_at)",
        "CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_used ON password_reset_tokens (used)",
    ]

    async with engine.begin() as conn:
        for statement in statements:
            await conn.execute(text(statement))


async def sync_admin_users_from_env() -> None:
    admin_phones = sorted(get_admin_phones())
    if not admin_phones:
        return

    async with engine.begin() as conn:
        await conn.execute(text("UPDATE users SET is_admin = FALSE"))
        await conn.execute(
            text("UPDATE users SET is_admin = TRUE WHERE phone IN :admin_phones").bindparams(
                bindparam("admin_phones", expanding=True),
            ),
            {"admin_phones": admin_phones},
        )
