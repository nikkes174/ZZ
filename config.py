from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


DB_URL = os.getenv("DB_URL")
DB_POOL_SIZE = _get_int("DB_POOL_SIZE", 5)
DB_MAX_OVERFLOW = _get_int("DB_MAX_OVERFLOW", 10)
DB_POOL_TIMEOUT = _get_int("DB_POOL_TIMEOUT", 15)
DB_STATEMENT_TIMEOUT_MS = _get_int("DB_STATEMENT_TIMEOUT_MS", 5000)
REDACTOR_PAGE_LIMIT = _get_int("REDACTOR_PAGE_LIMIT", 50)
