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
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE",
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
