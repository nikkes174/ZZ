from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def _get_csv(name: str) -> list[str]:
    return [
        item.strip()
        for item in os.getenv(name, "").split(",")
        if item.strip()
    ]


DB_URL = os.getenv("DB_URL")
DB_POOL_SIZE = _get_int("DB_POOL_SIZE", 5)
DB_MAX_OVERFLOW = _get_int("DB_MAX_OVERFLOW", 10)
DB_POOL_TIMEOUT = _get_int("DB_POOL_TIMEOUT", 15)
DB_STATEMENT_TIMEOUT_MS = _get_int("DB_STATEMENT_TIMEOUT_MS", 5000)
REDACTOR_PAGE_LIMIT = _get_int("REDACTOR_PAGE_LIMIT", 50)
API_IIKO = os.getenv('API_IIKO')
TERMINAL_ID_GROUP = os.getenv('TERMINAL_ID_GROUP')
IIKO_BASE_URL = os.getenv("IIKO_BASE_URL", "https://api-ru.iiko.services/api/1")
IIKO_ORGANIZATION_ID = os.getenv("IIKO_ORGANIZATION_ID")
IIKO_SYNC_TIMEOUT_SECONDS = _get_int("IIKO_SYNC_TIMEOUT_SECONDS", 20)
IIKO_SYNC_INTERVAL_SECONDS = _get_int("IIKO_SYNC_INTERVAL_SECONDS", 300)
IIKO_ORDER_TIMEOUT_SECONDS = _get_int("IIKO_ORDER_TIMEOUT_SECONDS", 60)
IIKO_ORDER_SOURCE_KEY = os.getenv("IIKO_ORDER_SOURCE_KEY", "zamzam-site")
IIKO_ORDER_STATUS_SYNC_INTERVAL_SECONDS = _get_int("IIKO_ORDER_STATUS_SYNC_INTERVAL_SECONDS", 30)
IIKO_ORDER_STATUS_SYNC_LIMIT = _get_int("IIKO_ORDER_STATUS_SYNC_LIMIT", 50)
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://127.0.0.1:8011")
PAYMENT_TEST_AMOUNT = _get_int("PAYMENT_TEST_AMOUNT", 1)
ADMIN_PHONES = _get_csv("ADMIN_PHONES")
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_TTL_MINUTES = _get_int("JWT_ACCESS_TOKEN_TTL_MINUTES", 30)
JWT_REFRESH_TOKEN_TTL_MINUTES = _get_int("JWT_REFRESH_TOKEN_TTL_MINUTES", 60 * 24 * 30)
