# ��I Code Bundle

## 📌 Параметры
- **Files:** `['']`
- **Dirs:** `['']`
- **Extensions:** `['.css', '.html', '.js', '.json', '.py']`

---


> ❌ **Файл не найден:** `C:\Users\pride\Desktop\python\zamzam`


# 📂 Директория: `C:\Users\pride\Desktop\python\zamzam`

## 📁 `.`

## 📄 `app_logging.py`

```python
from __future__ import annotations

import logging
from pathlib import Path


_configured = False


def configure_application_logging(level: int = logging.INFO) -> None:
    global _configured
    if _configured:
        return

    logs_dir = Path("files") / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "app.log"
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    root_logger.handlers.clear()
    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)
    _configured = True

```

## 📄 `config.py`

```python
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


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


DB_URL = os.getenv("DB_URL")
DB_POOL_SIZE = _get_int("DB_POOL_SIZE", 5)
DB_MAX_OVERFLOW = _get_int("DB_MAX_OVERFLOW", 10)
DB_POOL_TIMEOUT = _get_int("DB_POOL_TIMEOUT", 15)
DB_STATEMENT_TIMEOUT_MS = _get_int("DB_STATEMENT_TIMEOUT_MS", 5000)

REDACTOR_PAGE_LIMIT = _get_int("REDACTOR_PAGE_LIMIT", 50)
API_IIKO = os.getenv('API_IIKO')
TERMINAL_ID_GROUP_MALYSHAVA = os.getenv('TERMINAL_ID_GROUP_MALYSHAVA')
TERMINAL_ID_GROUP_SUH = os.getenv('TERMINAL_ID_GROUP_SUH')

IIKO_BASE_URL = os.getenv("IIKO_BASE_URL", "https://api-ru.iiko.services/api/1")
IIKO_ORGANIZATION_ID = os.getenv("IIKO_ORGANIZATION_ID")
IIKO_SYNC_TIMEOUT_SECONDS = _get_int("IIKO_SYNC_TIMEOUT_SECONDS", 20)
IIKO_SYNC_INTERVAL_SECONDS = _get_int("IIKO_SYNC_INTERVAL_SECONDS", 300)
IIKO_ORDER_TIMEOUT_SECONDS = _get_int("IIKO_ORDER_TIMEOUT_SECONDS", 60)
IIKO_ORDER_SOURCE_KEY = os.getenv("IIKO_ORDER_SOURCE_KEY", "zamzam-site")
IIKO_ONLINE_PAYMENT_TYPE_ID = os.getenv("IIKO_ONLINE_PAYMENT_TYPE_ID")
IIKO_ONLINE_PAYMENT_TYPE_KIND = os.getenv("IIKO_ONLINE_PAYMENT_TYPE_KIND", "Card")
IIKO_ORDER_STATUS_SYNC_INTERVAL_SECONDS = _get_int("IIKO_ORDER_STATUS_SYNC_INTERVAL_SECONDS", 30)
IIKO_ORDER_STATUS_SYNC_LIMIT = _get_int("IIKO_ORDER_STATUS_SYNC_LIMIT", 50)
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
YOOKASSA_VAT_CODE = _get_int("YOOKASSA_VAT_CODE", 1)
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://127.0.0.1:8011")
ADMIN_PHONES = _get_csv("ADMIN_PHONES")
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_TTL_MINUTES = _get_int("JWT_ACCESS_TOKEN_TTL_MINUTES", 30)
JWT_REFRESH_TOKEN_TTL_MINUTES = _get_int("JWT_REFRESH_TOKEN_TTL_MINUTES", 60 * 24 * 30)
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_PORT = _get_int("SMTP_PORT", 465)
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER).strip()
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.mail.ru").strip()
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "false").strip().lower() not in {"0", "false", "no", "off"}
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "true").strip().lower() in {"1", "true", "yes", "on"}
SMTP_TIMEOUT_SECONDS = _get_int("SMTP_TIMEOUT_SECONDS", 20)
SMTP_FORCE_IPV4 = os.getenv("SMTP_FORCE_IPV4", "true").strip().lower() not in {"0", "false", "no", "off"}

```

## 📄 `db.py`

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from config import (
    DB_MAX_OVERFLOW,
    DB_POOL_SIZE,
    DB_POOL_TIMEOUT,
    DB_STATEMENT_TIMEOUT_MS,
    DB_URL,
)

if not DB_URL:
    raise ValueError("DB_URL is not set")

engine = create_async_engine(
    DB_URL,
    echo=False,
    pool_pre_ping=True,
    future=True,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    connect_args={
        "ssl": False,
        "command_timeout": max(1, DB_STATEMENT_TIMEOUT_MS // 1000),
        "server_settings": {
            "statement_timeout": str(DB_STATEMENT_TIMEOUT_MS),
        },
    },
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

```

## 📄 `get_project_front.py`

```python

import argparse
import os
from typing import Set, List

# ✅ Расширения файлов
EXTENSIONS: Set[str] = {".py", ".json", ".html", ".css", ".js"}

# ✅ Игнорируемые директории
IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "__pycache__",
    ".idea",
    "env",
    "venv",
    "node_modules",
    "site-packages",
    "hooks",
    "logs",
    "refs",
    "pack",
}

DEFAULT_FILES: List[str] = [
''
]

DEFAULT_DIRS: List[str] = [
''
                           ]


EXTENSION_TO_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".json": "json",
    ".html": "html",
    ".css": "css",
}


def read_file_safe(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(path, encoding="latin-1") as f:
                return f.read()
        except Exception as e:
            return f"[Ошибка чтения (кодировка): {e}]"
    except Exception as e:
        return f"[Ошибка чтения файла: {e}]"


def should_take_file(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in EXTENSIONS


def get_lang(filename: str) -> str:
    return EXTENSION_TO_LANG.get(os.path.splitext(filename)[1].lower(), "")


def write_one_file_md(path: str, out, base_dir: str):
    abs_path = os.path.abspath(path)
    if not os.path.isfile(abs_path):
        out.write(f"\n> ❌ **Файл не найден:** `{abs_path}`\n\n")
        return

    rel_path = os.path.relpath(abs_path, base_dir) if base_dir else path
    lang = get_lang(path)

    out.write(f"\n## 📄 `{rel_path}`\n\n")
    out.write(f"```{lang}\n")
    out.write(read_file_safe(abs_path))
    out.write("\n```\n")


def collect_directory_md(root_dir: str, out):
    root_dir = os.path.abspath(root_dir)

    if not os.path.exists(root_dir):
        out.write(f"\n> ❌ **Папка не найдена:** `{root_dir}`\n\n")
        return

    out.write(f"\n# 📂 Директория: `{root_dir}`\n")

    for current_root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES]
        rel_root = os.path.relpath(current_root, root_dir)

        out.write(f"\n## 📁 `{rel_root}`\n")

        for filename in sorted(files):
            if should_take_file(filename):
                full_path = os.path.join(current_root, filename)
                write_one_file_md(full_path, out, root_dir)


def parse_args():
    p = argparse.ArgumentParser(
        description="Собрать файлы и директории в AI-friendly Markdown."
    )

    p.add_argument("--files", "-f", nargs="*", default=DEFAULT_FILES)
    p.add_argument("--dirs", "-d", nargs="*", default=DEFAULT_DIRS)
    p.add_argument("--out", "-o", default="combined_output.md")

    return p.parse_args()


def main():
    args = parse_args()

    with open(args.out, "w", encoding="utf-8") as out:
        out.write("# ��I Code Bundle\n\n")
        out.write("## 📌 Параметры\n")
        out.write(f"- **Files:** `{args.files}`\n")
        out.write(f"- **Dirs:** `{args.dirs}`\n")
        out.write(f"- **Extensions:** `{sorted(EXTENSIONS)}`\n")

        out.write("\n---\n\n")

        for fpath in args.files:
            write_one_file_md(fpath, out, None)

        for dpath in args.dirs:
            collect_directory_md(dpath, out)

    print(f"✅ Готово. Markdown файл: {args.out}")


if __name__ == "__main__":
    main()

```

## 📄 `main.py`

```python
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

from app_logging import configure_application_logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.auth import router as auth_router
from backend.orders import router as orders_router
from backend.orders.crud import SqlAlchemyOrderRepository
from backend.orders.iiko import IikoOrderGateway
from backend.orders.migrations import ensure_order_bonus_columns
from backend.orders.service import IikoOrderStatusSyncService, OrderService
from backend.payment.crud import SqlAlchemyPendingPaymentRepository
from backend.payment.router import _finalize_succeeded_payment, router as payment_router
from backend.payment.service import YooKassaPaymentService
from backend.iiko_manager.client import IikoApiClient
from backend.iiko_manager.repository import IikoCatalogRepository
from backend.iiko_manager.service import IikoCatalogSyncService
from backend.redactor import router as redactor_router
from backend.redactor.router import load_hero_content, load_menu_categories
from backend.redactor.crud import SqlAlchemyMenuItemRepository
from backend.redactor.migrations import ensure_menu_item_iiko_columns
from backend.redactor.service import MenuItemService
from backend.user import router as user_router
from backend.user.crud import SqlAlchemyUserRepository
from backend.user.migrations import ensure_user_auth_columns, sync_admin_users_from_env
from backend.user.service import UserService
from config import (
    API_IIKO,
    IIKO_BASE_URL,
    IIKO_ONLINE_PAYMENT_TYPE_ID,
    IIKO_ONLINE_PAYMENT_TYPE_KIND,
    IIKO_ORDER_SOURCE_KEY,
    IIKO_ORGANIZATION_ID,
    IIKO_ORDER_STATUS_SYNC_INTERVAL_SECONDS,
    IIKO_ORDER_STATUS_SYNC_LIMIT,
    IIKO_ORDER_TIMEOUT_SECONDS,
    IIKO_SYNC_INTERVAL_SECONDS,
    IIKO_SYNC_TIMEOUT_SECONDS,
    TERMINAL_ID_GROUP_MALYSHAVA,
    YOOKASSA_SECRET_KEY,
    YOOKASSA_SHOP_ID,
)
from db import AsyncSessionLocal, init_db


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
configure_application_logging()
logger = logging.getLogger(__name__)
OFERTA_TEXT_PATH = BASE_DIR / "files" / "legal" / "oferta.txt"
POLICY_TEXT_PATH = BASE_DIR / "files" / "legal" / "politic.txt"
PAYMENT_RECONCILE_CREATED_AFTER: datetime | None = None


MENU_ITEMS = [
    {
        "title": "  Zamzam",
        "description": " , ,       .",
        "price": 1290,
        "category": "signature",
        "badge": " ",
        "accent": "#d9a35f",
        "sort_order": 10,
    },
    {
        "title": "Ѹ  ",
        "description": " ,  ,     .",
        "price": 1180,
        "category": "seafood",
        "badge": " ",
        "accent": "#5ab6a6",
        "sort_order": 20,
    },
    {
        "title": "   ",
        "description": " ,     .",
        "price": 910,
        "category": "signature",
        "badge": " comfort",
        "accent": "#b98d62",
        "sort_order": 30,
    },
    {
        "title": "   ",
        "description": "  , , , ,    .",
        "price": 860,
        "category": "bowls",
        "badge": "˸ ",
        "accent": "#6da4ff",
        "sort_order": 40,
    },
    {
        "title": " Black Angus",
        "description": ",  dry-aged, ,    BBQ.",
        "price": 970,
        "category": "grill",
        "badge": " ",
        "accent": "#ef7b5c",
        "sort_order": 50,
    },
    {
        "title": "  ",
        "description": " , ,      .",
        "price": 540,
        "category": "dessert",
        "badge": " ",
        "accent": "#9ccf7f",
        "sort_order": 60,
    },
]

FEATURES = [
    "Доставка за 35 минут по городу",
    "Сборка заказа в термобоксах",
    "Премиальная упаковка для красивой подачи",
]

STEPS = [
    {
        "title": "Выберите блюда",
        "text": "Удобный каталог с быстрыми фильтрами и понятной карточкой состава.",
    },
    {
        "title": "Соберите заказ",
        "text": "Корзина обновляется мгновенно, а итоговая стоимость всегда перед глазами.",
    },
    {
        "title": "Получите доставку",
        "text": "Курьер привозит заказ горячим, аккуратно упакованным и точно ко времени.",
    },
]

REVIEWS = [
    {
        "author": "Алина, Сити",
        "text": "По уровню подачи это ресторанный вечер, только дома. Привезли быстро, всё выглядело безупречно.",
    },
    {
        "author": "Игорь, Парк",
        "text": "Интерфейс понятный, заказ собрал за минуту. Бургер и сёмга действительно на премиальном уровне.",
    },
    {
        "author": "Мария, Центр",
        "text": "Очень удобный каталог и сильный визуал. Чувствуется сервис, а не просто доставка еды.",
    },
]
async def _load_menu_items() -> list[dict[str, object]]:
    async with AsyncSessionLocal() as session:
        service = MenuItemService(repository=SqlAlchemyMenuItemRepository(session))
        items = await service.list_storefront_items()
        logger.info("Loaded %s active iiko menu items for storefront.", len(items))
        if not items:
            logger.warning("Storefront has zero active iiko menu items.")
        return [item.model_dump(mode="json") for item in items]


async def _sync_iiko_catalog() -> None:
    logger.info("Starting iiko catalog sync.")
    if not API_IIKO:
        raise RuntimeError("API_IIKO is required because iiko is the only source of truth for catalog data.")
    if not TERMINAL_ID_GROUP_MALYSHAVA:
        raise RuntimeError("TERMINAL_ID_GROUP is required because iiko is the only source of truth for catalog data.")

    async with AsyncSessionLocal() as session:
        service = IikoCatalogSyncService(
            client=IikoApiClient(
                api_login=API_IIKO,
                base_url=IIKO_BASE_URL,
                timeout_seconds=IIKO_SYNC_TIMEOUT_SECONDS,
            ),
            repository=IikoCatalogRepository(session),
            terminal_group_id=TERMINAL_ID_GROUP_MALYSHAVA,
            organization_id=IIKO_ORGANIZATION_ID,
        )
        result = await service.sync()
        logger.info(
            "Finished iiko catalog sync. created=%s updated=%s deactivated=%s",
            result.created,
            result.updated,
            result.deactivated,
        )


async def _run_iiko_sync_loop(stop_event: asyncio.Event) -> None:
    logger.info("Started background iiko sync loop. interval_seconds=%s", IIKO_SYNC_INTERVAL_SECONDS)
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=IIKO_SYNC_INTERVAL_SECONDS)
            break
        except asyncio.TimeoutError:
            pass

        try:
            logger.info("Running scheduled iiko catalog sync.")
            await _sync_iiko_catalog()
        except Exception:
            logger.exception("Background iiko catalog sync failed.")


async def _sync_iiko_order_statuses() -> None:
    if not API_IIKO:
        logger.info("Skipping iiko order status sync because API_IIKO is not configured.")
        return

    async with AsyncSessionLocal() as session:
        service = IikoOrderStatusSyncService(
            repository=SqlAlchemyOrderRepository(session),
            client=IikoApiClient(
                api_login=API_IIKO,
                base_url=IIKO_BASE_URL,
                timeout_seconds=IIKO_ORDER_TIMEOUT_SECONDS,
            ),
            organization_id=IIKO_ORGANIZATION_ID,
            limit=IIKO_ORDER_STATUS_SYNC_LIMIT,
        )
        result = await service.sync()
        if result.checked or result.updated:
            logger.info(
                "Finished iiko order status sync. checked=%s updated=%s",
                result.checked,
                result.updated,
            )


async def _retry_pending_iiko_order_submissions() -> None:
    if not API_IIKO:
        logger.info("Skipping iiko order submission retry because API_IIKO is not configured.")
        return
    if PAYMENT_RECONCILE_CREATED_AFTER is None:
        logger.info("Skipping iiko order submission retry because cutoff is not initialized.")
        return

    async with AsyncSessionLocal() as session:
        service = OrderService(
            repository=SqlAlchemyOrderRepository(session),
            menu_item_repository=SqlAlchemyMenuItemRepository(session),
            iiko_order_gateway=IikoOrderGateway(
                client=IikoApiClient(
                    api_login=API_IIKO,
                    base_url=IIKO_BASE_URL,
                    timeout_seconds=IIKO_ORDER_TIMEOUT_SECONDS,
                ),
                organization_id=IIKO_ORGANIZATION_ID,
                source_key=IIKO_ORDER_SOURCE_KEY,
                online_payment_type_id=IIKO_ONLINE_PAYMENT_TYPE_ID,
                online_payment_type_kind=IIKO_ONLINE_PAYMENT_TYPE_KIND,
            ),
        )
        result = await service.retry_pending_iiko_submissions(
            limit=IIKO_ORDER_STATUS_SYNC_LIMIT,
            created_after=PAYMENT_RECONCILE_CREATED_AFTER,
        )
        if result.enqueued or result.checked or result.submitted or result.failed:
            logger.info(
                "Finished iiko order submission retry. enqueued=%s checked=%s submitted=%s failed=%s",
                result.enqueued,
                result.checked,
                result.submitted,
                result.failed,
            )


async def _ensure_payment_reconcile_cutoff() -> datetime:
    created_after = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        await session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS app_runtime_settings (
                    key VARCHAR(128) PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        )
        await session.execute(
            text(
                """
                INSERT INTO app_runtime_settings (key, value)
                VALUES ('payment_reconcile_created_after', :value)
                ON CONFLICT (key) DO NOTHING
                """
            ),
            {"value": created_after.isoformat()},
        )
        result = await session.execute(
            text("SELECT value FROM app_runtime_settings WHERE key = 'payment_reconcile_created_after'")
        )
        value = result.scalar_one()
        await session.commit()

    return datetime.fromisoformat(str(value))


async def _reconcile_unfinished_yookassa_payments() -> None:
    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        logger.info("Skipping YooKassa payment reconciliation because credentials are not configured.")
        return
    if PAYMENT_RECONCILE_CREATED_AFTER is None:
        logger.info("Skipping YooKassa payment reconciliation because cutoff is not initialized.")
        return

    async with AsyncSessionLocal() as session:
        pending_payment_repository = SqlAlchemyPendingPaymentRepository(session)
        payments = await pending_payment_repository.list_unfinished_yookassa_payments(
            limit=IIKO_ORDER_STATUS_SYNC_LIMIT,
            created_after=PAYMENT_RECONCILE_CREATED_AFTER,
        )
        if not payments:
            return

        order_service = OrderService(
            repository=SqlAlchemyOrderRepository(session),
            menu_item_repository=SqlAlchemyMenuItemRepository(session),
            iiko_order_gateway=IikoOrderGateway(
                client=IikoApiClient(
                    api_login=API_IIKO or "",
                    base_url=IIKO_BASE_URL,
                    timeout_seconds=IIKO_ORDER_TIMEOUT_SECONDS,
                ),
                organization_id=IIKO_ORGANIZATION_ID,
                source_key=IIKO_ORDER_SOURCE_KEY,
                online_payment_type_id=IIKO_ONLINE_PAYMENT_TYPE_ID,
                online_payment_type_kind=IIKO_ONLINE_PAYMENT_TYPE_KIND,
            ),
        )
        payment_service = YooKassaPaymentService(repository=pending_payment_repository)
        user_service = UserService(repository=SqlAlchemyUserRepository(session))

        reconciled = 0
        for payment in payments:
            if not payment.yookassa_payment_id:
                continue
            try:
                result = await _finalize_succeeded_payment(
                    payment_id=payment.yookassa_payment_id,
                    payment_service=payment_service,
                    pending_payment_repository=pending_payment_repository,
                    order_service=order_service,
                    user_service=user_service,
                )
            except Exception:
                logger.exception(
                    "Could not reconcile unfinished YooKassa payment. pending_payment_id=%s payment_id=%s",
                    payment.id,
                    payment.yookassa_payment_id,
                )
                continue
            if result.get("order_id"):
                reconciled += 1

        if reconciled:
            logger.info("Finished YooKassa payment reconciliation. checked=%s reconciled=%s", len(payments), reconciled)


async def _run_iiko_order_status_sync_loop(stop_event: asyncio.Event) -> None:
    logger.info(
        "Started background iiko order status sync loop. interval_seconds=%s",
        IIKO_ORDER_STATUS_SYNC_INTERVAL_SECONDS,
    )
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=IIKO_ORDER_STATUS_SYNC_INTERVAL_SECONDS)
            break
        except asyncio.TimeoutError:
            pass

        try:
            await _sync_iiko_order_statuses()
        except Exception:
            logger.exception("Background iiko order status sync failed.")


async def _run_iiko_order_submission_retry_loop(stop_event: asyncio.Event) -> None:
    logger.info(
        "Started background iiko order submission retry loop. interval_seconds=%s",
        IIKO_ORDER_STATUS_SYNC_INTERVAL_SECONDS,
    )
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=IIKO_ORDER_STATUS_SYNC_INTERVAL_SECONDS)
            break
        except asyncio.TimeoutError:
            pass

        try:
            await _reconcile_unfinished_yookassa_payments()
            await _retry_pending_iiko_order_submissions()
        except Exception:
            logger.exception("Background iiko order submission retry failed.")


@asynccontextmanager
async def lifespan(_: FastAPI):
    global PAYMENT_RECONCILE_CREATED_AFTER
    logger.info("Application startup initiated.")
    await init_db()
    logger.info("Database metadata initialized.")
    await ensure_order_bonus_columns()
    logger.info("Order migrations ensured.")
    await ensure_menu_item_iiko_columns()
    logger.info("Menu item iiko migrations ensured.")
    await ensure_user_auth_columns()
    logger.info("User auth migrations ensured.")
    await sync_admin_users_from_env()
    logger.info("Admin users synchronized from environment.")
    PAYMENT_RECONCILE_CREATED_AFTER = await _ensure_payment_reconcile_cutoff()
    logger.info("YooKassa payment reconciliation cutoff initialized. created_after=%s", PAYMENT_RECONCILE_CREATED_AFTER.isoformat())
    await _sync_iiko_catalog()
    stop_event = asyncio.Event()
    sync_task = asyncio.create_task(_run_iiko_sync_loop(stop_event))
    order_status_sync_task = asyncio.create_task(_run_iiko_order_status_sync_loop(stop_event))
    order_submission_retry_task = asyncio.create_task(_run_iiko_order_submission_retry_loop(stop_event))
    try:
        logger.info("Application startup completed.")
        yield
    finally:
        logger.info("Application shutdown initiated.")
        stop_event.set()
        for task in (sync_task, order_status_sync_task, order_submission_retry_task):
            task.cancel()
        await asyncio.gather(sync_task, order_status_sync_task, order_submission_retry_task, return_exceptions=True)
        logger.info("Application shutdown completed.")


app = FastAPI(
    title="Zamzam",
    description="   ",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/files", StaticFiles(directory="files"), name="files")
app.include_router(redactor_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(orders_router)
app.include_router(payment_router)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    body = await request.body()
    errors = exc.errors()
    logger.warning(
        "Request validation failed. method=%s path=%s errors=%s body=%s",
        request.method,
        request.url.path,
        errors,
        body.decode("utf-8", errors="replace")[:2000],
    )
    if request.url.path == "/api/orders":
        for error in errors:
            location = error.get("loc") or ()
            if "customer_phone" in location:
                return JSONResponse(status_code=422, content={"detail": "Заполните имя и телефон."})
        return JSONResponse(status_code=422, content={"detail": "Проверьте данные заказа."})
    return JSONResponse(status_code=422, content={"detail": errors})


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "hero_content": load_hero_content(),
            "menu_categories": load_menu_categories().items,
            "menu_items": await _load_menu_items(),
            "features": FEATURES,
            "steps": STEPS,
            "reviews": REVIEWS,
        },
    )


@app.get("/oferta", response_class=HTMLResponse)
async def oferta_page(request: Request) -> HTMLResponse:
    oferta_text = OFERTA_TEXT_PATH.read_text(encoding="utf-8")
    return templates.TemplateResponse(
        request,
        "oferta.html",
        {
            "oferta_text": oferta_text,
        },
    )


@app.get("/policy", response_class=HTMLResponse)
async def policy_page(request: Request) -> HTMLResponse:
    policy_text = POLICY_TEXT_PATH.read_text(encoding="utf-8")
    return templates.TemplateResponse(
        request,
        "policy.html",
        {
            "policy_text": policy_text,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8053)

```

## 📁 `.agents`

## 📁 `.codex`

## 📁 `.codex\agents`

## 📁 `auth_recovery_example`

## 📄 `auth_recovery_example\__init__.py`

```python

```

## 📄 `auth_recovery_example\email_sender.py`

```python
from abc import ABC, abstractmethod
from email.message import EmailMessage

import aiosmtplib


class EmailSender(ABC):
    @abstractmethod
    async def send(self, email: str, text: str): ...


class EmailDeliveryError(Exception):
    pass


class SMTPEmailSender(EmailSender):
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        *,
        use_tls: bool = True,
    ) -> None:

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.use_tls = use_tls

    async def send(self, email: str, text: str) -> None:
        msg = EmailMessage()
        msg["From"] = self.from_email
        msg["To"] = email
        msg["Subject"] = "Восстановление пароля"
        msg.set_content(text)

        try:
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                start_tls=self.use_tls,
                timeout=10,
            )
        except (aiosmtplib.SMTPException, TimeoutError, OSError) as e:
            raise EmailDeliveryError("Не удалось отправить письмо") from e

```

## 📄 `auth_recovery_example\passwords.py`

```python
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

pwd = CryptContext(schemes=["argon2"], deprecated="auto")


class PasswordHasher:
    @staticmethod
    def hash(password: str) -> str:
        return pwd.hash(password)

    @staticmethod
    def verify(password: str, hashed: str) -> bool:
        try:
            return pwd.verify(password, hashed)
        except (UnknownHashError, ValueError, TypeError):
            return False

```

## 📄 `auth_recovery_example\recovery_service.py`

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth_recovery.email_sender import SMTPEmailSender
from backend.auth_recovery.passwords import PasswordHasher
from backend.auth_recovery.reset_tokens_repo import ResetTokenRepository
from backend.User.models import UserModel


class PasswordRecoveryService:
    def __init__(
        self,
        session: AsyncSession,
        token_repo: ResetTokenRepository,
        email_sender: SMTPEmailSender,
    ):
        self.session = session
        self.token_repo = token_repo
        self.email_sender = email_sender

    async def request_recovery(self, email: str) -> bool:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        user = result.scalars().first()

        if not user:
            return True

        token = await self.token_repo.create(user.id)

        text = (
            "Восстановление пароля\n\n"
            f"Код восстановления:\n{token}\n\n"
            "Срок действия: 10 минут"
        )

        await self.email_sender.send(user.email, text)
        return True

    async def confirm_recovery(self, token: str, new_password: str) -> bool:
        user_id = await self.token_repo.consume(token)
        if not user_id:
            return False

        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalars().first()

        if not user:
            return False

        user.password = PasswordHasher.hash(new_password)
        await self.session.commit()
        return True

```

## 📄 `auth_recovery_example\reset_tokens_repo.py`

```python
import datetime as dt
import secrets
import uuid
from abc import ABC, abstractmethod

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.User.models import PasswordResetTokenModel


class ResetTokenRepository(ABC):
    @abstractmethod
    async def create(self, user_id): ...

    @abstractmethod
    async def consume(self, token: str) -> uuid.UUID | None: ...


class DatabaseResetTokenRepo(ResetTokenRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id) -> str:
        token = secrets.token_urlsafe(32)
        expires_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
            minutes=10,
        )

        obj = PasswordResetTokenModel(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            used=False,
        )

        self.session.add(obj)
        await self.session.commit()
        return token

    async def consume(self, token: str) -> uuid.UUID | None:
        stmt = (
            update(PasswordResetTokenModel)
            .where(
                PasswordResetTokenModel.token == token,
                PasswordResetTokenModel.used.is_(False),
                PasswordResetTokenModel.expires_at
                > dt.datetime.now(dt.timezone.utc),
            )
            .values(used=True)
            .returning(PasswordResetTokenModel.user_id)
        )
        result = await self.session.execute(stmt)
        user_id = result.scalar_one_or_none()

        if not user_id:
            return None

        await self.session.commit()
        return user_id

```

## 📄 `auth_recovery_example\router.py`

```python
import logging

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from backend.auth_recovery.email_sender import EmailDeliveryError
from backend.auth_recovery.recovery_service import PasswordRecoveryService
from dependency import get_recovery_service

templates = Jinja2Templates(directory="backend/templates")
logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/recovery",
    tags=["Password recovery"],
)


@router.post("/restore", response_class=HTMLResponse)
async def restore_password(
    request: Request,
    email: str = Form(...),
    service: PasswordRecoveryService = Depends(get_recovery_service),
):
    try:
        await service.request_recovery(email)
    except EmailDeliveryError as e:
        logger.warning(
            "Не удалось отправить письмо для восстановления пароля: %s",
            type(e.__cause__).__name__ if e.__cause__ else type(e).__name__,
        )
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": (
                    "Не удалось отправить письмо. Выключите VPN или "
                    "проверьте подключение к интернету и попробуйте ещё раз."
                ),
                "open_restore": True,
            },
        )

    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "success": "Если email зарегистрирован, мы отправили код восстановления",
            "open_restore_confirm": True,
        },
    )


@router.post("/restore/confirm", response_class=HTMLResponse)
async def confirm_restore(
    request: Request,
    token: str = Form(..., min_length=1),
    password: str = Form(..., min_length=8),
    service: PasswordRecoveryService = Depends(get_recovery_service),
):
    ok = await service.confirm_recovery(token, password)

    if not ok:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Неверный или просроченный код восстановления",
            },
        )

    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "success": "Пароль успешно изменён",
        },
    )

```

## 📁 `backend`

## 📄 `backend\__init__.py`

```python

```

## 📄 `backend\rate_limit.py`

```python
from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._windows: dict[str, int] = {}
        self._lock = asyncio.Lock()
        self._last_cleanup = 0.0

    async def check(self, *, key: str, limit: int, window_seconds: int) -> None:
        now = time.monotonic()
        cutoff = now - window_seconds
        async with self._lock:
            if now - self._last_cleanup > 60:
                self._cleanup(now=now)
                self._last_cleanup = now
            self._windows[key] = max(window_seconds, self._windows.get(key, 0))
            hits = self._hits[key]
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= limit:
                retry_after = max(1, int(window_seconds - (now - hits[0])))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests.",
                    headers={"Retry-After": str(retry_after)},
                )
            hits.append(now)

    def _cleanup(self, *, now: float) -> None:
        empty_keys = []
        for key, hits in self._hits.items():
            cutoff = now - self._windows.get(key, 0)
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if not hits:
                empty_keys.append(key)
        for key in empty_keys:
            self._hits.pop(key, None)
            self._windows.pop(key, None)


rate_limiter = InMemoryRateLimiter()


def client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip() or "unknown"
    if request.client:
        return request.client.host
    return "unknown"

```

## 📁 `backend\auth`

## 📄 `backend\auth\__init__.py`

```python
from backend.auth.models import AuthRefreshSessionModel
from backend.auth.router import router

__all__ = ["AuthRefreshSessionModel", "router"]

```

## 📄 `backend\auth\dependencies.py`

```python
from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.auth.jwt_service import JWTError, JWTService
from backend.user.depencises import get_user_service
from backend.user.schemas import UserRead
from backend.user.service import UserNotFoundError, UserService


bearer_scheme = HTTPBearer(auto_error=False)
jwt_service = JWTService()


async def require_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token is required.")
    try:
        payload = jwt_service.decode_access_token(credentials.credentials)
        return await user_service.get_user_by_id(int(payload["user_id"]))
    except (JWTError, UserNotFoundError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token.") from exc


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    user_service: UserService = Depends(get_user_service),
) -> Optional[UserRead]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        payload = jwt_service.decode_access_token(credentials.credentials)
        return await user_service.get_user_by_id(int(payload["user_id"]))
    except (JWTError, UserNotFoundError, KeyError, TypeError, ValueError):
        return None


async def require_admin_user(
    user: UserRead = Depends(require_current_user),
) -> UserRead:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return user


def ensure_admin_user(user: Optional[UserRead]) -> UserRead:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token is required.")
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return user

```

## 📄 `backend\auth\email_sender.py`

```python
from __future__ import annotations

import asyncio
import socket
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol


class EmailDeliveryError(Exception):
    pass


class EmailSender(Protocol):
    async def send(self, *, email: str, subject: str, text: str) -> None: ...


def _create_ipv4_connection(
    host: str,
    port: int,
    timeout: int,
    source_address: tuple[str, int] | None = None,
) -> socket.socket:
    errors: list[OSError] = []
    for family, socket_type, proto, _, address in socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM):
        sock = socket.socket(family, socket_type, proto)
        sock.settimeout(timeout)
        try:
            if source_address:
                sock.bind(source_address)
            sock.connect(address)
            return sock
        except OSError as exc:
            errors.append(exc)
            sock.close()

    if errors:
        raise errors[-1]
    raise OSError(f"No IPv4 address found for {host}")


class IPv4SMTP(smtplib.SMTP):
    def _get_socket(self, host: str, port: int, timeout: int) -> socket.socket:
        return _create_ipv4_connection(host, port, timeout, self.source_address)


class IPv4SMTPSSL(smtplib.SMTP_SSL):
    def _get_socket(self, host: str, port: int, timeout: int) -> socket.socket:
        raw_socket = _create_ipv4_connection(host, port, timeout, self.source_address)
        return self.context.wrap_socket(raw_socket, server_hostname=host)


@dataclass
class SMTPEmailSender:
    host: str
    port: int
    username: str
    password: str
    from_email: str
    use_tls: bool = True
    use_ssl: bool = False
    timeout_seconds: int = 10
    force_ipv4: bool = True

    async def send(self, *, email: str, subject: str, text: str) -> None:
        if not self.host or not self.port or not self.username or not self.password or not self.from_email:
            raise EmailDeliveryError(
                "SMTP is not configured: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD and SMTP_FROM are required"
            )

        message = EmailMessage()
        message["From"] = self.from_email
        message["To"] = email
        message["Subject"] = subject
        message.set_content(text)

        try:
            await asyncio.to_thread(self._send_sync, message)
        except (smtplib.SMTPException, TimeoutError, OSError) as exc:
            raise EmailDeliveryError("Failed to send email") from exc

    def _send_sync(self, message: EmailMessage) -> None:
        if self.use_ssl:
            smtp_class = IPv4SMTPSSL if self.force_ipv4 else smtplib.SMTP_SSL
        else:
            smtp_class = IPv4SMTP if self.force_ipv4 else smtplib.SMTP
        with smtp_class(self.host, self.port, timeout=self.timeout_seconds) as smtp:
            if self.use_tls and not self.use_ssl:
                smtp.starttls()
            smtp.login(self.username.strip(), self.password)
            smtp.send_message(message)

```

## 📄 `backend\auth\jwt_service.py`

```python
from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from config import JWT_ACCESS_TOKEN_TTL_MINUTES, JWT_ALGORITHM, JWT_REFRESH_TOKEN_TTL_MINUTES, JWT_SECRET


class JWTError(Exception):
    pass


class JWTService:
    def create_access_token(self, *, user_id: int, is_admin: bool) -> tuple[str, int]:
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=JWT_ACCESS_TOKEN_TTL_MINUTES)
        payload = {
            "sub": str(user_id),
            "user_id": user_id,
            "is_admin": is_admin,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        return self._encode(payload), int((exp - now).total_seconds())

    def create_refresh_token(self, *, user_id: int) -> tuple[str, str, datetime, int]:
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=JWT_REFRESH_TOKEN_TTL_MINUTES)
        jti = str(uuid4())
        payload = {
            "sub": str(user_id),
            "user_id": user_id,
            "jti": jti,
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        return self._encode(payload), jti, exp, int((exp - now).total_seconds())

    def decode_access_token(self, token: str) -> dict[str, object]:
        payload = self._decode(token)
        if payload.get("type") != "access" or not isinstance(payload.get("user_id"), int):
            raise JWTError("Invalid access token.")
        return payload

    def decode_refresh_token(self, token: str) -> dict[str, object]:
        payload = self._decode(token)
        if payload.get("type") != "refresh" or not isinstance(payload.get("user_id"), int):
            raise JWTError("Invalid refresh token.")
        if not isinstance(payload.get("jti"), str) or not payload.get("jti"):
            raise JWTError("Invalid refresh token.")
        return payload

    def _encode(self, payload: dict[str, object]) -> str:
        if not JWT_SECRET:
            raise JWTError("JWT_SECRET is not configured.")
        header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
        signing_input = f"{self._b64_json(header)}.{self._b64_json(payload)}"
        signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
        return f"{signing_input}.{self._b64(signature)}"

    def _decode(self, token: str) -> dict[str, object]:
        if not JWT_SECRET:
            raise JWTError("JWT_SECRET is not configured.")
        try:
            header_raw, payload_raw, signature_raw = token.split(".", 2)
        except ValueError as exc:
            raise JWTError("Invalid token.") from exc

        header = self._loads(header_raw)
        if header.get("alg") != JWT_ALGORITHM:
            raise JWTError("Invalid token algorithm.")

        signing_input = f"{header_raw}.{payload_raw}"
        expected = self._b64(
            hmac.new(JWT_SECRET.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(expected, signature_raw):
            raise JWTError("Invalid token signature.")

        payload = self._loads(payload_raw)
        exp = payload.get("exp")
        if not isinstance(exp, int) or exp <= int(datetime.now(timezone.utc).timestamp()):
            raise JWTError("Token expired.")
        return payload

    def _loads(self, value: str) -> dict[str, object]:
        try:
            decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
            payload = json.loads(decoded)
        except (ValueError, json.JSONDecodeError) as exc:
            raise JWTError("Invalid token payload.") from exc
        if not isinstance(payload, dict):
            raise JWTError("Invalid token payload.")
        return payload

    def _b64_json(self, value: dict[str, object]) -> str:
        return self._b64(json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))

    def _b64(self, value: bytes) -> str:
        return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")

```

## 📄 `backend\auth\models.py`

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class AuthRefreshSessionModel(Base):
    __tablename__ = "auth_refresh_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    jti: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class PasswordResetTokenModel(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

```

## 📄 `backend\auth\recovery_service.py`

```python
from __future__ import annotations

import logging
from dataclasses import dataclass

from backend.auth.email_sender import SMTPEmailSender
from backend.auth.reset_tokens_repo import DatabaseResetTokenRepository
from backend.user.crud import SqlAlchemyUserRepository
from backend.user.service import UserAuthError, UserService


logger = logging.getLogger(__name__)


class PasswordResetError(Exception):
    pass


@dataclass
class PasswordRecoveryService:
    user_repository: SqlAlchemyUserRepository
    token_repository: DatabaseResetTokenRepository
    email_sender: SMTPEmailSender

    def _normalize_email(self, email: str) -> str:
        return UserService(self.user_repository).normalize_email(email)

    async def request_recovery(self, *, email: str) -> None:
        normalized_email = self._normalize_email(email)
        user = await self.user_repository.get_by_email(normalized_email)
        if user is None:
            logger.info("Password recovery requested for unknown email.")
            return

        token = await self.token_repository.create(user_id=user.id)
        text = (
            "Восстановление пароля Zamzam\n\n"
            f"Код восстановления:\n{token}\n\n"
            "Срок действия: 10 минут."
        )
        await self.email_sender.send(
            email=normalized_email,
            subject="Восстановление пароля Zamzam",
            text=text,
        )

    async def confirm_recovery(self, *, token: str, password: str) -> None:
        user_id = await self.token_repository.consume(token=token.strip())
        if user_id is None:
            raise PasswordResetError("Неверный или просроченный код восстановления.")

        try:
            await UserService(self.user_repository).reset_password(user_id=user_id, password=password)
        except UserAuthError as exc:
            raise PasswordResetError(str(exc)) from exc

```

## 📄 `backend\auth\reset_tokens_repo.py`

```python
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import randbelow
from typing import Optional

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.models import PasswordResetTokenModel


class DatabaseResetTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, user_id: int) -> str:
        token = f"{randbelow(1_000_000):06d}"
        reset_token = PasswordResetTokenModel(
            user_id=user_id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
            used=False,
        )
        self._session.add(reset_token)
        await self._session.commit()
        return token

    async def consume(self, *, token: str) -> Optional[int]:
        stmt = (
            update(PasswordResetTokenModel)
            .where(
                PasswordResetTokenModel.token == token,
                PasswordResetTokenModel.used.is_(False),
                PasswordResetTokenModel.expires_at > datetime.now(timezone.utc),
            )
            .values(used=True)
            .returning(PasswordResetTokenModel.user_id)
        )
        result = await self._session.execute(stmt)
        user_id = result.scalar_one_or_none()
        if user_id is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return int(user_id)

```

## 📄 `backend\auth\router.py`

```python
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.email_sender import EmailDeliveryError, SMTPEmailSender
from backend.auth.recovery_service import PasswordRecoveryService, PasswordResetError
from backend.auth.reset_tokens_repo import DatabaseResetTokenRepository
from backend.auth.schemas import AuthTokenRead, PasswordRecoveryRequest, PasswordResetRequest, RefreshTokenRequest
from backend.auth.token_service import AuthTokenError, AuthTokenService
from backend.rate_limit import client_ip, rate_limiter
from backend.user.crud import SqlAlchemyUserRepository
from backend.user.depencises import get_user_service
from backend.user.schemas import UserLoginRequest, UserRegisterRequest
from backend.user.service import UserAuthError, UserService
from config import (
    SMTP_FORCE_IPV4,
    SMTP_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_TIMEOUT_SECONDS,
    SMTP_USE_SSL,
    SMTP_USE_TLS,
    SMTP_USER,
)
from db import get_db


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])
token_service = AuthTokenService()


def get_password_recovery_service(session: AsyncSession = Depends(get_db)) -> PasswordRecoveryService:
    return PasswordRecoveryService(
        user_repository=SqlAlchemyUserRepository(session),
        token_repository=DatabaseResetTokenRepository(session),
        email_sender=SMTPEmailSender(
            host=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            from_email=SMTP_FROM,
            use_tls=SMTP_USE_TLS,
            use_ssl=SMTP_USE_SSL,
            timeout_seconds=SMTP_TIMEOUT_SECONDS,
            force_ipv4=SMTP_FORCE_IPV4,
        ),
    )


@router.post("/register", response_model=AuthTokenRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserRegisterRequest,
    request: Request,
    service: UserService = Depends(get_user_service),
    session: AsyncSession = Depends(get_db),
) -> AuthTokenRead:
    logger.info("HTTP register request received.")
    await rate_limiter.check(key=f"auth-register:ip:{client_ip(request)}", limit=10, window_seconds=3600)
    await rate_limiter.check(key=f"auth-register:phone:{payload.phone.strip()}", limit=3, window_seconds=3600)
    await rate_limiter.check(key=f"auth-register:email:{payload.email.strip().lower()}", limit=3, window_seconds=3600)
    try:
        auth_result = await service.register(payload)
        return await token_service.issue_token_pair(session=session, user=auth_result.user)
    except UserAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/login", response_model=AuthTokenRead)
async def login_user(
    payload: UserLoginRequest,
    request: Request,
    service: UserService = Depends(get_user_service),
    session: AsyncSession = Depends(get_db),
) -> AuthTokenRead:
    logger.info("HTTP login request received.")
    await rate_limiter.check(key=f"auth-login:ip:{client_ip(request)}", limit=30, window_seconds=60)
    await rate_limiter.check(key=f"auth-login:phone:{payload.phone.strip()}", limit=10, window_seconds=600)
    try:
        auth_result = await service.login(payload)
        return await token_service.issue_token_pair(session=session, user=auth_result.user)
    except UserAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/refresh", response_model=AuthTokenRead)
async def refresh_token(
    payload: RefreshTokenRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> AuthTokenRead:
    await rate_limiter.check(key=f"auth-refresh:ip:{client_ip(request)}", limit=60, window_seconds=60)
    try:
        return await token_service.refresh_token_pair(session=session, refresh_token=payload.refresh_token)
    except AuthTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/password/recovery")
async def request_password_recovery(
    payload: PasswordRecoveryRequest,
    request: Request,
    service: PasswordRecoveryService = Depends(get_password_recovery_service),
) -> dict[str, bool]:
    await rate_limiter.check(key=f"auth-recovery:ip:{client_ip(request)}", limit=5, window_seconds=3600)
    await rate_limiter.check(key=f"auth-recovery:email:{payload.email.strip().lower()}", limit=3, window_seconds=3600)
    try:
        await service.request_recovery(email=payload.email)
    except UserAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except EmailDeliveryError as exc:
        logger.warning(
            "Password recovery email delivery failed. reason=%s detail=%s",
            type(exc.__cause__).__name__ if exc.__cause__ else type(exc).__name__,
            str(exc),
        )
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Не удалось отправить письмо.") from exc
    return {"ok": True}


@router.post("/password/reset")
async def reset_password(
    payload: PasswordResetRequest,
    request: Request,
    service: PasswordRecoveryService = Depends(get_password_recovery_service),
) -> dict[str, bool]:
    await rate_limiter.check(key=f"auth-reset:ip:{client_ip(request)}", limit=10, window_seconds=3600)
    try:
        await service.confirm_recovery(token=payload.token, password=payload.password)
    except PasswordResetError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/logout")
async def logout_user(
    payload: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    logger.info("HTTP logout request received.")
    try:
        await token_service.revoke_refresh_token(session=session, refresh_token=payload.refresh_token)
    except AuthTokenError:
        pass
    return {"ok": True}

```

## 📄 `backend\auth\schemas.py`

```python
from __future__ import annotations

from pydantic import BaseModel, Field

from backend.user.schemas import UserRead


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class PasswordRecoveryRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)


class PasswordResetRequest(BaseModel):
    token: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    password: str = Field(..., min_length=6, max_length=128)


class AuthTokenRead(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int
    user: UserRead

```

## 📄 `backend\auth\token_service.py`

```python
from __future__ import annotations

from datetime import datetime, timezone
from typing import Union

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.jwt_service import JWTError, JWTService
from backend.auth.models import AuthRefreshSessionModel
from backend.auth.schemas import AuthTokenRead
from backend.user.migrations import is_admin_phone
from backend.user.models import UserModel
from backend.user.schemas import UserRead


class AuthTokenError(Exception):
    pass


class AuthTokenService:
    def __init__(self) -> None:
        self.jwt_service = JWTService()

    async def issue_token_pair(self, *, session: AsyncSession, user: Union[UserRead, UserModel]) -> AuthTokenRead:
        user_read = UserRead.model_validate(user)
        env_admin = is_admin_phone(user_read.phone)
        if user_read.is_admin != env_admin:
            if isinstance(user, UserModel):
                user.is_admin = env_admin
                await session.flush()
                user_read = UserRead.model_validate(user)
            else:
                user_read = user_read.model_copy(update={"is_admin": env_admin})

        access_token, access_expires_in = self.jwt_service.create_access_token(
            user_id=user_read.id,
            is_admin=user_read.is_admin,
        )
        refresh_token, jti, refresh_exp, refresh_expires_in = self.jwt_service.create_refresh_token(
            user_id=user_read.id,
        )
        session.add(
            AuthRefreshSessionModel(
                user_id=user_read.id,
                jti=jti,
                expires_at=refresh_exp,
                revoked=False,
            )
        )
        await session.commit()
        return AuthTokenRead(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=access_expires_in,
            refresh_expires_in=refresh_expires_in,
            user=user_read,
        )

    async def refresh_token_pair(self, *, session: AsyncSession, refresh_token: str) -> AuthTokenRead:
        try:
            payload = self.jwt_service.decode_refresh_token(refresh_token)
        except JWTError as exc:
            raise AuthTokenError("Invalid refresh token.") from exc

        user_id = int(payload["user_id"])
        jti = str(payload["jti"])
        refresh_session = await session.scalar(
            select(AuthRefreshSessionModel).where(
                AuthRefreshSessionModel.user_id == user_id,
                AuthRefreshSessionModel.jti == jti,
                AuthRefreshSessionModel.revoked.is_(False),
            )
        )
        if refresh_session is None:
            raise AuthTokenError("Invalid refresh token.")

        now = datetime.now(timezone.utc)
        expires_at = refresh_session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            refresh_session.revoked = True
            await session.commit()
            raise AuthTokenError("Refresh token expired.")

        user = await session.scalar(select(UserModel).where(UserModel.id == user_id))
        if user is None:
            raise AuthTokenError("User not found.")

        refresh_session.revoked = True
        return await self.issue_token_pair(session=session, user=user)

    async def revoke_refresh_token(self, *, session: AsyncSession, refresh_token: str) -> None:
        try:
            payload = self.jwt_service.decode_refresh_token(refresh_token)
        except JWTError as exc:
            raise AuthTokenError("Invalid refresh token.") from exc

        stmt = (
            update(AuthRefreshSessionModel)
            .where(
                AuthRefreshSessionModel.user_id == int(payload["user_id"]),
                AuthRefreshSessionModel.jti == str(payload["jti"]),
                AuthRefreshSessionModel.revoked.is_(False),
            )
            .values(revoked=True)
        )
        await session.execute(stmt)
        await session.commit()

```

## 📁 `backend\iiko_manager`

## 📄 `backend\iiko_manager\__init__.py`

```python
from backend.iiko_manager.service import IikoCatalogSyncError, IikoCatalogSyncService

__all__ = ["IikoCatalogSyncError", "IikoCatalogSyncService"]

```

## 📄 `backend\iiko_manager\client.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx
import logging


class IikoClientError(Exception):
    pass


logger = logging.getLogger(__name__)


@dataclass
class IikoApiClient:
    api_login: str
    base_url: str
    timeout_seconds: int = 20

    async def get_access_token(self) -> str:
        logger.info("Requesting iiko access token.")
        payload = await self._post("access_token", {"apiLogin": self.api_login}, token=None)
        token = payload.get("token")
        if not token:
            raise IikoClientError("iiko did not return an access token.")
        logger.info("iiko access token received successfully.")
        return str(token)

    async def get_organizations(self, *, token: str) -> list[dict[str, Any]]:
        logger.info("Requesting iiko organizations.")
        payload = await self._post("organizations", {}, token=token)
        organizations = payload.get("organizations")
        if not isinstance(organizations, list):
            raise IikoClientError("iiko organizations response is invalid.")
        logger.info("iiko organizations received. count=%s", len(organizations))
        return organizations

    async def get_nomenclature(self, *, token: str, organization_id: str) -> dict[str, Any]:
        logger.info("Requesting iiko nomenclature. organization_id=%s", organization_id)
        payload = await self._post("nomenclature", {"organizationId": organization_id}, token=token)
        if not isinstance(payload, dict):
            raise IikoClientError("iiko nomenclature response is invalid.")
        logger.info(
            "iiko nomenclature received. groups=%s products=%s",
            len(payload.get("groups", [])),
            len(payload.get("products", [])),
        )
        return payload

    async def get_delivery_order_types(self, *, token: str, organization_ids: list[str]) -> list[dict[str, Any]]:
        logger.info("Requesting iiko delivery order types. organization_ids=%s", organization_ids)
        payload = await self._post("deliveries/order_types", {"organizationIds": organization_ids}, token=token)
        order_types = payload.get("orderTypes")
        if not isinstance(order_types, list):
            raise IikoClientError("iiko delivery order types response is invalid.")
        logger.info("iiko delivery order types received. groups=%s", len(order_types))
        return order_types

    async def get_payment_types(self, *, token: str, organization_ids: list[str]) -> list[dict[str, Any]]:
        logger.info("Requesting iiko payment types. organization_ids=%s", organization_ids)
        payload = await self._post("payment_types", {"organizationIds": organization_ids}, token=token)
        payment_types = payload.get("paymentTypes")
        if not isinstance(payment_types, list):
            raise IikoClientError("iiko payment types response is invalid.")
        logger.info("iiko payment types received. count=%s", len(payment_types))
        return payment_types

    async def get_cities(self, *, token: str, organization_ids: list[str]) -> list[dict[str, Any]]:
        logger.info("Requesting iiko cities. organization_ids=%s", organization_ids)
        payload = await self._post(
            "cities",
            {"organizationIds": organization_ids, "includeDeleted": False},
            token=token,
        )
        items = payload.get("cities") or payload.get("items")
        if not isinstance(items, list):
            raise IikoClientError(f"iiko cities response is invalid. keys={sorted(payload.keys())}")

        cities: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            nested_items = item.get("items") or item.get("cities")
            if isinstance(nested_items, list):
                cities.extend(city for city in nested_items if isinstance(city, dict))
                continue
            if item.get("id") or item.get("name"):
                cities.append(item)
        logger.info("iiko cities received. count=%s", len(cities))
        return cities

    async def get_streets_by_city(self, *, token: str, organization_id: str, city_id: str) -> list[dict[str, Any]]:
        logger.info("Requesting iiko streets by city. organization_id=%s city_id=%s", organization_id, city_id)
        payload = await self._post(
            "streets/by_city",
            {
                "organizationId": organization_id,
                "cityId": city_id,
                "includeDeleted": False,
            },
            token=token,
        )
        streets = payload.get("streets") or payload.get("items")
        if not isinstance(streets, list):
            raise IikoClientError(f"iiko streets by city response is invalid. keys={sorted(payload.keys())}")
        logger.info("iiko streets by city received. count=%s", len(streets))
        return streets

    async def create_delivery_order(self, *, token: str, payload: dict[str, Any]) -> dict[str, Any]:
        logger.info(
            "Sending delivery order to iiko. organization_id=%s terminal_group_id=%s",
            payload.get("organizationId"),
            payload.get("terminalGroupId"),
        )
        response_payload = await self._post("deliveries/create", payload, token=token)
        if not isinstance(response_payload, dict):
            raise IikoClientError("iiko delivery create response is invalid.")
        return response_payload

    async def confirm_delivery_order(self, *, token: str, organization_id: str, order_id: str) -> dict[str, Any]:
        logger.info("Confirming iiko delivery order. organization_id=%s order_id=%s", organization_id, order_id)
        payload = await self._post(
            "deliveries/confirm",
            {
                "organizationId": organization_id,
                "orderId": order_id,
            },
            token=token,
        )
        if not isinstance(payload, dict):
            raise IikoClientError("iiko delivery confirm response is invalid.")
        return payload

    async def get_delivery_orders_by_ids(
        self,
        *,
        token: str,
        organization_id: str,
        order_ids: list[str],
    ) -> list[dict[str, Any]]:
        logger.info("Requesting iiko delivery orders by ids. count=%s", len(order_ids))
        payload = await self._post(
            "deliveries/by_id",
            {
                "organizationId": organization_id,
                "orderIds": order_ids,
            },
            token=token,
        )
        orders = payload.get("orders")
        if not isinstance(orders, list):
            raise IikoClientError("iiko deliveries by id response is invalid.")
        logger.info("iiko delivery orders received. count=%s", len(orders))
        return orders

    async def get_delivery_orders_by_pos_ids(
        self,
        *,
        token: str,
        organization_id: str,
        pos_order_ids: list[str],
    ) -> list[dict[str, Any]]:
        logger.info("Requesting iiko delivery orders by pos ids. count=%s", len(pos_order_ids))
        payload = await self._post(
            "deliveries/by_id",
            {
                "organizationId": organization_id,
                "posOrderIds": pos_order_ids,
            },
            token=token,
        )
        orders = payload.get("orders")
        if not isinstance(orders, list):
            raise IikoClientError("iiko deliveries by pos ids response is invalid.")
        logger.info("iiko delivery orders by pos ids received. count=%s", len(orders))
        return orders

    async def _post(self, path: str, json_payload: dict[str, Any], *, token: Optional[str]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}"} if token else None
        logger.debug("Sending iiko request. path=%s payload_keys=%s", path, sorted(json_payload.keys()))
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(f"{self.base_url}/{path}", json=json_payload, headers=headers)
        except httpx.HTTPError as exc:
            logger.warning("iiko request failed. path=%s error=%s", path, exc)
            raise IikoClientError(f"iiko request failed for {path}: {exc}") from exc

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = response.text.strip()
            logger.warning(
                "iiko request failed. path=%s status=%s detail=%s",
                path,
                response.status_code,
                detail,
            )
            raise IikoClientError(f"iiko request failed for {path}: {response.status_code} {detail}") from exc

        payload = response.json()
        if not isinstance(payload, dict):
            raise IikoClientError(f"iiko returned non-object payload for {path}.")
        logger.debug("iiko request finished successfully. path=%s status=%s", path, response.status_code)
        return payload

```

## 📄 `backend\iiko_manager\repository.py`

```python
from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import logging
from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.redactor.models import MenuItemModel


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CatalogSyncItem:
    iiko_product_id: str
    iiko_group_id: Optional[str]
    iiko_category_name: Optional[str]
    iiko_parent_group_id: Optional[str]
    iiko_terminal_group_id: str
    title: str
    description: str
    category: str
    price_from_iiko: Optional[int]
    is_active: bool
    is_deleted_in_iiko: bool
    sync_hash: str


@dataclass(frozen=True)
class CatalogSyncResult:
    created: int
    updated: int
    deactivated: int


class IikoCatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def sync_items(
        self,
        *,
        items: Sequence[CatalogSyncItem],
        synced_at: datetime,
        terminal_group_id: str,
    ) -> CatalogSyncResult:
        logger.info(
            "Repository sync started. terminal_group_id=%s items=%s synced_at=%s",
            terminal_group_id,
            len(items),
            synced_at.isoformat(),
        )
        existing = await self._get_existing_by_product_ids(
            product_ids=(item.iiko_product_id for item in items),
            terminal_group_id=terminal_group_id,
        )
        logger.info("Loaded existing iiko menu items from database. count=%s", len(existing))

        created = 0
        updated = 0
        seen_product_ids: set[str] = set()

        for item in items:
            seen_product_ids.add(item.iiko_product_id)
            model = existing.get(item.iiko_product_id)
            if model is None:
                self._session.add(self._build_model(item=item, synced_at=synced_at))
                created += 1
                continue

            if not self._needs_update(model=model, item=item):
                continue

            self._apply_remote_state(model=model, item=item, synced_at=synced_at)
            updated += 1

        deactivated = await self._deactivate_missing_items(
            active_product_ids=seen_product_ids,
            synced_at=synced_at,
            terminal_group_id=terminal_group_id,
        )
        await self._session.commit()
        logger.info(
            "Repository sync committed. created=%s updated=%s deactivated=%s",
            created,
            updated,
            deactivated,
        )
        return CatalogSyncResult(created=created, updated=updated, deactivated=deactivated)

    async def _get_existing_by_product_ids(
        self,
        *,
        product_ids: Iterable[str],
        terminal_group_id: str,
    ) -> dict[str, MenuItemModel]:
        ids = list(dict.fromkeys(product_ids))
        if not ids:
            return {}

        stmt: Select[tuple[MenuItemModel]] = select(MenuItemModel).where(
            MenuItemModel.iiko_product_id.in_(ids),
            MenuItemModel.sync_source == "iiko",
        )
        rows = (await self._session.scalars(stmt)).all()
        selected: dict[str, MenuItemModel] = {}
        for row in rows:
            product_id = row.iiko_product_id
            if not product_id:
                continue

            current = selected.get(product_id)
            if current is None or self._is_better_existing_match(
                candidate=row,
                current=current,
                terminal_group_id=terminal_group_id,
            ):
                selected[product_id] = row

        return selected

    def _is_better_existing_match(
        self,
        *,
        candidate: MenuItemModel,
        current: MenuItemModel,
        terminal_group_id: str,
    ) -> bool:
        candidate_score = self._existing_match_score(candidate, terminal_group_id=terminal_group_id)
        current_score = self._existing_match_score(current, terminal_group_id=terminal_group_id)
        if candidate_score != current_score:
            return candidate_score > current_score

        candidate_updated_at = candidate.updated_at or candidate.created_at
        current_updated_at = current.updated_at or current.created_at
        if candidate_updated_at != current_updated_at:
            return candidate_updated_at > current_updated_at

        return candidate.id > current.id

    def _existing_match_score(self, model: MenuItemModel, *, terminal_group_id: str) -> tuple[int, int, int]:
        return (
            int(model.is_published),
            int(model.iiko_terminal_group_id == terminal_group_id),
            int(not model.is_deleted_in_iiko),
        )

    async def _deactivate_missing_items(
        self,
        *,
        active_product_ids: set[str],
        synced_at: datetime,
        terminal_group_id: Optional[str],
    ) -> int:
        if terminal_group_id is None:
            return 0

        stmt = (
            update(MenuItemModel)
            .where(
                MenuItemModel.sync_source == "iiko",
                MenuItemModel.iiko_terminal_group_id == terminal_group_id,
                MenuItemModel.iiko_product_id.is_not(None),
                MenuItemModel.is_deleted_in_iiko.is_(False),
            )
            .values(
                is_active=False,
                is_deleted_in_iiko=True,
                last_synced_at=synced_at,
                version=MenuItemModel.version + 1,
            )
        )
        if active_product_ids:
            stmt = stmt.where(MenuItemModel.iiko_product_id.not_in(active_product_ids))

        result = await self._session.execute(stmt)
        return int(result.rowcount or 0)

    def _build_model(self, *, item: CatalogSyncItem, synced_at: datetime) -> MenuItemModel:
        accent = self._default_accent(item.iiko_group_id or item.category)
        return MenuItemModel(
            sync_source="iiko",
            iiko_product_id=item.iiko_product_id,
            iiko_group_id=item.iiko_group_id,
            iiko_category_name=item.iiko_category_name,
            iiko_parent_group_id=item.iiko_parent_group_id,
            iiko_terminal_group_id=item.iiko_terminal_group_id,
            title=item.title,
            description=item.description,
            price=item.price_from_iiko or 0,
            price_from_iiko=item.price_from_iiko,
            category=item.category,
            accent=accent,
            badge=None,
            image_path=None,
            sort_order=0,
            is_active=item.is_active,
            is_deleted_in_iiko=item.is_deleted_in_iiko,
            sync_hash=item.sync_hash,
            last_synced_at=synced_at,
        )

    def _needs_update(self, *, model: MenuItemModel, item: CatalogSyncItem) -> bool:
        return any(
            (
                model.sync_source != "iiko",
                model.iiko_group_id != item.iiko_group_id,
                model.iiko_category_name != item.iiko_category_name,
                model.iiko_parent_group_id != item.iiko_parent_group_id,
                model.iiko_terminal_group_id != item.iiko_terminal_group_id,
                model.title != item.title,
                model.description != item.description,
                model.price_from_iiko != item.price_from_iiko,
                model.price != (item.price_from_iiko or 0),
                model.is_active != item.is_active,
                model.is_deleted_in_iiko != item.is_deleted_in_iiko,
                model.sync_hash != item.sync_hash,
            )
        )

    def _apply_remote_state(self, *, model: MenuItemModel, item: CatalogSyncItem, synced_at: datetime) -> None:
        model.sync_source = "iiko"
        model.iiko_group_id = item.iiko_group_id
        model.iiko_category_name = item.iiko_category_name
        model.iiko_parent_group_id = item.iiko_parent_group_id
        model.iiko_terminal_group_id = item.iiko_terminal_group_id
        model.title = item.title
        model.description = item.description
        model.price_from_iiko = item.price_from_iiko
        model.price = item.price_from_iiko or 0
        model.is_active = item.is_active
        model.is_deleted_in_iiko = item.is_deleted_in_iiko
        model.sync_hash = item.sync_hash
        model.last_synced_at = synced_at
        model.version += 1

    def _default_accent(self, seed: str) -> str:
        palette = ("#e85424", "#d9a35f", "#5ab6a6", "#6da4ff", "#ef7b5c", "#9ccf7f")
        index = sum(ord(char) for char in seed) % len(palette)
        return palette[index]

```

## 📄 `backend\iiko_manager\service.py`

```python
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional, Tuple

from backend.iiko_manager.client import IikoApiClient
from backend.iiko_manager.repository import CatalogSyncItem, CatalogSyncResult, IikoCatalogRepository


class IikoCatalogSyncError(Exception):
    pass


logger = logging.getLogger(__name__)


@dataclass
class IikoCatalogSyncService:
    client: IikoApiClient
    repository: IikoCatalogRepository
    terminal_group_id: str
    organization_id: Optional[str] = None

    async def sync(self) -> CatalogSyncResult:
        logger.info("Catalog sync started. terminal_group_id=%s", self.terminal_group_id)
        token = await self.client.get_access_token()
        organization_id = await self._resolve_organization_id(token=token)
        nomenclature = await self.client.get_nomenclature(token=token, organization_id=organization_id)
        items = self._build_sync_items(nomenclature)
        synced_at = datetime.now(timezone.utc)
        logger.info("Prepared %s normalized iiko items for sync.", len(items))
        result = await self.repository.sync_items(
            items=items,
            synced_at=synced_at,
            terminal_group_id=self.terminal_group_id,
        )
        logger.info(
            "Catalog sync persisted successfully. created=%s updated=%s deactivated=%s",
            result.created,
            result.updated,
            result.deactivated,
        )
        return result

    async def _resolve_organization_id(self, *, token: str) -> str:
        if self.organization_id:
            logger.info("Using configured iiko organization id=%s", self.organization_id)
            return self.organization_id

        organizations = await self.client.get_organizations(token=token)
        if len(organizations) != 1:
            raise IikoCatalogSyncError(
                "IIKO_ORGANIZATION_ID is required when the iiko account contains more than one organization."
            )

        organization_id = organizations[0].get("id")
        if not organization_id:
            raise IikoCatalogSyncError("iiko organizations response did not include a valid organization id.")
        logger.info("Resolved iiko organization automatically. organization_id=%s", organization_id)
        return str(organization_id)

    def _build_sync_items(self, nomenclature: dict[str, Any]) -> list[CatalogSyncItem]:
        groups_by_id = {
            str(group.get("id")): group
            for group in nomenclature.get("groups", [])
            if isinstance(group, dict) and group.get("id")
        }

        normalized_items: list[CatalogSyncItem] = []
        products_without_price = 0
        deleted_products = 0
        seen_terminal_group_ids: set[str] = set()
        matched_by_current_price = 0
        for product in nomenclature.get("products", []):
            if not isinstance(product, dict):
                continue

            product_id = product.get("id")
            if not product_id:
                continue

            group_id = self._to_str_or_none(product.get("parentGroup") or product.get("groupId"))
            group = groups_by_id.get(group_id or "")
            parent_group_id = self._to_str_or_none(group.get("parentGroup")) if group else None
            title = self._resolve_title(product)
            category = self._resolve_category_name(group=group)
            description = self._resolve_description(product=product, category=category, title=title)
            seen_terminal_group_ids.update(self._collect_terminal_group_ids(product))
            price, price_source = self._extract_price(product)
            is_deleted = bool(product.get("isDeleted"))
            is_active = (not is_deleted) and price is not None
            if price is None:
                products_without_price += 1
            elif price_source == "currentPrice":
                matched_by_current_price += 1
            if is_deleted:
                deleted_products += 1

            normalized_items.append(
                CatalogSyncItem(
                    iiko_product_id=str(product_id),
                    iiko_group_id=group_id,
                    iiko_category_name=category,
                    iiko_parent_group_id=parent_group_id,
                    iiko_terminal_group_id=self.terminal_group_id,
                    title=title,
                    description=description,
                    category=category,
                    price_from_iiko=price,
                    is_active=is_active,
                    is_deleted_in_iiko=is_deleted,
                    sync_hash=self._build_sync_hash(
                        product_id=str(product_id),
                        group_id=group_id,
                        parent_group_id=parent_group_id,
                        title=title,
                        description=description,
                        category=category,
                        price=price,
                        is_active=is_active,
                        is_deleted=is_deleted,
                    ),
                )
            )

        logger.info(
            "Normalized iiko products. total=%s without_price=%s deleted=%s active=%s",
            len(normalized_items),
            products_without_price,
            deleted_products,
            sum(1 for item in normalized_items if item.is_active),
        )
        logger.info("Price extraction summary. matched_by_currentPrice=%s", matched_by_current_price)
        if products_without_price == len(normalized_items) and normalized_items:
            logger.warning(
                "No prices were matched for terminal group %s. Available terminalGroupId examples from iiko: %s",
                self.terminal_group_id,
                ", ".join(sorted(seen_terminal_group_ids)[:10]) or "none",
            )
        return normalized_items

    def _extract_price(self, product: dict[str, Any]) -> Tuple[Optional[int], Optional[str]]:
        for size_price in product.get("sizePrices", []):
            if not isinstance(size_price, dict):
                continue
            price_container = size_price.get("price") or {}
            current_prices = price_container.get("currentPrices") or []
            for price_item in current_prices:
                if not isinstance(price_item, dict):
                    continue
                if price_item.get("terminalGroupId") != self.terminal_group_id:
                    continue
                value = price_item.get("price")
                if value is None:
                    continue
                return int(value), "currentPrices"

            # В этой организации iiko отдает общую цену без terminalGroupId.
            current_price = price_container.get("currentPrice")
            if current_price is not None:
                return int(current_price), "currentPrice"
        return None, None

    def _collect_terminal_group_ids(self, product: dict[str, Any]) -> set[str]:
        terminal_group_ids: set[str] = set()
        for size_price in product.get("sizePrices", []):
            if not isinstance(size_price, dict):
                continue
            price_container = size_price.get("price") or {}
            current_prices = price_container.get("currentPrices") or []
            for price_item in current_prices:
                if not isinstance(price_item, dict):
                    continue
                terminal_group_id = self._to_str_or_none(price_item.get("terminalGroupId"))
                if terminal_group_id:
                    terminal_group_ids.add(terminal_group_id)
        return terminal_group_ids

    def _resolve_title(self, product: dict[str, Any]) -> str:
        title = str(product.get("name") or "").strip()
        if not title:
            raise IikoCatalogSyncError("iiko product without name was returned.")
        return title

    def _resolve_description(self, *, product: dict[str, Any], category: str, title: str) -> str:
        for key in ("description", "additionalInfo", "seoDescription"):
            value = product.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return f"{title} ({category})"

    def _resolve_category_name(self, *, group: Optional[dict[str, Any]]) -> str:
        if not group:
            return "Разное"

        name = str(group.get("name") or "").strip()
        return name or "Разное"

    def _build_sync_hash(
        self,
        *,
        product_id: str,
        group_id: Optional[str],
        parent_group_id: Optional[str],
        title: str,
        description: str,
        category: str,
        price: Optional[int],
        is_active: bool,
        is_deleted: bool,
    ) -> str:
        payload = {
            "category": category,
            "description": description,
            "group_id": group_id,
            "is_active": is_active,
            "is_deleted": is_deleted,
            "parent_group_id": parent_group_id,
            "price": price,
            "product_id": product_id,
            "title": title,
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _to_str_or_none(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

```

## 📁 `backend\orders`

## 📄 `backend\orders\__init__.py`

```python
from backend.orders.models import OrderModel
from backend.orders.router import router

__all__ = ["OrderModel", "router"]

```

## 📄 `backend\orders\availability.py`

```python
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import HTTPException, status


MOSCOW_TZ = timezone(timedelta(hours=3), name="MSK")
ORDER_OPEN_HOUR = 8
ORDER_CLOSE_HOUR = 21


def is_order_time_open(now: Optional[datetime] = None) -> bool:
    current_time = now.astimezone(MOSCOW_TZ) if now else datetime.now(MOSCOW_TZ)
    return ORDER_OPEN_HOUR <= current_time.hour < ORDER_CLOSE_HOUR


def ensure_order_time_open() -> None:
    if is_order_time_open():
        return

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="\u0417\u0430\u043a\u0430\u0437\u044b \u043f\u0440\u0438\u043d\u0438\u043c\u0430\u044e\u0442\u0441\u044f \u0441 08:00 \u0434\u043e 21:00 \u043f\u043e \u043c\u043e\u0441\u043a\u043e\u0432\u0441\u043a\u043e\u043c\u0443 \u0432\u0440\u0435\u043c\u0435\u043d\u0438.",
    )

```

## 📄 `backend\orders\branches.py`

```python
from enum import Enum
from typing import Optional

from config import (
    TERMINAL_ID_GROUP_MALYSHAVA,
    TERMINAL_ID_GROUP_SUH,
)


class BranchCode(str, Enum):
    MALYSHAVA = "malyshava"
    SUH = "suh"


TERMINAL_GROUP_BY_BRANCH: dict[BranchCode, Optional[str]] = {
    BranchCode.MALYSHAVA: TERMINAL_ID_GROUP_MALYSHAVA,
    BranchCode.SUH: TERMINAL_ID_GROUP_SUH,
}


def resolve_terminal_group_id(branch_code: BranchCode) -> str:
    terminal_group_id = TERMINAL_GROUP_BY_BRANCH.get(branch_code)

    if not terminal_group_id:
        raise ValueError(
            f"Для филиала {branch_code.value} не настроен терминал iiko."
        )

    return terminal_group_id

```

## 📄 `backend\orders\crud.py`

```python
from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime
from typing import Optional, Protocol

from sqlalchemy import func, or_, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.orders.models import OrderDeliveryJobModel, OrderModel
from backend.orders.schemas import OrderCreate
from backend.orders.statuses import ACTIVE_ORDER_STATUSES, ORDER_STATUS_PREPARING


class OrderRepository(Protocol):
    async def create(
        self,
        *,
        user_id: int,
        payload: OrderCreate,
        subtotal_amount: int,
        bonus_spent: int,
        total_amount: int,
        bonus_awarded: int,
        branch_code: str,
        iiko_terminal_group_id: str,
        idempotency_key: Optional[str] = None,
        iiko_order_id: Optional[str] = None,
        iiko_correlation_id: Optional[str] = None,
        iiko_creation_status: Optional[str] = None,
    ) -> OrderModel: ...
    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[OrderModel]: ...
    async def update_iiko_result(
        self,
        *,
        order_id: int,
        iiko_order_id: Optional[str],
        iiko_correlation_id: Optional[str],
        iiko_creation_status: Optional[str],
    ) -> Optional[OrderModel]: ...
    async def claim_iiko_submission(self, *, order_id: int) -> Optional[OrderModel]: ...
    async def list_by_user(self, user_id: int) -> Sequence[OrderModel]: ...
    async def get_latest_by_user(self, user_id: int) -> Optional[OrderModel]: ...
    async def get_latest_active_by_user(self, user_id: int) -> Optional[OrderModel]: ...
    async def count_active_by_user(self, user_id: int) -> int: ...
    async def list_recent(self, *, limit: int, phone: Optional[str] = None) -> Sequence[OrderModel]: ...
    async def get_by_id(self, order_id: int) -> Optional[OrderModel]: ...
    async def update_status(self, *, order_id: int, status: str) -> Optional[OrderModel]: ...
    async def list_active_iiko_orders(self, *, limit: int) -> Sequence[OrderModel]: ...
    async def list_orders_pending_iiko_submission(self, *, limit: int) -> Sequence[OrderModel]: ...
    async def update_status_by_iiko_order_id(self, *, iiko_order_id: str, status: str) -> Optional[OrderModel]: ...
    async def enqueue_iiko_submission_job(self, *, order_id: int) -> None: ...
    async def enqueue_missing_paid_iiko_submission_jobs(self, *, limit: int, created_after: Optional[datetime] = None) -> int: ...
    async def claim_due_iiko_submission_jobs(self, *, limit: int, created_after: Optional[datetime] = None) -> Sequence[OrderDeliveryJobModel]: ...
    async def mark_iiko_submission_job_done(self, *, job_id: int) -> None: ...
    async def mark_iiko_submission_job_failed(self, *, job_id: int, error_message: str, next_run_at: datetime) -> None: ...


class SqlAlchemyOrderRepository:
    ACTIVE_STATUSES = ACTIVE_ORDER_STATUSES

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: int,
        payload: OrderCreate,
        subtotal_amount: int,
        bonus_spent: int,
        total_amount: int,
        bonus_awarded: int,
        branch_code: str,
        iiko_terminal_group_id: str,
        idempotency_key: Optional[str] = None,
        iiko_order_id: Optional[str] = None,
        iiko_correlation_id: Optional[str] = None,
        iiko_creation_status: Optional[str] = None,
    ) -> OrderModel:
        model = OrderModel(
            user_id=user_id,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            checkout_type=payload.checkout_type,
            payment_type=payload.payment_type,
            delivery_address=payload.delivery_address,
            delivery_street=payload.delivery_street,
            delivery_house=payload.delivery_house,
            delivery_flat=payload.delivery_flat,
            entrance=payload.entrance,
            comment=payload.comment,
            items_json=json.dumps([item.model_dump() for item in payload.items], ensure_ascii=False),
            items_count=sum(item.quantity for item in payload.items),
            cutlery_count=payload.cutlery_count,
            subtotal_amount=subtotal_amount,
            bonus_spent=bonus_spent,
            total_amount=total_amount,
            bonus_awarded=bonus_awarded,
            idempotency_key=idempotency_key,
            iiko_order_id=iiko_order_id,
            iiko_correlation_id=iiko_correlation_id,
            iiko_creation_status=iiko_creation_status,
            branch_code=branch_code,
            iiko_terminal_group_id=iiko_terminal_group_id,
            status=ORDER_STATUS_PREPARING,
        )
        self._session.add(model)
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise
        await self._session.refresh(model)
        return model

    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[OrderModel]:
        stmt = select(OrderModel).where(OrderModel.idempotency_key == idempotency_key)
        return await self._session.scalar(stmt)

    async def update_iiko_result(
        self,
        *,
        order_id: int,
        iiko_order_id: Optional[str],
        iiko_correlation_id: Optional[str],
        iiko_creation_status: Optional[str],
    ) -> Optional[OrderModel]:
        stmt = (
            update(OrderModel)
            .where(OrderModel.id == order_id)
            .values(
                iiko_order_id=iiko_order_id,
                iiko_correlation_id=iiko_correlation_id,
                iiko_creation_status=iiko_creation_status,
                updated_at=func.now(),
            )
            .returning(OrderModel)
        )
        result = await self._session.execute(stmt)
        order = result.scalar_one_or_none()
        if order is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return order

    async def claim_iiko_submission(self, *, order_id: int) -> Optional[OrderModel]:
        stmt = (
            update(OrderModel)
            .where(
                OrderModel.id == order_id,
                OrderModel.iiko_order_id.is_(None),
                or_(
                    OrderModel.iiko_creation_status.in_(("LocalPending", "Failed")),
                    (
                        OrderModel.iiko_creation_status == "IikoProcessing"
                    )
                    & (OrderModel.updated_at < func.now() - text("interval '5 minutes'")),
                ),
            )
            .values(iiko_creation_status="IikoProcessing", updated_at=func.now())
            .returning(OrderModel)
        )
        result = await self._session.execute(stmt)
        order = result.scalar_one_or_none()
        if order is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return order

    async def list_by_user(self, user_id: int) -> Sequence[OrderModel]:
        stmt = select(OrderModel).where(OrderModel.user_id == user_id).order_by(OrderModel.created_at.desc(), OrderModel.id.desc())
        return (await self._session.scalars(stmt)).all()

    async def get_latest_by_user(self, user_id: int) -> Optional[OrderModel]:
        stmt = (
            select(OrderModel)
            .where(OrderModel.user_id == user_id)
            .order_by(OrderModel.created_at.desc(), OrderModel.id.desc())
            .limit(1)
        )
        return await self._session.scalar(stmt)

    async def get_latest_active_by_user(self, user_id: int) -> Optional[OrderModel]:
        stmt = (
            select(OrderModel)
            .where(OrderModel.user_id == user_id, OrderModel.status.in_(self.ACTIVE_STATUSES))
            .order_by(OrderModel.created_at.desc(), OrderModel.id.desc())
            .limit(1)
        )
        return await self._session.scalar(stmt)

    async def count_active_by_user(self, user_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(OrderModel)
            .where(OrderModel.user_id == user_id, OrderModel.status.in_(self.ACTIVE_STATUSES))
        )
        return int(await self._session.scalar(stmt) or 0)

    async def list_recent(self, *, limit: int, phone: Optional[str] = None) -> Sequence[OrderModel]:
        stmt = select(OrderModel)
        if phone:
            stmt = stmt.where(OrderModel.customer_phone == phone)
        stmt = stmt.order_by(OrderModel.created_at.desc(), OrderModel.id.desc()).limit(limit)
        return (await self._session.scalars(stmt)).all()

    async def get_by_id(self, order_id: int) -> Optional[OrderModel]:
        stmt = select(OrderModel).where(OrderModel.id == order_id)
        return await self._session.scalar(stmt)

    async def update_status(self, *, order_id: int, status: str) -> Optional[OrderModel]:
        stmt = (
            update(OrderModel)
            .where(OrderModel.id == order_id)
            .values(status=status, updated_at=func.now())
            .returning(OrderModel)
        )
        result = await self._session.execute(stmt)
        order = result.scalar_one_or_none()
        if order is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return order

    async def list_active_iiko_orders(self, *, limit: int) -> Sequence[OrderModel]:
        stmt = (
            select(OrderModel)
            .where(
                OrderModel.status.in_(self.ACTIVE_STATUSES),
                OrderModel.iiko_order_id.is_not(None),
            )
            .order_by(OrderModel.created_at.asc(), OrderModel.id.asc())
            .limit(limit)
        )
        return (await self._session.scalars(stmt)).all()

    async def list_orders_pending_iiko_submission(self, *, limit: int) -> Sequence[OrderModel]:
        stmt = (
            select(OrderModel)
            .where(
                OrderModel.iiko_order_id.is_(None),
                OrderModel.iiko_creation_status.in_(("LocalPending", "Failed")),
            )
            .order_by(OrderModel.updated_at.asc(), OrderModel.id.asc())
            .limit(limit)
        )
        return (await self._session.scalars(stmt)).all()

    async def update_status_by_iiko_order_id(self, *, iiko_order_id: str, status: str) -> Optional[OrderModel]:
        stmt = (
            update(OrderModel)
            .where(OrderModel.iiko_order_id == iiko_order_id)
            .values(status=status, updated_at=func.now())
            .returning(OrderModel)
        )
        result = await self._session.execute(stmt)
        order = result.scalar_one_or_none()
        if order is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return order

    async def enqueue_iiko_submission_job(self, *, order_id: int) -> None:
        stmt = (
            insert(OrderDeliveryJobModel)
            .values(order_id=order_id, job_type="send_to_iiko", status="pending")
            .on_conflict_do_nothing(index_elements=[OrderDeliveryJobModel.order_id])
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def enqueue_missing_paid_iiko_submission_jobs(self, *, limit: int, created_after: Optional[datetime] = None) -> int:
        safe_limit = max(1, min(limit, 100))
        created_after_filter = "AND pending_payments.created_at >= :created_after" if created_after is not None else ""
        stmt = text(
            f"""
            INSERT INTO order_delivery_jobs (order_id, job_type, status)
            SELECT orders.id, 'send_to_iiko', 'pending'
            FROM orders
            LEFT JOIN pending_payments ON pending_payments.order_id = orders.id
            LEFT JOIN order_delivery_jobs ON order_delivery_jobs.order_id = orders.id
            WHERE orders.iiko_order_id IS NULL
              AND orders.iiko_creation_status IN ('LocalPending', 'Failed')
              AND order_delivery_jobs.id IS NULL
              AND pending_payments.status IN ('succeeded', 'order_failed')
              AND (
                  orders.checkout_type <> 'delivery'
                  OR (
                      orders.delivery_street IS NOT NULL
                      AND btrim(orders.delivery_street) <> ''
                      AND orders.delivery_house IS NOT NULL
                      AND btrim(orders.delivery_house) <> ''
                  )
              )
              {created_after_filter}
            ORDER BY orders.updated_at ASC, orders.id ASC
            LIMIT :limit
            ON CONFLICT (order_id) DO NOTHING
            RETURNING id
            """
        )
        params = {"limit": safe_limit}
        if created_after is not None:
            params["created_after"] = created_after
        result = await self._session.execute(stmt, params)
        created = len(result.fetchall())
        await self._session.commit()
        return created

    async def claim_due_iiko_submission_jobs(self, *, limit: int, created_after: Optional[datetime] = None) -> Sequence[OrderDeliveryJobModel]:
        safe_limit = max(1, min(limit, 100))
        async with self._session.begin():
            stmt = select(OrderDeliveryJobModel).join(OrderModel).where(
                OrderDeliveryJobModel.job_type == "send_to_iiko",
                or_(
                    OrderDeliveryJobModel.status.in_(("pending", "failed")),
                    (
                        OrderDeliveryJobModel.status == "processing"
                    )
                    & (OrderDeliveryJobModel.locked_at < func.now() - text("interval '5 minutes'")),
                ),
                OrderDeliveryJobModel.next_run_at <= func.now(),
                or_(
                    OrderModel.checkout_type != "delivery",
                    (
                        OrderModel.delivery_street.is_not(None)
                        & (func.btrim(OrderModel.delivery_street) != "")
                        & OrderModel.delivery_house.is_not(None)
                        & (func.btrim(OrderModel.delivery_house) != "")
                    ),
                ),
            )
            if created_after is not None:
                stmt = stmt.where(OrderDeliveryJobModel.created_at >= created_after)
            stmt = (
                stmt.order_by(OrderDeliveryJobModel.next_run_at.asc(), OrderDeliveryJobModel.id.asc())
                .limit(safe_limit)
                .with_for_update(skip_locked=True)
            )
            jobs = list((await self._session.scalars(stmt)).all())
            if not jobs:
                return []

            await self._session.execute(
                update(OrderDeliveryJobModel)
                .where(OrderDeliveryJobModel.id.in_([job.id for job in jobs]))
                .values(
                    status="processing",
                    attempts=OrderDeliveryJobModel.attempts + 1,
                    locked_at=func.now(),
                    updated_at=func.now(),
                    error_message=None,
                )
            )
            return jobs

    async def mark_iiko_submission_job_done(self, *, job_id: int) -> None:
        stmt = (
            update(OrderDeliveryJobModel)
            .where(OrderDeliveryJobModel.id == job_id)
            .values(status="done", locked_at=None, error_message=None, updated_at=func.now())
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def mark_iiko_submission_job_failed(self, *, job_id: int, error_message: str, next_run_at: datetime) -> None:
        stmt = (
            update(OrderDeliveryJobModel)
            .where(OrderDeliveryJobModel.id == job_id)
            .values(
                status="failed",
                locked_at=None,
                error_message=error_message[:2000],
                next_run_at=next_run_at,
                updated_at=func.now(),
            )
        )
        await self._session.execute(stmt)
        await self._session.commit()

```

## 📄 `backend\orders\depencises.py`

```python
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

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
)
from db import get_db


def get_order_repository(
    session: AsyncSession = Depends(get_db),
) -> SqlAlchemyOrderRepository:
    return SqlAlchemyOrderRepository(session)


def get_order_menu_item_repository(
    session: AsyncSession = Depends(get_db),
) -> SqlAlchemyMenuItemRepository:
    return SqlAlchemyMenuItemRepository(session)


def get_iiko_order_gateway() -> IikoOrderGateway:
    return IikoOrderGateway(
        client=IikoApiClient(
            api_login=API_IIKO or "",
            base_url=IIKO_BASE_URL,
            timeout_seconds=IIKO_ORDER_TIMEOUT_SECONDS,
        ),
        organization_id=IIKO_ORGANIZATION_ID,
        source_key=IIKO_ORDER_SOURCE_KEY,
        online_payment_type_id=IIKO_ONLINE_PAYMENT_TYPE_ID,
        online_payment_type_kind=IIKO_ONLINE_PAYMENT_TYPE_KIND,
    )


def get_order_service(
    repository: SqlAlchemyOrderRepository = Depends(get_order_repository),
    menu_item_repository: SqlAlchemyMenuItemRepository = Depends(get_order_menu_item_repository),
    iiko_order_gateway: IikoOrderGateway = Depends(get_iiko_order_gateway),
) -> OrderService:
    return OrderService(
        repository=repository,
        menu_item_repository=menu_item_repository,
        iiko_order_gateway=iiko_order_gateway,
    )

```

## 📄 `backend\orders\iiko.py`

```python
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional

from backend.iiko_manager.client import IikoApiClient, IikoClientError
from backend.orders.schemas import OrderCreate


logger = logging.getLogger(__name__)
DEFAULT_DELIVERY_CITY = "Екатеринбург"
_STREET_CACHE: dict[str, list[dict[str, object]]] = {}
_ADDRESS_PART_LABEL_RE = re.compile(
    r"^(?:ул\.?|улица|пр\.?|проспект|пер\.?|переулок|бульвар|б-р|г\.?|город)\s+",
    re.IGNORECASE,
)


class IikoOrderError(Exception):
    pass


@dataclass(frozen=True)
class IikoOrderItem:
    product_id: str
    title: str
    price: int
    quantity: int


@dataclass
class IikoOrderGateway:
    client: IikoApiClient
    organization_id: Optional[str]
    source_key: str = "zamzam-site"
    online_payment_type_id: Optional[str] = None
    online_payment_type_kind: str = "Card"

    async def submit_order(
            self,
            *,
            payload: OrderCreate,
            items: list[IikoOrderItem],
            total_amount: int,
            terminal_group_id: str,
            external_number: Optional[str] = None,
    ) -> dict[str, str]:
        if not self.client.api_login:
            raise IikoOrderError("API_IIKO is not configured.")
        if not terminal_group_id:
            raise IikoOrderError("TERMINAL_ID_GROUP is not configured.")

        token = await self.client.get_access_token()
        organization_id = await self._resolve_organization_id(token=token)
        order_type_id = await self._resolve_order_type_id(
            token=token,
            checkout_type=payload.checkout_type,
            organization_id=organization_id,
        )
        payments = await self._build_payments(
            token=token,
            organization_id=organization_id,
            payment_type=payload.payment_type,
            total_amount=total_amount,
        )

        comment_parts = []
        if payload.comment:
            comment_parts.append(payload.comment.strip())
        if payload.cutlery_count > 0:
            comment_parts.append(f"Приборы: {payload.cutlery_count}")

        order_payload: dict[str, object] = {
            "organizationId": organization_id,
            "terminalGroupId": terminal_group_id,
            "order": {
                "phone": payload.customer_phone,
                "customer": {
                    "name": payload.customer_name,
                },
                "orderTypeId": order_type_id,
                "items": [
                    {
                        "productId": item.product_id,
                        "type": "Product",
                        "amount": item.quantity,
                        "price": item.price,
                    }
                    for item in items
                ],
            },
        }
        if self.source_key:
            order_payload["order"]["sourceKey"] = self.source_key
        if external_number:
            order_payload["order"]["externalNumber"] = external_number[:50]
        if comment_parts:
            order_payload["order"]["comment"] = " | ".join(comment_parts)
        if payments:
            order_payload["order"]["payments"] = payments
        if payload.checkout_type == "delivery" and payload.delivery_street and payload.delivery_house:
            order_payload["order"]["deliveryPoint"] = self._build_delivery_point(
                street=payload.delivery_street,
                house=payload.delivery_house,
                flat=payload.delivery_flat,
                entrance=payload.entrance,
            )
            logger.info(
                "Sending iiko delivery point. delivery_point=%s",
                order_payload["order"]["deliveryPoint"],
            )

        try:
            response_payload = await self.client.create_delivery_order(token=token, payload=order_payload)
        except IikoClientError as exc:
            raise IikoOrderError(str(exc)) from exc

        order_info = response_payload.get("orderInfo") or {}
        creation_status = str(order_info.get("creationStatus") or "")
        if creation_status not in {"Success", "InProgress"}:
            error_info = order_info.get("errorInfo") or {}
            error_code = error_info.get("code")
            error_message = str(error_info.get("message") or error_info.get("description") or "Unknown iiko error.")
            raise IikoOrderError(self._to_user_message(error_code=error_code, error_message=error_message))

        logger.info(
            "iiko order accepted. creation_status=%s order_id=%s correlation_id=%s",
            creation_status,
            order_info.get("id"),
            response_payload.get("correlationId"),
        )
        iiko_order_id = str(order_info.get("id") or "")
        if iiko_order_id:
            try:
                await self.client.confirm_delivery_order(
                    token=token,
                    organization_id=organization_id,
                    order_id=iiko_order_id,
                )
            except IikoClientError as exc:
                logger.warning("Could not confirm iiko delivery order. order_id=%s error=%s", iiko_order_id, exc)
        return {
            "iiko_order_id": iiko_order_id,
            "correlation_id": str(response_payload.get("correlationId") or ""),
            "creation_status": creation_status,
        }

    async def _resolve_organization_id(self, *, token: str) -> str:
        if self.organization_id:
            return self.organization_id

        try:
            organizations = await self.client.get_organizations(token=token)
        except IikoClientError as exc:
            raise IikoOrderError(str(exc)) from exc

        if len(organizations) != 1:
            raise IikoOrderError("IIKO_ORGANIZATION_ID is required for order submission.")

        organization_id = organizations[0].get("id")
        if not organization_id:
            raise IikoOrderError("iiko did not return a valid organization id.")
        return str(organization_id)

    async def _resolve_order_type_id(self, *, token: str, checkout_type: str, organization_id: str) -> str:
        try:
            groups = await self.client.get_delivery_order_types(token=token, organization_ids=[organization_id])
        except IikoClientError as exc:
            raise IikoOrderError(str(exc)) from exc

        target_service_type = "DeliveryPickUp" if checkout_type == "pickup" else "DeliveryByCourier"
        for group in groups:
            if str(group.get("organizationId") or "") != organization_id:
                continue
            for item in group.get("items", []) or []:
                if item.get("isDeleted"):
                    continue
                if item.get("orderServiceType") == target_service_type and item.get("id"):
                    return str(item["id"])

        raise IikoOrderError(f"iiko order type for {checkout_type} was not found.")

    async def _build_payments(
        self,
        *,
        token: str,
        organization_id: str,
        payment_type: str,
        total_amount: int,
    ) -> list[dict[str, object]]:
        if payment_type != "cash":
            if not self.online_payment_type_id:
                logger.warning("Online iiko payment type is not configured. order will be sent without payments.")
                return []
            if total_amount <= 0:
                return []
            return [
                {
                    "paymentTypeKind": self.online_payment_type_kind,
                    "sum": float(total_amount),
                    "paymentTypeId": self.online_payment_type_id,
                    "isProcessedExternally": True,
                    "isFiscalizedExternally": True,
                    "isPrepay": True,
                }
            ]
        if total_amount <= 0:
            return []

        try:
            payment_types = await self.client.get_payment_types(token=token, organization_ids=[organization_id])
        except IikoClientError as exc:
            raise IikoOrderError(str(exc)) from exc

        for payment in payment_types:
            if payment.get("isDeleted"):
                continue
            if payment.get("paymentTypeKind") != "Cash":
                continue
            payment_type_id = payment.get("id")
            if not payment_type_id:
                continue
            return [
                {
                    "paymentTypeKind": "Cash",
                    "sum": float(total_amount),
                    "paymentTypeId": str(payment_type_id),
                    "isProcessedExternally": False,
                    "isFiscalizedExternally": False,
                    "isPrepay": False,
                }
            ]

        logger.warning("Cash payment type was not found in iiko. order will be sent without payments.")
        return []

    async def list_delivery_street_suggestions(self, *, query: str, limit: int = 10) -> list[dict[str, str]]:
        normalized_query = self._normalize_street_name(self._remove_delivery_city(query))
        if len(normalized_query) < 2:
            return []

        if not self.client.api_login:
            raise IikoOrderError("API_IIKO is not configured.")

        token = await self.client.get_access_token()
        organization_id = await self._resolve_organization_id(token=token)
        try:
            streets = await self._get_delivery_streets(token=token, organization_id=organization_id)
        except IikoClientError as exc:
            raise IikoOrderError(f"iiko не дал загрузить улицы доставки: {exc}") from exc

        suggestions: list[dict[str, str]] = []
        for street in streets:
            if street.get("isDeleted"):
                continue
            street_name = str(street.get("name") or "").strip()
            if not street_name:
                continue
            normalized_street = self._normalize_street_name(street_name)
            if normalized_query not in normalized_street:
                continue
            suggestions.append(
                {
                    "name": street_name,
                    "value": street_name,
                }
            )
            if len(suggestions) >= max(1, min(limit, 20)):
                break

        return suggestions

    def _build_delivery_point(
            self,
            *,
            street: str,
            house: str,
            flat: Optional[str],
            entrance: Optional[str],
    ) -> dict[str, object]:
        normalized_street = street.strip()
        normalized_house = house.strip()

        address: dict[str, object] = {
            "type": "city",
            "line1": (
                f"{DEFAULT_DELIVERY_CITY}, "
                f"ул. {normalized_street}, "
                f"дом {normalized_house}"
            ),
            "house": normalized_house,
        }

        if flat and flat.strip():
            address["flat"] = flat.strip()[:64]

        if entrance and entrance.strip():
            address["entrance"] = entrance.strip()[:64]

        return {
            "address": address,
        }

    async def _get_delivery_streets(
        self,
        *,
        token: str,
        organization_id: str,
        city_id: Optional[str] = None,
    ) -> list[dict[str, object]]:
        cached = _STREET_CACHE.get(organization_id)
        if cached is not None:
            return cached

        resolved_city_id = city_id or await self._resolve_delivery_city_id(
            token=token,
            organization_id=organization_id,
        )

        streets = await self.client.get_streets_by_city(
            token=token,
            organization_id=organization_id,
            city_id=resolved_city_id,
        )
        _STREET_CACHE[organization_id] = streets
        return streets

    async def _resolve_delivery_city_id(self, *, token: str, organization_id: str) -> str:
        cities = await self.client.get_cities(token=token, organization_ids=[organization_id])
        city_id = self._find_delivery_city_id(cities)
        if not city_id:
            raise IikoOrderError(f"iiko не нашел город {DEFAULT_DELIVERY_CITY}.")
        return city_id

    def _find_delivery_city_id(self, cities: list[dict[str, object]]) -> Optional[str]:
        for city in cities:
            if city.get("isDeleted"):
                continue
            if str(city.get("name") or "").strip().casefold() == DEFAULT_DELIVERY_CITY.casefold():
                city_id = city.get("id")
                return str(city_id) if city_id else None
        return None

    def _find_street_id(self, *, streets: list[dict[str, object]], street: str) -> Optional[str]:
        target = self._normalize_street_name(street)
        for item in streets:
            if item.get("isDeleted"):
                continue
            item_name = self._normalize_street_name(str(item.get("name") or ""))
            if item_name == target:
                street_id = item.get("id")
                return str(street_id) if street_id else None
        return None

    def _normalize_street_name(self, value: str) -> str:
        return _ADDRESS_PART_LABEL_RE.sub("", value).strip().casefold()

    def _remove_delivery_city(self, value: str) -> str:
        city_pattern = re.compile(
            rf"(?:^|,\s*)(?:г\.?|город)?\s*{re.escape(DEFAULT_DELIVERY_CITY)}(?:\s*,|$)",
            re.IGNORECASE,
        )
        return city_pattern.sub("", value).strip()

    def _to_user_message(self, *, error_code: object, error_message: str) -> str:
        if error_code == "TerminalGroupDisabled":
            return "iiko не принял заказ: группа терминалов отключена или не зарегистрирована."
        return f"iiko не принял заказ: {error_message}"

```

## 📄 `backend\orders\migrations.py`

```python
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

```

## 📄 `backend\orders\models.py`

```python
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.orders.statuses import ORDER_STATUS_PREPARING
from db import Base


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    checkout_type: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    delivery_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    delivery_street: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    delivery_house: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    delivery_flat: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    entrance: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    items_json: Mapped[str] = mapped_column(Text, nullable=False)
    items_count: Mapped[int] = mapped_column(Integer, nullable=False)
    cutlery_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    subtotal_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    bonus_spent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    bonus_awarded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, unique=True, index=True)
    iiko_order_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    iiko_correlation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    iiko_creation_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    branch_code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    iiko_terminal_group_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(64), nullable=False, default=ORDER_STATUS_PREPARING)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("UserModel")


class OrderDeliveryJobModel(Base):
    __tablename__ = "order_delivery_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True,
                                          index=True)
    job_type: Mapped[str] = mapped_column(String(32), nullable=False, default="send_to_iiko")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    order = relationship("OrderModel")

```

## 📄 `backend\orders\router.py`

```python
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from backend.auth.dependencies import require_admin_user, require_current_user
from backend.orders.availability import ensure_order_time_open
from backend.orders.depencises import get_iiko_order_gateway, get_order_service
from backend.orders.iiko import IikoOrderError, IikoOrderGateway
from backend.orders.schemas import (
    AdminOrdersPage,
    OrderCreate,
    OrderRead,
    OrderStatusUpdate,
    StreetSuggestionsRead,
    UserOrdersPage,
)
from backend.orders.service import OrderNotFoundError, OrderService, OrderValidationError
from backend.payment.depencises import get_yookassa_payment_service
from backend.payment.schemas import PaymentInitRead
from backend.payment.service import PaymentError, YooKassaPaymentService
from backend.rate_limit import client_ip, rate_limiter
from backend.user.depencises import get_user_service
from backend.user.schemas import UserRead
from backend.user.service import UserBonusError, UserService

router = APIRouter(prefix="/api/orders", tags=["orders"])
logger = logging.getLogger(__name__)


def _build_order_idempotency_key(*, request: Request, user_id: int, payload: OrderCreate) -> str:
    header_key = (request.headers.get("idempotency-key") or "").strip()
    if header_key:
        return f"client:{user_id}:{header_key[:96]}"

    bucket = int(time.time() // 300)
    raw = json.dumps(payload.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"auto:{user_id}:{bucket}:{digest}"


@router.post("", response_model=PaymentInitRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    request: Request,
    user: UserRead = Depends(require_current_user),
    order_service: OrderService = Depends(get_order_service),
    payment_service: YooKassaPaymentService = Depends(get_yookassa_payment_service),
    user_service: UserService = Depends(get_user_service),
) -> PaymentInitRead:
    ensure_order_time_open()
    await rate_limiter.check(key=f"orders-create:ip:{client_ip(request)}", limit=30, window_seconds=60)
    await rate_limiter.check(key=f"orders-create:user:{user.id}", limit=10, window_seconds=60)
    logger.info(
        "Received order payload. checkout_type=%s branch_code=%s delivery_street=%s delivery_house=%s delivery_flat=%s entrance=%s comment=%s",
        payload.checkout_type,
        payload.branch_code,
        payload.delivery_street,
        payload.delivery_house,
        payload.delivery_flat,
        payload.entrance,
        payload.comment,
    )
    try:
        prepared_order = await order_service.prepare_order(
            payload=payload,
            available_bonus_balance=user.bonus_balance,
        )
        if prepared_order.total_amount <= 0:
            idempotency_key = _build_order_idempotency_key(
                request=request,
                user_id=user.id,
                payload=prepared_order.payload,
            )
            existing_order = await order_service.get_by_idempotency_key(idempotency_key)
            if existing_order is not None:
                await order_service.enqueue_iiko_submission_if_needed(order_id=existing_order.id)
                existing_status = "created"
                if existing_order.iiko_creation_status == "LocalPending":
                    existing_status = "processing"
                elif existing_order.iiko_creation_status == "Failed":
                    existing_status = "failed"
                return PaymentInitRead(
                    status=existing_status,
                    order_id=existing_order.id,
                    total_amount=existing_order.total_amount,
                    bonus_spent=existing_order.bonus_spent,
                    bonus_awarded=existing_order.bonus_awarded,
                    bonus_balance=user.bonus_balance,
                )

            claimed_order = await order_service.claim_order_creation(
                user_id=user.id,
                payload=prepared_order.payload,
                available_bonus_balance=user.bonus_balance,
                idempotency_key=idempotency_key,
            )
            if not claimed_order.is_owner or claimed_order.prepared_order is None:
                existing_order = claimed_order.order
                await order_service.enqueue_iiko_submission_if_needed(order_id=existing_order.id)
                existing_status = "created"
                if existing_order.iiko_creation_status == "LocalPending":
                    existing_status = "processing"
                elif existing_order.iiko_creation_status == "Failed":
                    existing_status = "failed"
                return PaymentInitRead(
                    status=existing_status,
                    order_id=existing_order.id,
                    total_amount=existing_order.total_amount,
                    bonus_spent=existing_order.bonus_spent,
                    bonus_awarded=existing_order.bonus_awarded,
                    bonus_balance=user.bonus_balance,
                )

            updated_user = user
            spent_bonus = prepared_order.payload.bonus_spent
            if spent_bonus:
                updated_user = await user_service.spend_bonus(user_id=user.id, bonus_amount=spent_bonus)
            await order_service.enqueue_iiko_submission_if_needed(order_id=claimed_order.order.id)
            order = claimed_order.order
            if order.bonus_awarded:
                updated_user = await user_service.add_bonus(user_id=user.id, bonus_delta=order.bonus_awarded)
            return PaymentInitRead(
                status="created",
                order_id=order.id,
                total_amount=order.total_amount,
                bonus_spent=order.bonus_spent,
                bonus_awarded=order.bonus_awarded,
                bonus_balance=updated_user.bonus_balance,
            )

        payment = await payment_service.create_payment(
            user_id=user.id,
            user_phone=user.phone,
            payload=prepared_order.payload,
            amount=prepared_order.total_amount,
        )
        payment.total_amount = prepared_order.total_amount
        payment.bonus_spent = prepared_order.payload.bonus_spent
        return payment
    except OrderValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except UserBonusError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PaymentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/my", response_model=UserOrdersPage)
async def list_my_orders(
    user: UserRead = Depends(require_current_user),
    order_service: OrderService = Depends(get_order_service),
) -> UserOrdersPage:
    return await order_service.list_user_orders(user.id)


@router.get("/admin", response_model=AdminOrdersPage)
async def list_admin_orders(
    limit: int = Query(default=30, ge=1, le=100),
    phone: Optional[str] = Query(default=None, min_length=6, max_length=32),
    admin_user: UserRead = Depends(require_admin_user),
    order_service: OrderService = Depends(get_order_service),
) -> AdminOrdersPage:
    _ = admin_user
    return await order_service.list_admin_orders(limit=limit, phone=phone)


@router.get("/address/streets", response_model=StreetSuggestionsRead)
async def list_address_streets(
    q: str = Query(default="", max_length=80),
    user: UserRead = Depends(require_current_user),
    iiko_order_gateway: IikoOrderGateway = Depends(get_iiko_order_gateway),
) -> StreetSuggestionsRead:
    _ = user
    try:
        return StreetSuggestionsRead(
            items=await iiko_order_gateway.list_delivery_street_suggestions(query=q, limit=10),
        )
    except IikoOrderError as exc:
        logger.warning("Could not load iiko street suggestions: %s", exc)
        return StreetSuggestionsRead(items=[])


@router.patch("/{order_id}/status", response_model=OrderRead)
async def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    admin_user: UserRead = Depends(require_admin_user),
    order_service: OrderService = Depends(get_order_service),
) -> OrderRead:
    _ = admin_user
    try:
        return await order_service.update_order_status(order_id=order_id, status=payload.status)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.") from exc
    except OrderValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

```

## 📄 `backend\orders\schemas.py`

```python
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from backend.orders.branches import BranchCode
from backend.orders.statuses import get_allowed_statuses


class OrderItemPayload(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=255)
    price: int = Field(..., ge=0, le=1_000_000)
    quantity: int = Field(..., ge=1, le=100)

    @field_validator("id", mode="before")
    @classmethod
    def normalize_id(cls, value: Any) -> str:
        return str(value)


class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=120)
    customer_phone: str = Field(..., min_length=6, max_length=32)
    checkout_type: str = Field(..., min_length=4, max_length=20)
    payment_type: str = Field(..., min_length=4, max_length=20)
    delivery_address: Optional[str] = Field(default=None, max_length=255)
    delivery_street: Optional[str] = Field(default=None, max_length=255)
    delivery_house: Optional[str] = Field(default=None, max_length=64)
    delivery_flat: Optional[str] = Field(default=None, max_length=64)
    entrance: Optional[str] = Field(default=None, max_length=64)
    comment: Optional[str] = Field(default=None, max_length=255)
    cutlery_count: int = Field(default=0, ge=0, le=50)
    bonus_spent: int = Field(default=0, ge=0, le=1_000_000)
    items: list[OrderItemPayload] = Field(..., min_length=1, max_length=100)
    branch_code: BranchCode

    @field_validator("checkout_type")
    @classmethod
    def validate_checkout_type(cls, value: str) -> str:
        if value not in {"pickup", "delivery"}:
            raise ValueError("Некорректный тип заказа.")
        return value

    @field_validator("payment_type")
    @classmethod
    def validate_payment_type(cls, value: str) -> str:
        if value != "card":
            raise ValueError("Некорректный способ оплаты.")
        return value


class OrderRead(BaseModel):
    id: int
    user_id: int
    customer_name: str
    customer_phone: str
    checkout_type: str
    payment_type: str
    delivery_address: Optional[str]
    delivery_street: Optional[str]
    delivery_house: Optional[str]
    delivery_flat: Optional[str]
    entrance: Optional[str]
    comment: Optional[str]
    items: list[OrderItemPayload]
    items_count: int
    cutlery_count: int
    subtotal_amount: int
    bonus_spent: int
    total_amount: int
    bonus_awarded: int
    iiko_order_id: Optional[str] = None
    iiko_correlation_id: Optional[str] = None
    iiko_creation_status: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    branch_code: BranchCode
    iiko_terminal_group_id: str

class UserOrdersPage(BaseModel):
    items: list[OrderRead]


class OrderStatusUpdate(BaseModel):
    status: str = Field(..., min_length=3, max_length=64)


class OrderStatusOptionsRead(BaseModel):
    checkout_type: str
    statuses: list[str]


class AdminOrdersPage(BaseModel):
    items: list[OrderRead]
    status_options: list[OrderStatusOptionsRead]

    @classmethod
    def build(cls, *, items: list[OrderRead]) -> "AdminOrdersPage":
        options = [
            OrderStatusOptionsRead(checkout_type=checkout_type, statuses=list(get_allowed_statuses(checkout_type)))
            for checkout_type in ("pickup", "delivery")
        ]
        return cls(items=items, status_options=options)


class StreetSuggestionRead(BaseModel):
    name: str
    value: str


class StreetSuggestionsRead(BaseModel):
    items: list[StreetSuggestionRead]

```

## 📄 `backend\orders\service.py`

```python
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy.exc import IntegrityError

from backend.iiko_manager.client import IikoApiClient, IikoClientError
from backend.orders.branches import BranchCode, resolve_terminal_group_id
from backend.orders.crud import OrderRepository
from backend.orders.iiko import IikoOrderError, IikoOrderGateway, IikoOrderItem
from backend.orders.schemas import AdminOrdersPage, OrderCreate, OrderItemPayload, OrderRead, UserOrdersPage
from backend.orders.statuses import (
    ORDER_STATUS_CANCELLED,
    ORDER_STATUS_COOKED,
    ORDER_STATUS_DELIVERED,
    ORDER_STATUS_DELIVERY_SENT,
    ORDER_STATUS_PICKUP_DONE,
    ORDER_STATUS_PICKUP_READY,
    ORDER_STATUS_PREPARING,
    get_allowed_statuses,
)
from backend.redactor.crud import MenuItemRepository
logger = logging.getLogger(__name__)
BONUS_AWARD_PERCENT = 5


class OrderValidationError(Exception):
    pass


class OrderNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class NormalizedOrderItem:
    order_item: OrderItemPayload
    iiko_product_id: str


@dataclass(frozen=True)
class PreparedOrder:
    payload: OrderCreate
    normalized_items: list[NormalizedOrderItem]
    subtotal_amount: int
    total_amount: int
    branch_code: BranchCode
    terminal_group_id: str


@dataclass(frozen=True)
class OrderStatusSyncResult:
    checked: int = 0
    updated: int = 0


@dataclass(frozen=True)
class IikoOrderRetryResult:
    checked: int = 0
    submitted: int = 0
    failed: int = 0
    enqueued: int = 0


@dataclass(frozen=True)
class ClaimedOrder:
    order: OrderRead
    prepared_order: Optional[PreparedOrder]
    is_owner: bool


@dataclass
class IikoOrderStatusSyncService:
    repository: OrderRepository
    client: IikoApiClient
    organization_id: Optional[str]
    limit: int = 50

    async def sync(self) -> OrderStatusSyncResult:
        if not self.client.api_login:
            logger.info("Skipping iiko order status sync because API_IIKO is not configured.")
            return OrderStatusSyncResult()

        active_orders = await self.repository.list_active_iiko_orders(limit=self.limit)
        orders_by_iiko_id = {
            str(order.iiko_order_id): order
            for order in active_orders
            if order.iiko_order_id
        }
        if not orders_by_iiko_id:
            return OrderStatusSyncResult()

        token = await self.client.get_access_token()
        organization_id = await self._resolve_organization_id(token=token)
        iiko_orders = await self.client.get_delivery_orders_by_ids(
            token=token,
            organization_id=organization_id,
            order_ids=list(orders_by_iiko_id),
        )

        updated = 0
        for iiko_order in iiko_orders:
            iiko_order_id = self._extract_iiko_order_id(iiko_order)
            if not iiko_order_id:
                continue

            local_order = orders_by_iiko_id.get(iiko_order_id)
            if local_order is None:
                continue

            iiko_status = self._extract_iiko_status(iiko_order)
            if (iiko_status or "").strip().lower() == "error":
                pos_order = await self._load_pos_order(
                    token=token,
                    organization_id=organization_id,
                    iiko_order=iiko_order,
                )
                pos_status = self._extract_iiko_status(pos_order) if pos_order else None
                next_status = self._map_iiko_status(iiko_status=pos_status, checkout_type=local_order.checkout_type)
                if next_status:
                    if next_status != local_order.status:
                        await self.repository.update_status_by_iiko_order_id(
                            iiko_order_id=iiko_order_id,
                            status=next_status,
                        )
                    await self.repository.update_iiko_result(
                        order_id=local_order.id,
                        iiko_order_id=local_order.iiko_order_id,
                        iiko_correlation_id=local_order.iiko_correlation_id,
                        iiko_creation_status="Success",
                    )
                    updated += 1
                    logger.info(
                        "Synced order status from iiko pos order. order_id=%s iiko_order_id=%s pos_status=%s status=%s",
                        local_order.id,
                        iiko_order_id,
                        pos_status,
                        next_status,
                    )
                    continue
                logger.warning(
                    "iiko order is in Error status. order_id=%s iiko_order_id=%s payload=%s",
                    local_order.id,
                    iiko_order_id,
                    json.dumps(iiko_order, ensure_ascii=False, default=str)[:4000],
                )
                if self._extract_iiko_pos_order_id(iiko_order):
                    if local_order.iiko_creation_status == "Failed":
                        await self.repository.update_iiko_result(
                            order_id=local_order.id,
                            iiko_order_id=local_order.iiko_order_id,
                            iiko_correlation_id=local_order.iiko_correlation_id,
                            iiko_creation_status="InProgress",
                        )
                        updated += 1
                    continue
                await self.repository.update_iiko_result(
                    order_id=local_order.id,
                    iiko_order_id=local_order.iiko_order_id,
                    iiko_correlation_id=local_order.iiko_correlation_id,
                    iiko_creation_status="Failed",
                )
                updated += 1
                continue
            next_status = self._map_iiko_status(iiko_status=iiko_status, checkout_type=local_order.checkout_type)
            if not next_status or next_status == local_order.status:
                if next_status and local_order.iiko_creation_status == "Failed":
                    await self.repository.update_iiko_result(
                        order_id=local_order.id,
                        iiko_order_id=local_order.iiko_order_id,
                        iiko_correlation_id=local_order.iiko_correlation_id,
                        iiko_creation_status="Success",
                    )
                    updated += 1
                continue

            await self.repository.update_status_by_iiko_order_id(
                iiko_order_id=iiko_order_id,
                status=next_status,
            )
            if local_order.iiko_creation_status == "Failed":
                await self.repository.update_iiko_result(
                    order_id=local_order.id,
                    iiko_order_id=local_order.iiko_order_id,
                    iiko_correlation_id=local_order.iiko_correlation_id,
                    iiko_creation_status="Success",
                )
            updated += 1
            logger.info(
                "Synced order status from iiko. order_id=%s iiko_order_id=%s iiko_status=%s status=%s",
                local_order.id,
                iiko_order_id,
                iiko_status,
                next_status,
            )

        return OrderStatusSyncResult(checked=len(orders_by_iiko_id), updated=updated)

    async def _load_pos_order(
        self,
        *,
        token: str,
        organization_id: str,
        iiko_order: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        pos_id = self._extract_iiko_pos_order_id(iiko_order)
        if not pos_id:
            return None
        try:
            pos_orders = await self.client.get_delivery_orders_by_pos_ids(
                token=token,
                organization_id=organization_id,
                pos_order_ids=[pos_id],
            )
        except IikoClientError as exc:
            logger.info("Could not load iiko order by posId. pos_id=%s error=%s", pos_id, exc)
            return None
        if not pos_orders:
            logger.info("iiko order by posId was not found yet. pos_id=%s", pos_id)
            return None
        return pos_orders[0] if pos_orders else None

    async def _resolve_organization_id(self, *, token: str) -> str:
        if self.organization_id:
            return self.organization_id

        try:
            organizations = await self.client.get_organizations(token=token)
        except IikoClientError as exc:
            raise OrderValidationError(str(exc)) from exc

        if len(organizations) != 1:
            raise OrderValidationError("IIKO_ORGANIZATION_ID is required for order status sync.")

        organization_id = organizations[0].get("id")
        if not organization_id:
            raise OrderValidationError("iiko did not return a valid organization id.")
        return str(organization_id)

    def _extract_iiko_order_id(self, payload: dict[str, Any]) -> Optional[str]:
        for candidate in (
            payload.get("id"),
            payload.get("orderId"),
            (payload.get("order") or {}).get("id") if isinstance(payload.get("order"), dict) else None,
            (payload.get("orderInfo") or {}).get("id") if isinstance(payload.get("orderInfo"), dict) else None,
        ):
            if candidate:
                return str(candidate)
        return None

    def _extract_iiko_pos_order_id(self, payload: dict[str, Any]) -> Optional[str]:
        for candidate in (
            payload.get("posId"),
            payload.get("posOrderId"),
            (payload.get("order") or {}).get("posId") if isinstance(payload.get("order"), dict) else None,
            (payload.get("orderInfo") or {}).get("posId") if isinstance(payload.get("orderInfo"), dict) else None,
        ):
            if candidate:
                return str(candidate)
        return None

    def _extract_iiko_status(self, payload: dict[str, Any]) -> Optional[str]:
        candidates: list[Any] = [
            payload.get("status"),
            payload.get("deliveryStatus"),
        ]
        for key in ("order", "orderInfo"):
            nested = payload.get(key)
            if isinstance(nested, dict):
                candidates.extend(
                    [
                        nested.get("status"),
                        nested.get("deliveryStatus"),
                    ]
                )
        candidates.append(payload.get("creationStatus"))
        for key in ("order", "orderInfo"):
            nested = payload.get(key)
            if isinstance(nested, dict):
                candidates.append(nested.get("creationStatus"))

        for candidate in candidates:
            if candidate:
                return str(candidate)
        return None

    def _map_iiko_status(self, *, iiko_status: Optional[str], checkout_type: str) -> Optional[str]:
        if not iiko_status:
            return None

        normalized = iiko_status.strip().lower()
        if normalized in {"cancelled", "canceled", "deleted"}:
            return ORDER_STATUS_CANCELLED
        if normalized in {"delivered"}:
            return ORDER_STATUS_DELIVERED if checkout_type == "delivery" else ORDER_STATUS_PICKUP_DONE
        if normalized in {"closed"}:
            return ORDER_STATUS_PICKUP_DONE if checkout_type == "pickup" else ORDER_STATUS_DELIVERED
        if normalized in {"onway", "on_way", "on way"}:
            return ORDER_STATUS_DELIVERY_SENT if checkout_type == "delivery" else ORDER_STATUS_PICKUP_READY
        if normalized in {"cookingcompleted", "cooking_completed", "cooking completed", "ready", "waiting"}:
            return ORDER_STATUS_PICKUP_READY if checkout_type == "pickup" else ORDER_STATUS_COOKED
        if normalized in {
            "success",
            "inprogress",
            "in_progress",
            "unconfirmed",
            "waitcooking",
            "wait_cooking",
            "readyforcooking",
            "ready_for_cooking",
            "cookingstarted",
            "cooking_started",
            "new",
        }:
            return ORDER_STATUS_PREPARING

        logger.info("Unknown iiko order status received. iiko_status=%s", iiko_status)
        return None


@dataclass
class OrderService:
    repository: OrderRepository
    menu_item_repository: MenuItemRepository
    iiko_order_gateway: IikoOrderGateway

    def _build_delivery_address_text(self, *, street: str, house: str, flat: Optional[str]) -> str:
        parts = [street.strip(), house.strip()]
        if flat and flat.strip():
            parts.append(f"кв. {flat.strip()}")
        return ", ".join(part for part in parts if part)

    def _calculate_bonus_awarded(self, total_amount: int) -> int:
        return max(0, total_amount * BONUS_AWARD_PERCENT // 100)

    async def claim_order_creation(
        self,
        *,
        user_id: int,
        payload: OrderCreate,
        available_bonus_balance: int,
        idempotency_key: str,
    ) -> ClaimedOrder:
        normalized_idempotency_key = idempotency_key.strip()[:128]
        if not normalized_idempotency_key:
            raise OrderValidationError("Order idempotency key is required.")

        existing_order = await self.repository.get_by_idempotency_key(normalized_idempotency_key)
        if existing_order is not None:
            return ClaimedOrder(
                order=self._to_read(existing_order),
                prepared_order=None,
                is_owner=False,
            )

        prepared_order = await self.prepare_order(
            payload=payload,
            available_bonus_balance=available_bonus_balance,
        )
        bonus_awarded = self._calculate_bonus_awarded(prepared_order.total_amount)
        try:
            local_order = await self.repository.create(
                user_id=user_id,
                payload=prepared_order.payload,
                subtotal_amount=prepared_order.subtotal_amount,
                bonus_spent=prepared_order.payload.bonus_spent,
                total_amount=prepared_order.total_amount,
                bonus_awarded=bonus_awarded,
                idempotency_key=normalized_idempotency_key,
                iiko_creation_status="LocalPending",
                branch_code=prepared_order.branch_code.value,
                iiko_terminal_group_id=prepared_order.terminal_group_id,
            )
        except IntegrityError:
            existing_order = await self.repository.get_by_idempotency_key(normalized_idempotency_key)
            if existing_order is not None:
                return ClaimedOrder(
                    order=self._to_read(existing_order),
                    prepared_order=None,
                    is_owner=False,
                )
            raise

        return ClaimedOrder(
            order=self._to_read(local_order),
            prepared_order=prepared_order,
            is_owner=True,
        )

    async def submit_claimed_order(self, *, order_id: int, prepared_order: PreparedOrder) -> OrderRead:
        claimed_order = await self.repository.claim_iiko_submission(order_id=order_id)
        if claimed_order is None:
            order = await self.repository.get_by_id(order_id)
            if order is None:
                raise OrderNotFoundError(order_id)
            return self._to_read(order)

        try:
            iiko_result = await self.iiko_order_gateway.submit_order(
                payload=prepared_order.payload,
                items=[
                    IikoOrderItem(
                        product_id=item.iiko_product_id,
                        title=item.order_item.title,
                        price=item.order_item.price,
                        quantity=item.order_item.quantity,
                    )
                    for item in prepared_order.normalized_items
                ],
                total_amount=prepared_order.total_amount,
                terminal_group_id=prepared_order.terminal_group_id,
                external_number=self._build_iiko_external_number(order_id),
            )
        except IikoOrderError as exc:
            await self.repository.update_iiko_result(
                order_id=order_id,
                iiko_order_id=None,
                iiko_correlation_id=None,
                iiko_creation_status="Failed",
            )
            raise OrderValidationError(str(exc)) from exc

        order = await self.repository.update_iiko_result(
            order_id=order_id,
            iiko_order_id=iiko_result.get("iiko_order_id") or None,
            iiko_correlation_id=iiko_result.get("correlation_id") or None,
            iiko_creation_status=iiko_result.get("creation_status") or None,
        )
        if order is None:
            raise OrderNotFoundError(order_id)
        return self._to_read(order)

    async def retry_pending_iiko_submissions(
        self,
        *,
        limit: int = 20,
        created_after: Optional[datetime] = None,
    ) -> IikoOrderRetryResult:
        safe_limit = max(1, min(limit, 100))
        enqueued = await self.repository.enqueue_missing_paid_iiko_submission_jobs(
            limit=safe_limit,
            created_after=created_after,
        )
        jobs = await self.repository.claim_due_iiko_submission_jobs(
            limit=safe_limit,
            created_after=created_after,
        )
        submitted = 0
        failed = 0

        for job in jobs:
            try:
                order = await self.submit_existing_order_to_iiko(order_id=job.order_id)
            except OrderValidationError as exc:
                failed += 1
                await self.repository.mark_iiko_submission_job_failed(
                    job_id=job.id,
                    error_message=str(exc),
                    next_run_at=self._next_iiko_retry_at(job.attempts),
                )
                logger.exception("Could not retry iiko order submission. order_id=%s job_id=%s", job.order_id, job.id)
                continue
            if order.iiko_order_id:
                await self.repository.mark_iiko_submission_job_done(job_id=job.id)
            else:
                failed += 1
                await self.repository.mark_iiko_submission_job_failed(
                    job_id=job.id,
                    error_message="iiko submission is still processing.",
                    next_run_at=self._next_iiko_retry_at(job.attempts),
                )
                continue
            submitted += 1

        return IikoOrderRetryResult(checked=len(jobs), submitted=submitted, failed=failed, enqueued=enqueued)

    async def submit_existing_order_to_iiko(self, *, order_id: int) -> OrderRead:
        order = await self.repository.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        if order.iiko_order_id and order.iiko_creation_status not in {"Failed", "LocalPending"}:
            return self._to_read(order)

        prepared_order = await self._prepare_existing_order_for_iiko(order)
        return await self.submit_claimed_order(order_id=order.id, prepared_order=prepared_order)

    async def enqueue_iiko_submission_if_needed(self, *, order_id: int) -> None:
        order = await self.repository.get_by_id(order_id)
        if order is None or order.iiko_order_id:
            return
        if order.iiko_creation_status not in {"LocalPending", "Failed"}:
            return
        await self.repository.enqueue_iiko_submission_job(order_id=order.id)

    async def prepare_order(self, *, payload: OrderCreate, available_bonus_balance: int) -> PreparedOrder:
        normalized_items = await self._normalize_order_items(payload)
        subtotal_amount = sum(item.order_item.price * item.order_item.quantity for item in normalized_items)
        if subtotal_amount <= 0:
            raise OrderValidationError("Сумма заказа должна быть больше нуля.")
        if payload.checkout_type == "delivery" and not (payload.delivery_street or "").strip():
            raise OrderValidationError("Укажите улицу доставки.")
        if payload.checkout_type == "delivery" and not (payload.delivery_house or "").strip():
            raise OrderValidationError("Укажите номер дома.")
        if payload.bonus_spent > available_bonus_balance:
            raise OrderValidationError("Недостаточно бонусов для списания.")
        if payload.bonus_spent > subtotal_amount:
            raise OrderValidationError("Нельзя списать бонусов больше суммы заказа.")

        terminal_group_id = resolve_terminal_group_id(payload.branch_code)
        payload_updates: dict[str, object] = {"items": [item.order_item for item in normalized_items]}
        if payload.checkout_type == "delivery":
            payload_updates["delivery_address"] = self._build_delivery_address_text(
                street=payload.delivery_street or "",
                house=payload.delivery_house or "",
                flat=payload.delivery_flat,
            )
        else:
            payload_updates.update(
                {
                    "delivery_address": None,
                    "delivery_street": None,
                    "delivery_house": None,
                    "delivery_flat": None,
                    "entrance": None,
                }
            )
        normalized_payload = payload.model_copy(update=payload_updates)
        total_amount = subtotal_amount - normalized_payload.bonus_spent
        return PreparedOrder(
            payload=normalized_payload,
            normalized_items=normalized_items,
            subtotal_amount=subtotal_amount,
            total_amount=total_amount,
            branch_code=normalized_payload.branch_code,
            terminal_group_id=terminal_group_id,
        )

    async def create_order(
        self,
        *,
        user_id: int,
        payload: OrderCreate,
        available_bonus_balance: int,
        idempotency_key: Optional[str] = None,
    ) -> OrderRead:
        normalized_idempotency_key = (idempotency_key or "").strip()[:128] or None
        if normalized_idempotency_key:
            existing_order = await self.repository.get_by_idempotency_key(normalized_idempotency_key)
            if existing_order is not None:
                return self._to_read(existing_order)

        prepared_order = await self.prepare_order(
            payload=payload,
            available_bonus_balance=available_bonus_balance,
        )

        bonus_awarded = self._calculate_bonus_awarded(prepared_order.total_amount)
        try:
            local_order = await self.repository.create(
                user_id=user_id,
                payload=prepared_order.payload,
                subtotal_amount=prepared_order.subtotal_amount,
                bonus_spent=prepared_order.payload.bonus_spent,
                total_amount=prepared_order.total_amount,
                bonus_awarded=bonus_awarded,
                idempotency_key=normalized_idempotency_key,
                iiko_creation_status="LocalPending",
                branch_code=prepared_order.branch_code.value,
                iiko_terminal_group_id=prepared_order.terminal_group_id,
            )
        except IntegrityError:
            if normalized_idempotency_key:
                existing_order = await self.repository.get_by_idempotency_key(normalized_idempotency_key)
                if existing_order is not None:
                    await self.enqueue_iiko_submission_if_needed(order_id=existing_order.id)
                    return self._to_read(existing_order)
            raise

        await self.repository.enqueue_iiko_submission_job(order_id=local_order.id)
        return self._to_read(local_order)

    def _build_iiko_external_number(self, order_id: int) -> str:
        return f"zamzam-order-{order_id}"

    def _next_iiko_retry_at(self, attempts: int) -> datetime:
        delay_seconds = min(15 * 60, 30 * (2 ** max(0, attempts - 1)))
        return datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)

    async def list_user_orders(self, user_id: int) -> UserOrdersPage:
        orders = await self.repository.list_by_user(user_id)
        return UserOrdersPage(items=[self._to_read(order) for order in orders])

    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[OrderRead]:
        normalized_idempotency_key = idempotency_key.strip()[:128]
        if not normalized_idempotency_key:
            return None
        order = await self.repository.get_by_idempotency_key(normalized_idempotency_key)
        return self._to_read(order) if order is not None else None

    async def get_latest_status(self, user_id: int) -> Optional[str]:
        latest_order = await self.repository.get_latest_active_by_user(user_id)
        if latest_order is None:
            latest_order = await self.repository.get_latest_by_user(user_id)
        return latest_order.status if latest_order else None

    async def count_active_orders(self, user_id: int) -> int:
        return await self.repository.count_active_by_user(user_id)

    async def list_admin_orders(self, *, limit: int = 30, phone: Optional[str] = None) -> AdminOrdersPage:
        safe_limit = max(1, min(limit, 100))
        normalized_phone = (phone or "").strip() or None
        orders = await self.repository.list_recent(limit=safe_limit, phone=normalized_phone)
        return AdminOrdersPage.build(items=[self._to_read(order) for order in orders])

    async def update_order_status(self, *, order_id: int, status: str) -> OrderRead:
        order = await self.repository.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)

        next_status = status.strip()
        if next_status not in get_allowed_statuses(order.checkout_type):
            raise OrderValidationError("Некорректный статус для этого типа заказа.")

        updated_order = await self.repository.update_status(order_id=order_id, status=next_status)
        if updated_order is None:
            raise OrderNotFoundError(order_id)

        return self._to_read(updated_order)

    def _to_read(self, order) -> OrderRead:
        return OrderRead(
            id=order.id,
            user_id=order.user_id,
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            checkout_type=order.checkout_type,
            payment_type=order.payment_type,
            delivery_address=order.delivery_address,
            delivery_street=order.delivery_street,
            delivery_house=order.delivery_house,
            delivery_flat=order.delivery_flat,
            entrance=order.entrance,
            comment=order.comment,
            items=json.loads(order.items_json),
            items_count=order.items_count,
            cutlery_count=order.cutlery_count,
            subtotal_amount=order.subtotal_amount,
            bonus_spent=order.bonus_spent,
            total_amount=order.total_amount,
            bonus_awarded=order.bonus_awarded,
            iiko_order_id=order.iiko_order_id,
            iiko_correlation_id=order.iiko_correlation_id,
            iiko_creation_status=order.iiko_creation_status,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at,
            branch_code=BranchCode(order.branch_code),
            iiko_terminal_group_id=order.iiko_terminal_group_id,
        )

    async def _normalize_order_items(self, payload: OrderCreate) -> list[NormalizedOrderItem]:
        ordered_ids: list[int] = []
        quantities_by_id: dict[int, int] = {}
        for item in payload.items:
            try:
                item_id = int(item.id)
            except (TypeError, ValueError) as exc:
                raise OrderValidationError("Некорректный идентификатор позиции в заказе.") from exc
            if item_id not in quantities_by_id:
                ordered_ids.append(item_id)
                quantities_by_id[item_id] = 0
            quantities_by_id[item_id] += item.quantity

        menu_items = await self.menu_item_repository.get_many_by_ids(ordered_ids)
        menu_items_by_id = {item.id: item for item in menu_items}
        if len(menu_items_by_id) != len(ordered_ids):
            raise OrderValidationError("Одна или несколько позиций заказа больше недоступны.")

        normalized_items: list[NormalizedOrderItem] = []
        for item_id in ordered_ids:
            menu_item = menu_items_by_id[item_id]
            if not menu_item.is_active or not menu_item.is_published:
                raise OrderValidationError(f"Позиция «{menu_item.title}» сейчас недоступна для заказа.")
            if not menu_item.iiko_product_id:
                raise OrderValidationError(f"Позиция «{menu_item.title}» не связана с товаром iiko.")

            normalized_items.append(
                NormalizedOrderItem(
                    order_item=OrderItemPayload(
                        id=str(menu_item.id),
                        title=menu_item.site_title or menu_item.title,
                        price=int(menu_item.price),
                        quantity=quantities_by_id[item_id],
                    ),
                    iiko_product_id=str(menu_item.iiko_product_id),
                )
            )

        return normalized_items

    async def _prepare_existing_order_for_iiko(self, order) -> PreparedOrder:
        if order.checkout_type == "delivery":
            if not (order.delivery_street or "").strip() or not (order.delivery_house or "").strip():
                raise OrderValidationError("У заказа доставки не заполнены улица и дом для отправки в iiko.")

        order_items = [OrderItemPayload.model_validate(item) for item in json.loads(order.items_json)]
        ordered_ids: list[int] = []
        for item in order_items:
            try:
                item_id = int(item.id)
            except (TypeError, ValueError) as exc:
                raise OrderValidationError("Order contains an invalid menu item id.") from exc
            ordered_ids.append(item_id)

        menu_items = await self.menu_item_repository.get_many_by_ids(ordered_ids)
        menu_items_by_id = {item.id: item for item in menu_items}
        normalized_items: list[NormalizedOrderItem] = []
        for item in order_items:
            item_id = int(item.id)
            menu_item = menu_items_by_id.get(item_id)
            if menu_item is None or not menu_item.iiko_product_id:
                raise OrderValidationError(f"Order item {item.id} is not linked to an iiko product.")
            normalized_items.append(
                NormalizedOrderItem(
                    order_item=item,
                    iiko_product_id=str(menu_item.iiko_product_id),
                )
            )

        payload = OrderCreate(
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            checkout_type=order.checkout_type,
            payment_type=order.payment_type,
            delivery_address=order.delivery_address,
            delivery_street=order.delivery_street,
            delivery_house=order.delivery_house,
            delivery_flat=order.delivery_flat,
            entrance=order.entrance,
            comment=order.comment,
            cutlery_count=order.cutlery_count,
            bonus_spent=order.bonus_spent,
            items=order_items,
            branch_code=BranchCode(order.branch_code),
        )
        return PreparedOrder(
            payload=payload,
            normalized_items=normalized_items,
            subtotal_amount=order.subtotal_amount,
            total_amount=order.total_amount,
            branch_code=BranchCode(order.branch_code),
            terminal_group_id=order.iiko_terminal_group_id,
        )

```

## 📄 `backend\orders\statuses.py`

```python
from __future__ import annotations

ORDER_STATUS_PREPARING = "Готовится"
ORDER_STATUS_COOKED = "Приготовлен"
ORDER_STATUS_DELIVERY_SENT = "Заказ отправлен"
ORDER_STATUS_DELIVERED = "Доставлен"
ORDER_STATUS_PICKUP_READY = "Готов к выдаче"
ORDER_STATUS_PICKUP_DONE = "Выдан"
ORDER_STATUS_CANCELLED = "Отменен"

ORDER_STATUSES_BY_CHECKOUT_TYPE: dict[str, tuple[str, ...]] = {
    "delivery": (
        ORDER_STATUS_PREPARING,
        ORDER_STATUS_COOKED,
        ORDER_STATUS_DELIVERY_SENT,
        ORDER_STATUS_DELIVERED,
        ORDER_STATUS_CANCELLED,
    ),
    "pickup": (
        ORDER_STATUS_PREPARING,
        ORDER_STATUS_PICKUP_READY,
        ORDER_STATUS_PICKUP_DONE,
        ORDER_STATUS_CANCELLED,
    ),
}

ACTIVE_ORDER_STATUSES = {
    ORDER_STATUS_PREPARING,
    ORDER_STATUS_COOKED,
    ORDER_STATUS_DELIVERY_SENT,
    ORDER_STATUS_PICKUP_READY,
}


def get_allowed_statuses(checkout_type: str) -> tuple[str, ...]:
    return ORDER_STATUSES_BY_CHECKOUT_TYPE.get(checkout_type, (ORDER_STATUS_PREPARING,))

```

## 📁 `backend\payment`

## 📄 `backend\payment\__init__.py`

```python
from backend.payment.models import PendingPaymentModel

__all__ = ["PendingPaymentModel"]

```

## 📄 `backend\payment\crud.py`

```python
from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Optional

from sqlalchemy import or_, select, text, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.payment.models import PendingPaymentModel


class SqlAlchemyPendingPaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_pending(
        self,
        *,
        user_id: int,
        amount: int,
        payload_json: str,
    ) -> PendingPaymentModel:
        model = PendingPaymentModel(
            user_id=user_id,
            amount=amount,
            payload_json=payload_json,
            status="pending",
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return model

    async def attach_yookassa_payment(
        self,
        *,
        pending_payment_id: int,
        yookassa_payment_id: str,
        confirmation_url: str,
        status: str,
    ) -> Optional[PendingPaymentModel]:
        stmt = (
            update(PendingPaymentModel)
            .where(PendingPaymentModel.id == pending_payment_id)
            .values(
                yookassa_payment_id=yookassa_payment_id,
                confirmation_url=confirmation_url,
                status=status,
                updated_at=func.now(),
            )
            .returning(PendingPaymentModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            await self._session.rollback()
            return None
        await self._session.commit()
        return model

    async def get_by_yookassa_payment_id(self, payment_id: str) -> Optional[PendingPaymentModel]:
        stmt = select(PendingPaymentModel).where(PendingPaymentModel.yookassa_payment_id == payment_id)
        return await self._session.scalar(stmt)

    async def list_unfinished_yookassa_payments(
        self,
        *,
        limit: int,
        created_after: Optional[datetime] = None,
    ) -> Sequence[PendingPaymentModel]:
        stmt = select(PendingPaymentModel).where(
            PendingPaymentModel.yookassa_payment_id.is_not(None),
            PendingPaymentModel.order_id.is_(None),
            PendingPaymentModel.status.in_(("pending", "processing", "order_failed")),
        )
        if created_after is not None:
            stmt = stmt.where(PendingPaymentModel.created_at >= created_after)
        stmt = stmt.order_by(PendingPaymentModel.updated_at.asc(), PendingPaymentModel.id.asc()).limit(max(1, min(limit, 100)))
        return (await self._session.scalars(stmt)).all()

    async def claim_for_order_creation(
        self,
        *,
        pending_payment_id: int,
    ) -> Optional[PendingPaymentModel]:
        stmt = (
            update(PendingPaymentModel)
            .where(
                PendingPaymentModel.id == pending_payment_id,
                PendingPaymentModel.order_id.is_(None),
                or_(
                    PendingPaymentModel.status != "processing",
                    PendingPaymentModel.updated_at < func.now() - text("interval '2 minutes'"),
                ),
            )
            .values(status="processing", error_message=None, updated_at=func.now())
            .returning(PendingPaymentModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return model

    async def mark_order_created(
        self,
        *,
        pending_payment_id: int,
        order_id: int,
    ) -> Optional[PendingPaymentModel]:
        stmt = (
            update(PendingPaymentModel)
            .where(PendingPaymentModel.id == pending_payment_id)
            .values(status="succeeded", order_id=order_id, error_message=None, updated_at=func.now())
            .returning(PendingPaymentModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            await self._session.rollback()
            return None
        await self._session.commit()
        return model

    async def mark_failed(
        self,
        *,
        pending_payment_id: int,
        status: str,
        error_message: str,
    ) -> Optional[PendingPaymentModel]:
        stmt = (
            update(PendingPaymentModel)
            .where(PendingPaymentModel.id == pending_payment_id)
            .values(status=status, error_message=error_message, updated_at=func.now())
            .returning(PendingPaymentModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            await self._session.rollback()
            return None
        await self._session.commit()
        return model

```

## 📄 `backend\payment\depencises.py`

```python
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.payment.crud import SqlAlchemyPendingPaymentRepository
from backend.payment.service import YooKassaPaymentService
from db import get_db


def get_pending_payment_repository(
    session: AsyncSession = Depends(get_db),
) -> SqlAlchemyPendingPaymentRepository:
    return SqlAlchemyPendingPaymentRepository(session)


def get_yookassa_payment_service(
    repository: SqlAlchemyPendingPaymentRepository = Depends(get_pending_payment_repository),
) -> YooKassaPaymentService:
    return YooKassaPaymentService(repository=repository)

```

## 📄 `backend\payment\models.py`

```python
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class PendingPaymentModel(Base):
    __tablename__ = "pending_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    yookassa_payment_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    confirmation_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

```

## 📄 `backend\payment\router.py`

```python
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from backend.auth.dependencies import require_current_user
from backend.orders.depencises import get_order_service
from backend.orders.schemas import OrderCreate
from backend.orders.service import OrderService, OrderValidationError
from backend.payment.depencises import get_pending_payment_repository, get_yookassa_payment_service
from backend.payment.crud import SqlAlchemyPendingPaymentRepository
from backend.payment.service import PaymentError, YooKassaPaymentService
from backend.rate_limit import client_ip, rate_limiter
from backend.user.depencises import get_user_service
from backend.user.schemas import UserRead
from backend.user.service import UserBonusError, UserNotFoundError, UserService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payments", tags=["payments"])


async def _finalize_succeeded_payment(
    *,
    payment_id: str,
    payment_service: YooKassaPaymentService,
    pending_payment_repository: SqlAlchemyPendingPaymentRepository,
    order_service: OrderService,
    user_service: UserService,
) -> dict[str, object]:
    try:
        payment_payload = await payment_service.fetch_payment(payment_id)
    except PaymentError:
        logger.exception("Could not verify YooKassa payment. payment_id=%s", payment_id)
        raise

    if str(payment_payload.get("status") or "") != "succeeded":
        return {"ok": True, "status": str(payment_payload.get("status") or "")}

    pending_payment = await pending_payment_repository.get_by_yookassa_payment_id(payment_id)
    if pending_payment is None:
        logger.warning("YooKassa webhook payment was not found locally. payment_id=%s", payment_id)
        return {"ok": True}
    if pending_payment.order_id is not None:
        await order_service.enqueue_iiko_submission_if_needed(order_id=pending_payment.order_id)
        return {"ok": True, "order_id": pending_payment.order_id}

    claimed_payment = await pending_payment_repository.claim_for_order_creation(
        pending_payment_id=pending_payment.id,
    )
    if claimed_payment is None:
        pending_payment = await pending_payment_repository.get_by_yookassa_payment_id(payment_id)
        if pending_payment is not None and pending_payment.order_id is not None:
            return {"ok": True, "order_id": pending_payment.order_id}
        return {"ok": True, "status": "processing"}

    pending_payment = claimed_payment

    spent_bonus = 0
    bonus_was_spent = False
    try:
        order_payload = OrderCreate.model_validate(json.loads(pending_payment.payload_json))
        user = await user_service.get_user_by_id(pending_payment.user_id)
        claimed_order = await order_service.claim_order_creation(
            user_id=pending_payment.user_id,
            payload=order_payload,
            available_bonus_balance=user.bonus_balance,
            idempotency_key=f"payment:{payment_id}",
        )
        await order_service.enqueue_iiko_submission_if_needed(order_id=claimed_order.order.id)
        await pending_payment_repository.mark_order_created(
            pending_payment_id=pending_payment.id,
            order_id=claimed_order.order.id,
        )

        if not claimed_order.is_owner or claimed_order.prepared_order is None:
            return {"ok": True, "order_id": claimed_order.order.id}

        spent_bonus = order_payload.bonus_spent
        try:
            if spent_bonus:
                await user_service.spend_bonus(user_id=pending_payment.user_id, bonus_amount=spent_bonus)
                bonus_was_spent = True
            if claimed_order.order.bonus_awarded:
                await user_service.add_bonus(user_id=pending_payment.user_id, bonus_delta=claimed_order.order.bonus_awarded)
        except UserBonusError:
            logger.exception(
                "Could not apply bonuses after YooKassa payment. payment_id=%s order_id=%s",
                payment_id,
                claimed_order.order.id,
            )
            if bonus_was_spent:
                try:
                    await user_service.refund_bonus(user_id=pending_payment.user_id, bonus_amount=spent_bonus)
                except UserBonusError:
                    logger.exception(
                        "Could not refund bonuses after bonus application failure. payment_id=%s order_id=%s",
                        payment_id,
                        claimed_order.order.id,
                    )
        return {"ok": True, "order_id": claimed_order.order.id, "status": "iiko_queued"}
    except (OrderValidationError, UserBonusError, UserNotFoundError) as exc:
        logger.exception("Could not create order after YooKassa payment. payment_id=%s", payment_id)
        if bonus_was_spent:
            await user_service.refund_bonus(user_id=pending_payment.user_id, bonus_amount=spent_bonus)
        await pending_payment_repository.mark_failed(
            pending_payment_id=pending_payment.id,
            status="order_failed",
            error_message=str(exc),
        )
        raise


@router.post("/yookassa/webhook")
async def yookassa_webhook(
    request: Request,
    payment_service: YooKassaPaymentService = Depends(get_yookassa_payment_service),
    pending_payment_repository: SqlAlchemyPendingPaymentRepository = Depends(get_pending_payment_repository),
    order_service: OrderService = Depends(get_order_service),
    user_service: UserService = Depends(get_user_service),
) -> JSONResponse:
    await rate_limiter.check(key=f"payment-webhook:ip:{client_ip(request)}", limit=120, window_seconds=60)
    payload: dict[str, Any] = await request.json()
    event = str(payload.get("event") or "")
    payment_object = payload.get("object") or {}
    payment_id = str(payment_object.get("id") or "")
    payment_status = str(payment_object.get("status") or "")
    if payment_id:
        await rate_limiter.check(key=f"payment-webhook:payment:{payment_id}", limit=30, window_seconds=60)
    if event and event != "payment.succeeded":
        return JSONResponse({"ok": True})
    if not payment_id or payment_status != "succeeded":
        return JSONResponse({"ok": True})

    try:
        result = await _finalize_succeeded_payment(
            payment_id=payment_id,
            payment_service=payment_service,
            pending_payment_repository=pending_payment_repository,
            order_service=order_service,
            user_service=user_service,
        )
    except (PaymentError, OrderValidationError, UserBonusError, UserNotFoundError):
        return JSONResponse({"ok": False}, status_code=400)
    return JSONResponse(result)


@router.post("/{payment_id}/sync")
async def sync_payment(
    payment_id: str,
    request: Request,
    user: UserRead = Depends(require_current_user),
    payment_service: YooKassaPaymentService = Depends(get_yookassa_payment_service),
    pending_payment_repository: SqlAlchemyPendingPaymentRepository = Depends(get_pending_payment_repository),
    order_service: OrderService = Depends(get_order_service),
    user_service: UserService = Depends(get_user_service),
) -> JSONResponse:
    await rate_limiter.check(key=f"payment-sync:ip:{client_ip(request)}", limit=60, window_seconds=60)
    await rate_limiter.check(key=f"payment-sync:user:{user.id}", limit=30, window_seconds=60)
    await rate_limiter.check(key=f"payment-sync:payment:{payment_id}", limit=10, window_seconds=60)
    pending_payment = await pending_payment_repository.get_by_yookassa_payment_id(payment_id)
    if pending_payment is None or pending_payment.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")

    try:
        result = await _finalize_succeeded_payment(
            payment_id=payment_id,
            payment_service=payment_service,
            pending_payment_repository=pending_payment_repository,
            order_service=order_service,
            user_service=user_service,
        )
    except PaymentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except (OrderValidationError, UserBonusError, UserNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return JSONResponse(result)

```

## 📄 `backend\payment\schemas.py`

```python
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class PaymentInitRead(BaseModel):
    payment_id: str = ""
    confirmation_url: Optional[str] = None
    status: str
    order_id: Optional[int] = None
    total_amount: Optional[int] = None
    bonus_spent: Optional[int] = None
    bonus_awarded: Optional[int] = None
    bonus_balance: Optional[int] = None

```

## 📄 `backend\payment\service.py`

```python
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import uuid4

import httpx

from backend.orders.schemas import OrderCreate
from backend.payment.crud import SqlAlchemyPendingPaymentRepository
from backend.payment.schemas import PaymentInitRead
from config import WEBAPP_URL, YOOKASSA_SECRET_KEY, YOOKASSA_SHOP_ID, YOOKASSA_VAT_CODE


logger = logging.getLogger(__name__)


class PaymentError(Exception):
    pass


@dataclass
class YooKassaPaymentService:
    repository: SqlAlchemyPendingPaymentRepository

    def _ensure_configured(self) -> None:
        if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
            raise PaymentError("YooKassa credentials are not configured.")

    def _resolve_amount(self, amount: int) -> str:
        value = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return f"{value:.2f}"

    def _resolve_amount_from_cents(self, amount_cents: int) -> str:
        value = (Decimal(amount_cents) / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return f"{value:.2f}"

    def _build_return_url(self) -> str:
        return (WEBAPP_URL or "http://127.0.0.1:8011").rstrip("/")

    def _build_receipt_phone(self, *phones: str) -> str:
        for phone in phones:
            digits = re.sub(r"\D+", "", phone)
            if len(digits) == 10:
                digits = f"7{digits}"
            if len(digits) == 11 and digits.startswith("8"):
                digits = f"7{digits[1:]}"
            if 10 <= len(digits) <= 15:
                return digits
        return ""

    def _build_receipt_items(self, *, payload: OrderCreate, amount: int) -> list[dict[str, Any]]:
        subtotal_cents = sum(item.price * item.quantity * 100 for item in payload.items)
        payment_cents = amount * 100
        discount_cents = max(0, subtotal_cents - payment_cents)
        remaining_discount_cents = discount_cents
        receipt_items: list[dict[str, Any]] = []

        for index, item in enumerate(payload.items):
            line_total_cents = item.price * item.quantity * 100
            if index == len(payload.items) - 1:
                line_discount_cents = remaining_discount_cents
            elif subtotal_cents > 0:
                line_discount_cents = discount_cents * line_total_cents // subtotal_cents
                remaining_discount_cents -= line_discount_cents
            else:
                line_discount_cents = 0

            paid_line_cents = max(0, line_total_cents - line_discount_cents)
            if paid_line_cents <= 0:
                continue

            unit_cents = paid_line_cents // item.quantity
            remainder_units = paid_line_cents % item.quantity
            regular_units = item.quantity - remainder_units

            if regular_units > 0 and unit_cents > 0:
                receipt_items.append(
                    self._build_receipt_item(
                        title=item.title,
                        quantity=regular_units,
                        amount_cents=unit_cents,
                    )
                )
            if remainder_units > 0:
                receipt_items.append(
                    self._build_receipt_item(
                        title=item.title,
                        quantity=remainder_units,
                        amount_cents=unit_cents + 1,
                    )
                )

        return receipt_items

    def _build_receipt_item(self, *, title: str, quantity: int, amount_cents: int) -> dict[str, Any]:
        return {
            "description": title[:128],
            "quantity": f"{quantity:.2f}",
            "amount": {
                "value": self._resolve_amount_from_cents(amount_cents),
                "currency": "RUB",
            },
            "vat_code": YOOKASSA_VAT_CODE,
            "payment_mode": "full_payment",
            "payment_subject": "commodity",
        }

    async def create_payment(
        self,
        *,
        user_id: int,
        user_phone: str,
        payload: OrderCreate,
        amount: int,
    ) -> PaymentInitRead:
        self._ensure_configured()
        pending_payment = await self.repository.create_pending(
            user_id=user_id,
            amount=amount,
            payload_json=json.dumps(payload.model_dump(mode="json"), ensure_ascii=False),
        )
        request_payload = {
            "amount": {
                "value": self._resolve_amount(amount),
                "currency": "RUB",
            },
            "confirmation": {
                "type": "redirect",
                "return_url": self._build_return_url(),
            },
            "capture": True,
            "description": f"Zamzam заказ #{pending_payment.id}, телефон {user_phone}",
            "receipt": {
                "customer": {
                    "phone": self._build_receipt_phone(payload.customer_phone, user_phone),
                },
                "items": self._build_receipt_items(payload=payload, amount=amount),
            },
            "metadata": {
                "pending_payment_id": str(pending_payment.id),
                "user_id": str(user_id),
            },
        }

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    "https://api.yookassa.ru/v3/payments",
                    json=request_payload,
                    auth=(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY),
                    headers={"Idempotence-Key": str(uuid4())},
                )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip()
            logger.warning("YooKassa payment creation failed. status=%s detail=%s", exc.response.status_code, detail)
            await self.repository.mark_failed(
                pending_payment_id=pending_payment.id,
                status="create_failed",
                error_message=detail,
            )
            raise PaymentError(f"YooKassa payment creation failed: {detail}") from exc
        except httpx.HTTPError as exc:
            await self.repository.mark_failed(
                pending_payment_id=pending_payment.id,
                status="create_failed",
                error_message=str(exc),
            )
            raise PaymentError("YooKassa payment creation failed.") from exc

        response_payload = response.json()
        payment_id = str(response_payload.get("id") or "")
        status = str(response_payload.get("status") or "pending")
        confirmation = response_payload.get("confirmation") or {}
        confirmation_url = str(confirmation.get("confirmation_url") or "")
        if not payment_id or not confirmation_url:
            raise PaymentError("YooKassa payment response is incomplete.")

        await self.repository.attach_yookassa_payment(
            pending_payment_id=pending_payment.id,
            yookassa_payment_id=payment_id,
            confirmation_url=confirmation_url,
            status=status,
        )
        return PaymentInitRead(
            payment_id=payment_id,
            confirmation_url=confirmation_url,
            status=status,
        )

    async def fetch_payment(self, payment_id: str) -> dict[str, Any]:
        self._ensure_configured()
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(
                    f"https://api.yookassa.ru/v3/payments/{payment_id}",
                    auth=(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY),
                )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise PaymentError("YooKassa payment lookup failed.") from exc

        payload = response.json()
        if not isinstance(payload, dict):
            raise PaymentError("YooKassa payment lookup response is invalid.")
        return payload

```

## 📁 `backend\redactor`

## 📄 `backend\redactor\__init__.py`

```python
from backend.redactor.router import router

__all__ = ["router"]

```

## 📄 `backend\redactor\crud.py`

```python
from __future__ import annotations

from collections.abc import Sequence
from typing import Optional, Protocol

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.redactor.models import MenuItemModel
from backend.redactor.schemas import MenuItemCreate, MenuItemUpdate


class MenuItemRepository(Protocol):
    async def list(
        self,
        *,
        limit: int,
        offset: int,
        include_inactive: bool,
    ) -> tuple[Sequence[MenuItemModel], int]: ...
    async def list_storefront(self) -> Sequence[MenuItemModel]: ...
    async def search_catalog(
        self,
        *,
        query: str,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[MenuItemModel], int]: ...
    async def get(self, item_id: int) -> Optional[MenuItemModel]: ...
    async def get_many_by_ids(self, item_ids: Sequence[int]) -> Sequence[MenuItemModel]: ...
    async def create(self, payload: MenuItemCreate) -> MenuItemModel: ...
    async def update(self, item_id: int, payload: MenuItemUpdate) -> Optional[MenuItemModel]: ...
    async def hard_delete(self, item_id: int, version: int) -> Optional[MenuItemModel]: ...
    async def count_all(self) -> int: ...
    async def seed_defaults(self, items: list[MenuItemCreate]) -> None: ...


class SqlAlchemyMenuItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        include_inactive: bool,
    ) -> tuple[Sequence[MenuItemModel], int]:
        filters = [MenuItemModel.sync_source == "iiko", MenuItemModel.is_published.is_(True)]
        if not include_inactive:
            filters.append(MenuItemModel.is_active.is_(True))

        total_stmt = select(func.count()).select_from(MenuItemModel)
        if filters:
            total_stmt = total_stmt.where(*filters)

        items_stmt = (
            select(MenuItemModel)
            .where(*filters)
            .order_by(MenuItemModel.sort_order.asc(), MenuItemModel.id.asc())
            .limit(limit)
            .offset(offset)
        )

        total = int(await self._session.scalar(total_stmt) or 0)
        items = (await self._session.scalars(items_stmt)).all()
        return items, total

    async def list_storefront(self) -> Sequence[MenuItemModel]:
        stmt = (
            select(MenuItemModel)
            .where(
                MenuItemModel.sync_source == "iiko",
                MenuItemModel.is_published.is_(True),
                MenuItemModel.is_active.is_(True),
            )
            .order_by(MenuItemModel.sort_order.asc(), MenuItemModel.id.asc())
        )
        return (await self._session.scalars(stmt)).all()

    async def search_catalog(
        self,
        *,
        query: str,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[MenuItemModel], int]:
        filters = [
            MenuItemModel.sync_source == "iiko",
            MenuItemModel.is_active.is_(True),
            MenuItemModel.is_deleted_in_iiko.is_(False),
        ]
        normalized_query = query.strip()
        if normalized_query:
            pattern = f"%{normalized_query}%"
            filters.append(
                or_(
                    MenuItemModel.title.ilike(pattern),
                    MenuItemModel.site_title.ilike(pattern),
                    MenuItemModel.iiko_category_name.ilike(pattern),
                    MenuItemModel.category.ilike(pattern),
                )
            )

        total_stmt = select(func.count()).select_from(MenuItemModel).where(*filters)
        items_stmt = (
            select(MenuItemModel)
            .where(*filters)
            .order_by(
                MenuItemModel.is_published.desc(),
                MenuItemModel.is_active.desc(),
                MenuItemModel.title.asc(),
            )
            .limit(limit)
            .offset(offset)
        )

        total = int(await self._session.scalar(total_stmt) or 0)
        items = (await self._session.scalars(items_stmt)).all()
        return items, total

    async def get(self, item_id: int) -> Optional[MenuItemModel]:
        stmt = select(MenuItemModel).where(MenuItemModel.id == item_id, MenuItemModel.sync_source == "iiko")
        return await self._session.scalar(stmt)

    async def get_many_by_ids(self, item_ids: Sequence[int]) -> Sequence[MenuItemModel]:
        normalized_ids = [int(item_id) for item_id in item_ids]
        if not normalized_ids:
            return []

        stmt = select(MenuItemModel).where(
            MenuItemModel.id.in_(normalized_ids),
            MenuItemModel.sync_source == "iiko",
        )
        return (await self._session.scalars(stmt)).all()

    async def create(self, payload: MenuItemCreate) -> MenuItemModel:
        model = MenuItemModel(**payload.model_dump())
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return model

    async def update(self, item_id: int, payload: MenuItemUpdate) -> Optional[MenuItemModel]:
        values = payload.model_dump(exclude_unset=True, exclude={"version"})
        if not values:
            return await self.get(item_id)

        stmt = (
            update(MenuItemModel)
            .where(MenuItemModel.id == item_id, MenuItemModel.version == payload.version)
            .values(**values, version=MenuItemModel.version + 1)
            .returning(MenuItemModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return model

    async def hard_delete(self, item_id: int, version: int) -> Optional[MenuItemModel]:
        stmt = (
            delete(MenuItemModel)
            .where(MenuItemModel.id == item_id, MenuItemModel.version == version)
            .returning(MenuItemModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return model

    async def count_all(self) -> int:
        return int(await self._session.scalar(select(func.count()).select_from(MenuItemModel)) or 0)

    async def seed_defaults(self, items: list[MenuItemCreate]) -> None:
        if not items:
            return
        if await self.count_all():
            return

        self._session.add_all(MenuItemModel(**item.model_dump()) for item in items)
        await self._session.commit()

```

## 📄 `backend\redactor\depencises.py`

```python
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.redactor.crud import SqlAlchemyMenuItemRepository
from backend.redactor.service import MenuItemService
from db import get_db


def get_menu_item_repository(
    session: AsyncSession = Depends(get_db),
) -> SqlAlchemyMenuItemRepository:
    return SqlAlchemyMenuItemRepository(session)


def get_menu_item_service(
    repository: SqlAlchemyMenuItemRepository = Depends(get_menu_item_repository),
) -> MenuItemService:
    return MenuItemService(repository=repository)

```

## 📄 `backend\redactor\migrations.py`

```python
from __future__ import annotations

from sqlalchemy import text

from db import engine


async def ensure_menu_item_iiko_columns() -> None:
    statements = [
        "ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS sync_source VARCHAR(32) NOT NULL DEFAULT 'manual'",
        "ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS iiko_product_id VARCHAR(64)",
        "ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS iiko_group_id VARCHAR(64)",
        "ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS iiko_category_name VARCHAR(255)",
        "ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS iiko_parent_group_id VARCHAR(64)",
        "ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS iiko_terminal_group_id VARCHAR(64)",
        "ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS price_from_iiko INTEGER",
        "ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS site_title VARCHAR(255)",
        "ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS site_description TEXT",
        "ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS is_published BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS is_deleted_in_iiko BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS sync_hash VARCHAR(64)",
        "ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMPTZ",
        "DROP INDEX IF EXISTS ix_menu_items_iiko_product_id",
        "CREATE INDEX IF NOT EXISTS ix_menu_items_iiko_group_id ON menu_items (iiko_group_id)",
        "CREATE INDEX IF NOT EXISTS ix_menu_items_iiko_terminal_group_id ON menu_items (iiko_terminal_group_id)",
        "CREATE INDEX IF NOT EXISTS ix_menu_items_sync_source_active ON menu_items (sync_source, is_active)",
        "CREATE INDEX IF NOT EXISTS ix_menu_items_published_active ON menu_items (is_published, is_active)",
        (
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_menu_items_iiko_product_terminal "
            "ON menu_items (iiko_product_id, iiko_terminal_group_id) "
            "WHERE iiko_product_id IS NOT NULL AND iiko_terminal_group_id IS NOT NULL"
        ),
    ]

    async with engine.begin() as conn:
        for statement in statements:
            await conn.execute(text(statement))

```

## 📄 `backend\redactor\models.py`

```python
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class MenuItemModel(Base):
    __tablename__ = "menu_items"
    __table_args__ = (
        Index("ix_menu_items_active_sort", "is_active", "sort_order"),
        Index("ix_menu_items_category_active", "category", "is_active"),
        Index("ix_menu_items_iiko_group_id", "iiko_group_id"),
        Index("ix_menu_items_iiko_terminal_group_id", "iiko_terminal_group_id"),
        Index("ix_menu_items_sync_source_active", "sync_source", "is_active"),
        Index("ix_menu_items_published_active", "is_published", "is_active"),
        Index("ux_menu_items_iiko_product_terminal", "iiko_product_id", "iiko_terminal_group_id", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sync_source: Mapped[str] = mapped_column(String(32), nullable=False, default="manual", server_default="manual")
    iiko_product_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    iiko_group_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    iiko_category_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    iiko_parent_group_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    iiko_terminal_group_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    site_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    site_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    price_from_iiko: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    accent: Mapped[str] = mapped_column(String(32), nullable=False)
    badge: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    image_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    is_deleted_in_iiko: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    sync_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

```

## 📄 `backend\redactor\router.py`

```python
from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from PIL import Image, ImageOps, UnidentifiedImageError

from backend.auth.dependencies import ensure_admin_user, get_optional_current_user, require_admin_user
from backend.redactor.depencises import get_menu_item_service
from backend.redactor.schemas import (
    HeroContentRead,
    HeroContentUpdate,
    MenuCategoriesRead,
    MenuCategoriesUpdate,
    MenuCategoryItem,
    MenuSectionContentRead,
    MenuSectionContentUpdate,
    MenuItemCreate,
    MenuItemDelete,
    MenuItemCatalogPage,
    MenuItemLocalUpdate,
    MenuItemRead,
    MenuItemsPage,
    MenuItemUpdate,
)
from backend.redactor.service import (
    MenuItemConflictError,
    MenuItemNotFoundError,
    MenuItemService,
)
from backend.user.schemas import UserRead

router = APIRouter(prefix="/api/redactor/menu-items", tags=["redactor"])

BASE_DIR = Path(__file__).resolve().parents[2]
STATIC_FILES_DIR = BASE_DIR / "static" / "files"
HERO_CONTENT_FILE = BASE_DIR / "files" / "hero-content.json"
MENU_SECTION_CONTENT_FILE = BASE_DIR / "files" / "menu-section-content.json"
DELIVERY_SECTION_CONTENT_FILE = BASE_DIR / "files" / "delivery-section-content.json"
CONTACT_SECTION_CONTENT_FILE = BASE_DIR / "files" / "contact-section-content.json"
MENU_CATEGORIES_FILE = BASE_DIR / "files" / "menu-categories.json"
MAX_IMAGE_SIZE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_SIDE_PX = 1600
WEBP_QUALITY = 82
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

DEFAULT_HERO_CONTENT = HeroContentRead(
    kicker="Восточная • Кавказская • Авторская кухня",
    title="Zamzam",
    address="Доставка по городу, ресторанная подача и быстрый онлайн-заказ",
    subtitle_primary="Яркая восточная кухня с характером",
    subtitle_secondary="Полностью халяльное производство",
)

DEFAULT_MENU_SECTION_CONTENT = MenuSectionContentRead(
    kicker="Наше меню",
    title="Наша кухня - это богатое сочетание традиций, ароматов и вкусов, которые передаются из поколения в поколение.",
)
DEFAULT_DELIVERY_SECTION_CONTENT = MenuSectionContentRead(
    kicker="Доставка",
    title="Путь к заказу остался простым: выбрать, собрать, получить.",
)

DEFAULT_CONTACT_SECTION_CONTENT = MenuSectionContentRead(
    kicker="Контакты",
    title="Работаем каждый день и держим быструю доставку в центре внимания.",
)


def _resolve_image_file_path(image_path: Optional[str]) -> Optional[Path]:
    if not image_path:
        return None

    candidate = STATIC_FILES_DIR / Path(image_path).name
    try:
        candidate.resolve().relative_to(STATIC_FILES_DIR.resolve())
    except ValueError:
        return None
    return candidate


def _optimize_menu_image(content: bytes) -> bytes:
    try:
        with Image.open(BytesIO(content)) as image:
            image = ImageOps.exif_transpose(image)
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA" if "A" in image.getbands() else "RGB")

            if image.mode == "RGBA":
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(image, mask=image.getchannel("A"))
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")

            image.thumbnail((MAX_IMAGE_SIDE_PX, MAX_IMAGE_SIDE_PX), Image.Resampling.LANCZOS)

            output = BytesIO()
            image.save(output, format="WEBP", quality=WEBP_QUALITY, method=6)
            return output.getvalue()
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file.") from exc


def load_hero_content() -> HeroContentRead:
    if not HERO_CONTENT_FILE.exists():
        return DEFAULT_HERO_CONTENT

    try:
        payload = json.loads(HERO_CONTENT_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_HERO_CONTENT

    try:
        return HeroContentRead.model_validate(payload)
    except Exception:
        return DEFAULT_HERO_CONTENT


def save_hero_content(payload: HeroContentUpdate) -> HeroContentRead:
    HERO_CONTENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    HERO_CONTENT_FILE.write_text(
        json.dumps(payload.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return HeroContentRead.model_validate(payload)


def load_menu_section_content() -> MenuSectionContentRead:
    if not MENU_SECTION_CONTENT_FILE.exists():
        return DEFAULT_MENU_SECTION_CONTENT

    try:
        payload = json.loads(MENU_SECTION_CONTENT_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_MENU_SECTION_CONTENT

    try:
        return MenuSectionContentRead.model_validate(payload)
    except Exception:
        return DEFAULT_MENU_SECTION_CONTENT


def save_menu_section_content(payload: MenuSectionContentUpdate) -> MenuSectionContentRead:
    MENU_SECTION_CONTENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    MENU_SECTION_CONTENT_FILE.write_text(
        json.dumps(payload.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return MenuSectionContentRead.model_validate(payload)


def load_delivery_section_content() -> MenuSectionContentRead:
    if not DELIVERY_SECTION_CONTENT_FILE.exists():
        return DEFAULT_DELIVERY_SECTION_CONTENT

    try:
        payload = json.loads(DELIVERY_SECTION_CONTENT_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_DELIVERY_SECTION_CONTENT

    try:
        return MenuSectionContentRead.model_validate(payload)
    except Exception:
        return DEFAULT_DELIVERY_SECTION_CONTENT


def save_delivery_section_content(payload: MenuSectionContentUpdate) -> MenuSectionContentRead:
    DELIVERY_SECTION_CONTENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    DELIVERY_SECTION_CONTENT_FILE.write_text(
        json.dumps(payload.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return MenuSectionContentRead.model_validate(payload)


def load_contact_section_content() -> MenuSectionContentRead:
    if not CONTACT_SECTION_CONTENT_FILE.exists():
        return DEFAULT_CONTACT_SECTION_CONTENT

    try:
        payload = json.loads(CONTACT_SECTION_CONTENT_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_CONTACT_SECTION_CONTENT

    try:
        return MenuSectionContentRead.model_validate(payload)
    except Exception:
        return DEFAULT_CONTACT_SECTION_CONTENT


def save_contact_section_content(payload: MenuSectionContentUpdate) -> MenuSectionContentRead:
    CONTACT_SECTION_CONTENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONTACT_SECTION_CONTENT_FILE.write_text(
        json.dumps(payload.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return MenuSectionContentRead.model_validate(payload)


DEFAULT_MENU_CATEGORIES = MenuCategoriesRead(
    items=[
        MenuCategoryItem(value="signature", label="Блюда на углях"),
        MenuCategoryItem(value="seafood", label="Супы"),
        MenuCategoryItem(value="bowls", label="Салаты"),
        MenuCategoryItem(value="grill", label="Горячее"),
        MenuCategoryItem(value="dessert", label="Десерты"),
    ]
)


def load_menu_categories() -> MenuCategoriesRead:
    if not MENU_CATEGORIES_FILE.exists():
        return DEFAULT_MENU_CATEGORIES

    try:
        payload = json.loads(MENU_CATEGORIES_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_MENU_CATEGORIES

    try:
        return MenuCategoriesRead.model_validate(payload)
    except Exception:
        return DEFAULT_MENU_CATEGORIES


def save_menu_categories(payload: MenuCategoriesUpdate) -> MenuCategoriesRead:
    normalized_items: list[dict[str, str]] = []
    seen_values: set[str] = set()

    for item in payload.items:
        value = item.value.strip().lower()
        label = item.label.strip()
        if not value or not label or value in seen_values:
            continue
        seen_values.add(value)
        normalized_items.append({"value": value, "label": label})

    if not normalized_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one category is required.")

    normalized_payload = MenuCategoriesRead.model_validate({"items": normalized_items})
    MENU_CATEGORIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    MENU_CATEGORIES_FILE.write_text(
        json.dumps(normalized_payload.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return normalized_payload


@router.get("/hero-content", response_model=HeroContentRead)
async def get_hero_content() -> HeroContentRead:
    return load_hero_content()


@router.patch("/hero-content", response_model=HeroContentRead)
async def update_hero_content(
    payload: HeroContentUpdate,
    admin_user: UserRead = Depends(require_admin_user),
) -> HeroContentRead:
    _ = admin_user
    return save_hero_content(payload)


@router.get("/menu-section-content", response_model=MenuSectionContentRead)
async def get_menu_section_content() -> MenuSectionContentRead:
    return load_menu_section_content()


@router.patch("/menu-section-content", response_model=MenuSectionContentRead)
async def update_menu_section_content(
    payload: MenuSectionContentUpdate,
    admin_user: UserRead = Depends(require_admin_user),
) -> MenuSectionContentRead:
    _ = admin_user
    return save_menu_section_content(payload)


@router.get("/delivery-section-content", response_model=MenuSectionContentRead)
async def get_delivery_section_content() -> MenuSectionContentRead:
    return load_delivery_section_content()


@router.patch("/delivery-section-content", response_model=MenuSectionContentRead)
async def update_delivery_section_content(
    payload: MenuSectionContentUpdate,
    admin_user: UserRead = Depends(require_admin_user),
) -> MenuSectionContentRead:
    _ = admin_user
    return save_delivery_section_content(payload)


@router.get("/contact-section-content", response_model=MenuSectionContentRead)
async def get_contact_section_content() -> MenuSectionContentRead:
    return load_contact_section_content()


@router.patch("/contact-section-content", response_model=MenuSectionContentRead)
async def update_contact_section_content(
    payload: MenuSectionContentUpdate,
    admin_user: UserRead = Depends(require_admin_user),
) -> MenuSectionContentRead:
    _ = admin_user
    return save_contact_section_content(payload)


@router.get("/menu-categories", response_model=MenuCategoriesRead)
async def get_menu_categories() -> MenuCategoriesRead:
    return load_menu_categories()


@router.patch("/menu-categories", response_model=MenuCategoriesRead)
async def update_menu_categories(
    payload: MenuCategoriesUpdate,
    admin_user: UserRead = Depends(require_admin_user),
) -> MenuCategoriesRead:
    _ = admin_user
    return save_menu_categories(payload)


@router.get("", response_model=MenuItemsPage)
async def list_menu_items(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    include_inactive: bool = Query(default=False),
    current_user: Optional[UserRead] = Depends(get_optional_current_user),
    service: MenuItemService = Depends(get_menu_item_service),
) -> MenuItemsPage:
    if include_inactive:
        ensure_admin_user(current_user)
    return await service.list_items(
        limit=limit,
        offset=offset,
        include_inactive=include_inactive,
    )


@router.get("/catalog/search", response_model=MenuItemCatalogPage)
async def search_catalog_items(
    q: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    admin_user: UserRead = Depends(require_admin_user),
    service: MenuItemService = Depends(get_menu_item_service),
) -> MenuItemCatalogPage:
    _ = admin_user
    return await service.search_catalog_items(
        query=q,
        limit=limit,
        offset=offset,
    )


@router.get("/{item_id}", response_model=MenuItemRead)
async def get_menu_item(
    item_id: int,
    admin_user: UserRead = Depends(require_admin_user),
    service: MenuItemService = Depends(get_menu_item_service),
) -> MenuItemRead:
    _ = admin_user
    try:
        return await service.get_item(item_id)
    except MenuItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found") from exc


@router.post("", response_model=MenuItemRead, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    payload: MenuItemCreate,
    admin_user: UserRead = Depends(require_admin_user),
    service: MenuItemService = Depends(get_menu_item_service),
) -> MenuItemRead:
    _ = admin_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Catalog products are managed by iiko and cannot be created manually.",
    )


@router.patch("/{item_id}", response_model=MenuItemRead)
async def update_menu_item(
    item_id: int,
    payload: MenuItemLocalUpdate,
    admin_user: UserRead = Depends(require_admin_user),
    service: MenuItemService = Depends(get_menu_item_service),
) -> MenuItemRead:
    _ = admin_user
    try:
        return await service.update_item(
            item_id,
            MenuItemUpdate(
                version=payload.version,
                site_title=payload.title,
                site_description=payload.description,
                category=payload.category,
                is_published=payload.is_published,
            ),
        )
    except MenuItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found") from exc
    except MenuItemConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Menu item was changed concurrently. Reload and retry.",
        ) from exc


@router.post("/{item_id}/image", response_model=MenuItemRead)
async def upload_menu_item_image(
    item_id: int,
    version: int = Form(..., ge=1),
    image: UploadFile = File(...),
    admin_user: UserRead = Depends(require_admin_user),
    service: MenuItemService = Depends(get_menu_item_service),
) -> MenuItemRead:
    _ = admin_user
    try:
        previous_item = await service.get_item(item_id)
    except MenuItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found") from exc
    extension = ALLOWED_IMAGE_TYPES.get(image.content_type or "")
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image type. Use JPG, PNG or WEBP.",
        )

    content = await image.read(MAX_IMAGE_SIZE_BYTES + 1)
    await image.close()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image file is empty.")
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image is too large.")

    STATIC_FILES_DIR.mkdir(parents=True, exist_ok=True)
    optimized_content = _optimize_menu_image(content)
    file_name = f"menu-item-{item_id}-{uuid4().hex}.webp"
    target_path = STATIC_FILES_DIR / file_name

    try:
        target_path.write_bytes(optimized_content)
        updated_item = await service.update_item(
            item_id,
            MenuItemUpdate(version=version, image_path=f"files/{file_name}"),
        )
        previous_image_path = _resolve_image_file_path(previous_item.image_path)
        if previous_image_path is not None and previous_image_path != target_path:
            previous_image_path.unlink(missing_ok=True)
        return updated_item
    except MenuItemNotFoundError as exc:
        target_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found") from exc
    except MenuItemConflictError as exc:
        target_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Menu item was changed concurrently. Reload and retry.",
        ) from exc


@router.delete("/{item_id}", response_model=MenuItemRead)
async def delete_menu_item(
    item_id: int,
    payload: MenuItemDelete,
    admin_user: UserRead = Depends(require_admin_user),
    service: MenuItemService = Depends(get_menu_item_service),
) -> MenuItemRead:
    _ = admin_user
    try:
        return await service.update_item(
            item_id,
            MenuItemUpdate(
                version=payload.version,
                is_published=False,
            ),
        )
    except MenuItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found") from exc
    except MenuItemConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Menu item was changed concurrently. Reload and retry.",
        ) from exc

```

## 📄 `backend\redactor\schemas.py`

```python
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MenuItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=4000)
    price: int = Field(..., ge=0, le=1_000_000)
    category: str = Field(..., min_length=1, max_length=64)
    accent: str = Field(..., min_length=3, max_length=32)
    badge: Optional[str] = Field(default=None, max_length=128)
    image_path: Optional[str] = Field(default=None, max_length=255)
    sort_order: int = Field(default=0, ge=0, le=100_000)
    is_active: bool = True


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    version: int = Field(..., ge=1)
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, min_length=1, max_length=4000)
    site_title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    site_description: Optional[str] = Field(default=None, min_length=1, max_length=4000)
    price: Optional[int] = Field(default=None, ge=0, le=1_000_000)
    category: Optional[str] = Field(default=None, min_length=1, max_length=64)
    accent: Optional[str] = Field(default=None, min_length=3, max_length=32)
    badge: Optional[str] = Field(default=None, max_length=128)
    image_path: Optional[str] = Field(default=None, max_length=255)
    sort_order: Optional[int] = Field(default=None, ge=0, le=100_000)
    is_published: Optional[bool] = None
    is_active: Optional[bool] = None


class MenuItemLocalUpdate(BaseModel):
    version: int = Field(..., ge=1)
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, min_length=1, max_length=4000)
    category: str = Field(..., min_length=1, max_length=64)
    is_published: bool = True


class MenuItemDelete(BaseModel):
    version: int = Field(..., ge=1)


class MenuItemRead(MenuItemBase):
    id: int
    iiko_title: str
    iiko_description: str
    is_published: bool
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MenuItemsPage(BaseModel):
    items: list[MenuItemRead]
    total: int
    limit: int
    offset: int


class MenuItemCatalogPage(BaseModel):
    items: list[MenuItemRead]
    total: int
    limit: int
    offset: int
    query: str


class MenuCategoryItem(BaseModel):
    value: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9_-]+$")
    label: str = Field(..., min_length=1, max_length=64)


class MenuCategoriesRead(BaseModel):
    items: list[MenuCategoryItem]


class MenuCategoriesUpdate(MenuCategoriesRead):
    pass


class HeroContentRead(BaseModel):
    kicker: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=255)
    address: str = Field(..., min_length=1, max_length=500)
    subtitle_primary: str = Field(..., min_length=1, max_length=255)
    subtitle_secondary: str = Field(..., min_length=1, max_length=255)


class HeroContentUpdate(HeroContentRead):
    pass


class MenuSectionContentRead(BaseModel):
    kicker: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)


class MenuSectionContentUpdate(MenuSectionContentRead):
    pass

```

## 📄 `backend\redactor\service.py`

```python
from __future__ import annotations

from dataclasses import dataclass

from config import REDACTOR_PAGE_LIMIT

from backend.redactor.crud import MenuItemRepository
from backend.redactor.schemas import (
    MenuItemCatalogPage,
    MenuItemCreate,
    MenuItemDelete,
    MenuItemRead,
    MenuItemsPage,
    MenuItemUpdate,
)


class MenuItemNotFoundError(Exception):
    pass


class MenuItemConflictError(Exception):
    pass


@dataclass
class MenuItemService:
    repository: MenuItemRepository

    def _to_read_model(self, item) -> MenuItemRead:
        payload = {
            "id": item.id,
            "title": item.site_title or item.title,
            "description": item.site_description or item.description,
            "iiko_title": item.title,
            "iiko_description": item.description,
            "price": item.price,
            "category": item.category,
            "accent": item.accent,
            "badge": item.badge,
            "image_path": item.image_path,
            "sort_order": item.sort_order,
            "is_active": item.is_active,
            "is_published": item.is_published,
            "version": item.version,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
        return MenuItemRead.model_validate(payload)

    async def list_items(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        include_inactive: bool = False,
    ) -> MenuItemsPage:
        safe_limit = max(1, min(limit, REDACTOR_PAGE_LIMIT))
        safe_offset = max(0, offset)
        items, total = await self.repository.list(
            limit=safe_limit,
            offset=safe_offset,
            include_inactive=include_inactive,
        )
        return MenuItemsPage(
            items=[self._to_read_model(item) for item in items],
            total=total,
            limit=safe_limit,
            offset=safe_offset,
        )

    async def list_storefront_items(self) -> list[MenuItemRead]:
        items = await self.repository.list_storefront()
        return [self._to_read_model(item) for item in items]

    async def search_catalog_items(
        self,
        *,
        query: str = "",
        limit: int = 20,
        offset: int = 0,
    ) -> MenuItemCatalogPage:
        safe_limit = max(1, min(limit, REDACTOR_PAGE_LIMIT))
        safe_offset = max(0, offset)
        items, total = await self.repository.search_catalog(
            query=query,
            limit=safe_limit,
            offset=safe_offset,
        )
        return MenuItemCatalogPage(
            items=[self._to_read_model(item) for item in items],
            total=total,
            limit=safe_limit,
            offset=safe_offset,
            query=query,
        )

    async def get_item(self, item_id: int) -> MenuItemRead:
        item = await self.repository.get(item_id)
        if item is None:
            raise MenuItemNotFoundError(item_id)
        return self._to_read_model(item)

    async def create_item(self, payload: MenuItemCreate) -> MenuItemRead:
        item = await self.repository.create(payload)
        return self._to_read_model(item)

    async def update_item(self, item_id: int, payload: MenuItemUpdate) -> MenuItemRead:
        item = await self.repository.update(item_id, payload)
        if item is not None:
            return self._to_read_model(item)

        existing = await self.repository.get(item_id)
        if existing is None:
            raise MenuItemNotFoundError(item_id)
        raise MenuItemConflictError(item_id)

    async def delete_item(self, item_id: int, payload: MenuItemDelete) -> MenuItemRead:
        item = await self.repository.hard_delete(item_id, payload.version)
        if item is not None:
            return self._to_read_model(item)

        existing = await self.repository.get(item_id)
        if existing is None:
            raise MenuItemNotFoundError(item_id)
        raise MenuItemConflictError(item_id)

    async def ensure_seed_data(self, items: list[MenuItemCreate]) -> None:
        await self.repository.seed_defaults(items)

```

## 📁 `backend\user`

## 📄 `backend\user\__init__.py`

```python
from backend.user.models import UserModel
from backend.user.router import router

__all__ = ["UserModel", "router"]

```

## 📄 `backend\user\crud.py`

```python
from __future__ import annotations

from typing import Optional, Protocol

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.user.models import UserModel


class UserRepository(Protocol):
    async def get_by_id(self, user_id: int) -> Optional[UserModel]: ...
    async def get_by_phone(self, phone: str) -> Optional[UserModel]: ...
    async def get_by_email(self, email: str) -> Optional[UserModel]: ...
    async def get_by_session_token(self, session_token: str) -> Optional[UserModel]: ...
    async def create_user(
        self,
        *,
        phone: str,
        email: str,
        password_hash: str,
        full_name: Optional[str],
        session_token: str,
        is_admin: bool,
    ) -> UserModel: ...
    async def activate_existing_user(
        self,
        *,
        user_id: int,
        password_hash: str,
        email: str,
        full_name: Optional[str],
        session_token: str,
        is_admin: bool,
    ) -> UserModel: ...
    async def update_session_token(self, *, user_id: int, session_token: str, is_admin: bool) -> UserModel: ...
    async def clear_session_token(self, *, user_id: int) -> Optional[UserModel]: ...
    async def update_admin_status(self, *, user_id: int, is_admin: bool) -> UserModel: ...
    async def update_phone(self, *, user_id: int, phone: str, is_admin: bool) -> UserModel: ...
    async def update_password(self, *, user_id: int, password_hash: str) -> Optional[UserModel]: ...
    async def add_bonus(self, *, user_id: int, bonus_delta: int) -> Optional[UserModel]: ...
    async def spend_bonus(self, *, user_id: int, bonus_amount: int) -> Optional[UserModel]: ...


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.id == user_id)
        return await self._session.scalar(stmt)

    async def get_by_phone(self, phone: str) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.phone == phone)
        return await self._session.scalar(stmt)

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.email == email)
        return await self._session.scalar(stmt)

    async def get_by_session_token(self, session_token: str) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.session_token == session_token)
        return await self._session.scalar(stmt)

    async def create_user(
        self,
        *,
        phone: str,
        email: str,
        password_hash: str,
        full_name: Optional[str],
        session_token: str,
        is_admin: bool,
    ) -> UserModel:
        user = UserModel(
            phone=phone,
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            is_admin=is_admin,
            is_verified=True,
            session_token=session_token,
            verification_code=None,
            verification_expires_at=None,
        )
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def activate_existing_user(
        self,
        *,
        user_id: int,
        password_hash: str,
        email: str,
        full_name: Optional[str],
        session_token: str,
        is_admin: bool,
    ) -> UserModel:
        values: dict[str, object] = {
            "password_hash": password_hash,
            "email": email,
            "is_admin": is_admin,
            "is_verified": True,
            "session_token": session_token,
            "verification_code": None,
            "verification_expires_at": None,
        }
        if full_name:
            values["full_name"] = full_name

        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(**values)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        user = result.scalar_one()
        await self._session.commit()
        return user

    async def update_session_token(self, *, user_id: int, session_token: str, is_admin: bool) -> UserModel:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(
                is_admin=is_admin,
                is_verified=True,
                session_token=session_token,
            )
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        user = result.scalar_one()
        await self._session.commit()
        return user

    async def clear_session_token(self, *, user_id: int) -> Optional[UserModel]:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(session_token=None)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return user

    async def update_admin_status(self, *, user_id: int, is_admin: bool) -> UserModel:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(is_admin=is_admin)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        user = result.scalar_one()
        await self._session.commit()
        return user

    async def update_phone(self, *, user_id: int, phone: str, is_admin: bool) -> UserModel:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(phone=phone, is_admin=is_admin)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        user = result.scalar_one()
        await self._session.commit()
        return user

    async def update_password(self, *, user_id: int, password_hash: str) -> Optional[UserModel]:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(password_hash=password_hash)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return user

    async def add_bonus(self, *, user_id: int, bonus_delta: int) -> Optional[UserModel]:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(bonus_balance=UserModel.bonus_balance + bonus_delta)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return user

    async def spend_bonus(self, *, user_id: int, bonus_amount: int) -> Optional[UserModel]:
        stmt = (
            update(UserModel)
            .where(
                UserModel.id == user_id,
                UserModel.bonus_balance >= bonus_amount,
            )
            .values(bonus_balance=UserModel.bonus_balance - bonus_amount)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return user

```

## 📄 `backend\user\depencises.py`

```python
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.user.crud import SqlAlchemyUserRepository
from backend.user.service import UserService
from db import get_db


def get_user_repository(
    session: AsyncSession = Depends(get_db),
) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


def get_user_service(
    repository: SqlAlchemyUserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository=repository)

```

## 📄 `backend\user\migrations.py`

```python
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

```

## 📄 `backend\user\models.py`

```python
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bonus_balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verification_code: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    verification_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    session_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

```

## 📄 `backend\user\router.py`

```python
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth.dependencies import require_current_user
from backend.orders.depencises import get_order_service
from backend.orders.service import OrderService
from backend.user.depencises import get_user_service
from backend.user.schemas import UserDashboardRead, UserProfileUpdateRequest, UserRead
from backend.user.service import UserAuthError, UserConflictError, UserService

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/me", response_model=UserDashboardRead)
async def get_current_user_dashboard(
    user: UserRead = Depends(require_current_user),
    user_service: UserService = Depends(get_user_service),
    order_service: OrderService = Depends(get_order_service),
) -> UserDashboardRead:
    latest_order_status = await order_service.get_latest_status(user.id)
    active_orders_count = await order_service.count_active_orders(user.id)
    return user_service.build_dashboard(
        user=user,
        latest_order_status=latest_order_status,
        active_orders_count=active_orders_count,
    )


@router.patch("/me", response_model=UserRead)
async def update_current_user(
    payload: UserProfileUpdateRequest,
    user: UserRead = Depends(require_current_user),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    try:
        return await user_service.update_phone(user_id=user.id, phone=payload.phone)
    except UserAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except UserConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

```

## 📄 `backend\user\schemas.py`

```python
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserRegisterRequest(BaseModel):
    phone: str = Field(..., min_length=6, max_length=32)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=120)


class UserLoginRequest(BaseModel):
    phone: str = Field(..., min_length=6, max_length=32)
    password: str = Field(..., min_length=6, max_length=128)


class UserProfileUpdateRequest(BaseModel):
    phone: str = Field(..., min_length=6, max_length=32)


class UserRead(BaseModel):
    id: int
    phone: str
    email: Optional[str]
    full_name: Optional[str]
    bonus_balance: int
    is_admin: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserAuthRead(BaseModel):
    session_token: str
    user: UserRead


class UserDashboardRead(BaseModel):
    user: UserRead
    latest_order_status: Optional[str] = None
    active_orders_count: int = 0

```

## 📄 `backend\user\service.py`

```python
from __future__ import annotations

import hashlib
import hmac
import logging
import re
from dataclasses import dataclass
from secrets import token_hex
from typing import Optional

from backend.user.crud import UserRepository
from backend.user.migrations import is_admin_phone
from backend.user.schemas import UserAuthRead, UserDashboardRead, UserLoginRequest, UserRead, UserRegisterRequest


logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    pass


class UserAuthError(Exception):
    pass


class UserConflictError(Exception):
    pass


class UserBonusError(Exception):
    pass


@dataclass
class UserService:
    repository: UserRepository

    def normalize_phone(self, phone: str) -> str:
        digits = re.sub(r"\D+", "", phone)
        if len(digits) == 11 and digits.startswith("8"):
            digits = f"7{digits[1:]}"
        if len(digits) != 11 or not digits.startswith("7"):
            raise UserAuthError("Укажите корректный номер телефона в формате +7.")
        return f"+{digits}"

    def normalize_email(self, email: str) -> str:
        normalized = email.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise UserAuthError("Укажите корректный email.")
        return normalized

    def hash_password(self, password: str) -> str:
        normalized = password.strip()
        if len(normalized) < 6:
            raise UserAuthError("Пароль должен содержать не менее 6 символов.")

        salt = token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            normalized.encode("utf-8"),
            salt.encode("utf-8"),
            120_000,
        )
        return f"{salt}${digest.hex()}"

    def _verify_password(self, password: str, password_hash: Optional[str]) -> bool:
        if not password_hash:
            return False
        try:
            salt, digest = password_hash.split("$", 1)
        except ValueError:
            return False

        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.strip().encode("utf-8"),
            salt.encode("utf-8"),
            120_000,
        ).hex()
        return hmac.compare_digest(candidate, digest)

    async def register(self, payload: UserRegisterRequest) -> UserAuthRead:
        normalized_phone = self.normalize_phone(payload.phone)
        normalized_email = self.normalize_email(payload.email)
        full_name = (payload.full_name or "").strip() or None
        password_hash = self.hash_password(payload.password)
        session_token = token_hex(24)
        is_admin = is_admin_phone(normalized_phone)
        logger.info("Registering user. phone=%s", normalized_phone)

        user = await self.repository.get_by_phone(normalized_phone)
        if user is not None and user.password_hash:
            raise UserAuthError("Пользователь с таким номером уже зарегистрирован.")

        email_user = await self.repository.get_by_email(normalized_email)
        if email_user is not None and (user is None or email_user.id != user.id):
            raise UserAuthError("Пользователь с таким email уже зарегистрирован.")

        if user is None:
            created_user = await self.repository.create_user(
                phone=normalized_phone,
                email=normalized_email,
                password_hash=password_hash,
                full_name=full_name,
                session_token=session_token,
                is_admin=is_admin,
            )
        else:
            created_user = await self.repository.activate_existing_user(
                user_id=user.id,
                password_hash=password_hash,
                email=normalized_email,
                full_name=full_name,
                session_token=session_token,
                is_admin=is_admin,
            )

        return UserAuthRead(
            session_token=session_token,
            user=UserRead.model_validate(created_user),
        )

    async def login(self, payload: UserLoginRequest) -> UserAuthRead:
        normalized_phone = self.normalize_phone(payload.phone)
        logger.info("Login attempt. phone=%s", normalized_phone)
        user = await self.repository.get_by_phone(normalized_phone)
        if user is None or not self._verify_password(payload.password, user.password_hash):
            logger.warning("Login failed. phone=%s", normalized_phone)
            raise UserAuthError("Неверный номер телефона или пароль.")

        session_token = token_hex(24)
        logged_user = await self.repository.update_session_token(
            user_id=user.id,
            session_token=session_token,
            is_admin=is_admin_phone(normalized_phone),
        )
        logger.info("Login succeeded. user_id=%s", logged_user.id)
        return UserAuthRead(
            session_token=session_token,
            user=UserRead.model_validate(logged_user),
        )

    async def logout(self, *, session_token: str) -> UserRead:
        user = await self.repository.get_by_session_token(session_token)
        if user is None:
            raise UserNotFoundError(session_token)

        logged_out_user = await self.repository.clear_session_token(user_id=user.id)
        if logged_out_user is None:
            raise UserNotFoundError(session_token)

        logger.info("Logout succeeded. user_id=%s", logged_out_user.id)
        return UserRead.model_validate(logged_out_user)

    async def get_user_by_session_token(self, session_token: str) -> UserRead:
        user = await self.repository.get_by_session_token(session_token)
        if user is None:
            raise UserNotFoundError(session_token)
        return UserRead.model_validate(user)

    async def get_user_by_id(self, user_id: int) -> UserRead:
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        env_admin = is_admin_phone(user.phone)
        if user.is_admin != env_admin:
            user = await self.repository.update_admin_status(user_id=user.id, is_admin=env_admin)
        return UserRead.model_validate(user)

    async def add_bonus(self, *, user_id: int, bonus_delta: int) -> UserRead:
        user = await self.repository.add_bonus(user_id=user_id, bonus_delta=bonus_delta)
        if user is None:
            raise UserNotFoundError(user_id)
        return UserRead.model_validate(user)

    async def spend_bonus(self, *, user_id: int, bonus_amount: int) -> UserRead:
        if bonus_amount <= 0:
            return await self.get_user_by_id(user_id)

        user = await self.repository.spend_bonus(user_id=user_id, bonus_amount=bonus_amount)
        if user is None:
            raise UserBonusError("РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ Р±РѕРЅСѓСЃРѕРІ РґР»СЏ СЃРїРёСЃР°РЅРёСЏ.")
        return UserRead.model_validate(user)

    async def refund_bonus(self, *, user_id: int, bonus_amount: int) -> UserRead:
        if bonus_amount <= 0:
            return await self.get_user_by_id(user_id)
        return await self.add_bonus(user_id=user_id, bonus_delta=bonus_amount)

    async def update_phone(self, *, user_id: int, phone: str) -> UserRead:
        normalized_phone = self.normalize_phone(phone)
        existing_user = await self.repository.get_by_phone(normalized_phone)
        if existing_user is not None and existing_user.id != user_id:
            raise UserConflictError("Этот номер телефона уже используется.")

        user = await self.repository.update_phone(
            user_id=user_id,
            phone=normalized_phone,
            is_admin=is_admin_phone(normalized_phone),
        )
        return UserRead.model_validate(user)

    async def reset_password(self, *, user_id: int, password: str) -> UserRead:
        password_hash = self.hash_password(password)
        user = await self.repository.update_password(user_id=user_id, password_hash=password_hash)
        if user is None:
            raise UserNotFoundError(user_id)
        return UserRead.model_validate(user)

    def build_dashboard(
        self,
        *,
        user: UserRead,
        latest_order_status: Optional[str],
        active_orders_count: int,
    ) -> UserDashboardRead:
        return UserDashboardRead(
            user=user,
            latest_order_status=latest_order_status,
            active_orders_count=active_orders_count,
        )

```

## 📁 `deploy`

## 📁 `deploy\nginx`

## 📁 `files`

## 📄 `files\hero-content.json`

```json
{
  "kicker": "Восточная • Кавказская • Авторская кухня",
  "title": "ZamZam",
  "address": "Доставка по городу, вкуснейшие блюда и быстрый онлайн-заказ",
  "subtitle_primary": "Яркая восточная кухня с характером",
  "subtitle_secondary": "Сервис современного уровня"
}
```

## 📁 `files\legal`

## 📁 `static`

## 📄 `static\account.js`

```javascript
(() => {
const SESSION_STORAGE_KEY = "zamzam_session_token";
const REFRESH_STORAGE_KEY = "zamzam_refresh_token";
const PENDING_PAYMENT_STORAGE_KEY = "zamzam_pending_payment_id";
const PENDING_PAYMENT_SYNC_RETRY_DELAYS = [3000, 7000, 15000, 30000];
let pendingPaymentSyncRetryIndex = 0;
let pendingPaymentSyncTimeoutId = null;
window.zamzamAuthFallbackBound = true;
window.zamzamAccountCheckoutEnabled = true;

function readPersistentStorage(key) {
    try {
        return window.localStorage.getItem(key) || window.sessionStorage.getItem(key) || "";
    } catch (error) {
        return window.sessionStorage.getItem(key) || "";
    }
}

function writePersistentStorage(key, value) {
    if (!value) {
        return;
    }
    try {
        window.localStorage.setItem(key, value);
    } catch (error) {
        // Keep checkout working in restricted mobile browser storage modes.
    }
    window.sessionStorage.setItem(key, value);
}

function removePersistentStorage(key) {
    try {
        window.localStorage.removeItem(key);
    } catch (error) {
        // Keep logout working even when persistent storage is unavailable.
    }
    window.sessionStorage.removeItem(key);
}

const ACTIVE_ORDER_STATUSES = new Set(["Готовится", "Приготовлен", "Заказ отправлен", "Готов к выдаче"]);

const authModal = document.getElementById("auth-modal");
const authBackdrop = document.getElementById("auth-backdrop");
const authBack = document.getElementById("auth-back");
const authClose = document.getElementById("auth-close");
const authHint = document.getElementById("auth-hint");
const authTabLogin = document.getElementById("auth-tab-login");
const authTabRegister = document.getElementById("auth-tab-register");
const authLoginForm = document.getElementById("auth-login-form");
const authRegisterForm = document.getElementById("auth-register-form");
const authPhone = document.getElementById("auth-phone");
const authPassword = document.getElementById("auth-password");
const authRegisterName = document.getElementById("auth-register-name");
const authRegisterPhone = document.getElementById("auth-register-phone");
const authRegisterEmail = document.getElementById("auth-register-email");
const authRegisterPassword = document.getElementById("auth-register-password");
const authRecoveryForm = document.getElementById("auth-recovery-form");
const authRecoveryEmail = document.getElementById("auth-recovery-email");
const authRecoveryTokenField = document.getElementById("auth-recovery-token-field");
const authRecoveryToken = document.getElementById("auth-recovery-token");
const authRecoveryPasswordField = document.getElementById("auth-recovery-password-field");
const authRecoveryPassword = document.getElementById("auth-recovery-password");
const authForgotPassword = document.getElementById("auth-forgot-password");
const authRecoverySubmit = document.getElementById("auth-recovery-submit");
const authResetSubmit = document.getElementById("auth-reset-submit");
const authLoginSubmit = document.getElementById("auth-login-submit");
const authRegisterSubmit = document.getElementById("auth-register-submit");
const authRegisterOfertaConsent = document.getElementById("auth-register-oferta-consent");
const authRegisterPolicyConsent = document.getElementById("auth-register-policy-consent");
const authRegisterConsents = document.getElementById("auth-register-consents");

const authRequiredModal = document.getElementById("auth-required-modal");
const authRequiredClose = document.getElementById("auth-required-close");
const authRequiredLogin = document.getElementById("auth-required-login");
const authRequiredRegister = document.getElementById("auth-required-register");

const accountSection = document.getElementById("account");
const accountClose = document.getElementById("account-close");
const accountBonusBalance = document.getElementById("account-bonus-balance");
const accountUserPhone = document.getElementById("account-user-phone");
const accountOrderStatus = document.getElementById("account-order-status");
const accountOrdersCount = document.getElementById("account-orders-count");
const accountOrdersList = document.getElementById("account-orders-list");
const accountCurrentOrderCard = document.getElementById("account-current-order-card");
const accountCurrentRefresh = document.getElementById("account-current-refresh");
const accountHistoryRefresh = document.getElementById("account-history-refresh");
const accountPhoneForm = document.getElementById("account-phone-form");
const accountPhoneInput = document.getElementById("account-phone-input");
const accountPhoneSubmit = document.getElementById("account-phone-submit");
const accountPhoneHint = document.getElementById("account-phone-hint");
const accountFloatingTrigger = document.getElementById("account-floating-trigger");

const loginButton = document.getElementById("cart-open-topbar");
const checkoutForm = document.getElementById("checkout-form");
const checkoutBonusSpent = document.getElementById("checkout-bonus-spent");
const checkoutBonusBalanceText = document.getElementById("checkout-bonus-balance-text");
const checkoutPreviewTotal = document.getElementById("checkout-preview-total");
const checkoutButton = document.getElementById("checkout-button");
const floatingTools = document.querySelector(".floating-tools");
const checkoutOfertaConsent = document.getElementById("checkout-oferta-consent");
const checkoutPolicyConsent = document.getElementById("checkout-policy-consent");
const checkoutAddressInput = document.getElementById("checkout-address");
const checkoutHouseInput = document.getElementById("checkout-house");
const checkoutFlatInput = document.getElementById("checkout-flat");
const checkoutAddressSuggestions = document.getElementById("checkout-address-suggestions");

let sessionToken = readPersistentStorage(SESSION_STORAGE_KEY);
let authMode = "login";
let recoveryCodeSent = false;
let currentBonusBalance = 0;
let lastAutofilledCheckoutName = "";
let lastAutofilledCheckoutPhone = "";
let latestCheckoutProfileUser = null;
let accountAutoRefreshInFlight = false;
let checkoutWarningTimeoutId = null;
let streetSuggestionsTimeoutId = null;
let streetSuggestionsController = null;

function refreshSessionToken() {
    sessionToken = readPersistentStorage(SESSION_STORAGE_KEY);
    return sessionToken;
}

function setAuthTokens(payload) {
    sessionToken = payload?.access_token || "";
    const refreshToken = payload?.refresh_token || "";
    if (sessionToken) {
        writePersistentStorage(SESSION_STORAGE_KEY, sessionToken);
    }
    if (refreshToken) {
        writePersistentStorage(REFRESH_STORAGE_KEY, refreshToken);
    }
}

function clearAuthTokens() {
    removePersistentStorage(SESSION_STORAGE_KEY);
    removePersistentStorage(REFRESH_STORAGE_KEY);
    sessionToken = "";
}

async function refreshAccessToken() {
    const refreshToken = readPersistentStorage(REFRESH_STORAGE_KEY);
    if (!refreshToken) {
        return false;
    }

    const response = await fetch("/api/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload?.access_token) {
        clearAuthTokens();
        return false;
    }
    setAuthTokens(payload);
    return true;
}

function ensurePhonePrefixValue(input) {
    if (typeof window.zamzamEnsurePhonePrefix === "function") {
        return window.zamzamEnsurePhonePrefix(input);
    }

    if (!input) {
        return "";
    }

    const digits = input.value.replace(/\D/g, "");
    let normalized = digits;

    if (!normalized) {
        normalized = "7";
    } else if (normalized[0] === "8") {
        normalized = `7${normalized.slice(1)}`;
    } else if (normalized[0] !== "7") {
        normalized = `7${normalized}`;
    }

    input.value = `+${normalized}`;
    return input.value;
}

function getAppApi() {
    return window.zamzamApp || null;
}

function getCheckoutPhone() {
    const input = document.getElementById("checkout-phone");
    return ensurePhonePrefixValue(input).trim();
}

function isValidCheckoutPhone(phone) {
    const digits = String(phone || "").replace(/\D/g, "");
    return digits.length === 11 && digits[0] === "7";
}

function getResponseErrorMessage(payload, fallbackMessage) {
    return typeof payload?.detail === "string" ? payload.detail : fallbackMessage;
}

function showCheckoutWarning(message) {
    let popup = document.getElementById("checkout-warning-popup");
    if (!popup) {
        popup = document.createElement("div");
        popup.id = "checkout-warning-popup";
        popup.className = "checkout-consent-popup checkout-warning-popup";
        popup.setAttribute("role", "alert");
        document.body.appendChild(popup);
    }

    popup.textContent = message;
    popup.classList.add("is-visible");

    if (checkoutWarningTimeoutId) {
        window.clearTimeout(checkoutWarningTimeoutId);
    }

    checkoutWarningTimeoutId = window.setTimeout(() => {
        popup.classList.remove("is-visible");
    }, 3200);
}

function getCheckoutName() {
    return document.getElementById("checkout-name")?.value.trim() || "";
}

function isCheckoutPhonePlaceholderValue(value) {
    const normalized = String(value || "").trim();
    if (!normalized) {
        return true;
    }

    const digits = normalized.replace(/\D/g, "");
    return digits === "" || digits === "7";
}

function syncCheckoutProfileFields(user) {
    if (!user) {
        return;
    }

    latestCheckoutProfileUser = {
        full_name: (user.full_name || "").trim(),
        phone: (user.phone || "").trim(),
    };

    const checkoutNameInput = document.getElementById("checkout-name");
    const checkoutPhoneInput = document.getElementById("checkout-phone");
    const nextName = latestCheckoutProfileUser.full_name;
    const nextPhone = latestCheckoutProfileUser.phone;

    if (checkoutNameInput && nextName) {
        const currentName = checkoutNameInput.value.trim();
        if (!currentName || currentName === lastAutofilledCheckoutName) {
            checkoutNameInput.value = nextName;
            lastAutofilledCheckoutName = nextName;
        }
    }

    if (checkoutPhoneInput && nextPhone) {
        const currentPhone = checkoutPhoneInput.value.trim();
        if (isCheckoutPhonePlaceholderValue(currentPhone) || currentPhone === lastAutofilledCheckoutPhone) {
            checkoutPhoneInput.value = nextPhone;
            ensurePhonePrefixValue(checkoutPhoneInput);
            lastAutofilledCheckoutPhone = checkoutPhoneInput.value.trim();
        }
    }
}

window.zamzamSyncCheckoutProfileFields = (user = null) => {
    if (user) {
        syncCheckoutProfileFields(user);
        return;
    }

    if (latestCheckoutProfileUser) {
        syncCheckoutProfileFields(latestCheckoutProfileUser);
    }
};

function getCartSubtotal() {
    const appApi = getAppApi();
    if (!appApi) {
        return 0;
    }
    return appApi.getCartTotals().totalPriceValue || 0;
}

function validateCheckoutConsents() {
    if (!checkoutOfertaConsent?.checked || !checkoutPolicyConsent?.checked) {
        window.alert("Подтвердите согласие с офертой и политикой конфиденциальности.");
        return false;
    }
    return true;
}

function getBonusSpentValue() {
    return Math.max(0, Number(checkoutBonusSpent?.value || 0));
}

function clampBonusSpent(nextValue) {
    const subtotal = getCartSubtotal();
    return Math.max(0, Math.min(nextValue, currentBonusBalance, subtotal));
}

function syncBonusUi() {
    if (checkoutBonusBalanceText) {
        checkoutBonusBalanceText.textContent = `Доступно бонусов: ${currentBonusBalance}`;
    }

    if (!checkoutBonusSpent) {
        return;
    }

    const clampedValue = clampBonusSpent(getBonusSpentValue());
    checkoutBonusSpent.max = `${Math.max(0, Math.min(currentBonusBalance, getCartSubtotal()))}`;
    checkoutBonusSpent.value = `${clampedValue}`;

    if (checkoutPreviewTotal) {
        const appApi = getAppApi();
        if (appApi) {
            checkoutPreviewTotal.textContent = appApi.formatPrice(getCartSubtotal() - clampedValue);
        }
    }
}

function setHint(message, isError = false) {
    if (!authHint) {
        return;
    }

    authHint.textContent = message;
    authHint.style.color = isError ? "#9f2d0f" : "";
}

function hasRegisterConsents() {
    return Boolean(authRegisterOfertaConsent?.checked && authRegisterPolicyConsent?.checked);
}

function showRegisterConsentWarning() {
    authRegisterConsents?.classList.add("is-attention");
    setHint("Подтвердите согласие с офертой и политикой конфиденциальности.", true);

    const missingConsent = !authRegisterOfertaConsent?.checked
        ? authRegisterOfertaConsent
        : authRegisterPolicyConsent;
    missingConsent?.focus();
}

function syncRecoveryStep() {
    authRecoveryTokenField?.classList.toggle("is-hidden", !recoveryCodeSent);
    authRecoveryPasswordField?.classList.toggle("is-hidden", !recoveryCodeSent);
    authResetSubmit?.classList.toggle("is-hidden", !recoveryCodeSent);
    authRecoverySubmit?.classList.toggle("is-hidden", recoveryCodeSent);

    if (authRecoveryToken) {
        authRecoveryToken.required = recoveryCodeSent;
    }
    if (authRecoveryPassword) {
        authRecoveryPassword.required = recoveryCodeSent;
    }
}

function setAccountPhoneHint(message, isError = false) {
    if (!accountPhoneHint) {
        return;
    }

    accountPhoneHint.textContent = message;
    accountPhoneHint.style.color = isError ? "#9f2d0f" : "";
}

function syncAuthMode() {
    authLoginForm?.classList.toggle("is-hidden", authMode !== "login");
    authRegisterForm?.classList.toggle("is-hidden", authMode !== "register");
    authRecoveryForm?.classList.toggle("is-hidden", authMode !== "recovery");
    authTabLogin?.classList.toggle("is-active", authMode === "login");
    authTabRegister?.classList.toggle("is-active", authMode === "register");
    if (authBack) {
        authBack.style.visibility = authMode === "recovery" ? "visible" : "hidden";
    }
}

function setAuthMode(mode = "login") {
    authMode = ["login", "register", "recovery"].includes(mode) ? mode : "login";
    if (authMode === "recovery") {
        recoveryCodeSent = false;
    }
    syncAuthMode();
    syncRecoveryStep();
    setHint("");

    if (authMode === "login") {
        if (authPhone && !authPhone.value.trim()) {
            authPhone.value = getCheckoutPhone();
        }
        return;
    }

    if (authMode === "recovery") {
        if (authRecoveryEmail && authRegisterEmail?.value.trim() && !authRecoveryEmail.value.trim()) {
            authRecoveryEmail.value = authRegisterEmail.value.trim();
        }
        if (authRecoveryToken) {
            authRecoveryToken.value = "";
        }
        if (authRecoveryPassword) {
            authRecoveryPassword.value = "";
        }
        return;
    }

    if (authRegisterPhone && !authRegisterPhone.value.trim()) {
        authRegisterPhone.value = getCheckoutPhone();
    }
    if (authRegisterName && !authRegisterName.value.trim()) {
        authRegisterName.value = getCheckoutName();
    }
}

window.setZamzamAuthMode = setAuthMode;

function syncSharedBackdrop() {
    const isAnyModalOpen =
        authModal?.classList.contains("is-open") ||
        authRequiredModal?.classList.contains("is-open") ||
        !accountSection?.classList.contains("is-hidden");

    authBackdrop?.classList.toggle("is-open", Boolean(isAnyModalOpen));
    document.body.classList.toggle("admin-open", Boolean(isAnyModalOpen));
}

function openAuthModal(mode = "login") {
    setAuthMode(mode);
    authModal?.classList.add("is-open");
    authModal?.setAttribute("aria-hidden", "false");
    syncSharedBackdrop();
}

window.openZamzamAuthModal = async function openZamzamAuthModal(mode = "login") {
    refreshSessionToken();
    if (sessionToken) {
        await loadAccount();
        if (sessionToken) {
            showAccountSection();
            return false;
        }
    }

    openAuthModal(mode);
    return false;
};

function closeAuthModal() {
    authModal?.classList.remove("is-open");
    authModal?.setAttribute("aria-hidden", "true");
    setHint("");
    syncSharedBackdrop();
}

function openAuthRequiredModal() {
    authRequiredModal?.classList.add("is-open");
    authRequiredModal?.setAttribute("aria-hidden", "false");
    syncSharedBackdrop();
}

function closeAuthRequiredModal() {
    authRequiredModal?.classList.remove("is-open");
    authRequiredModal?.setAttribute("aria-hidden", "true");
    syncSharedBackdrop();
}

function openAccountModal() {
    if (!accountSection) {
        return;
    }

    accountSection.classList.remove("is-hidden");
    accountSection.setAttribute("aria-hidden", "false");
    syncSharedBackdrop();
}

function closeAccountModal() {
    if (!accountSection) {
        return;
    }

    accountSection.classList.add("is-hidden");
    accountSection.setAttribute("aria-hidden", "true");
    setAccountPhoneHint("");
    syncSharedBackdrop();
}

function openAuthFromRequired(mode) {
    closeAuthRequiredModal();
    openAuthModal(mode);
}

function updateLoginButton() {
    refreshSessionToken();
    if (loginButton) {
        loginButton.textContent = sessionToken ? "Кабинет" : "Войти";
    }
    accountFloatingTrigger?.classList.toggle("is-hidden", !sessionToken);
}

function getSessionHeaders() {
    refreshSessionToken();
    return {
        "Content-Type": "application/json",
        Authorization: `Bearer ${sessionToken}`,
    };
}

function clearStreetSuggestions() {
    if (checkoutAddressSuggestions) {
        checkoutAddressSuggestions.innerHTML = "";
    }
}

async function loadStreetSuggestions(query) {
    const normalizedQuery = (query || "").trim();
    if (!checkoutAddressSuggestions || normalizedQuery.length < 2) {
        clearStreetSuggestions();
        return;
    }

    refreshSessionToken();
    if (!sessionToken) {
        clearStreetSuggestions();
        return;
    }

    streetSuggestionsController?.abort();
    streetSuggestionsController = new AbortController();

    try {
        const response = await fetch(`/api/orders/address/streets?q=${encodeURIComponent(normalizedQuery)}`, {
            headers: getSessionHeaders(),
            signal: streetSuggestionsController.signal,
        });
        if (!response.ok) {
            clearStreetSuggestions();
            return;
        }

        const payload = await response.json().catch(() => ({}));
        const items = Array.isArray(payload?.items) ? payload.items : [];
        checkoutAddressSuggestions.innerHTML = "";
        items.forEach((item) => {
            const value = String(item?.value || "").trim();
            if (!value) {
                return;
            }
            const option = document.createElement("option");
            option.value = value;
            option.label = String(item?.name || value);
            checkoutAddressSuggestions.appendChild(option);
        });
    } catch (error) {
        if (error?.name !== "AbortError") {
            clearStreetSuggestions();
        }
    }
}

function scheduleStreetSuggestions() {
    window.clearTimeout(streetSuggestionsTimeoutId);
    streetSuggestionsTimeoutId = window.setTimeout(() => {
        loadStreetSuggestions(checkoutAddressInput?.value || "");
    }, 250);
}

const baseUpdateLoginButton = updateLoginButton;
updateLoginButton = function () {
    baseUpdateLoginButton();
    if (loginButton) {
        loginButton.textContent = sessionToken ? "Выйти" : "Войти";
    }
    if (sessionToken) {
        floatingTools?.classList.remove("is-hidden");
    }
};

function formatOrderDate(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "" : date.toLocaleString("ru-RU");
}

function getCheckoutTypeLabel(checkoutType) {
    return checkoutType === "delivery" ? "Доставка" : "Самовывоз";
}

function getOrderStatusClass(status) {
    if (status === "Готовится") {
        return "account-order-status-preparing";
    }
    if (status === "Готов к выдаче") {
        return "account-order-status-ready";
    }
    if (status === "Приготовлен") {
        return "account-order-status-ready";
    }
    return "";
}

function renderCurrentOrder(order) {
    if (!accountCurrentOrderCard) {
        return;
    }

    if (!order) {
        accountCurrentOrderCard.innerHTML = '<div class="account-order-empty">Активного заказа пока нет.</div>';
        return;
    }

    const itemsText = order.items.map((item) => `${item.title} x ${item.quantity}`).join(", ");
    const addressText = order.delivery_address || "Самовывоз";

    accountCurrentOrderCard.innerHTML = `
        <article class="account-order-card account-order-card-current">
            <div class="account-order-head">
                <strong>Заказ №${order.id}</strong>
                <span class="account-order-status ${getOrderStatusClass(order.status)}">${order.status}</span>
            </div>
            <div class="account-order-meta">Тип: ${getCheckoutTypeLabel(order.checkout_type)} • Создан: ${formatOrderDate(order.created_at)}</div>
            <div class="account-order-meta">Сумма: ${order.total_amount} руб. • Бонусы: +${order.bonus_awarded}</div>
            <div class="account-order-meta">Получение: ${addressText}</div>
            <div class="account-order-items">${itemsText}</div>
        </article>
    `;
}

function renderOrders(orders) {
    if (!accountOrdersList) {
        return;
    }

    if (!orders.length) {
        accountOrdersList.innerHTML = '<div class="account-order-empty">После первого подтвержденного заказа история появится здесь.</div>';
        renderCurrentOrder(null);
        return;
    }

    const activeOrder = orders.find((order) => ACTIVE_ORDER_STATUSES.has(order.status)) || null;
    renderCurrentOrder(activeOrder);

    accountOrdersList.innerHTML = orders
        .map((order) => {
            const itemsText = order.items.map((item) => `${item.title} x ${item.quantity}`).join(", ");
            return `
                <article class="account-order-card">
                    <div class="account-order-head">
                        <strong>Заказ №${order.id}</strong>
                        <span class="account-order-status ${getOrderStatusClass(order.status)}">${order.status}</span>
                    </div>
                    <div class="account-order-meta">Создан: ${formatOrderDate(order.created_at)}</div>
                    <div class="account-order-meta">Сумма: ${order.total_amount} руб. • Бонусы: +${order.bonus_awarded}</div>
                    <div class="account-order-items">${itemsText}</div>
                </article>
            `;
        })
        .join("");
}

function showAccountSection() {
    openAccountModal();
}

function isAccountModalOpen() {
    return Boolean(accountSection && !accountSection.classList.contains("is-hidden"));
}

async function loadAccount() {
    refreshSessionToken();
    if (!sessionToken) {
        currentBonusBalance = 0;
        latestCheckoutProfileUser = null;
        window.zamzamApp?.setAdminMode?.(false);
        updateLoginButton();
        syncBonusUi();
        closeAccountModal();
        return;
    }

    try {
        let [dashboardResponse, ordersResponse] = await Promise.all([
            fetch("/api/user/me", { headers: { Authorization: `Bearer ${sessionToken}` } }),
            fetch("/api/orders/my", { headers: { Authorization: `Bearer ${sessionToken}` } }),
        ]);

        if (dashboardResponse.status === 401 || ordersResponse.status === 401) {
            const refreshed = await refreshAccessToken();
            if (refreshed) {
                refreshSessionToken();
                [dashboardResponse, ordersResponse] = await Promise.all([
                    fetch("/api/user/me", { headers: { Authorization: `Bearer ${sessionToken}` } }),
                    fetch("/api/orders/my", { headers: { Authorization: `Bearer ${sessionToken}` } }),
                ]);
            }
        }

        if (dashboardResponse.status === 401 || ordersResponse.status === 401) {
            clearAuthTokens();
            currentBonusBalance = 0;
            latestCheckoutProfileUser = null;
            window.zamzamApp?.setAdminMode?.(false);
            updateLoginButton();
            syncBonusUi();
            closeAccountModal();
            return;
        }

        if (!dashboardResponse.ok || !ordersResponse.ok) {
            throw new Error("Не удалось загрузить личный кабинет.");
        }

        const dashboard = await dashboardResponse.json();
        const ordersPage = await ordersResponse.json();
        currentBonusBalance = dashboard.user.bonus_balance || 0;
        window.zamzamApp?.setAdminMode?.(Boolean(dashboard.user.is_admin));

        if (accountBonusBalance) {
            accountBonusBalance.textContent = `${dashboard.user.bonus_balance}`;
        }
        if (accountUserPhone) {
            accountUserPhone.textContent = dashboard.user.phone;
        }
        if (accountPhoneInput) {
            accountPhoneInput.value = dashboard.user.phone;
        }
        syncCheckoutProfileFields(dashboard.user);
        if (accountOrderStatus) {
            accountOrderStatus.textContent = dashboard.latest_order_status || "Заказов пока нет";
        }
        if (accountOrdersCount) {
            accountOrdersCount.textContent = `Активных заказов: ${dashboard.active_orders_count}`;
        }

        renderOrders(ordersPage.items || []);
        updateLoginButton();
        syncBonusUi();
    } catch (error) {
        console.error(error);
    }
}

window.loadZamzamAccount = loadAccount;

async function syncPendingPayment() {
    refreshSessionToken();
    const paymentId = readPersistentStorage(PENDING_PAYMENT_STORAGE_KEY);
    if (!paymentId || !sessionToken) {
        pendingPaymentSyncRetryIndex = 0;
        if (pendingPaymentSyncTimeoutId) {
            window.clearTimeout(pendingPaymentSyncTimeoutId);
            pendingPaymentSyncTimeoutId = null;
        }
        return;
    }

    try {
        const response = await fetch(`/api/payments/${encodeURIComponent(paymentId)}/sync`, {
            method: "POST",
            headers: { Authorization: `Bearer ${sessionToken}` },
        });
        const payload = await response.json().catch(() => ({}));
        if (response.ok && payload?.order_id) {
            removePersistentStorage(PENDING_PAYMENT_STORAGE_KEY);
            pendingPaymentSyncRetryIndex = 0;
            if (pendingPaymentSyncTimeoutId) {
                window.clearTimeout(pendingPaymentSyncTimeoutId);
                pendingPaymentSyncTimeoutId = null;
            }
            await loadAccount();
            if (typeof window.showZamzamOrderSuccessModal === "function") {
                window.showZamzamOrderSuccessModal("Ваш заказ принят. Скоро с вами свяжется наш оператор.");
            } else if (typeof window.showZamzamToast === "function") {
                window.showZamzamToast("Заказ успешно оплачен");
            }
        }
    } catch (error) {
        console.error(error);
    }

    if (!readPersistentStorage(PENDING_PAYMENT_STORAGE_KEY)) {
        pendingPaymentSyncRetryIndex = 0;
        return;
    }
    if (pendingPaymentSyncTimeoutId || pendingPaymentSyncRetryIndex >= PENDING_PAYMENT_SYNC_RETRY_DELAYS.length) {
        return;
    }
    const retryDelay = PENDING_PAYMENT_SYNC_RETRY_DELAYS[pendingPaymentSyncRetryIndex];
    pendingPaymentSyncRetryIndex += 1;
    pendingPaymentSyncTimeoutId = window.setTimeout(() => {
        pendingPaymentSyncTimeoutId = null;
        syncPendingPayment();
    }, retryDelay);
}

async function handleAuthSuccess(payload) {
    setAuthTokens(payload);
    updateLoginButton();
    closeAuthModal();
    await loadAccount();
    showAccountSection();
}

async function login(event) {
    event.preventDefault();

    const phone = ensurePhonePrefixValue(authPhone).trim();
    const password = authPassword?.value.trim() || "";
    if (!phone || !password) {
        setHint("Введите номер телефона и пароль.", true);
        return;
    }

    if (authLoginSubmit) {
        authLoginSubmit.disabled = true;
    }
    setHint("");

    try {
        const response = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ phone, password }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload?.detail || "Не удалось выполнить вход.");
        }

        await handleAuthSuccess(payload);
    } catch (error) {
        setHint(error.message || "Не удалось выполнить вход.", true);
    } finally {
        if (authLoginSubmit) {
            authLoginSubmit.disabled = false;
        }
    }
}

async function register(event) {
    event.preventDefault();

    const phone = ensurePhonePrefixValue(authRegisterPhone).trim();
    const email = authRegisterEmail?.value.trim() || "";
    const password = authRegisterPassword?.value.trim() || "";
    const fullName = authRegisterName?.value.trim() || getCheckoutName() || null;
    if (!phone || !email || !password) {
        setHint("Введите номер телефона, email и пароль.", true);
        return;
    }

    if (!hasRegisterConsents()) {
        showRegisterConsentWarning();
        return;
    }

    if (authRegisterSubmit) {
        authRegisterSubmit.disabled = true;
    }
    setHint("");

    try {
        const response = await fetch("/api/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                phone,
                email,
                password,
                full_name: fullName,
            }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload?.detail || "Не удалось завершить регистрацию.");
        }

        await handleAuthSuccess(payload);
    } catch (error) {
        setHint(error.message || "Не удалось завершить регистрацию.", true);
    } finally {
        if (authRegisterSubmit) {
            authRegisterSubmit.disabled = false;
        }
    }
}

async function requestPasswordRecovery(event) {
    event.preventDefault();

    const email = authRecoveryEmail?.value.trim() || "";
    if (!email) {
        setHint("Введите email для восстановления пароля.", true);
        return;
    }

    if (authRecoverySubmit) {
        authRecoverySubmit.disabled = true;
    }
    setHint("");

    try {
        const response = await fetch("/api/auth/password/recovery", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload?.detail || "Не удалось отправить письмо.");
        }

        recoveryCodeSent = true;
        syncRecoveryStep();
        setHint("Если email зарегистрирован, код восстановления отправлен.", false);
        authRecoveryToken?.focus();
    } catch (error) {
        setHint(error.message || "Не удалось отправить письмо.", true);
    } finally {
        if (authRecoverySubmit) {
            authRecoverySubmit.disabled = false;
        }
    }
}

async function resetPassword(event) {
    event.preventDefault();

    const token = authRecoveryToken?.value.trim() || "";
    const password = authRecoveryPassword?.value.trim() || "";
    if (!token || !password) {
        setHint("Введите код из письма и новый пароль.", true);
        return;
    }

    if (authResetSubmit) {
        authResetSubmit.disabled = true;
    }
    setHint("");

    try {
        const response = await fetch("/api/auth/password/reset", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token, password }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload?.detail || "Не удалось сменить пароль.");
        }

        setHint("Пароль успешно изменен. Теперь можно войти.", false);
        setAuthMode("login");
        if (authPassword) {
            authPassword.value = "";
            authPassword.focus();
        }
    } catch (error) {
        setHint(error.message || "Не удалось сменить пароль.", true);
    } finally {
        if (authResetSubmit) {
            authResetSubmit.disabled = false;
        }
    }
}

async function updatePhone(event) {
    event.preventDefault();

    const phone = ensurePhonePrefixValue(accountPhoneInput).trim();
    if (!phone) {
        setAccountPhoneHint("Введите номер телефона.", true);
        return;
    }

    if (accountPhoneSubmit) {
        accountPhoneSubmit.disabled = true;
    }
    setAccountPhoneHint("");

    try {
        const response = await fetch("/api/user/me", {
            method: "PATCH",
            headers: getSessionHeaders(),
            body: JSON.stringify({ phone }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload?.detail || "Не удалось обновить номер телефона.");
        }

        if (accountUserPhone) {
            accountUserPhone.textContent = payload.phone;
        }
        if (accountPhoneInput) {
            accountPhoneInput.value = payload.phone;
        }
        syncCheckoutProfileFields({
            full_name: latestCheckoutProfileUser?.full_name || "",
            phone: payload.phone,
        });
        setAccountPhoneHint("Номер телефона обновлен.");
    } catch (error) {
        setAccountPhoneHint(error.message || "Не удалось обновить номер телефона.", true);
    } finally {
        if (accountPhoneSubmit) {
            accountPhoneSubmit.disabled = false;
        }
    }
}

function buildOrderPayload(appApi) {
    const entries = appApi.getCartEntries();
    const checkoutState = appApi.getCheckoutState();
    const customerName = getCheckoutName();
    const customerPhone = getCheckoutPhone();
    const deliveryStreet = checkoutAddressInput?.value.trim() || "";
    const deliveryHouse = checkoutHouseInput?.value.trim() || "";
    const deliveryFlat = checkoutFlatInput?.value.trim() || "";
    const entrance = document.getElementById("checkout-entrance")?.value.trim() || "";
    const comment = document.getElementById("checkout-comment")?.value.trim() || "";
    const isDelivery = checkoutState.checkoutType === "delivery";

    return {
        entries,
        customerName,
        customerPhone,
        bonusSpent: clampBonusSpent(getBonusSpentValue()),
        payload: {
            customer_name: customerName,
            customer_phone: customerPhone,
            checkout_type: checkoutState.checkoutType,
            branch_code: checkoutState.branchCode,
            payment_type: "card",
            delivery_address: null,
            delivery_street: isDelivery ? deliveryStreet || null : null,
            delivery_house: isDelivery ? deliveryHouse || null : null,
            delivery_flat: isDelivery ? deliveryFlat || null : null,
            entrance: isDelivery ? entrance || null : null,
            comment: comment || null,
            cutlery_count: checkoutState.cutleryItemsCount,
            bonus_spent: clampBonusSpent(getBonusSpentValue()),
            items: entries.map((item) => ({
                id: item.id,
                title: item.title,
                price: item.price,
                quantity: item.quantity,
            })),
        },
    };
}

async function submitOrderWithSession() {
    const appApi = getAppApi();
    if (!appApi) {
        return;
    }

    const { entries, customerName, customerPhone, payload } = buildOrderPayload(appApi);
    const checkoutSubmit = document.getElementById("checkout-submit");

    if (!entries.length) {
        window.alert("Сначала добавьте блюда в корзину.");
        return;
    }

    if (!customerName || !isValidCheckoutPhone(customerPhone)) {
        showCheckoutWarning("Заполните имя и телефон.");
        document.getElementById("checkout-phone")?.focus();
        return;
    }

    if (payload.checkout_type === "delivery" && !payload.delivery_street) {
        showCheckoutWarning("Укажите улицу доставки.");
        checkoutAddressInput?.focus();
        return;
    }

    if (payload.checkout_type === "delivery" && !payload.delivery_house) {
        showCheckoutWarning("Укажите номер дома.");
        checkoutHouseInput?.focus();
        return;
    }

    if (!validateCheckoutConsents()) {
        return;
    }

    syncBonusUi();
    checkoutSubmit.disabled = true;

    try {
        const response = await fetch("/api/orders", {
            method: "POST",
            headers: getSessionHeaders(),
            body: JSON.stringify(payload),
        });
        const responsePayload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(getResponseErrorMessage(responsePayload, "Не удалось оформить заказ."));
        }

        if (responsePayload?.order_id && !responsePayload?.confirmation_url) {
            currentBonusBalance = Math.max(
                0,
                Number(responsePayload.bonus_balance ?? currentBonusBalance - payload.bonus_spent),
            );
            if (checkoutBonusSpent) {
                checkoutBonusSpent.value = "0";
            }
            syncBonusUi();
            appApi.resetAfterOrder();
            await loadAccount();
            window.showZamzamOrderSuccessModal?.("Ваш заказ принят. Скоро с вами свяжется наш оператор.");
            return;
        }

        if (!responsePayload?.confirmation_url) {
            throw new Error("Не удалось получить ссылку на оплату.");
        }
        if (responsePayload.payment_id) {
            writePersistentStorage(PENDING_PAYMENT_STORAGE_KEY, responsePayload.payment_id);
        }
        window.location.href = responsePayload.confirmation_url;
        currentBonusBalance = Math.max(0, currentBonusBalance - payload.bonus_spent);
        if (checkoutBonusSpent) {
            checkoutBonusSpent.value = "0";
        }
    } catch (error) {
        showCheckoutWarning(error.message || "Не удалось оформить заказ.");
    } finally {
        checkoutSubmit.disabled = false;
    }
}

async function submitOrder(event) {
    event.preventDefault();
    event.stopImmediatePropagation();
    refreshSessionToken();

    const appApi = getAppApi();
    if (!appApi) {
        showCheckoutWarning("Не удалось подготовить заказ. Обновите страницу и попробуйте снова.");
        return;
    }

    const { entries, customerName, customerPhone } = buildOrderPayload(appApi);

    if (!entries.length) {
        window.alert("Сначала добавьте блюда в корзину.");
        return;
    }

    if (!customerName || !isValidCheckoutPhone(customerPhone)) {
        showCheckoutWarning("Заполните имя и телефон.");
        document.getElementById("checkout-phone")?.focus();
        return;
    }

    if (!validateCheckoutConsents()) {
        return;
    }

    if (!sessionToken) {
        openAuthRequiredModal();
        return;
    }

    await submitOrderWithSession();
}

function logout() {
    const refreshToken = readPersistentStorage(REFRESH_STORAGE_KEY);
    fetch("/api/auth/logout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
    }).catch(() => null).finally(() => {
        clearAuthTokens();
        currentBonusBalance = 0;
        latestCheckoutProfileUser = null;
        window.zamzamApp?.setAdminMode?.(false);
        closeAuthModal();
        closeAuthRequiredModal();
        closeAccountModal();
        updateLoginButton();
        syncBonusUi();
    });
}

async function handleLoginButtonClick(event) {
    event?.preventDefault?.();
    refreshSessionToken();
    if (sessionToken) {
        logout();
        return;
    }
    await window.openZamzamAuthModal("login");
}

if (loginButton) {
    loginButton.onclick = handleLoginButtonClick;
    loginButton.addEventListener("click", handleLoginButtonClick);
}

accountFloatingTrigger?.addEventListener("click", async () => {
    refreshSessionToken();
    await loadAccount();
    if (sessionToken) {
        showAccountSection();
        return;
    }
    await window.openZamzamAuthModal("login");
});

authTabLogin?.addEventListener("click", () => {
    setAuthMode("login");
});
authTabRegister?.addEventListener("click", () => {
    setAuthMode("register");
});
authForgotPassword?.addEventListener("click", () => {
    setAuthMode("recovery");
});
authBack?.addEventListener("click", () => {
    setAuthMode("login");
});
authBackdrop?.addEventListener("click", () => {
    closeAuthModal();
    closeAuthRequiredModal();
    closeAccountModal();
});
authClose?.addEventListener("click", closeAuthModal);
authRequiredClose?.addEventListener("click", closeAuthRequiredModal);
accountClose?.addEventListener("click", closeAccountModal);
authRequiredLogin?.addEventListener("click", () => {
    openAuthFromRequired("login");
});
authRequiredRegister?.addEventListener("click", () => {
    openAuthFromRequired("register");
});
authLoginForm?.addEventListener("submit", login);
authRegisterForm?.addEventListener("submit", register);
authRecoveryForm?.addEventListener("submit", requestPasswordRecovery);
authResetSubmit?.addEventListener("click", resetPassword);
authRegisterSubmit?.addEventListener(
    "click",
    (event) => {
        if (hasRegisterConsents()) {
            return;
        }

        event.preventDefault();
        event.stopImmediatePropagation();
        showRegisterConsentWarning();
    },
    true,
);
[authRegisterOfertaConsent, authRegisterPolicyConsent].forEach((consent) => {
    consent?.addEventListener("invalid", (event) => {
        event.preventDefault();
        showRegisterConsentWarning();
    });
    consent?.addEventListener("change", () => {
        if (hasRegisterConsents()) {
            authRegisterConsents?.classList.remove("is-attention");
            setHint("");
        }
    });
});
accountCurrentRefresh?.addEventListener("click", loadAccount);
accountHistoryRefresh?.addEventListener("click", loadAccount);
accountPhoneForm?.addEventListener("submit", updatePhone);
checkoutAddressInput?.addEventListener("input", scheduleStreetSuggestions);
checkoutAddressInput?.addEventListener("focus", scheduleStreetSuggestions);
checkoutForm?.addEventListener("submit", submitOrder, true);

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeAuthModal();
        closeAuthRequiredModal();
        closeAccountModal();
    }
});

updateLoginButton();
syncBonusUi();
syncAuthMode();

if (sessionToken) {
    loadAccount();
    syncPendingPayment();
}

checkoutBonusSpent?.addEventListener("input", syncBonusUi);
checkoutButton?.addEventListener("click", () => {
    window.setTimeout(syncBonusUi, 0);
});
document.getElementById("cart-checkout-type-pickup")?.addEventListener("click", () => {
    window.setTimeout(syncBonusUi, 0);
});
document.getElementById("cart-checkout-type-delivery")?.addEventListener("click", () => {
    window.setTimeout(syncBonusUi, 0);
});

window.setInterval(async () => {
    refreshSessionToken();
    if (!sessionToken || !isAccountModalOpen() || document.hidden || accountAutoRefreshInFlight) {
        return;
    }

    accountAutoRefreshInFlight = true;
    try {
        await loadAccount();
    } finally {
        accountAutoRefreshInFlight = false;
    }
}, 15000);
})();

```

## 📄 `static\app.js`

```javascript
const cart = new Map();
const FREE_DELIVERY_AMOUNT = 5000;
const SESSION_STORAGE_KEY = "zamzam_session_token";

function readPersistentStorage(key) {
    try {
        return window.localStorage.getItem(key) || window.sessionStorage.getItem(key) || "";
    } catch (error) {
        return window.sessionStorage.getItem(key) || "";
    }
}

const formatPrice = (value) => `${value.toLocaleString("ru-RU")} руб.`;

function getAdminHeaders(extraHeaders = {}) {
    const token = readPersistentStorage(SESSION_STORAGE_KEY);
    return token ? { ...extraHeaders, Authorization: `Bearer ${token}` } : { ...extraHeaders };
}

const orderItems = document.getElementById("order-items");
const totalPrice = document.getElementById("total-price");
const itemsCount = document.getElementById("items-count");
const cutleryCount = document.getElementById("cutlery-count");
const cutlerySummaryItem = document.getElementById("cutlery-summary-item");
const cutleryDecrease = document.getElementById("cutlery-decrease");
const cutleryIncrease = document.getElementById("cutlery-increase");
const floatingCount = document.getElementById("floating-count");
const cartCheckoutNote = document.getElementById("cart-checkout-note");
const filtersContainer = document.getElementById("filters");
const menuGrid = document.getElementById("menu-grid");
const menuSection = document.getElementById("menu");
const cartDrawer = document.getElementById("order-panel");
const cartBackdrop = document.getElementById("cart-backdrop");
const checkoutBackdrop = document.getElementById("checkout-backdrop");
const footerMapBackdrop = document.getElementById("footer-map-backdrop");
const cartToggle = document.getElementById("cart-toggle");
const menuStartTrigger = document.getElementById("menu-start-trigger");
const cartOpenInline = document.getElementById("cart-open-inline");
const cartOpenTopbar = document.getElementById("cart-open-topbar");
const cartOpenHero = document.getElementById("cart-open-hero");
const cartClose = document.getElementById("cart-close");
const checkoutButton = document.getElementById("checkout-button");
const checkoutModal = document.getElementById("checkout-modal");
const checkoutModalFormWrap = document.querySelector("#checkout-modal .checkout-modal-form-wrap");
const checkoutClose = document.getElementById("checkout-close");
const footerMapModal = document.getElementById("footer-map-modal");
const footerMapOpen = document.getElementById("footer-map-open");
const footerMapClose = document.getElementById("footer-map-close");
const checkoutForm = document.getElementById("checkout-form");
const checkoutTypePickup = document.getElementById("cart-checkout-type-pickup");
const checkoutTypeDelivery = document.getElementById("cart-checkout-type-delivery");
const cartBranchMalyshava = document.getElementById("cart-branch-malyshava");
const cartBranchSuh = document.getElementById("cart-branch-suh");
const checkoutPaymentCash = document.getElementById("checkout-payment-cash");
const checkoutPaymentCard = document.getElementById("checkout-payment-card");
const checkoutDeliveryFields = document.getElementById("checkout-delivery-fields");
const checkoutAddress = document.getElementById("checkout-address");
const checkoutHouse = document.getElementById("checkout-house");
const checkoutFlat = document.getElementById("checkout-flat");
const checkoutEntrance = document.getElementById("checkout-entrance");
const checkoutComment = document.getElementById("checkout-comment");
const checkoutName = document.getElementById("checkout-name");
const checkoutPhone = document.getElementById("checkout-phone");
const checkoutSubmit = document.getElementById("checkout-submit");
const checkoutNote = document.getElementById("checkout-note");
const checkoutPreviewItems = document.getElementById("checkout-preview-items");
const checkoutPreviewCutlery = document.getElementById("checkout-preview-cutlery");
const checkoutPreviewTotal = document.getElementById("checkout-preview-total");
const checkoutPreviewLines = document.getElementById("checkout-preview-lines");
const checkoutBonusSpent = document.getElementById("checkout-bonus-spent");
const checkoutBonusDecrease = document.getElementById("checkout-bonus-decrease");
const checkoutBonusIncrease = document.getElementById("checkout-bonus-increase");
const floatingTools = document.querySelector(".floating-tools");
const adminToggle = document.getElementById("admin-toggle");
const adminModal = document.getElementById("admin-modal");
const adminModalTitle = document.getElementById("admin-modal-title");
const adminBackdrop = document.getElementById("admin-backdrop");
const adminClose = document.getElementById("admin-close");
const adminForm = document.getElementById("admin-form");
const adminItemId = document.getElementById("admin-item-id");
const adminItemVersion = document.getElementById("admin-item-version");
const adminTitle = document.getElementById("admin-title");
const adminDescription = document.getElementById("admin-description");
const adminPrice = document.getElementById("admin-price");
const adminCategory = document.getElementById("admin-category");
const adminImage = document.getElementById("admin-image");
const adminSave = document.getElementById("admin-save");
const adminDelete = (() => {
    const actions = document.querySelector("#admin-form .admin-actions");
    if (!actions) {
        return null;
    }

    const existing = document.getElementById("admin-delete");
    if (existing) {
        return existing;
    }

    const button = document.createElement("button");
    button.id = "admin-delete";
    button.type = "button";
    button.className = "admin-delete is-hidden";
    button.textContent = "Удалить с сайта";
    actions.prepend(button);
    return button;
})();
const heroSection = document.getElementById("hero");
const heroAdminModal = document.getElementById("hero-admin-modal");
const heroAdminClose = document.getElementById("hero-admin-close");
const heroAdminForm = document.getElementById("hero-admin-form");
const heroAdminKicker = document.getElementById("hero-admin-kicker");
const heroAdminTitle = document.getElementById("hero-admin-title");
const heroAdminAddress = document.getElementById("hero-admin-address");
const heroAdminSubtitlePrimary = document.getElementById("hero-admin-subtitle-primary");
const heroAdminSubtitleSecondary = document.getElementById("hero-admin-subtitle-secondary");
const heroAdminSave = document.getElementById("hero-admin-save");
const menuSectionHead = document.querySelector("#menu .section-head > div");
const deliverySectionHead = document.querySelector("#delivery .section-head > div");
const contactSectionHead = document.querySelector("#contact .contact-copy");
const menuSectionAdminModal = document.getElementById("menu-section-admin-modal");
const menuSectionAdminModalTitle = document.getElementById("menu-section-admin-modal-title");
const menuSectionAdminClose = document.getElementById("menu-section-admin-close");
const menuSectionAdminForm = document.getElementById("menu-section-admin-form");
const menuSectionAdminKicker = document.getElementById("menu-section-admin-kicker");
const menuSectionAdminTitle = document.getElementById("menu-section-admin-title");
const menuSectionAdminSave = document.getElementById("menu-section-admin-save");
const menuCategoriesOpen = document.getElementById("menu-categories-open");
const menuCategoriesAdminModal = document.getElementById("menu-categories-admin-modal");
const menuCategoriesAdminClose = document.getElementById("menu-categories-admin-close");
const menuCategoriesAdminForm = document.getElementById("menu-categories-admin-form");
const menuCategoriesAdminList = document.getElementById("menu-categories-admin-list");
const menuCategoriesAdminAdd = document.getElementById("menu-categories-admin-add");
const menuCategoriesAdminSave = document.getElementById("menu-categories-admin-save");
const CART_TOUCH_DRAG_THRESHOLD = 6;
const MENU_START_TRIGGER_OFFSET = 120;

let lastScrollY = window.scrollY;
let activeAdminCard = null;
let activeFilter = filtersContainer?.querySelector(".filter-chip.active")?.dataset.filter || "all";
let adminMode = "edit";
let heroEditControlsBound = false;
let activeSectionEditor = null;
let cutleryItemsCount = 0;
let checkoutType = "pickup";
let checkoutPayment = "card";
let branchCode = "malyshava";
let isDelivery = false;
let cartToastTimeoutId = null;
let revealObserver = null;
let cartLockedScrollY = 0;
let checkoutLockedScrollY = 0;
let orderSuccessScrollY = 0;

menuStartTrigger?.classList.add("button-shiny");

if ("scrollRestoration" in window.history) {
    window.history.scrollRestoration = "auto";
}

const cartToast = (() => {
    const node = document.createElement("div");
    node.className = "cart-toast";
    node.setAttribute("aria-live", "polite");
    document.body.appendChild(node);
    return node;
})();

function ensurePhonePrefixValue(input) {
    if (!input) {
        return "";
    }

    const digits = input.value.replace(/\D/g, "");
    let normalized = digits;

    if (!normalized) {
        normalized = "7";
    } else if (normalized[0] === "8") {
        normalized = `7${normalized.slice(1)}`;
    } else if (normalized[0] !== "7") {
        normalized = `7${normalized}`;
    }

    input.value = `+${normalized}`;
    return input.value;
}

function bindPhonePrefix(input) {
    if (!input) {
        return;
    }

    ensurePhonePrefixValue(input);

    input.addEventListener("focus", () => {
        ensurePhonePrefixValue(input);
    });

    input.addEventListener("input", () => {
        const moveCaretToEnd = input.selectionStart === input.value.length;
        ensurePhonePrefixValue(input);
        if (moveCaretToEnd) {
            input.setSelectionRange(input.value.length, input.value.length);
        }
    });

    input.addEventListener("blur", () => {
        ensurePhonePrefixValue(input);
    });
}

window.zamzamEnsurePhonePrefix = ensurePhonePrefixValue;

function getCards() {
    return Array.from(document.querySelectorAll(".dish-card"));
}

function bindClick(element, handler) {
    if (element) {
        element.addEventListener("click", handler);
    }
}

function setMobileMenuOpenState(isOpen) {
    if (typeof window.setZamzamMobileMenuOpen !== "function") {
        return false;
    }

    window.setZamzamMobileMenuOpen(Boolean(isOpen));
    return true;
}

function closeMobileMenu() {
    setMobileMenuOpenState(false);
}

function syncCartCheckoutNote() {
    if (cartCheckoutNote) {
        if (checkoutType !== "delivery") {
            cartCheckoutNote.textContent = "";
            cartCheckoutNote.hidden = true;
            return;
        }

        cartCheckoutNote.hidden = false;
        const { totalPriceValue } = getCartTotals();
        const remainingToFreeDelivery = Math.max(0, FREE_DELIVERY_AMOUNT - totalPriceValue);
        cartCheckoutNote.innerHTML = remainingToFreeDelivery > 0
            ? `<br>Сумма заказа для бесплатной доставки от ${formatPrice(FREE_DELIVERY_AMOUNT)}<br>До бесплатной доставки осталось ${formatPrice(remainingToFreeDelivery)}`
            : "Доставка будет бесплатной.";
    }
}

function canCheckoutWithCurrentType() {
    return true;
}

const HERO_PARTICLE_SELECTOR = ".hero-kicker, .hero h1, .hero-address, .hero h2 > span";
const heroParticleState = {
    animationFrameId: 0,
    canvas: null,
    ctx: null,
    initialized: false,
    mouse: {
        active: false,
        x: 0,
        y: 0,
    },
    particles: [],
    viewportHeight: 0,
    viewportWidth: 0,
};

function getHeroParticleNodes() {
    return heroSection ? Array.from(heroSection.querySelectorAll(HERO_PARTICLE_SELECTOR)) : [];
}

function normalizeHeroParticleSources() {
    getHeroParticleNodes().forEach((node) => {
        const sourceText = node.dataset.particleSourceText || node.textContent || "";
        node.textContent = sourceText;
        node.dataset.particleSourceText = sourceText;
        node.classList.add("hero-particle-source");
    });
}

function getHeroParticleColor(node) {
    if (node.matches("h1, .hero-gradient-text")) {
        return { r: 255, g: 245, b: 228 };
    }

    if (node.matches(".hero-address")) {
        return { r: 255, g: 224, b: 168 };
    }

    return { r: 255, g: 234, b: 194 };
}

function ensureHeroParticleCanvas() {
    const heroInner = heroSection?.querySelector(".hero-inner");
    if (!heroInner) {
        return null;
    }

    if (!heroParticleState.canvas) {
        const canvas = document.createElement("canvas");
        canvas.className = "hero-particle-canvas";
        heroInner.appendChild(canvas);
        heroParticleState.canvas = canvas;
        heroParticleState.ctx = canvas.getContext("2d");
    }

    return heroParticleState.canvas;
}

function buildHeroParticles() {
    const heroInner = heroSection?.querySelector(".hero-inner");
    const canvas = ensureHeroParticleCanvas();
    const ctx = heroParticleState.ctx;

    if (!heroInner || !canvas || !ctx) {
        return;
    }

    normalizeHeroParticleSources();

    const nodes = getHeroParticleNodes().filter((node) => (node.dataset.particleSourceText || node.textContent || "").trim());
    if (!nodes.length) {
        heroParticleState.particles = [];
        return;
    }

    const innerRect = heroInner.getBoundingClientRect();
    const entries = nodes.map((node) => {
        const rect = node.getBoundingClientRect();
        return {
            color: getHeroParticleColor(node),
            left: rect.left - innerRect.left,
            node,
            text: node.dataset.particleSourceText || node.textContent || "",
            top: rect.top - innerRect.top,
            width: rect.width,
            height: rect.height,
        };
    });

    const minLeft = Math.min(...entries.map((entry) => entry.left));
    const minTop = Math.min(...entries.map((entry) => entry.top));
    const maxRight = Math.max(...entries.map((entry) => entry.left + entry.width));
    const maxBottom = Math.max(...entries.map((entry) => entry.top + entry.height));
    const viewportWidth = Math.max(1, Math.ceil(maxRight - minLeft));
    const viewportHeight = Math.max(1, Math.ceil(maxBottom - minTop));
    const dpr = window.devicePixelRatio || 1;

    canvas.style.left = `${minLeft}px`;
    canvas.style.top = `${minTop}px`;
    canvas.style.width = `${viewportWidth}px`;
    canvas.style.height = `${viewportHeight}px`;
    canvas.width = Math.max(1, Math.floor(viewportWidth * dpr));
    canvas.height = Math.max(1, Math.floor(viewportHeight * dpr));

    heroParticleState.viewportWidth = viewportWidth;
    heroParticleState.viewportHeight = viewportHeight;

    const offscreenCanvas = document.createElement("canvas");
    offscreenCanvas.width = canvas.width;
    offscreenCanvas.height = canvas.height;
    const offscreenCtx = offscreenCanvas.getContext("2d");

    if (!offscreenCtx) {
        heroParticleState.particles = [];
        return;
    }

    offscreenCtx.setTransform(1, 0, 0, 1, 0, 0);
    offscreenCtx.scale(dpr, dpr);
    offscreenCtx.lineJoin = "round";
    offscreenCtx.lineCap = "round";
    offscreenCtx.textBaseline = "top";
    offscreenCtx.clearRect(0, 0, viewportWidth, viewportHeight);

    entries.forEach((entry) => {
        const style = window.getComputedStyle(entry.node);
        const fontSize = parseFloat(style.fontSize) || 16;
        const font = `${style.fontStyle} ${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
        const x = entry.left - minLeft;
        const y = entry.top - minTop;

        offscreenCtx.font = font;
        offscreenCtx.lineWidth = Math.max(1, fontSize * 0.08);
        offscreenCtx.strokeStyle = "rgba(255,255,255,1)";
        offscreenCtx.fillStyle = "rgba(255,255,255,1)";
        offscreenCtx.strokeText(entry.text, x, y);
        offscreenCtx.fillText(entry.text, x, y);
    });

    const imageData = offscreenCtx.getImageData(0, 0, canvas.width, canvas.height).data;
    const particles = [];
    const step = 3;

    entries.forEach((entry) => {
        const color = entry.color;
        const startX = Math.max(0, Math.floor((entry.left - minLeft) * dpr));
        const startY = Math.max(0, Math.floor((entry.top - minTop) * dpr));
        const endX = Math.min(canvas.width, Math.ceil((entry.left - minLeft + entry.width) * dpr));
        const endY = Math.min(canvas.height, Math.ceil((entry.top - minTop + entry.height) * dpr));

        for (let y = startY; y < endY; y += step) {
            for (let x = startX; x < endX; x += step) {
                const index = (y * canvas.width + x) * 4;
                if (imageData[index + 3] <= 0) {
                    continue;
                }

                const targetX = x / dpr;
                const targetY = y / dpr;
                particles.push({
                    color,
                    size: 1.9,
                    targetX,
                    targetY,
                    vx: 0,
                    vy: 0,
                    x: targetX,
                    y: targetY,
                });
            }
        }
    });

    heroParticleState.particles = particles;
}

function animateHeroParticles() {
    const canvas = heroParticleState.canvas;
    const ctx = heroParticleState.ctx;

    if (!canvas || !ctx) {
        heroParticleState.animationFrameId = 0;
        return;
    }

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);

    heroParticleState.particles.forEach((particle) => {
        particle.vx += (particle.targetX - particle.x) * 0.065;
        particle.vy += (particle.targetY - particle.y) * 0.065;

        if (heroParticleState.mouse.active) {
            const dx = particle.x - heroParticleState.mouse.x;
            const dy = particle.y - heroParticleState.mouse.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            const repelRadius = 54;

            if (distance > 0 && distance < repelRadius) {
                const force = (1 - distance / repelRadius) * 0.95;
                particle.vx += (dx / distance) * force;
                particle.vy += (dy / distance) * force;
            }
        }

        particle.vx *= 0.84;
        particle.vy *= 0.84;
        particle.x += particle.vx;
        particle.y += particle.vy;

        ctx.fillStyle = `rgb(${particle.color.r}, ${particle.color.g}, ${particle.color.b})`;
        ctx.fillRect(particle.x, particle.y, particle.size, particle.size);
    });

    heroParticleState.animationFrameId = window.requestAnimationFrame(animateHeroParticles);
}

function updateHeroParticleMouse(event) {
    const canvas = heroParticleState.canvas;
    if (!canvas) {
        return;
    }

    const rect = canvas.getBoundingClientRect();
    heroParticleState.mouse.x = event.clientX - rect.left;
    heroParticleState.mouse.y = event.clientY - rect.top;
}

function initHeroSmokeText() {
    return;
}

function getCartEntries() {
    return [...cart.values()];
}

function getCartTotals() {
    const entries = getCartEntries();
    return {
        entries,
        totalItems: entries.reduce((sum, item) => sum + item.quantity, 0),
        totalPriceValue: entries.reduce((sum, item) => sum + item.price * item.quantity, 0),
    };
}

function openCart() {
    if (!cartDrawer || !cartBackdrop) {
        return;
    }

    closeMobileMenu();
    cartLockedScrollY = window.scrollY || window.pageYOffset || 0;
    document.body.style.position = "fixed";
    document.body.style.top = `-${cartLockedScrollY}px`;
    document.body.style.left = "0";
    document.body.style.right = "0";
    document.body.style.width = "100%";
    cartDrawer.classList.add("is-open");
    cartBackdrop.classList.add("is-open");
    document.body.classList.add("cart-open");
}

function closeCart() {
    cartDrawer?.classList.remove("is-open");
    cartBackdrop?.classList.remove("is-open");
    document.body.classList.remove("cart-open");
    document.body.style.position = "";
    document.body.style.top = "";
    document.body.style.left = "";
    document.body.style.right = "";
    document.body.style.width = "";
    window.scrollTo(0, cartLockedScrollY);
}

function bindTouchScrollFallback(container, isActive) {
    if (!container) {
        return;
    }

    let touchScrollState = null;
    let suppressClickUntil = 0;

    container.addEventListener(
        "touchstart",
        (event) => {
            if (!isActive() || event.touches.length !== 1) {
                touchScrollState = null;
                return;
            }

            const touch = event.touches[0];
            touchScrollState = {
                startX: touch.clientX,
                startY: touch.clientY,
                startScrollTop: container.scrollTop,
                moved: false,
            };
        },
        { passive: true },
    );

    container.addEventListener(
        "touchmove",
        (event) => {
            if (!isActive() || !touchScrollState || event.touches.length !== 1) {
                return;
            }

            const touch = event.touches[0];
            const deltaX = touch.clientX - touchScrollState.startX;
            const deltaY = touch.clientY - touchScrollState.startY;

            if (Math.abs(deltaY) < CART_TOUCH_DRAG_THRESHOLD || Math.abs(deltaY) <= Math.abs(deltaX)) {
                return;
            }

            touchScrollState.moved = true;
            container.scrollTop = touchScrollState.startScrollTop - deltaY;
            event.preventDefault();
        },
        { passive: false },
    );

    const releaseTouchScroll = () => {
        if (touchScrollState?.moved) {
            suppressClickUntil = Date.now() + 250;
        }

        touchScrollState = null;
    };

    container.addEventListener("touchend", releaseTouchScroll, { passive: true });
    container.addEventListener("touchcancel", releaseTouchScroll, { passive: true });
    container.addEventListener(
        "click",
        (event) => {
            if (Date.now() < suppressClickUntil) {
                event.preventDefault();
                event.stopPropagation();
            }
        },
        true,
    );
}

window.setZamzamCartDrawerOpen = (isOpen) => {
    if (isOpen) {
        openCart();
        return;
    }

    closeCart();
};

bindTouchScrollFallback(cartDrawer, () => cartDrawer.classList.contains("is-open"));
bindTouchScrollFallback(checkoutModalFormWrap, () => checkoutModal?.classList.contains("is-open") ?? false);

function showCartToast(message) {
    cartToast.textContent = message;
    cartToast.classList.add("is-visible");

    if (cartToastTimeoutId) {
        window.clearTimeout(cartToastTimeoutId);
    }

    cartToastTimeoutId = window.setTimeout(() => {
        cartToast.classList.remove("is-visible");
    }, 1800);
}

window.showZamzamToast = showCartToast;

function ensureOrderSuccessModal() {
    let backdrop = document.getElementById("order-success-backdrop");
    let modal = document.getElementById("order-success-modal");

    if (backdrop && modal) {
        return { backdrop, modal };
    }

    backdrop = document.createElement("div");
    backdrop.id = "order-success-backdrop";
    backdrop.className = "order-success-backdrop";

    modal = document.createElement("section");
    modal.id = "order-success-modal";
    modal.className = "order-success-modal";
    modal.setAttribute("aria-hidden", "true");
    modal.innerHTML = `
        <div class="order-success-shell">
            <button class="order-success-close" id="order-success-close" type="button" aria-label="Закрыть">x</button>
            <div class="order-success-badge">Заказ принят</div>
            <h3>Спасибо за заказ</h3>
            <p id="order-success-message">Ваш заказ принят. Скоро с вами свяжется наш оператор.</p>
            <div class="order-success-actions">
                <button class="order-success-button button-shiny" id="order-success-button" type="button"><span>Понятно</span></button>
            </div>
        </div>
    `;

    document.body.append(backdrop, modal);

    const closeOrderSuccessModal = () => {
        backdrop.classList.remove("is-open");
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
        document.body.classList.remove("order-success-open");
        document.body.style.position = "";
        document.body.style.top = "";
        document.body.style.left = "";
        document.body.style.right = "";
        document.body.style.width = "";
        window.scrollTo(0, orderSuccessScrollY);
    };

    backdrop.addEventListener("click", closeOrderSuccessModal);
    modal.querySelector("#order-success-close")?.addEventListener("click", closeOrderSuccessModal);
    modal.querySelector("#order-success-button")?.addEventListener("click", closeOrderSuccessModal);
    window.closeZamzamOrderSuccessModal = closeOrderSuccessModal;

    return { backdrop, modal };
}

function showOrderSuccessModal(message = "Ваш заказ принят. Скоро с вами свяжется наш оператор.") {
    const { backdrop, modal } = ensureOrderSuccessModal();
    const messageNode = modal.querySelector("#order-success-message");

    if (messageNode) {
        messageNode.textContent = message;
    }

    orderSuccessScrollY = window.scrollY || window.pageYOffset || 0;
    document.body.style.position = "fixed";
    document.body.style.top = `-${orderSuccessScrollY}px`;
    document.body.style.left = "0";
    document.body.style.right = "0";
    document.body.style.width = "100%";
    document.body.classList.add("order-success-open");
    backdrop.classList.add("is-open");
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
}

window.showZamzamOrderSuccessModal = showOrderSuccessModal;

function ensureRevealObserver() {
    if (revealObserver || !("IntersectionObserver" in window)) {
        return;
    }

    revealObserver = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) {
                    return;
                }

                entry.target.classList.add("is-visible");
                revealObserver.unobserve(entry.target);
            });
        },
        {
            threshold: 0.12,
            rootMargin: "0px 0px -8% 0px",
        },
    );
}

function registerRevealElement(element, index = 0) {
    if (!element || element.classList.contains("is-hidden")) {
        return;
    }

    if (!("IntersectionObserver" in window)) {
        element.classList.add("is-visible");
        return;
    }

    ensureRevealObserver();
    element.classList.add("reveal-on-scroll");
    element.style.setProperty("--reveal-delay", `${Math.min(index, 8) * 70}ms`);
    revealObserver?.observe(element);
}

function initRevealAnimations() {
    const groups = [
        { selector: ".hero-inner > *", stagger: 90 },
        { selector: ".section-head", stagger: 0 },
        { selector: ".account-summary-card", stagger: 80 },
        { selector: ".account-orders", stagger: 120 },
        { selector: ".dish-card", stagger: 70 },
        { selector: ".step-card", stagger: 90 },
        { selector: ".review-card", stagger: 90 },
        { selector: ".contact-copy", stagger: 0 },
        { selector: ".contact-card", stagger: 120 },
        { selector: ".site-footer-inner > *", stagger: 100 },
    ];

    groups.forEach((group) => {
        document.querySelectorAll(group.selector).forEach((element, index) => {
            registerRevealElement(element, Math.round((index * group.stagger) / 70));
        });
    });
}

function syncCheckoutPreview() {
    const { entries, totalItems, totalPriceValue } = getCartTotals();

    if (checkoutPreviewItems) {
        checkoutPreviewItems.textContent = `${totalItems}`;
    }
    if (checkoutPreviewCutlery) {
        checkoutPreviewCutlery.textContent = `${cutleryItemsCount}`;
    }
    if (checkoutPreviewTotal) {
        checkoutPreviewTotal.textContent = formatPrice(totalPriceValue);
    }
    if (checkoutPreviewLines) {
        if (!entries.length) {
            checkoutPreviewLines.innerHTML = `
                <div class="order-empty">
                    <strong>Пока пусто</strong>
                    <p>Добавьте блюда из каталога, и они появятся перед подтверждением заказа.</p>
                </div>
            `;
            return;
        }

        checkoutPreviewLines.innerHTML = entries.map((item) => renderCartLine(item, "checkout")).join("");
    }
}

function setCartItemQuantity(id, nextQuantity) {
    if (!id || !cart.has(id)) {
        return false;
    }

    const safeNextQuantity = Math.max(0, Number(nextQuantity) || 0);
    if (safeNextQuantity <= 0) {
        cart.delete(id);
    } else {
        cart.get(id).quantity = safeNextQuantity;
    }

    renderCart();
    return true;
}

function changeCartItemQuantity(id, delta) {
    if (!id || !cart.has(id)) {
        return false;
    }

    const currentQuantity = Number(cart.get(id).quantity || 0);
    return setCartItemQuantity(id, currentQuantity + delta);
}

function renderCartLine(item, variant = "cart") {
    const lineVariantClass = variant === "checkout" ? " order-line-checkout" : "";
    return `
        <div class="order-line${lineVariantClass}">
            <div class="order-line-copy">
                <strong class="order-line-title">${item.title}</strong>
                <small class="order-line-meta">${formatPrice(item.price)} за порцию</small>
            </div>
            <div class="order-line-actions">
                <div class="qty-picker qty-picker-ghost order-line-qty" data-cart-line-id="${item.id}">
                    <button class="qty-button" type="button" data-cart-qty-action="decrease" data-cart-item-id="${item.id}" aria-label="Уменьшить количество">-</button>
                    <span class="qty-value">${item.quantity}</span>
                    <button class="qty-button" type="button" data-cart-qty-action="increase" data-cart-item-id="${item.id}" aria-label="Увеличить количество">+</button>
                </div>
                <strong class="order-line-total">${formatPrice(item.price * item.quantity)}</strong>
                <button class="order-remove-button" type="button" data-remove-id="${item.id}" aria-label="Удалить блюдо">x</button>
            </div>
        </div>
    `;
}

function normalizeCheckoutBonusSpentValue(nextValue) {
    if (!checkoutBonusSpent) {
        return 0;
    }

    const min = Math.max(0, Number(checkoutBonusSpent.min || "0") || 0);
    const rawMax = Number(checkoutBonusSpent.max || "0");
    const max = Number.isFinite(rawMax) && rawMax >= min ? rawMax : min;
    const normalized = Math.min(max, Math.max(min, Math.floor(Number(nextValue) || 0)));
    checkoutBonusSpent.value = String(normalized);
    return normalized;
}

function changeCheckoutBonusSpent(delta) {
    if (!checkoutBonusSpent) {
        return;
    }

    normalizeCheckoutBonusSpentValue(Number(checkoutBonusSpent.value || "0") + delta);
}

function syncCheckoutType() {
    isDelivery = checkoutType === "delivery";
    if (!isDelivery) {
        checkoutPayment = "card";
    }

    checkoutTypePickup?.classList.toggle("is-active", !isDelivery);
    checkoutTypeDelivery?.classList.toggle("is-active", isDelivery);
    checkoutDeliveryFields?.classList.toggle("is-hidden", !isDelivery);

    if (checkoutAddress) {
        checkoutAddress.required = isDelivery;
    }
    if (checkoutHouse) {
        checkoutHouse.required = isDelivery;
    }
    if (!isDelivery) {
        if (checkoutAddress) {
            checkoutAddress.value = "";
        }
        if (checkoutHouse) {
            checkoutHouse.value = "";
        }
        if (checkoutFlat) {
            checkoutFlat.value = "";
        }
        if (checkoutEntrance) {
            checkoutEntrance.value = "";
        }
    }

    if (checkoutNote) {
        checkoutNote.textContent = isDelivery
            ? "Доставка: заполните адрес и детали для курьера, чтобы оператор подтвердил заказ без уточнений."
            : "Самовывоз: заказ будет готов к выдаче после подтверждения оператором.";
    }

}

function syncCheckoutPayment() {
    checkoutPayment = "card";
    checkoutPaymentCard?.classList.toggle("is-active", checkoutPayment === "card");
}

function syncBranchSelection() {
    cartBranchMalyshava?.classList.toggle("is-active", branchCode === "malyshava");
    cartBranchSuh?.classList.toggle("is-active", branchCode === "suh");
}

function openCheckoutModal() {
    if (!checkoutModal || !checkoutBackdrop || !checkoutForm) {
        return;
    }

    const { entries, totalPriceValue } = getCartTotals();
    if (!entries.length || !canCheckoutWithCurrentType(totalPriceValue)) {
        return;
    }

    closeCart();
    checkoutLockedScrollY = window.scrollY || window.pageYOffset || 0;
    document.body.style.position = "fixed";
    document.body.style.top = `-${checkoutLockedScrollY}px`;
    document.body.style.left = "0";
    document.body.style.right = "0";
    document.body.style.width = "100%";
    document.body.classList.add("checkout-open");
    window.zamzamSyncCheckoutProfileFields?.();
    syncCheckoutPreview();
    syncCheckoutType();
    syncCheckoutPayment();
    checkoutBackdrop.classList.add("is-open");
    checkoutModal.classList.add("is-open");
    checkoutModal.setAttribute("aria-hidden", "false");
}

function closeCheckoutModal() {
    if (!checkoutModal || !checkoutBackdrop) {
        return;
    }

    checkoutBackdrop.classList.remove("is-open");
    checkoutModal.classList.remove("is-open");
    checkoutModal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("checkout-open");
    document.body.style.position = "";
    document.body.style.top = "";
    document.body.style.left = "";
    document.body.style.right = "";
    document.body.style.width = "";
    window.scrollTo(0, checkoutLockedScrollY);
}

function openFooterMapModal() {
    if (!footerMapModal || !footerMapBackdrop) {
        return;
    }

    footerMapBackdrop.classList.add("is-open");
    footerMapModal.classList.add("is-open");
    footerMapModal.setAttribute("aria-hidden", "false");
}

function closeFooterMapModal() {
    if (!footerMapModal || !footerMapBackdrop) {
        return;
    }

    footerMapBackdrop.classList.remove("is-open");
    footerMapModal.classList.remove("is-open");
    footerMapModal.setAttribute("aria-hidden", "true");
}

function scrollToMenuStart() {
    if (!menuSection) {
        return;
    }

    const topbarHeight = document.querySelector(".topbar-wrap")?.offsetHeight || 0;
    const targetTop = Math.max(0, window.scrollY + menuSection.getBoundingClientRect().top - topbarHeight - 18);
    window.scrollTo({
        top: targetTop,
        behavior: "smooth",
    });
}

function updateFloatingToolsVisibility() {
    const hasCartItems = cart.size > 0;
    const menuTriggerY = menuSection ? Math.max(280, menuSection.offsetTop - MENU_START_TRIGGER_OFFSET) : 280;
    const menuTopPassed = window.scrollY >= menuTriggerY;

    menuStartTrigger?.classList.toggle("is-hidden", !menuTopPassed);

    if (!floatingTools) {
        return;
    }

    const hasVisibleAccountTrigger = document.getElementById("account-floating-trigger")?.classList.contains("is-hidden") === false;
    const hasVisibleMenuStartTrigger = menuStartTrigger?.classList.contains("is-hidden") === false;
    const shouldShow = hasCartItems || hasVisibleAccountTrigger || hasVisibleMenuStartTrigger || window.scrollY >= menuTriggerY;

    floatingTools.classList.toggle("is-hidden", !shouldShow);
}

function toStaticUrl(imagePath) {
    if (!imagePath) {
        return "";
    }

    const normalizedPath = imagePath.startsWith("/") ? imagePath.slice(1) : imagePath;
    return `/static/${normalizedPath}`;
}

function applyFilter(selected) {
    activeFilter = selected;

    if (filtersContainer) {
        filtersContainer.querySelectorAll(".filter-chip").forEach((chip) => {
            chip.classList.toggle("active", chip.dataset.filter === selected);
        });
    }

    getCards().forEach((card) => {
        const matchesFilter = selected === "all" || card.dataset.category === selected;
        const isActive = card.dataset.itemIsActive !== "false";
        card.classList.toggle("is-hidden", !(matchesFilter && isActive));
    });
}

function ensureFilterChip(category) {
    if (!filtersContainer || !category || category === "all") {
        return;
    }

    const existingChip = filtersContainer.querySelector(`[data-filter="${category}"]`);
    if (existingChip) {
        return;
    }

    const chip = document.createElement("button");
    chip.className = "filter-chip";
    chip.type = "button";
    chip.dataset.filter = category;
    chip.textContent = category;
    filtersContainer.appendChild(chip);
}

function getMenuCategoriesFromFilters() {
    if (!filtersContainer) {
        return [];
    }

    return Array.from(filtersContainer.querySelectorAll(".filter-chip"))
        .map((chip) => ({
            value: chip.dataset.filter || "",
            label: chip.textContent?.trim() || "",
        }))
        .filter((category) => category.value && category.value !== "all");
}

function renderFilterChips(categories) {
    if (!filtersContainer) {
        return;
    }

    const allChip = filtersContainer.querySelector('[data-filter="all"]');
    filtersContainer.innerHTML = "";
    if (allChip) {
        filtersContainer.appendChild(allChip);
    } else {
        const chip = document.createElement("button");
        chip.className = "filter-chip active";
        chip.type = "button";
        chip.dataset.filter = "all";
        chip.textContent = "Все блюда";
        filtersContainer.appendChild(chip);
    }

    categories.forEach((category) => {
        const chip = document.createElement("button");
        chip.className = "filter-chip";
        chip.type = "button";
        chip.dataset.filter = category.value;
        chip.textContent = category.label;
        filtersContainer.appendChild(chip);
    });

    const hasActiveFilter = activeFilter === "all" || categories.some((category) => category.value === activeFilter);
    applyFilter(hasActiveFilter ? activeFilter : "all");
}

function syncCategoryOptions(selectedCategory = "") {
    if (!adminCategory || !filtersContainer) {
        return;
    }

    const categories = getMenuCategoriesFromFilters();
    if (selectedCategory && !categories.some((category) => category.value === selectedCategory)) {
        categories.push({ value: selectedCategory, label: selectedCategory });
    }

    adminCategory.innerHTML = categories
        .map((category) => `<option value="${category.value}">${category.label}</option>`)
        .join("");

    if (selectedCategory && categories.some((category) => category.value === selectedCategory)) {
        adminCategory.value = selectedCategory;
    } else if (categories.length) {
        adminCategory.value = categories[0].value;
    }
}

function removeEmptyFilterChip(category) {
    if (!filtersContainer || !category || category === "all") {
        return;
    }

    const hasCardsInCategory = getCards().some((card) => card.dataset.category === category);
    if (hasCardsInCategory) {
        return;
    }

    filtersContainer.querySelector(`[data-filter="${category}"]`)?.remove();
    if (activeFilter === category) {
        applyFilter("all");
    }
}

function createDishCard(item) {
    const article = document.createElement("article");
    article.className = "dish-card";
    article.dataset.category = item.category;
    article.dataset.itemId = String(item.id);
    article.dataset.itemVersion = String(item.version);
    article.dataset.itemIsActive = item.is_active ? "true" : "false";
    article.dataset.imagePath = item.image_path || "";
    article.style.setProperty("--card-accent", item.accent);

    const imageMarkup = item.image_path
        ? `<img class="dish-image" src="${toStaticUrl(item.image_path)}" alt="${item.title}">`
        : `<img class="dish-image is-hidden" src="" alt="${item.title}">`;
    const plateHiddenClass = item.image_path ? " is-hidden" : "";

    article.innerHTML = `
        <div class="dish-visual">
            ${imageMarkup}
            <div class="dish-plate${plateHiddenClass}">
                <div class="dish-center"></div>
            </div>
        </div>
        <div class="dish-body">
            <div class="dish-admin-row">
                <h3 class="dish-title"></h3>
                <button class="dish-edit-button" type="button">Редактировать</button>
            </div>
            <p class="dish-description"></p>
        </div>
        <div class="dish-footer">
            <strong class="dish-price"></strong>
            <div class="dish-actions">
                <div class="qty-picker" data-qty-picker>
                    <button class="qty-button" type="button" data-qty-action="decrease">-</button>
                    <span class="qty-value" data-qty-value>1</span>
                    <button class="qty-button" type="button" data-qty-action="increase">+</button>
                </div>
                <button class="add-button" type="button" data-id="${item.id}" data-title="${item.title}" data-price="${item.price}">
                    Добавить
                </button>
            </div>
        </div>
    `;

    syncCardFromItem(article, item);
    registerRevealElement(article, 0);
    return article;
}

function syncCardFromItem(card, item) {
    if (!card || !item) {
        return;
    }

    const titleNode = card.querySelector(".dish-title");
    const descriptionNode = card.querySelector(".dish-description");
    const priceNode = card.querySelector(".dish-price");
    const addButton = card.querySelector(".add-button");
    const imageNode = card.querySelector(".dish-image");
    const plateNode = card.querySelector(".dish-plate");

    if (titleNode) {
        titleNode.textContent = item.title;
    }

    if (descriptionNode) {
        descriptionNode.textContent = item.description;
    }

    if (priceNode) {
        priceNode.textContent = formatPrice(item.price);
    }

    if (addButton) {
        addButton.dataset.id = String(item.id);
        addButton.dataset.title = item.title;
        addButton.dataset.price = String(item.price);
    }

    if (imageNode) {
        const imagePath = item.image_path || "";
        imageNode.src = imagePath ? toStaticUrl(imagePath) : "";
        imageNode.alt = item.title;
        imageNode.classList.toggle("is-hidden", !imagePath);
    }

    if (plateNode) {
        plateNode.classList.toggle("is-hidden", Boolean(item.image_path));
    }

    card.dataset.category = item.category;
    card.dataset.itemId = String(item.id);
    card.dataset.itemVersion = String(item.version);
    card.dataset.itemIsActive = item.is_active ? "true" : "false";
    card.dataset.imagePath = item.image_path || "";
    card.style.setProperty("--card-accent", item.accent);
    card.classList.toggle("is-hidden", !(item.is_active && (activeFilter === "all" || activeFilter === item.category)));
}

function populateAdminFormFromItem(item) {
    if (!item) {
        return;
    }

    adminModalTitle.textContent = "Редактирование карточки";
    adminItemId.value = item.id ? String(item.id) : "";
    adminItemVersion.value = item.version ? String(item.version) : "1";
    adminTitle.value = item.title || "";
    adminDescription.value = item.description || "";
    adminPrice.value = String(Number(item.price || 0));
    syncCategoryOptions(item.category || "");
    adminDelete?.classList.toggle("is-hidden", !item.id);
    if (adminDelete) {
        adminDelete.disabled = false;
    }
}

function openAdminModalWithItem(item) {
    if (!adminModal || !adminBackdrop || !adminForm || !item) {
        return;
    }

    adminMode = "edit";
    activeAdminCard = menuGrid?.querySelector(`.dish-card[data-item-id="${item.id}"]`) || null;
    adminForm.reset();
    if (adminImage) {
        adminImage.value = "";
    }

    populateAdminFormFromItem(item);
    adminBackdrop.classList.add("is-open");
    adminModal.classList.add("is-open");
    adminModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("admin-open");
}

function openAdminModal(mode, card = null) {
    if (!adminModal || !adminBackdrop || !adminForm) {
        return;
    }
    if (mode !== "edit" || !card) {
        return;
    }

    adminMode = "edit";
    activeAdminCard = card;
    adminForm.reset();
    if (adminImage) {
        adminImage.value = "";
    }

    const titleNode = card.querySelector(".dish-title");
    const descriptionNode = card.querySelector(".dish-description");
    const priceNode = card.querySelector(".dish-price");

    adminModalTitle.textContent = "Редактирование карточки";
    adminItemId.value = card.dataset.itemId || "";
    adminItemVersion.value = card.dataset.itemVersion || "1";
    adminTitle.value = titleNode?.textContent?.trim() || "";
    adminDescription.value = descriptionNode?.textContent?.trim() || "";
    adminPrice.value = String(parseInt(priceNode?.textContent || "0", 10) || 0);
    syncCategoryOptions(card.dataset.category || "");
    adminDelete?.classList.toggle("is-hidden", !card.dataset.itemId);
    if (adminDelete) {
        adminDelete.disabled = false;
    }

    adminBackdrop.classList.add("is-open");
    adminModal.classList.add("is-open");
    adminModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("admin-open");
}

function closeAdminModal() {
    if (!adminModal || !adminBackdrop || !adminForm) {
        return;
    }

    adminBackdrop.classList.remove("is-open");
    adminModal.classList.remove("is-open");
    adminModal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("admin-open");
    activeAdminCard = null;
    adminMode = "edit";
    adminForm.reset();
    adminDelete?.classList.add("is-hidden");
    if (adminDelete) {
        adminDelete.disabled = false;
    }
}

function setAdminMode(enabled) {
    document.body.classList.toggle("admin-mode", enabled);
    adminToggle?.classList.toggle("is-active", enabled);
}

function getHeroFields() {
    return {
        kicker: heroSection?.querySelector(".hero-kicker"),
        title: heroSection?.querySelector("h1"),
        address: heroSection?.querySelector(".hero-address"),
        subtitlePrimary: heroSection?.querySelector("h2 span:first-child"),
        subtitleSecondary: heroSection?.querySelector("h2 span:last-child"),
    };
}

function getHeroPayload() {
    const fields = getHeroFields();
    return {
        kicker: fields.kicker?.textContent?.trim() || "",
        title: fields.title?.textContent?.trim() || "",
        address: fields.address?.textContent?.trim() || "",
        subtitle_primary: fields.subtitlePrimary?.textContent?.trim() || "",
        subtitle_secondary: fields.subtitleSecondary?.textContent?.trim() || "",
    };
}

function syncHeroContent(content) {
    const fields = getHeroFields();
    if (fields.kicker) {
        fields.kicker.textContent = content.kicker || "";
    }
    if (fields.title) {
        fields.title.textContent = content.title || "";
    }
    if (fields.address) {
        fields.address.textContent = content.address || "";
    }
    if (fields.subtitlePrimary) {
        fields.subtitlePrimary.textContent = content.subtitle_primary || "";
    }
    if (fields.subtitleSecondary) {
        fields.subtitleSecondary.textContent = content.subtitle_secondary || "";
    }
}

function ensureHeroEditControls() {
    if (!heroSection || heroEditControlsBound) {
        return;
    }

    const fieldNodes = [
        heroSection.querySelector(".hero-kicker"),
        heroSection.querySelector("h1"),
        heroSection.querySelector(".hero-address"),
        heroSection.querySelector("h2"),
    ].filter(Boolean);

    fieldNodes.forEach((node) => {
        const wrapper = document.createElement("div");
        wrapper.className = "hero-copy-row";
        if (node.matches(".hero-address, h2")) {
            wrapper.classList.add("hero-copy-row-block");
        }

        node.parentNode.insertBefore(wrapper, node);
        wrapper.appendChild(node);

        const button = document.createElement("button");
        button.className = "hero-edit-button";
        button.type = "button";
        button.dataset.heroEdit = "true";
        button.setAttribute("aria-label", "Редактировать hero-секцию");
        button.innerHTML = "&#9998;";
        wrapper.appendChild(button);
    });

    heroEditControlsBound = true;
}

function openHeroAdminModal() {
    if (!heroAdminModal || !adminBackdrop || !heroAdminForm) {
        return;
    }

    const content = getHeroPayload();
    heroAdminKicker.value = content.kicker;
    heroAdminTitle.value = content.title;
    heroAdminAddress.value = content.address;
    heroAdminSubtitlePrimary.value = content.subtitle_primary;
    heroAdminSubtitleSecondary.value = content.subtitle_secondary;

    closeAdminModal();
    adminBackdrop.classList.add("is-open");
    heroAdminModal.classList.add("is-open");
    heroAdminModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("admin-open");
}

function closeHeroAdminModal() {
    if (!heroAdminModal || !adminBackdrop || !heroAdminForm) {
        return;
    }

    adminBackdrop.classList.remove("is-open");
    heroAdminModal.classList.remove("is-open");
    heroAdminModal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("admin-open");
    heroAdminForm.reset();
}

async function loadHeroContent() {
    if (!heroSection) {
        return;
    }

    try {
        const response = await fetch("/api/redactor/menu-items/hero-content");
        if (!response.ok) {
            throw new Error("Не удалось загрузить hero-секцию.");
        }

        const content = await response.json();
        syncHeroContent(content);
        initHeroSmokeText();
    } catch (error) {
        window.console.error(error);
    }
}

function getSectionFields(sectionHead) {
    return {
        kicker: sectionHead?.querySelector(".section-kicker"),
        title: sectionHead?.querySelector("h2"),
    };
}

function getSectionPayload(sectionHead) {
    const fields = getSectionFields(sectionHead);
    return {
        kicker: fields.kicker?.textContent?.trim() || "",
        title: fields.title?.textContent?.trim() || "",
    };
}

function syncSectionContent(sectionHead, content) {
    const fields = getSectionFields(sectionHead);
    if (fields.kicker) {
        fields.kicker.textContent = content.kicker || "";
    }
    if (fields.title) {
        fields.title.textContent = content.title || "";
    }
}

function ensureSectionEditControls(sectionHead, datasetKey, ariaLabel) {
    if (!sectionHead || sectionHead.dataset.sectionEditBound === "true") {
        return;
    }

    const fieldNodes = [
        sectionHead.querySelector(".section-kicker"),
        sectionHead.querySelector("h2"),
    ].filter(Boolean);

    fieldNodes.forEach((node) => {
        const wrapper = document.createElement("div");
        wrapper.className = "section-copy-row";
        node.parentNode.insertBefore(wrapper, node);
        wrapper.appendChild(node);

        const button = document.createElement("button");
        button.className = "section-edit-button";
        button.type = "button";
        button.dataset[datasetKey] = "true";
        button.setAttribute("aria-label", ariaLabel);
        button.innerHTML = "&#9998;";
        wrapper.appendChild(button);
    });

    sectionHead.dataset.sectionEditBound = "true";
}

function openSectionAdminModal(config) {
    if (!menuSectionAdminModal || !adminBackdrop || !menuSectionAdminForm) {
        return;
    }

    const content = getSectionPayload(config.head);
    menuSectionAdminKicker.value = content.kicker;
    menuSectionAdminTitle.value = content.title;
    activeSectionEditor = config;
    if (menuSectionAdminModalTitle) {
        menuSectionAdminModalTitle.textContent = config.modalTitle;
    }

    closeAdminModal();
    closeHeroAdminModal();
    adminBackdrop.classList.add("is-open");
    menuSectionAdminModal.classList.add("is-open");
    menuSectionAdminModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("admin-open");
}

function closeMenuSectionAdminModal() {
    if (!menuSectionAdminModal || !adminBackdrop || !menuSectionAdminForm) {
        return;
    }

    adminBackdrop.classList.remove("is-open");
    menuSectionAdminModal.classList.remove("is-open");
    menuSectionAdminModal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("admin-open");
    activeSectionEditor = null;
    menuSectionAdminForm.reset();
}

function createCategoryAdminRow(category = { value: "", label: "" }) {
    const row = document.createElement("div");
    row.className = "category-admin-row";
    row.innerHTML = `
        <input class="category-admin-input" type="text" maxlength="64" placeholder="slug, например grill" value="${category.value || ""}">
        <input class="category-admin-input" type="text" maxlength="64" placeholder="Название категории" value="${category.label || ""}">
        <button class="admin-close category-admin-remove" type="button" aria-label="Удалить категорию">x</button>
    `;
    return row;
}

function closeMenuCategoriesAdminModal() {
    if (!menuCategoriesAdminModal || !adminBackdrop || !menuCategoriesAdminForm) {
        return;
    }

    adminBackdrop.classList.remove("is-open");
    menuCategoriesAdminModal.classList.remove("is-open");
    menuCategoriesAdminModal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("admin-open");
    menuCategoriesAdminForm.reset();
    if (menuCategoriesAdminList) {
        menuCategoriesAdminList.innerHTML = "";
    }
}

async function openMenuCategoriesAdminModal() {
    if (!menuCategoriesAdminModal || !adminBackdrop || !menuCategoriesAdminList) {
        return;
    }

    closeAdminModal();
    closeHeroAdminModal();
    closeMenuSectionAdminModal();

    const response = await fetch("/api/redactor/menu-items/menu-categories");
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody?.detail || "Не удалось загрузить категории.");
    }

    const payload = await response.json();
    menuCategoriesAdminList.innerHTML = "";
    (payload.items || []).forEach((item) => {
        menuCategoriesAdminList.appendChild(createCategoryAdminRow(item));
    });

    adminBackdrop.classList.add("is-open");
    menuCategoriesAdminModal.classList.add("is-open");
    menuCategoriesAdminModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("admin-open");
}

async function loadSectionContent(url, sectionHead) {
    if (!sectionHead) {
        return;
    }

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error("Не удалось загрузить секцию.");
        }

        const content = await response.json();
        syncSectionContent(sectionHead, content);
    } catch (error) {
        window.console.error(error);
    }
}

function renderCart() {
    const { entries, totalItems, totalPriceValue } = getCartTotals();
    const hasEntries = entries.length > 0;
    const canCheckout = hasEntries && canCheckoutWithCurrentType(totalPriceValue);

    syncCartCheckoutNote();

    if (cutleryCount) {
        cutleryCount.textContent = `${cutleryItemsCount}`;
    }
    if (cutlerySummaryItem) {
        cutlerySummaryItem.style.display = hasEntries ? "" : "none";
    }
    if (checkoutButton) {
        checkoutButton.disabled = !canCheckout;
    }

    if (!hasEntries) {
        orderItems.innerHTML = `
            <div class="order-empty">
                <strong>Пока пусто</strong>
                <p>Добавьте блюда из каталога, и заказ появится здесь.</p>
            </div>
        `;
        totalPrice.textContent = "0 руб.";
        itemsCount.textContent = "0";
        floatingCount.textContent = "0";
        syncCheckoutPreview();
        updateFloatingToolsVisibility();
        return;
    }

    orderItems.innerHTML = entries.map((item) => renderCartLine(item, "cart")).join("");

    totalPrice.textContent = formatPrice(totalPriceValue);
    itemsCount.textContent = `${totalItems}`;
    floatingCount.textContent = `${totalItems}`;
    syncCheckoutPreview();
    updateFloatingToolsVisibility();
}

function updateCutleryCount(nextValue) {
    cutleryItemsCount = Math.max(0, nextValue);
    renderCart();
}

async function uploadImage(itemId, version) {
    if (!adminImage?.files?.length) {
        return null;
    }

    const formData = new FormData();
    formData.append("version", String(version));
    formData.append("image", adminImage.files[0]);

    const response = await fetch(`/api/redactor/menu-items/${itemId}/image`, {
        method: "POST",
        headers: getAdminHeaders(),
        body: formData,
    });

    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody?.detail || "Не удалось загрузить фото.");
    }

    return response.json();
}

if (menuGrid) {
    menuGrid.addEventListener("click", (event) => {
        const target = event.target.closest("button");
        if (!target) {
            return;
        }

        if (target.matches(".add-button")) {
            const id = target.dataset.id;
            const title = target.dataset.title;
            const price = Number(target.dataset.price);
            const card = target.closest(".dish-card");
            const qtyValue = card?.querySelector("[data-qty-value]");
            const quantityToAdd = Math.max(1, Number(qtyValue?.textContent || "1"));

            if (!cart.has(id)) {
                cart.set(id, { id, title, price, quantity: 0 });
            }

            cart.get(id).quantity += quantityToAdd;
            renderCart();
            showCartToast(`Блюдо добавлено в корзину`);
            return;
        }

        if (target.matches("[data-qty-action]")) {
            const picker = target.closest("[data-qty-picker]");
            const valueNode = picker?.querySelector("[data-qty-value]");
            const current = Number(valueNode?.textContent || "1");
            const next =
                target.dataset.qtyAction === "increase"
                    ? current + 1
                    : Math.max(1, current - 1);

            if (valueNode) {
                valueNode.textContent = `${next}`;
            }
            return;
        }

        if (target.matches(".dish-edit-button")) {
            if (!document.body.classList.contains("admin-mode")) {
                return;
            }

            openAdminModal("edit", target.closest(".dish-card"));
        }
    });
}

if (orderItems) {
    orderItems.addEventListener("click", (event) => {
        const qtyButton = event.target.closest("[data-cart-qty-action]");
        if (qtyButton) {
            const id = qtyButton.dataset.cartItemId;
            if (!id) {
                return;
            }

            changeCartItemQuantity(id, qtyButton.dataset.cartQtyAction === "increase" ? 1 : -1);
            return;
        }

        const removeButton = event.target.closest("[data-remove-id]");
        if (!removeButton) {
            return;
        }

        const id = removeButton.dataset.removeId;
        if (!id) {
            return;
        }

        setCartItemQuantity(id, 0);
    });
}

if (checkoutPreviewLines) {
    checkoutPreviewLines.addEventListener("click", (event) => {
        const qtyButton = event.target.closest("[data-cart-qty-action]");
        if (qtyButton) {
            const id = qtyButton.dataset.cartItemId;
            if (!id) {
                return;
            }

            changeCartItemQuantity(id, qtyButton.dataset.cartQtyAction === "increase" ? 1 : -1);
            return;
        }

        const removeButton = event.target.closest("[data-remove-id]");
        if (!removeButton) {
            return;
        }

        const id = removeButton.dataset.removeId;
        if (!id) {
            return;
        }

        setCartItemQuantity(id, 0);
    });
}

bindClick(cutleryDecrease, (event) => {
    event.preventDefault();
    event.stopPropagation();
    updateCutleryCount(cutleryItemsCount - 1);
});
bindClick(cutleryIncrease, (event) => {
    event.preventDefault();
    event.stopPropagation();
    updateCutleryCount(cutleryItemsCount + 1);
});

if (heroSection) {
    heroSection.addEventListener("click", (event) => {
        const target = event.target.closest("[data-hero-edit]");
        if (!target || !document.body.classList.contains("admin-mode")) {
            return;
        }

        openHeroAdminModal();
    });
}

if (menuSectionHead) {
    menuSectionHead.addEventListener("click", (event) => {
        const target = event.target.closest("[data-menu-section-edit]");
        if (!target || !document.body.classList.contains("admin-mode")) {
            return;
        }

        openSectionAdminModal({
            head: menuSectionHead,
            modalTitle: "Редактирование блока меню",
            saveUrl: "/api/redactor/menu-items/menu-section-content",
        });
    });
}

if (deliverySectionHead) {
    deliverySectionHead.addEventListener("click", (event) => {
        const target = event.target.closest("[data-delivery-section-edit]");
        if (!target || !document.body.classList.contains("admin-mode")) {
            return;
        }

        openSectionAdminModal({
            head: deliverySectionHead,
            modalTitle: "Редактирование блока доставки",
            saveUrl: "/api/redactor/menu-items/delivery-section-content",
        });
    });
}

if (contactSectionHead) {
    contactSectionHead.addEventListener("click", (event) => {
        const target = event.target.closest("[data-contact-section-edit]");
        if (!target || !document.body.classList.contains("admin-mode")) {
            return;
        }

        openSectionAdminModal({
            head: contactSectionHead,
            modalTitle: "Редактирование блока контактов",
            saveUrl: "/api/redactor/menu-items/contact-section-content",
        });
    });
}

if (filtersContainer) {
    filtersContainer.addEventListener("click", (event) => {
        const chip = event.target.closest(".filter-chip");
        if (!chip) {
            return;
        }

        applyFilter(chip.dataset.filter || "all");
    });
}

if (checkoutButton) {
    checkoutButton.addEventListener("click", () => {
        if (!cart.size) {
            window.alert("Сначала добавьте блюда в корзину.");
            return;
        }

        window.alert("Демо-экран готов. Следующим шагом можно подключить оформление, оплату и API заказа.");
    });
}

checkoutButton?.addEventListener(
    "click",
    (event) => {
        if (!cart.size) {
            return;
        }

        const sessionToken = readPersistentStorage(SESSION_STORAGE_KEY);
        if (!sessionToken) {
            event.preventDefault();
            event.stopImmediatePropagation();
            closeCart();
            window.openZamzamAuthModal?.("login");
            return;
        }

        event.preventDefault();
        event.stopImmediatePropagation();
        openCheckoutModal();
    },
    true,
);

bindClick(cartToggle, openCart);
bindClick(menuStartTrigger, scrollToMenuStart);
bindClick(cartOpenInline, openCart);
bindClick(cartClose, closeCart);
bindClick(cartBackdrop, closeCart);
bindClick(checkoutClose, closeCheckoutModal);
bindClick(checkoutBackdrop, closeCheckoutModal);
bindClick(footerMapOpen, openFooterMapModal);
bindClick(footerMapClose, closeFooterMapModal);
bindClick(footerMapBackdrop, closeFooterMapModal);
bindClick(checkoutTypePickup, () => {
    checkoutType = "pickup";
    syncCheckoutType();
    syncCartCheckoutNote();
    renderCart();
});
bindClick(checkoutTypeDelivery, () => {
    checkoutType = "delivery";
    syncCheckoutType();
    syncCartCheckoutNote();
    renderCart();
});
bindClick(cartBranchMalyshava, () => {
    branchCode = "malyshava";
    syncBranchSelection();
});
bindClick(cartBranchSuh, () => {
    branchCode = "suh";
    syncBranchSelection();
});
bindClick(checkoutPaymentCard, () => {
    checkoutPayment = "card";
    syncCheckoutPayment();
});
bindClick(checkoutBonusDecrease, () => {
    changeCheckoutBonusSpent(-1);
});
bindClick(checkoutBonusIncrease, () => {
    changeCheckoutBonusSpent(1);
});
bindClick(adminToggle, () => {
    setAdminMode(!document.body.classList.contains("admin-mode"));
});
bindClick(adminClose, closeAdminModal);
bindClick(heroAdminClose, closeHeroAdminModal);
bindClick(menuSectionAdminClose, closeMenuSectionAdminModal);
bindClick(menuCategoriesAdminClose, closeMenuCategoriesAdminModal);
bindClick(adminBackdrop, () => {
    closeAdminModal();
    closeHeroAdminModal();
    closeMenuSectionAdminModal();
    closeMenuCategoriesAdminModal();
    window.zamzamCatalogAdmin?.close?.();
});
bindClick(menuCategoriesOpen, async () => {
    try {
        await openMenuCategoriesAdminModal();
    } catch (error) {
        window.alert(error.message || "Не удалось открыть категории.");
    }
});
bindClick(menuCategoriesAdminAdd, () => {
    menuCategoriesAdminList?.appendChild(createCategoryAdminRow());
});

if (adminForm) {
    adminForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const basePayload = {
            title: adminTitle.value.trim(),
            description: adminDescription.value.trim(),
            category: adminCategory.value.trim(),
            is_published: true,
        };

        adminSave.disabled = true;

        try {
            if (!adminItemId.value) {
                throw new Error("Не выбрана карточка для редактирования.");
            }

            const previousCategory = activeAdminCard?.dataset.category || "";
            const updateResponse = await fetch(`/api/redactor/menu-items/${adminItemId.value}`, {
                method: "PATCH",
                headers: getAdminHeaders({
                    "Content-Type": "application/json",
                }),
                body: JSON.stringify({
                    ...basePayload,
                    version: Number(adminItemVersion.value || "1"),
                }),
            });

            if (!updateResponse.ok) {
                const errorBody = await updateResponse.json().catch(() => ({}));
                throw new Error(errorBody?.detail || "Не удалось сохранить изменения.");
            }

            let item = await updateResponse.json();

            if (adminImage?.files?.length) {
                item = (await uploadImage(item.id, item.version)) || item;
            }

            ensureFilterChip(item.category);
            if (activeAdminCard) {
                syncCardFromItem(activeAdminCard, item);
                removeEmptyFilterChip(previousCategory);
            } else {
                const card = createDishCard(item);
                menuGrid?.appendChild(card);
                activeAdminCard = card;
            }
            applyFilter(activeFilter);

            closeAdminModal();
        } catch (error) {
            window.alert(error.message || "Не удалось выполнить действие.");
        } finally {
            adminSave.disabled = false;
        }
    });
}

bindClick(adminDelete, async () => {
    if (!adminItemId.value) {
        return;
    }

    const confirmed = window.confirm("Удалить блюдо с сайта? Его можно будет вернуть позже через каталог iiko.");
    if (!confirmed) {
        return;
    }

    const previousCategory = activeAdminCard?.dataset.category || "";
    adminSave.disabled = true;
    adminDelete.disabled = true;

    try {
        const response = await fetch(`/api/redactor/menu-items/${adminItemId.value}`, {
            method: "DELETE",
            headers: getAdminHeaders({
                "Content-Type": "application/json",
            }),
            body: JSON.stringify({
                version: Number(adminItemVersion.value || "1"),
            }),
        });

        if (!response.ok) {
            const errorBody = await response.json().catch(() => ({}));
            throw new Error(errorBody?.detail || "Не удалось удалить блюдо с сайта.");
        }

        activeAdminCard?.remove();
        removeEmptyFilterChip(previousCategory);
        applyFilter(activeFilter);
        closeAdminModal();
    } catch (error) {
        window.alert(error.message || "Не удалось удалить блюдо с сайта.");
    } finally {
        adminSave.disabled = false;
        adminDelete.disabled = false;
    }
});

if (heroAdminForm) {
    heroAdminForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const payload = {
            kicker: heroAdminKicker.value.trim(),
            title: heroAdminTitle.value.trim(),
            address: heroAdminAddress.value.trim(),
            subtitle_primary: heroAdminSubtitlePrimary.value.trim(),
            subtitle_secondary: heroAdminSubtitleSecondary.value.trim(),
        };

        heroAdminSave.disabled = true;

        try {
            const response = await fetch("/api/redactor/menu-items/hero-content", {
                method: "PATCH",
                headers: getAdminHeaders({
                    "Content-Type": "application/json",
                }),
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorBody = await response.json().catch(() => ({}));
                throw new Error(errorBody?.detail || "Не удалось сохранить hero-секцию.");
            }

            const content = await response.json();
            syncHeroContent(content);
            initHeroSmokeText();
            closeHeroAdminModal();
        } catch (error) {
            window.alert(error.message || "Не удалось сохранить hero-секцию.");
        } finally {
            heroAdminSave.disabled = false;
        }
    });
}

if (menuSectionAdminForm) {
    menuSectionAdminForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        if (!activeSectionEditor) {
            return;
        }

        const payload = {
            kicker: menuSectionAdminKicker.value.trim(),
            title: menuSectionAdminTitle.value.trim(),
        };

        menuSectionAdminSave.disabled = true;

        try {
            const response = await fetch(activeSectionEditor.saveUrl, {
                method: "PATCH",
                headers: getAdminHeaders({
                    "Content-Type": "application/json",
                }),
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorBody = await response.json().catch(() => ({}));
                throw new Error(errorBody?.detail || "Не удалось сохранить блок меню.");
            }

            const content = await response.json();
            syncSectionContent(activeSectionEditor.head, content);
            closeMenuSectionAdminModal();
        } catch (error) {
            window.alert(error.message || "Не удалось сохранить секцию.");
        } finally {
            menuSectionAdminSave.disabled = false;
        }
    });
}

menuCategoriesAdminList?.addEventListener("click", (event) => {
    const button = event.target.closest(".category-admin-remove");
    if (!button) {
        return;
    }

    button.closest(".category-admin-row")?.remove();
});

if (menuCategoriesAdminForm) {
    menuCategoriesAdminForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const items = Array.from(menuCategoriesAdminList?.querySelectorAll(".category-admin-row") || [])
            .map((row) => {
                const inputs = row.querySelectorAll(".category-admin-input");
                return {
                    value: (inputs[0]?.value || "").trim().toLowerCase(),
                    label: (inputs[1]?.value || "").trim(),
                };
            })
            .filter((item) => item.value && item.label);

        menuCategoriesAdminSave.disabled = true;

        try {
            const response = await fetch("/api/redactor/menu-items/menu-categories", {
                method: "PATCH",
                headers: getAdminHeaders({
                    "Content-Type": "application/json",
                }),
                body: JSON.stringify({ items }),
            });

            if (!response.ok) {
                const errorBody = await response.json().catch(() => ({}));
                throw new Error(errorBody?.detail || "Не удалось сохранить категории.");
            }

            const payload = await response.json();
            renderFilterChips(payload.items || []);
            syncCategoryOptions(adminCategory?.value || "");
            closeMenuCategoriesAdminModal();
        } catch (error) {
            window.alert(error.message || "Не удалось сохранить категории.");
        } finally {
            menuCategoriesAdminSave.disabled = false;
        }
    });
}

if (checkoutForm) {
    checkoutForm.addEventListener("submit", (event) => {
        if (window.zamzamAccountCheckoutEnabled) {
            return;
        }

        event.preventDefault();

        const { totalItems } = getCartTotals();
        if (!totalItems) {
            window.alert("Сначала добавьте блюда в корзину.");
            return;
        }

        const customerName = checkoutName?.value.trim() || "";
        const customerPhone = ensurePhonePrefixValue(checkoutPhone).trim();
        const deliveryStreet = checkoutAddress?.value.trim() || "";
        const deliveryHouse = checkoutHouse?.value.trim() || "";

        if (!customerName || !customerPhone) {
            window.alert("Укажите телефон для связи.");
            return;
        }

        if (checkoutType === "delivery" && !deliveryStreet) {
            window.alert("Укажите улицу доставки.");
            return;
        }

        if (checkoutType === "delivery" && !deliveryHouse) {
            window.alert("Укажите номер дома.");
            return;
        }

        if (checkoutSubmit) {
            checkoutSubmit.disabled = true;
        }

        const orderModeLabel = checkoutType === "delivery" ? "доставку" : "самовывоз";
        const paymentLabel = "безналично";
        const orderedCutleryCount = cutleryItemsCount;

        window.setTimeout(() => {
            if (checkoutSubmit) {
                checkoutSubmit.disabled = false;
            }

            cart.clear();
            cutleryItemsCount = 0;
            checkoutForm.reset();
            checkoutType = "pickup";
            checkoutPayment = "card";
            ensurePhonePrefixValue(checkoutPhone);
            syncCheckoutType();
            syncCheckoutPayment();
            syncCartCheckoutNote();
            renderCart();
            closeCheckoutModal();
            closeCart();
            showOrderSuccessModal("Ваш заказ принят. Скоро с вами свяжется наш оператор.");
        }, 350);
    });
}

checkoutBonusSpent?.addEventListener("input", () => {
    normalizeCheckoutBonusSpentValue(checkoutBonusSpent.value);
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeCart();
        closeCheckoutModal();
        window.closeZamzamOrderSuccessModal?.();
        closeFooterMapModal();
        closeAdminModal();
        closeHeroAdminModal();
        closeMenuSectionAdminModal();
        closeMenuCategoriesAdminModal();
        window.zamzamCatalogAdmin?.close?.();
    }
});

window.addEventListener("scroll", () => {
    lastScrollY = window.scrollY;
    updateFloatingToolsVisibility();
});

setAdminMode(false);
bindPhonePrefix(checkoutPhone);
bindPhonePrefix(document.getElementById("auth-phone"));
bindPhonePrefix(document.getElementById("auth-register-phone"));
bindPhonePrefix(document.getElementById("orders-admin-phone"));
bindPhonePrefix(document.getElementById("account-phone-input"));
syncCheckoutType();
syncCheckoutPayment();
syncCartCheckoutNote();
ensureHeroEditControls();
ensureSectionEditControls(menuSectionHead, "menuSectionEdit", "Редактировать блок меню");
ensureSectionEditControls(deliverySectionHead, "deliverySectionEdit", "Редактировать блок доставки");
ensureSectionEditControls(contactSectionHead, "contactSectionEdit", "Редактировать блок контактов");
applyFilter(activeFilter);
renderCart();
updateFloatingToolsVisibility();
initRevealAnimations();
initHeroSmokeText();

window.setTimeout(() => {
    loadHeroContent();
    loadSectionContent("/api/redactor/menu-items/menu-section-content", menuSectionHead);
    loadSectionContent("/api/redactor/menu-items/delivery-section-content", deliverySectionHead);
    loadSectionContent("/api/redactor/menu-items/contact-section-content", contactSectionHead);
}, 0);

window.zamzamApp = {
    getCartEntries: () => getCartEntries().map((item) => ({ ...item })),
    getCartTotals: () => ({ ...getCartTotals() }),
    getCheckoutState: () => ({
        checkoutType,
        checkoutPayment,
        branchCode,
        cutleryItemsCount,
    }),
    closeCart,
    closeCheckoutModal,
    openAdminModalWithItem,
    setAdminMode,
    formatPrice,
    resetAfterOrder() {
        cart.clear();
        cutleryItemsCount = 0;
        checkoutForm?.reset();
        checkoutType = "pickup";
        checkoutPayment = "card";
        branchCode = "malyshava";
        ensurePhonePrefixValue(checkoutPhone);
        syncCheckoutType();
        syncCheckoutPayment();
        syncBranchSelection();
        syncCartCheckoutNote();
        renderCart();
        closeCheckoutModal();
        closeCart();
    },
};

```

## 📄 `static\auth-bridge.js`

```javascript
(function () {
    const SESSION_STORAGE_KEY = "zamzam_session_token";
    const REFRESH_STORAGE_KEY = "zamzam_refresh_token";

    const authModal = document.getElementById("auth-modal");
    const authBackdrop = document.getElementById("auth-backdrop");
    const authHint = document.getElementById("auth-hint");
    const authLoginForm = document.getElementById("auth-login-form");
    const authRegisterForm = document.getElementById("auth-register-form");
    const authPhone = document.getElementById("auth-phone");
    const authPassword = document.getElementById("auth-password");
    const authRegisterName = document.getElementById("auth-register-name");
    const authRegisterPhone = document.getElementById("auth-register-phone");
    const authRegisterEmail = document.getElementById("auth-register-email");
    const authRegisterPassword = document.getElementById("auth-register-password");
    const authLoginSubmit = document.getElementById("auth-login-submit");
    const authRegisterSubmit = document.getElementById("auth-register-submit");
    const authRegisterOfertaConsent = document.getElementById("auth-register-oferta-consent");
    const authRegisterPolicyConsent = document.getElementById("auth-register-policy-consent");
    const authRegisterConsents = document.getElementById("auth-register-consents");
    const loginButton = document.getElementById("cart-open-topbar");
    const accountFloatingTrigger = document.getElementById("account-floating-trigger");
    const floatingTools = document.querySelector(".floating-tools");
    const checkoutName = document.getElementById("checkout-name");
    const checkoutPhone = document.getElementById("checkout-phone");

    function getSessionToken() {
        return window.sessionStorage.getItem(SESSION_STORAGE_KEY) || "";
    }

    function setSessionToken(value) {
        if (value) {
            window.sessionStorage.setItem(SESSION_STORAGE_KEY, value);
        } else {
            window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
        }
    }

    function setAuthTokens(payload) {
        setSessionToken(payload?.access_token || "");
        if (payload?.refresh_token) {
            window.sessionStorage.setItem(REFRESH_STORAGE_KEY, payload.refresh_token);
        }
    }

    function clearAuthTokens() {
        setSessionToken("");
        window.sessionStorage.removeItem(REFRESH_STORAGE_KEY);
    }

    function setHint(message, isError) {
        if (!authHint) {
            return;
        }
        authHint.textContent = message || "";
        authHint.style.color = isError ? "#9f2d0f" : "";
    }

    function hasRegisterConsents() {
        return Boolean(authRegisterOfertaConsent?.checked && authRegisterPolicyConsent?.checked);
    }

    function showRegisterConsentWarning() {
        authRegisterConsents?.classList.add("is-attention");
        setHint("Подтвердите согласие с офертой и политикой конфиденциальности.", true);

        const missingConsent = !authRegisterOfertaConsent?.checked
            ? authRegisterOfertaConsent
            : authRegisterPolicyConsent;
        missingConsent?.focus();
    }

    function ensurePhonePrefixValue(input) {
        if (typeof window.zamzamEnsurePhonePrefix === "function") {
            return window.zamzamEnsurePhonePrefix(input);
        }
        if (!input) {
            return "";
        }

        const digits = input.value.replace(/\D/g, "");
        let normalized = digits;

        if (!normalized) {
            normalized = "7";
        } else if (normalized[0] === "8") {
            normalized = `7${normalized.slice(1)}`;
        } else if (normalized[0] !== "7") {
            normalized = `7${normalized}`;
        }

        input.value = `+${normalized}`;
        return input.value;
    }

    function closeAuthModal() {
        authModal?.classList.remove("is-open");
        authModal?.setAttribute("aria-hidden", "true");
        authBackdrop?.classList.remove("is-open");
        document.body.classList.remove("admin-open");
    }

    function syncAuthorizedUi(user) {
        const sessionToken = getSessionToken();
        if (loginButton) {
            loginButton.textContent = sessionToken ? "Выйти" : "Войти";
        }
        accountFloatingTrigger?.classList.toggle("is-hidden", !sessionToken);
        if (sessionToken) {
            floatingTools?.classList.remove("is-hidden");
        }

        if (user?.full_name && checkoutName && !checkoutName.value.trim()) {
            checkoutName.value = user.full_name;
        }
        if (user?.phone && checkoutPhone && !checkoutPhone.value.trim()) {
            checkoutPhone.value = user.phone;
            ensurePhonePrefixValue(checkoutPhone);
        }
    }

    async function fetchCurrentUser() {
        const sessionToken = getSessionToken();
        if (!sessionToken) {
            syncAuthorizedUi(null);
            return;
        }

        try {
            const response = await fetch("/api/user/me", {
                headers: { Authorization: `Bearer ${sessionToken}` },
            });
            if (!response.ok) {
                throw new Error("unauthorized");
            }

            const payload = await response.json();
            syncAuthorizedUi(payload.user || null);
        } catch (_) {
            clearAuthTokens();
            syncAuthorizedUi(null);
        }
    }

    async function submitLogin(event) {
        event.preventDefault();
        event.stopImmediatePropagation();

        const phone = ensurePhonePrefixValue(authPhone).trim();
        const password = authPassword?.value.trim() || "";
        if (!phone || !password) {
            setHint("Введите номер телефона и пароль.", true);
            return;
        }

        if (authLoginSubmit) {
            authLoginSubmit.disabled = true;
        }
        setHint("", false);

        try {
            const response = await fetch("/api/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ phone, password }),
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(payload?.detail || "Не удалось выполнить вход.");
            }

            setAuthTokens(payload);
            closeAuthModal();
            await fetchCurrentUser();
        } catch (error) {
            setHint(error.message || "Не удалось выполнить вход.", true);
        } finally {
            if (authLoginSubmit) {
                authLoginSubmit.disabled = false;
            }
        }
    }

    async function submitRegister(event) {
        event.preventDefault();
        event.stopImmediatePropagation();

        const phone = ensurePhonePrefixValue(authRegisterPhone).trim();
        const email = authRegisterEmail?.value.trim() || "";
        const password = authRegisterPassword?.value.trim() || "";
        const fullName = authRegisterName?.value.trim() || checkoutName?.value.trim() || null;
        if (!phone || !email || !password) {
            setHint("Введите номер телефона, email и пароль.", true);
            return;
        }

        if (!hasRegisterConsents()) {
            showRegisterConsentWarning();
            return;
        }

        if (authRegisterSubmit) {
            authRegisterSubmit.disabled = true;
        }
        setHint("", false);

        try {
            const response = await fetch("/api/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    phone,
                    email,
                    password,
                    full_name: fullName,
                }),
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(payload?.detail || "Не удалось завершить регистрацию.");
            }

            setAuthTokens(payload);
            closeAuthModal();
            await fetchCurrentUser();
        } catch (error) {
            setHint(error.message || "Не удалось завершить регистрацию.", true);
        } finally {
            if (authRegisterSubmit) {
                authRegisterSubmit.disabled = false;
            }
        }
    }

    async function logout(event) {
        event?.preventDefault?.();
        event?.stopImmediatePropagation?.();

        const sessionToken = getSessionToken();
        if (!sessionToken) {
            syncAuthorizedUi(null);
            return;
        }

        try {
            await fetch("/api/auth/logout", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ refresh_token: window.sessionStorage.getItem(REFRESH_STORAGE_KEY) || "" }),
            });
        } catch (_) {
        } finally {
            clearAuthTokens();
            syncAuthorizedUi(null);
        }
    }

    authLoginForm?.addEventListener("submit", submitLogin, true);
    authRegisterForm?.addEventListener("submit", submitRegister, true);
    authRegisterSubmit?.addEventListener(
        "click",
        (event) => {
            if (hasRegisterConsents()) {
                return;
            }

            event.preventDefault();
            event.stopImmediatePropagation();
            showRegisterConsentWarning();
        },
        true,
    );
    [authRegisterOfertaConsent, authRegisterPolicyConsent].forEach((consent) => {
        consent?.addEventListener("invalid", (event) => {
            event.preventDefault();
            showRegisterConsentWarning();
        });
        consent?.addEventListener("change", () => {
            if (hasRegisterConsents()) {
                authRegisterConsents?.classList.remove("is-attention");
                setHint("", false);
            }
        });
    });
    loginButton?.addEventListener("click", (event) => {
        if (!getSessionToken()) {
            return;
        }
        logout(event);
    }, true);

    fetchCurrentUser();
})();

```

## 📄 `static\catalog-admin.js`

```javascript
const catalogSearchOpen = document.getElementById("catalog-search-open");
const catalogAdminModal = document.getElementById("catalog-admin-modal");
const catalogAdminClose = document.getElementById("catalog-admin-close");
const catalogSearchInput = document.getElementById("catalog-search-input");
const catalogSearchSubmit = document.getElementById("catalog-search-submit");
const catalogSearchResults = document.getElementById("catalog-search-results");
const adminBackdropShared = document.getElementById("admin-backdrop");
let catalogSearchDebounceId = null;

function getAdminHeaders(extraHeaders = {}) {
    const token = window.sessionStorage.getItem("zamzam_session_token") || "";
    return token ? { ...extraHeaders, Authorization: `Bearer ${token}` } : { ...extraHeaders };
}

function openCatalogAdminModal() {
    if (!catalogAdminModal || !adminBackdropShared) {
        return;
    }

    adminBackdropShared.classList.add("is-open");
    catalogAdminModal.classList.add("is-open");
    catalogAdminModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("admin-open");
}

function closeCatalogAdminModal() {
    if (!catalogAdminModal || !adminBackdropShared) {
        return;
    }

    catalogAdminModal.classList.remove("is-open");
    catalogAdminModal.setAttribute("aria-hidden", "true");
    if (!document.getElementById("admin-modal")?.classList.contains("is-open")) {
        adminBackdropShared.classList.remove("is-open");
        document.body.classList.remove("admin-open");
    }
}

window.zamzamCatalogAdmin = {
    close: closeCatalogAdminModal,
};

function renderCatalogSearchResults(items) {
    if (!catalogSearchResults) {
        return;
    }

    if (!items.length) {
        catalogSearchResults.innerHTML = '<div class="account-order-empty">Ничего не найдено.</div>';
        return;
    }

    catalogSearchResults.innerHTML = items
        .map(
            (item) => `
                <div class="order-line">
                    <div>
                        <strong>${item.iiko_title || item.title}</strong>
                        <small>${window.zamzamApp?.formatPrice ? window.zamzamApp.formatPrice(item.price) : item.price}</small>
                    </div>
                    <button class="topbar-action topbar-action-button" type="button" data-catalog-item-id="${item.id}">
                        ${item.is_published ? "Редактировать" : "Добавить"}
                    </button>
                </div>
            `,
        )
        .join("");
}

async function searchCatalogItems() {
    if (!catalogSearchInput || !catalogSearchSubmit) {
        return;
    }

    const query = catalogSearchInput.value.trim();
    catalogSearchSubmit.disabled = true;

    try {
        const response = await fetch(`/api/redactor/menu-items/catalog/search?q=${encodeURIComponent(query)}&limit=30&offset=0`, {
            headers: getAdminHeaders(),
        });
        if (!response.ok) {
            const errorBody = await response.json().catch(() => ({}));
            throw new Error(errorBody?.detail || "Не удалось выполнить поиск.");
        }

        const payload = await response.json();
        renderCatalogSearchResults(payload.items || []);
    } catch (error) {
        if (catalogSearchResults) {
            catalogSearchResults.innerHTML = `<div class="account-order-empty">${error.message || "Не удалось выполнить поиск."}</div>`;
        }
    } finally {
        catalogSearchSubmit.disabled = false;
    }
}

async function openItemFromSearch(itemId) {
    const response = await fetch(`/api/redactor/menu-items/${itemId}`, {
        headers: getAdminHeaders(),
    });
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody?.detail || "Не удалось загрузить товар.");
    }

    const item = await response.json();
    closeCatalogAdminModal();
    window.zamzamApp?.openAdminModalWithItem?.(item);
}

catalogSearchOpen?.addEventListener("click", () => {
    if (!document.body.classList.contains("admin-mode")) {
        document.getElementById("admin-toggle")?.click();
    }
    openCatalogAdminModal();
    searchCatalogItems();
});

catalogAdminClose?.addEventListener("click", closeCatalogAdminModal);
catalogSearchSubmit?.addEventListener("click", searchCatalogItems);
catalogSearchInput?.addEventListener("input", () => {
    if (catalogSearchDebounceId) {
        window.clearTimeout(catalogSearchDebounceId);
    }

    catalogSearchDebounceId = window.setTimeout(() => {
        searchCatalogItems();
    }, 250);
});
catalogSearchInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        if (catalogSearchDebounceId) {
            window.clearTimeout(catalogSearchDebounceId);
            catalogSearchDebounceId = null;
        }
        searchCatalogItems();
    }
});

catalogSearchResults?.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-catalog-item-id]");
    if (!button) {
        return;
    }

    button.disabled = true;
    try {
        await openItemFromSearch(button.dataset.catalogItemId);
    } catch (error) {
        window.alert(error.message || "Не удалось открыть товар.");
    } finally {
        button.disabled = false;
    }
});

adminBackdropShared?.addEventListener("click", closeCatalogAdminModal);

```

## 📄 `static\checkout-bridge.js`

```javascript
(function () {
    window.zamzamAccountCheckoutEnabled = true;

    const SESSION_STORAGE_KEY = "zamzam_session_token";
    const REFRESH_STORAGE_KEY = "zamzam_refresh_token";
    const PENDING_PAYMENT_STORAGE_KEY = "zamzam_pending_payment_id";
    const checkoutForm = document.getElementById("checkout-form");
    const checkoutSubmit = document.getElementById("checkout-submit");
    const checkoutName = document.getElementById("checkout-name");
    const checkoutPhone = document.getElementById("checkout-phone");
    const checkoutAddress = document.getElementById("checkout-address");
    const checkoutEntrance = document.getElementById("checkout-entrance");
    const checkoutComment = document.getElementById("checkout-comment");
    const checkoutBonusSpent = document.getElementById("checkout-bonus-spent");
    const checkoutOfertaConsent = document.getElementById("checkout-oferta-consent");
    const checkoutPolicyConsent = document.getElementById("checkout-policy-consent");
    const checkoutConsents = document.querySelector(".checkout-consents");
    let consentPopupTimeoutId = null;
    let checkoutWarningTimeoutId = null;

    function readPersistentStorage(key) {
        try {
            return window.localStorage.getItem(key) || window.sessionStorage.getItem(key) || "";
        } catch (error) {
            return window.sessionStorage.getItem(key) || "";
        }
    }

    function writePersistentStorage(key, value) {
        if (!value) {
            return;
        }
        try {
            window.localStorage.setItem(key, value);
        } catch (error) {
            // Keep checkout working in restricted mobile browser storage modes.
        }
        window.sessionStorage.setItem(key, value);
    }

    function showConsentPopup() {
        let popup = document.getElementById("checkout-consent-popup");
        if (!popup) {
            popup = document.createElement("div");
            popup.id = "checkout-consent-popup";
            popup.className = "checkout-consent-popup";
            popup.setAttribute("role", "alert");
            document.body.appendChild(popup);
        }

        popup.textContent = "\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u0435 \u0441\u043e\u0433\u043b\u0430\u0441\u0438\u0435 \u0441 \u043e\u0444\u0435\u0440\u0442\u043e\u0439 \u0438 \u043f\u043e\u043b\u0438\u0442\u0438\u043a\u043e\u0439 \u043a\u043e\u043d\u0444\u0438\u0434\u0435\u043d\u0446\u0438\u0430\u043b\u044c\u043d\u043e\u0441\u0442\u0438.";
        popup.classList.add("is-visible");
        checkoutConsents?.classList.add("is-attention");

        if (consentPopupTimeoutId) {
            window.clearTimeout(consentPopupTimeoutId);
        }

        consentPopupTimeoutId = window.setTimeout(() => {
            popup.classList.remove("is-visible");
            checkoutConsents?.classList.remove("is-attention");
        }, 3200);
    }

    function showCheckoutWarning(message) {
        let popup = document.getElementById("checkout-warning-popup");
        if (!popup) {
            popup = document.createElement("div");
            popup.id = "checkout-warning-popup";
            popup.className = "checkout-consent-popup checkout-warning-popup";
            popup.setAttribute("role", "alert");
            document.body.appendChild(popup);
        }

        popup.textContent = message;
        popup.classList.add("is-visible");

        if (checkoutWarningTimeoutId) {
            window.clearTimeout(checkoutWarningTimeoutId);
        }

        checkoutWarningTimeoutId = window.setTimeout(() => {
            popup.classList.remove("is-visible");
        }, 3200);
    }

    function hasCheckoutConsents() {
        return Boolean(checkoutOfertaConsent?.checked && checkoutPolicyConsent?.checked);
    }

    function getSessionToken() {
        return readPersistentStorage(SESSION_STORAGE_KEY);
    }

    function ensurePhonePrefixValue(input) {
        if (typeof window.zamzamEnsurePhonePrefix === "function") {
            return window.zamzamEnsurePhonePrefix(input);
        }
        if (!input) {
            return "";
        }

        const digits = input.value.replace(/\D/g, "");
        let normalized = digits;

        if (!normalized) {
            normalized = "7";
        } else if (normalized[0] === "8") {
            normalized = `7${normalized.slice(1)}`;
        } else if (normalized[0] !== "7") {
            normalized = `7${normalized}`;
        }

        input.value = `+${normalized}`;
        return input.value;
    }

    function getBonusSpentValue() {
        return Math.max(0, Number(checkoutBonusSpent?.value || 0));
    }

    function isValidCheckoutPhone(phone) {
        const digits = String(phone || "").replace(/\D/g, "");
        return digits.length === 11 && digits[0] === "7";
    }

    function getResponseErrorMessage(payload, fallbackMessage) {
        return typeof payload?.detail === "string" ? payload.detail : fallbackMessage;
    }

    function buildOrderPayload() {
        const appApi = window.zamzamApp || null;
        if (!appApi) {
            throw new Error("Не удалось подготовить заказ. Обновите страницу и попробуйте снова.");
        }

        const entries = appApi.getCartEntries();
        const checkoutState = appApi.getCheckoutState();
        const customerName = checkoutName?.value.trim() || "";
        const customerPhone = ensurePhonePrefixValue(checkoutPhone).trim();
        const deliveryAddress = checkoutAddress?.value.trim() || "";
        const entrance = checkoutEntrance?.value.trim() || "";
        const comment = checkoutComment?.value.trim() || "";
        const bonusSpent = getBonusSpentValue();

        return {
            appApi,
            entries,
            customerName,
            customerPhone,
            payload: {
                customer_name: customerName,
                customer_phone: customerPhone,
                checkout_type: checkoutState.checkoutType,
                branch_code: checkoutState.branchCode,
                payment_type: "card",
                delivery_address: deliveryAddress || null,
                entrance: entrance || null,
                comment: comment || null,
                cutlery_count: checkoutState.cutleryItemsCount,
                bonus_spent: bonusSpent,
                items: entries.map((item) => ({
                    id: item.id,
                    title: item.title,
                    price: item.price,
                    quantity: item.quantity,
                })),
            },
        };
    }

    function validateCheckoutConsents() {
        if (hasCheckoutConsents()) {
            return true;
        }
        showConsentPopup();
        return false;

        if (!checkoutOfertaConsent?.checked || !checkoutPolicyConsent?.checked) {
            window.alert("Подтвердите согласие с офертой и политикой конфиденциальности.");
            return false;
        }
        return true;
    }

    async function submitCheckout(event) {
        event.preventDefault();
        event.stopImmediatePropagation();

        const sessionToken = getSessionToken();
        if (!sessionToken) {
            window.alert("Сначала войдите в кабинет.");
            return;
        }

        let orderData;
        try {
            orderData = buildOrderPayload();
        } catch (error) {
            window.alert(error.message || "Не удалось подготовить заказ.");
            return;
        }

        if (!orderData.entries.length) {
            window.alert("Сначала добавьте блюда в корзину.");
            return;
        }

        if (!orderData.customerName || !isValidCheckoutPhone(orderData.customerPhone)) {
            showCheckoutWarning("Заполните имя и телефон.");
            checkoutPhone?.focus();
            return;
        }

        if (!validateCheckoutConsents()) {
            return;
        }

        if (checkoutSubmit) {
            checkoutSubmit.disabled = true;
        }

        try {
            const response = await fetch("/api/orders", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${sessionToken}`,
                },
                body: JSON.stringify(orderData.payload),
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(getResponseErrorMessage(payload, "Не удалось оформить заказ."));
            }

            if (payload?.order_id && !payload?.confirmation_url) {
                if (checkoutBonusSpent) {
                    checkoutBonusSpent.value = "0";
                }
                orderData.appApi.resetAfterOrder();
                window.loadZamzamAccount?.();
                window.showZamzamOrderSuccessModal?.("Ваш заказ принят. Скоро с вами свяжется наш оператор.");
                return;
            }

            if (!payload?.confirmation_url) {
                throw new Error("Не удалось получить ссылку на оплату.");
            }
            if (payload.payment_id) {
                writePersistentStorage(PENDING_PAYMENT_STORAGE_KEY, payload.payment_id);
            }
            window.location.href = payload.confirmation_url;
            if (checkoutBonusSpent) {
                checkoutBonusSpent.value = "0";
            }
        } catch (error) {
            showCheckoutWarning(error.message || "Не удалось оформить заказ.");
        } finally {
            if (checkoutSubmit) {
                checkoutSubmit.disabled = false;
            }
        }
    }

    checkoutForm?.addEventListener("submit", submitCheckout, true);
    checkoutSubmit?.addEventListener(
        "click",
        (event) => {
            if (hasCheckoutConsents()) {
                return;
            }

            event.preventDefault();
            event.stopImmediatePropagation();
            showConsentPopup();

            const missingConsent = !checkoutOfertaConsent?.checked
                ? checkoutOfertaConsent
                : checkoutPolicyConsent;
            missingConsent?.focus();
        },
        true,
    );
    [checkoutOfertaConsent, checkoutPolicyConsent].forEach((consent) => {
        consent?.addEventListener("invalid", (event) => {
            event.preventDefault();
            showConsentPopup();
        });
        consent?.addEventListener("change", () => {
            if (hasCheckoutConsents()) {
                checkoutConsents?.classList.remove("is-attention");
            }
        });
    });
})();

```

## 📄 `static\orders-admin.js`

```javascript
const ordersAdminModal = document.getElementById("orders-admin-modal");
const ordersAdminOpen = document.getElementById("orders-admin-open");
const ordersAdminClose = document.getElementById("orders-admin-close");
const ordersAdminPhone = document.getElementById("orders-admin-phone");
const ordersAdminSearch = document.getElementById("orders-admin-search");
const ordersAdminRefresh = document.getElementById("orders-admin-refresh");
const ordersAdminResults = document.getElementById("orders-admin-results");
const adminBackdropShared = document.getElementById("admin-backdrop");

function getAdminHeaders(extraHeaders = {}) {
    const token = window.sessionStorage.getItem("zamzam_session_token") || "";
    return token ? { ...extraHeaders, Authorization: `Bearer ${token}` } : { ...extraHeaders };
}

let ordersAdminPhoneFilter = "";
let ordersAdminStatusOptions = {
    pickup: ["Готовится", "Готов к выдаче", "Выдан", "Отменен"],
    delivery: ["Готовится", "Приготовлен", "Заказ отправлен", "Доставлен", "Отменен"],
};

function ensureOrdersAdminPhoneValue() {
    if (typeof window.zamzamEnsurePhonePrefix === "function") {
        return window.zamzamEnsurePhonePrefix(ordersAdminPhone);
    }
    return ordersAdminPhone?.value || "";
}

function openOrdersAdminModal() {
    if (!ordersAdminModal || !adminBackdropShared) {
        return;
    }

    adminBackdropShared.classList.add("is-open");
    ordersAdminModal.classList.add("is-open");
    ordersAdminModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("admin-open");
}

function closeOrdersAdminModal() {
    if (!ordersAdminModal) {
        return;
    }

    ordersAdminModal.classList.remove("is-open");
    ordersAdminModal.setAttribute("aria-hidden", "true");
    if (!document.querySelector(".admin-modal.is-open")) {
        adminBackdropShared?.classList.remove("is-open");
        document.body.classList.remove("admin-open");
    }
}

window.zamzamOrdersAdmin = {
    close: closeOrdersAdminModal,
};

function formatOrdersAdminDate(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "" : date.toLocaleString("ru-RU");
}

function getCheckoutTypeLabel(checkoutType) {
    return checkoutType === "delivery" ? "Доставка" : "Самовывоз";
}

function getPaymentTypeLabel(paymentType) {
    return paymentType === "cash" ? "Наличные" : "Безналичные";
}

function getStatusOptions(checkoutType) {
    return ordersAdminStatusOptions[checkoutType] || ["Готовится"];
}

function renderOrdersAdmin(orders) {
    if (!ordersAdminResults) {
        return;
    }

    if (!orders.length) {
        ordersAdminResults.innerHTML = '<div class="account-order-empty">Заказы по выбранному фильтру не найдены.</div>';
        return;
    }

    ordersAdminResults.innerHTML = orders
        .map((order) => {
            const itemsText = order.items.map((item) => `${item.title} x ${item.quantity}`).join(", ");
            const addressText = order.delivery_address || "Не требуется";
            const iikoText = order.iiko_order_id
                ? `iiko: ${order.iiko_creation_status || "unknown"} | order ${order.iiko_order_id} | correlation ${order.iiko_correlation_id || "-"}`
                : "iiko: no data";
            const statusOptions = getStatusOptions(order.checkout_type)
                .map((status) => `<option value="${status}" ${status === order.status ? "selected" : ""}>${status}</option>`)
                .join("");

            return `
                <article class="account-order-card" data-order-id="${order.id}">
                    <div class="account-order-head">
                        <strong>Заказ №${order.id}</strong>
                        <span class="account-order-status">${order.status}</span>
                    </div>
                    <div class="order-admin-meta-grid">
                        <div class="order-admin-meta-card">
                            <span>Клиент</span>
                            <strong>${order.customer_name}</strong>
                        </div>
                        <div class="order-admin-meta-card">
                            <span>Телефон</span>
                            <strong>${order.customer_phone}</strong>
                        </div>
                        <div class="order-admin-meta-card">
                            <span>Тип заказа</span>
                            <strong>${getCheckoutTypeLabel(order.checkout_type)}</strong>
                        </div>
                        <div class="order-admin-meta-card">
                            <span>Оплата</span>
                            <strong>${getPaymentTypeLabel(order.payment_type)}</strong>
                        </div>
                    </div>
                    <div class="account-order-meta">Создан: ${formatOrdersAdminDate(order.created_at)}</div>
                    <div class="account-order-meta">Сумма: ${order.total_amount} руб. • Бонусы: +${order.bonus_awarded}</div>
                    <div class="account-order-meta">Адрес: ${addressText}</div>
                    <div class="account-order-meta">${iikoText}</div>
                    <div class="order-admin-items">${itemsText}</div>
                    <form class="order-admin-actions" data-order-status-form>
                        <label class="admin-field">
                            <span>Статус заказа</span>
                            <select data-order-status-select>${statusOptions}</select>
                        </label>
                        <button class="admin-save" type="submit">Сохранить</button>
                    </form>
                </article>
            `;
        })
        .join("");
}

async function loadOrdersAdmin(phone = "") {
    const params = new URLSearchParams();
    params.set("limit", "30");
    if (phone) {
        params.set("phone", phone);
    }

    const response = await fetch(`/api/orders/admin?${params.toString()}`, {
        headers: getAdminHeaders(),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(payload?.detail || "Не удалось загрузить список заказов.");
    }

    ordersAdminStatusOptions = (payload.status_options || []).reduce((acc, item) => {
        if (item?.checkout_type && Array.isArray(item.statuses)) {
            acc[item.checkout_type] = item.statuses;
        }
        return acc;
    }, { ...ordersAdminStatusOptions });

    renderOrdersAdmin(payload.items || []);
}

async function openAndLoadOrdersAdmin(phone = "") {
    openOrdersAdminModal();
    if (ordersAdminResults) {
        ordersAdminResults.innerHTML = '<div class="account-order-empty">Загружаем заказы...</div>';
    }
    await loadOrdersAdmin(phone);
}

async function searchOrdersAdmin() {
    const phone = ensureOrdersAdminPhoneValue().trim();
    ordersAdminPhoneFilter = phone;
    await openAndLoadOrdersAdmin(phone);
}

async function refreshOrdersAdmin() {
    ordersAdminPhoneFilter = "";
    if (ordersAdminPhone) {
        ordersAdminPhone.value = "+7";
    }
    await openAndLoadOrdersAdmin("");
}

ordersAdminOpen?.addEventListener("click", async () => {
    try {
        if (!document.body.classList.contains("admin-mode")) {
            document.getElementById("admin-toggle")?.click();
        }
        await openAndLoadOrdersAdmin(ordersAdminPhoneFilter);
    } catch (error) {
        window.alert(error.message || "Не удалось открыть управление заказами.");
    }
});

ordersAdminClose?.addEventListener("click", closeOrdersAdminModal);
ordersAdminSearch?.addEventListener("click", async () => {
    try {
        await searchOrdersAdmin();
    } catch (error) {
        window.alert(error.message || "Не удалось найти заказы.");
    }
});
ordersAdminRefresh?.addEventListener("click", async () => {
    try {
        await refreshOrdersAdmin();
    } catch (error) {
        window.alert(error.message || "Не удалось обновить заказы.");
    }
});
adminBackdropShared?.addEventListener("click", closeOrdersAdminModal);

ordersAdminResults?.addEventListener("submit", async (event) => {
    event.preventDefault();

    const form = event.target.closest("[data-order-status-form]");
    const orderCard = event.target.closest("[data-order-id]");
    const select = form?.querySelector("[data-order-status-select]");
    const submitButton = form?.querySelector('button[type="submit"]');
    const orderId = orderCard?.dataset.orderId;
    const status = select?.value || "";

    if (!orderId || !status || !submitButton) {
        return;
    }

    submitButton.disabled = true;

    try {
        const response = await fetch(`/api/orders/${orderId}/status`, {
            method: "PATCH",
            headers: getAdminHeaders({
                "Content-Type": "application/json",
            }),
            body: JSON.stringify({ status }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload?.detail || "Не удалось обновить статус.");
        }

        await loadOrdersAdmin(ordersAdminPhoneFilter);
        if (typeof window.loadZamzamAccount === "function") {
            await window.loadZamzamAccount();
        }
    } catch (error) {
        window.alert(error.message || "Не удалось обновить статус.");
    } finally {
        submitButton.disabled = false;
    }
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeOrdersAdminModal();
    }
});

ensureOrdersAdminPhoneValue();

```

## 📄 `static\styles.css`

```css
@import url("https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&display=swap");

@property --button-shiny-angle {
    syntax: "<angle>";
    initial-value: 0deg;
    inherits: false;
}

:root {
    --bg: #f7f4eb;
    --surface: #ffffff;
    --surface-soft: #fff8ee;
    --text: #0f0f0f;
    --text-soft: rgba(15, 15, 15, 0.68);
    --orange: #e85424;
    --green: #234220;
    --yellow: #f3d86d;
    --line: rgba(15, 15, 15, 0.08);
    --shadow: 0 24px 60px rgba(17, 17, 17, 0.12);
    --radius-xl: 32px;
    --radius-lg: 24px;
    --radius-md: 18px;
    --shell: min(1240px, calc(100% - 32px));
}

* {
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
    -webkit-text-size-adjust: 100%;
    text-size-adjust: 100%;
}

body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    overflow-x: hidden;
    touch-action: manipulation;
}

body.cart-open {
    overflow: hidden;
    overscroll-behavior: none;
}

body.checkout-open {
    overflow: hidden;
    overscroll-behavior: none;
}

body.admin-open {
    overflow: hidden;
}

body.mobile-menu-open {
    overflow: hidden;
}

body.order-success-open {
    overflow: hidden;
    overscroll-behavior: none;
}

body.preloader-active {
    overflow: hidden;
}

.page-preloader {
    position: fixed;
    inset: 0;
    z-index: 120;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    background:
        radial-gradient(circle at top right, rgba(243, 216, 109, 0.18), transparent 22%),
        radial-gradient(circle at left top, rgba(232, 84, 36, 0.16), transparent 24%),
        rgba(247, 244, 235, 0.98);
    opacity: 1;
    visibility: visible;
    transition: opacity 0.45s ease, visibility 0.45s ease;
}

.page-preloader.is-hidden {
    opacity: 0;
    visibility: hidden;
    pointer-events: none;
}

.page-preloader-shell {
    display: grid;
    justify-items: center;
    gap: 16px;
    min-width: min(320px, calc(100vw - 48px));
    padding: 28px 32px;
    border: 1px solid rgba(15, 15, 15, 0.08);
    border-radius: 28px;
    background: rgba(255, 255, 255, 0.88);
    box-shadow: 0 24px 60px rgba(15, 15, 15, 0.1);
    backdrop-filter: blur(12px);
}

.page-preloader-icon-wrap {
    position: relative;
    display: grid;
    place-items: center;
    width: 96px;
    height: 96px;
}

.page-preloader-icon-wrap::before {
    content: "";
    position: absolute;
    inset: 6px;
    border: 2px solid rgba(232, 84, 36, 0.16);
    border-top-color: var(--orange);
    border-radius: 50%;
    animation: preloaderSpin 1.2s linear infinite;
}

.page-preloader-icon {
    position: relative;
    z-index: 1;
    width: 64px;
    height: 64px;
    object-fit: contain;
    animation: preloaderFloat 1.8s ease-in-out infinite;
}

.page-preloader-title {
    color: var(--text);
    font-family: "Space Grotesk", "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 1.4rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: -0.03em;
}

.page-preloader-copy {
    color: var(--text-soft);
    font-family: "JetBrains Mono", monospace;
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    text-align: center;
}

.reveal-on-scroll {
    opacity: 0;
    filter: blur(14px);
    transform: translateY(60px);
    transition:
        opacity 1.15s ease,
        filter 1.15s ease,
        transform 1.15s cubic-bezier(0.22, 1, 0.36, 1);
    transition-delay: var(--reveal-delay, 0ms);
    will-change: opacity, filter, transform;
}

.reveal-on-scroll.is-visible {
    opacity: 1;
    filter: blur(0);
    transform: translateY(0);
}

@keyframes heroGradientShift {
    0% {
        background-position: 0% 50%;
    }
    50% {
        background-position: 100% 50%;
    }
    100% {
        background-position: 0% 50%;
    }
}

@keyframes heroTextReveal {
    0% {
        opacity: 0;
        filter: blur(10px);
        transform: translateY(42px);
    }

    55% {
        opacity: 0.55;
        filter: blur(5px);
        transform: translateY(-4px);
    }

    100% {
        opacity: 1;
        filter: blur(0);
        transform: translateY(0);
    }
}

@keyframes heroBadgeReveal {
    0% {
        opacity: 0;
        filter: blur(8px);
        transform: translateY(18px);
    }

    100% {
        opacity: 1;
        filter: blur(0);
        transform: translateY(0);
    }
}

@keyframes heroBackgroundPulse {
    0% {
        transform: scale(1.04);
    }

    100% {
        transform: scale(1.1);
    }
}

@keyframes heroScrollBounce {
    0%,
    100% {
        transform: translateX(-50%) translateY(0);
        opacity: 0.72;
    }

    50% {
        transform: translateX(-50%) translateY(8px);
        opacity: 0.96;
    }
}

@keyframes heroSmokeOut {
    0% {
        opacity: 1;
        filter: blur(0);
        transform: translate3d(0, 0, 0) rotate(0deg) scale(1);
    }

    100% {
        opacity: 0;
        filter: blur(18px);
        transform: translate3d(132px, -96px, 0) rotate(220deg) scale(2.15);
    }
}

@keyframes heroSmokeBack {
    0% {
        opacity: 0;
        filter: blur(18px);
        transform: translate3d(36px, -24px, 0) scale(1.34);
    }

    100% {
        opacity: 1;
        filter: blur(0);
        transform: translate3d(0, 0, 0) scale(1);
    }
}

@keyframes ambientFloat {
    0% {
        transform: translate3d(0, 0, 0) rotate(0deg) scale(1);
    }

    50% {
        transform: translate3d(18px, -20px, 0) rotate(3deg) scale(1.04);
    }

    100% {
        transform: translate3d(0, 0, 0) rotate(0deg) scale(1);
    }
}

@keyframes ambientFloatReverse {
    0% {
        transform: translate3d(0, 0, 0) rotate(0deg) scale(1);
    }

    50% {
        transform: translate3d(-20px, 18px, 0) rotate(-3deg) scale(1.06);
    }

    100% {
        transform: translate3d(0, 0, 0) rotate(0deg) scale(1);
    }
}

@keyframes ambientPulse {
    0% {
        opacity: 0.42;
        transform: scale(1);
    }

    50% {
        opacity: 0.62;
        transform: scale(1.08);
    }

    100% {
        opacity: 0.42;
        transform: scale(1);
    }
}

@keyframes menuBackgroundDrift {
    0% {
        background-position: 50% 0%, 18% 26%, 86% 22%, 36% 74%, 74% 82%, 0% 0%, 0% 0%;
    }

    50% {
        background-position: 46% 8%, 58% 18%, 64% 62%, 16% 58%, 88% 38%, 100% 42%, 0% 0%;
    }

    100% {
        background-position: 54% 0%, 82% 36%, 28% 28%, 62% 86%, 20% 44%, 0% 100%, 0% 0%;
    }
}

@keyframes menuGlowFloat {
    0% {
        transform: translate3d(0, 0, 0) scale(1);
    }

    28% {
        transform: translate3d(-180px, 46px, 0) scale(1.08);
    }

    62% {
        transform: translate3d(-82vw, 210px, 0) scale(1.18);
    }

    100% {
        transform: translate3d(-18vw, 360px, 0) scale(1.04);
    }
}

@keyframes menuGlowFloatReverse {
    0% {
        transform: translate3d(0, 0, 0) scale(1);
    }

    30% {
        transform: translate3d(180px, -120px, 0) scale(1.1);
    }

    66% {
        transform: translate3d(78vw, -260px, 0) scale(1.16);
    }

    100% {
        transform: translate3d(26vw, -380px, 0) scale(1.05);
    }
}

@keyframes preloaderSpin {
    from {
        transform: rotate(0deg);
    }

    to {
        transform: rotate(360deg);
    }
}

@keyframes preloaderFloat {
    0%,
    100% {
        transform: translateY(0);
    }

    50% {
        transform: translateY(-4px);
    }
}

@media (prefers-reduced-motion: reduce) {
    .reveal-on-scroll,
    .reveal-on-scroll.is-visible,
    .hero-badge-pill,
    .hero-kicker,
    .hero h1,
    .hero-address,
    .hero h2 > span,
    .hero-actions,
    .hero-scroll-indicator span:first-child,
    .menu-section,
    .hero::before,
    .hero::after,
    .menu-section::before,
    .menu-section::after,
    .delivery-section::before,
    .delivery-section::after,
    .site-footer::before,
    .site-footer::after {
        opacity: 1;
        filter: none;
        transform: none;
        transition: none;
        animation: none;
    }

    .page-preloader-icon-wrap::before,
    .page-preloader-icon {
        animation: none;
    }

    .hero-smoke-letter.active,
    .hero-smoke-letter.back {
        animation: none;
    }
}

.floating-tools {
    position: fixed;
    top: 53px;
    right: 20px;
    z-index: 65;
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 10px;
    transition: transform 0.25s ease, opacity 0.25s ease;
}

.floating-tools.is-hidden {
    opacity: 0;
    transform: translateY(-16px);
    pointer-events: none;
}

.floating-tool {
    position: relative;
    display: grid;
    place-items: center;
    width: 78px;
    height: 78px;
    border: 0;
    border-radius: 22px;
    background: #f0ece6;
    box-shadow: 0 16px 32px rgba(15, 15, 15, 0.1);
    color: #111111;
    cursor: pointer;
    text-decoration: none;
    transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.floating-tool-pill {
    width: auto;
    min-width: 0;
    height: 56px;
    padding: 0 18px;
    border-radius: 999px;
    grid-auto-flow: column;
    gap: 10px;
}

.floating-tool-pill span {
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    white-space: nowrap;
}

.floating-tool-arrow-icon {
    width: 18px;
    height: 18px;
}

.floating-tool-menu-start {
    position: fixed;
    top: auto;
    left: auto;
    right: 20px;
    bottom: 20px;
    z-index: 66;
    max-width: calc(100vw - 40px);
    color: #d8b26b;
    border-color: rgba(216, 178, 107, 0.28);
    background:
        radial-gradient(circle at top right, rgba(216, 178, 107, 0.18), transparent 34%),
        linear-gradient(180deg, rgba(20, 16, 12, 0.96), rgba(12, 10, 8, 0.98));
    box-shadow:
        inset 0 0 0 1px rgba(255, 255, 255, 0.04),
        0 18px 36px rgba(0, 0, 0, 0.24);
}

#menu-start-trigger {
    position: fixed;
    right: 20px;
    bottom: calc(20px + env(safe-area-inset-bottom));
    z-index: 120;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    min-height: 56px;
    padding: 0 18px;
    border: 1px solid rgba(216, 178, 107, 0.28);
    border-radius: 999px;
    appearance: none;
    -webkit-appearance: none;
    opacity: 1;
    visibility: visible;
    pointer-events: auto;
}

#menu-start-trigger svg,
#menu-start-trigger span {
    position: relative;
    z-index: 1;
}

#menu-start-trigger.is-hidden {
    display: none !important;
}

.floating-tool-menu-start.button-shiny {
    --button-shiny-bg: rgba(12, 10, 8, 0.92);
    --button-shiny-bg-soft: rgba(31, 23, 16, 0.92);
    --button-shiny-fg: #d8b26b;
    --button-shiny-highlight: #e5c98d;
    --button-shiny-highlight-soft: #fff8e6;
    --button-shiny-shadow: rgba(216, 178, 107, 0.18);
    border-color: transparent;
}

.floating-tool-menu-start.button-shiny > span {
    position: relative;
    z-index: 1;
}

.floating-tool svg {
    width: 26px;
    height: 26px;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.8;
    stroke-linecap: round;
    stroke-linejoin: round;
    transform: scale(1);
    transition: transform 0.35s ease;
}

.floating-tool-icon {
    width: 28px;
    height: 28px;
    object-fit: contain;
    transform: scale(1);
    transition: transform 0.35s ease;
}

.floating-tool-accent {
    border: 1px solid rgba(216, 178, 107, 0.28);
    background:
        radial-gradient(circle at top right, rgba(216, 178, 107, 0.18), transparent 34%),
        linear-gradient(180deg, rgba(20, 16, 12, 0.96), rgba(12, 10, 8, 0.98));
    color: #d8b26b;
    box-shadow:
        inset 0 0 0 1px rgba(255, 255, 255, 0.04),
        0 18px 36px rgba(0, 0, 0, 0.24);
}

.floating-tool-neutral {
    border: 1px solid rgba(216, 178, 107, 0.18);
    background:
        radial-gradient(circle at top right, rgba(216, 178, 107, 0.1), transparent 34%),
        linear-gradient(180deg, rgba(16, 13, 10, 0.94), rgba(11, 9, 7, 0.98));
    color: rgba(245, 240, 232, 0.92);
    box-shadow:
        inset 0 0 0 1px rgba(255, 255, 255, 0.03),
        0 16px 32px rgba(0, 0, 0, 0.22);
}

.floating-tool.is-hidden {
    display: none;
}

.floating-tool:hover {
    transform: translateY(-4px);
    box-shadow: 0 22px 40px rgba(15, 15, 15, 0.16);
}

.floating-tool:hover svg,
.floating-tool:hover .floating-tool-icon {
    transform: scale(1.08);
}

.floating-tool-cart-icon {
    width: 28px;
    height: 28px;
    transform: scale(1);
    transition: transform 0.35s ease, color 0.35s ease;
}

.floating-tool-account-icon {
    width: 27px;
    height: 27px;
    transform: scale(1);
    transition: transform 0.35s ease, color 0.35s ease;
}

.floating-tool:hover .floating-tool-cart-icon {
    transform: scale(1.08);
}

.floating-tool:hover .floating-tool-account-icon {
    transform: scale(1.08);
}

.floating-count {
    position: absolute;
    top: 10px;
    right: 10px;
    min-width: 20px;
    height: 20px;
    padding: 0 6px;
    border-radius: 999px;
    background: #d8b26b;
    color: #15120d;
    font-size: 0.7rem;
    font-weight: 700;
    line-height: 20px;
    text-align: center;
}

.cart-toast {
    position: fixed;
    right: 20px;
    bottom: 92px;
    z-index: 80;
    max-width: min(360px, calc(100% - 24px));
    padding: 14px 18px;
    border-radius: 8px;
    background: var(--green);
    color: #ffffff;
    box-shadow: 0 18px 36px rgba(35, 66, 32, 0.28);
    opacity: 0;
    transform: translateY(12px);
    pointer-events: none;
    transition: opacity 0.22s ease, transform 0.22s ease;
}

.cart-toast.is-visible {
    opacity: 1;
    transform: translateY(0);
}

.cart-backdrop {
    position: fixed;
    inset: 0;
    z-index: 69;
    background:
        radial-gradient(circle at top right, rgba(200, 146, 42, 0.1), transparent 28%),
        rgba(8, 8, 8, 0.54);
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.25s ease;
}

.cart-backdrop.is-open {
    opacity: 1;
    pointer-events: auto;
}

.checkout-backdrop {
    position: fixed;
    inset: 0;
    z-index: 71;
    background:
        radial-gradient(circle at top left, rgba(232, 84, 36, 0.18), transparent 34%),
        rgba(15, 15, 15, 0.54);
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.25s ease;
}

.checkout-backdrop.is-open {
    opacity: 1;
    pointer-events: auto;
}

.admin-backdrop {
    position: fixed;
    inset: 0;
    z-index: 71;
    background: rgba(15, 15, 15, 0.42);
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.25s ease;
}

.admin-backdrop.is-open {
    opacity: 1;
    pointer-events: auto;
}

.cart-drawer {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    z-index: 70;
    display: flex;
    width: min(420px, 100%);
    height: auto;
    max-height: none;
    overflow-x: hidden;
    overflow-y: auto;
    background: #120d09;
    color: #ffffff;
    box-shadow: -24px 0 48px rgba(15, 15, 15, 0.18);
    transform: translateX(100%);
    transition: transform 0.34s cubic-bezier(0.22, 1, 0.36, 1);
    will-change: transform;
    overscroll-behavior-y: contain;
    -webkit-overflow-scrolling: touch;
    touch-action: pan-y;
}

.cart-drawer.is-open {
    transform: translateX(0);
}

.cart-drawer,
.cart-drawer * {
    -webkit-tap-highlight-color: transparent;
}

.cart-drawer-shell {
    position: relative;
    display: flex;
    flex-direction: column;
    width: 100%;
    min-height: 100%;
    padding: 28px;
    height: auto;
    overflow: visible;
    touch-action: pan-y;
}

.cart-drawer-shell > * {
    min-width: 0;
    touch-action: pan-y;
}

.cart-drawer :where(
    .section-kicker,
    h3,
    .cart-checkout-mode,
    .cart-checkout-mode-label,
    .cart-checkout-note,
    .order-items,
    .order-empty,
    .order-line,
    .order-line-copy,
    .order-line-title,
    .order-line-meta,
    .order-line-actions,
    .order-line-total,
    .order-summary,
    .order-summary > div,
    .order-summary span,
    .order-summary strong,
    .qty-picker,
    .qty-value,
    .checkout-button
) {
    touch-action: pan-y;
    -webkit-user-select: none;
    user-select: none;
    -webkit-touch-callout: none;
}

.cart-drawer button,
.cart-drawer [role="button"] {
    touch-action: pan-y;
    -webkit-user-select: none;
    user-select: none;
}

.cart-drawer-shell > .cart-checkout-mode,
.cart-drawer-shell > .order-summary,
.cart-drawer-shell > .checkout-button {
    flex: 0 0 auto;
}

.cart-drawer-shell > .order-items {
    flex: 0 0 auto;
}

.cart-close {
    align-self: end;
    width: 42px;
    height: 42px;
    margin-bottom: 12px;
    border: 0;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.04);
    color: rgba(245, 240, 232, 0.88);
    font-size: 1.2rem;
    cursor: pointer;
}

.topbar-wrap {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 50;
    display: flex;
    justify-content: center;
    padding: 0 24px;
    border-bottom: 1px solid transparent;
    background: transparent;
    backdrop-filter: none;
    transition:
        background 0.3s ease,
        border-color 0.3s ease,
        box-shadow 0.3s ease,
        backdrop-filter 0.3s ease;
}

.topbar-wrap.is-scrolled {
    background: rgba(8, 8, 8, 0.72);
    border-bottom-color: rgba(216, 178, 107, 0.18);
    box-shadow: 0 14px 40px rgba(0, 0, 0, 0.24);
    backdrop-filter: blur(10px);
}

.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    width: 100%;
    max-width: 1240px;
    min-height: 84px;
    padding: 0;
    border-radius: 0;
    background: transparent;
    box-shadow: none;
}

.topbar-burger {
    display: none;
    width: 42px;
    height: 42px;
    padding: 0;
    border: 1px solid rgba(245, 240, 232, 0.12);
    border-radius: 999px;
    background: rgba(8, 8, 8, 0.26);
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.18);
    cursor: pointer;
    transition:
        transform 0.22s ease,
        background 0.24s ease,
        border-color 0.24s ease,
        box-shadow 0.24s ease;
}

.topbar-burger span {
    display: block;
    grid-area: 1 / 1;
    width: 18px;
    height: 2px;
    margin: 0 auto;
    border-radius: 999px;
    background: #f5f0e8;
    transition: transform 0.24s ease, opacity 0.2s ease, background 0.24s ease;
    transform-origin: center;
}

.topbar-burger span:nth-child(1) {
    transform: translateY(-6px);
}

.topbar-burger span:nth-child(2) {
    transform: translateY(0);
}

.topbar-burger span:nth-child(3) {
    transform: translateY(6px);
}

.topbar.is-menu-open .topbar-burger span:nth-child(1) {
    transform: translateY(0) rotate(45deg);
}

.topbar.is-menu-open .topbar-burger span:nth-child(2) {
    opacity: 0;
    transform: scaleX(0.45);
}

.topbar.is-menu-open .topbar-burger span:nth-child(3) {
    transform: translateY(0) rotate(-45deg);
}

.topbar.is-menu-open .topbar-burger {
    background: #d8b26b;
    border-color: rgba(216, 178, 107, 0.8);
    box-shadow: 0 18px 32px rgba(0, 0, 0, 0.28);
}

.topbar.is-menu-open .topbar-burger span {
    background: #16120d;
}

.hero h1,
.hero h2,
.section-head h2,
.about-copy h2,
.contact-copy h2,
.dish-body h3,
.step-card h3,
.review-card strong,
.contact-card h3 {
    font-family: "Space Grotesk", "Inter", "Segoe UI", Arial, sans-serif;
    text-transform: uppercase;
    letter-spacing: -0.03em;
}

.brand,
.nav-links a,
.topbar-action,
.hero-button,
.section-link {
    text-decoration: none;
}

.topbar-action-button,
.hero-button-secondary,
.section-link-button {
    border: 0;
    cursor: pointer;
    font: inherit;
}

.brand {
    position: relative;
    z-index: 45;
    color: #d8b26b;
    font-family: "Playfair Display", Georgia, serif;
    font-size: 1.45rem;
    font-weight: 500;
    letter-spacing: -0.04em;
    text-transform: none;
    transition: color 0.24s ease;
}

.nav-links {
    display: flex;
    align-items: center;
    gap: 32px;
}

.nav-links a {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    padding: 10px 16px;
    color: rgba(245, 240, 232, 0.8);
    font-size: 0.84rem;
    font-weight: 300;
    letter-spacing: 0.08em;
    text-transform: none;
    transition: color 0.3s ease;
    z-index: 0;
}

.nav-links a::before,
.nav-links a::after {
    content: "";
    position: absolute;
    left: 0;
    width: 100%;
    pointer-events: none;
    transition: all 0.3s ease;
}

.nav-links a::before {
    inset: 0;
    border-top: 0;
    border-bottom: 0;
    transform: scaleY(1.9);
    opacity: 0;
}

.nav-links a::after {
    top: 2px;
    bottom: 2px;
    background: linear-gradient(180deg, #d8b26b, #b88b3c);
    transform: scale(0);
    opacity: 0;
    transform-origin: top;
    z-index: -1;
}

.nav-links a:hover,
.nav-links a:focus-visible {
    color: #16120d;
}

.nav-links a:hover::before,
.nav-links a:focus-visible::before {
    transform: scaleY(1);
    opacity: 1;
}

.nav-links a:hover::after,
.nav-links a:focus-visible::after {
    transform: scale(1);
    opacity: 1;
}

.topbar-controls {
    display: flex;
    align-items: center;
    gap: 12px;
}

.admin-toggle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 42px;
    padding: 0 18px;
    border: 1px solid rgba(15, 15, 15, 0.12);
    border-radius: 12px;
    background: #f4efe8;
    color: var(--text);
    font: inherit;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    cursor: pointer;
    transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;
}

.admin-toggle:hover,
.admin-toggle.is-active {
    background: var(--orange);
    color: #ffffff;
    transform: translateY(-2px);
}

.admin-toggle-accent {
    background: var(--green);
    border-color: var(--green);
    color: #ffffff;
}

.admin-toggle-accent:hover {
    background: var(--orange);
    border-color: var(--orange);
}

.topbar-action {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 42px;
    padding: 0 22px;
    border: 1px solid rgba(216, 178, 107, 0.48);
    border-radius: 999px;
    background: transparent;
    color: #d8b26b;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 0.88rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    text-transform: none;
    transition:
        background 0.24s ease,
        color 0.24s ease,
        border-color 0.24s ease,
        transform 0.24s ease;
}

.topbar-action:hover {
    background: #d8b26b;
    color: #12100d;
    border-color: #d8b26b;
}

.hero {
    position: relative;
    min-height: 100vh;
    overflow: hidden;
    background: #0f110e;
}

.hero::before,
.menu-section::before,
.menu-section::after,
.delivery-section::before,
.delivery-section::after,
.site-footer::before,
.site-footer::after {
    content: "";
    position: absolute;
    pointer-events: none;
}

.hero::before {
    inset: 0;
    background:
        radial-gradient(circle at 50% 18%, rgba(255, 255, 255, 0.18), transparent 28%),
        radial-gradient(circle at 14% 22%, rgba(200, 146, 42, 0.18), transparent 24%),
        radial-gradient(circle at 86% 20%, rgba(255, 255, 255, 0.1), transparent 24%);
    z-index: 1;
}

.hero-overlay {
    position: absolute;
    inset: 0;
    background:
        linear-gradient(180deg, rgba(0, 0, 0, 0.32) 0%, rgba(0, 0, 0, 0.14) 42%, rgba(10, 10, 10, 0.36) 100%),
        radial-gradient(circle at center, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.18) 74%);
    backdrop-filter: blur(0.35px);
    z-index: 2;
}

.hero-media {
    position: absolute;
    inset: 0;
    z-index: 0;
    overflow: hidden;
}

.hero-background-image {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 100vw;
    height: 100vh;
    min-width: 100%;
    min-height: 100%;
    object-fit: cover;
    object-position: center;
    transform: translate(-50%, -50%) scale(1.025);
    filter: brightness(1.08) contrast(1.06) saturate(1.18) blur(1.15px);
}

.hero-inner {
    position: relative;
    z-index: 3;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0;
    max-width: 980px;
    margin: 0 auto;
    min-height: 100vh;
    padding: 136px 24px 124px;
    text-align: center;
}

.hero-badge-pill,
.hero-kicker,
.hero h1,
.hero-address,
.hero h2 > span,
.hero-actions,
.hero-scroll-indicator span:first-child {
    opacity: 0;
    filter: blur(10px);
    transform: translateY(42px);
    animation: heroTextReveal 0.9s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    will-change: opacity, filter, transform;
}

.hero-badge-pill {
    animation-name: heroBadgeReveal;
    animation-duration: 1.15s;
    animation-timing-function: cubic-bezier(0.16, 1, 0.3, 1);
    animation-fill-mode: forwards;
    animation-delay: 0.12s;
}

.hero-kicker {
    animation-delay: 0.18s;
}

.hero h1 {
    animation-delay: 0.28s;
}

.hero-address {
    animation-delay: 0.38s;
}

.hero h2 > span:first-child {
    animation-delay: 0.48s;
}

.hero h2 > span:last-child {
    animation-delay: 0.58s;
}

.hero-actions {
    animation-delay: 0.68s;
}

.hero-scroll-indicator span:first-child {
    animation-delay: 0.8s;
}

.hero-gradient-text,
.hero-kicker,
.hero h1,
.hero-address,
.hero h2 > span,
.hero-button > span,
.hero-scroll-indicator span:first-child {
    color: transparent !important;
    background-image: linear-gradient(90deg, #fff7df, #d8b26b, #ffefd0, #ffffff, #d8b26b);
    background-size: 300% 100%;
    background-position: 0% 50%;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation-name: heroTextReveal, heroGradientShift;
    animation-duration: 0.9s, 8s;
    animation-timing-function: cubic-bezier(0.22, 1, 0.36, 1), ease-in-out;
    animation-fill-mode: forwards, none;
    animation-iteration-count: 1, infinite;
    animation-direction: normal, alternate;
}

.hero-badge-pill {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 18px;
    padding: 10px 18px;
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(10px);
    color: #d8b26b;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.18);
}

.hero-badge-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #d8b26b;
    box-shadow: 0 0 16px rgba(216, 178, 107, 0.72);
}

.hero-kicker,
.section-kicker {
    display: block;
    margin-bottom: 18px;
    font-size: 0.9rem;
    font-weight: 600;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
}

.hero-kicker {
    color: rgba(255, 248, 236, 0.8);
    text-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
}

.hero h1 {
    margin: 0;
    color: #d8b26b;
    font-size: clamp(4.8rem, 10vw, 8.2rem);
    line-height: 0.9;
    font-weight: 600;
    font-family: "Playfair Display", Georgia, serif;
    letter-spacing: -0.04em;
    text-transform: none;
    text-shadow: 0 18px 45px rgba(0, 0, 0, 0.34);
}

.hero-address {
    margin: 18px 0 0;
    max-width: 760px;
    color: rgba(245, 240, 232, 0.82);
    font-size: 1.08rem;
    font-weight: 300;
    line-height: 1.75;
    letter-spacing: 0.02em;
    text-transform: none;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    text-shadow: 0 10px 28px rgba(0, 0, 0, 0.32);
}

.hero h2 {
    margin: 28px 0 0;
    width: min(1500px, calc(100vw - 48px));
    max-width: none;
    display: flex;
    flex-direction: column;
    align-items: center;
    color: #ffffff;
    font-size: clamp(2rem, 4.8vw, 4.35rem);
    line-height: 1.08;
    font-weight: 500;
    font-family: "Playfair Display", Georgia, serif;
    letter-spacing: -0.035em;
    text-transform: none;
    text-shadow: 0 18px 42px rgba(0, 0, 0, 0.3);
    padding-bottom: 0.08em;
}

.hero h2 > span {
    display: block;
    width: 100%;
    max-width: 100%;
    margin-inline: auto;
    text-align: center;
    white-space: nowrap;
    overflow-wrap: normal;
}

.hero h2 > span:last-child {
    color: #d8b26b;
    font-style: italic;
    font-weight: 400;
}

.hero h2 > span:first-child {
    transform: none;
}

.hero-copy-row {
    display: inline-flex;
    align-items: flex-start;
    justify-content: center;
    gap: 10px;
}

.hero-copy-row + .hero-copy-row {
    margin-top: 10px;
}

.hero-copy-row-block {
    display: flex;
    width: 100%;
    justify-content: center;
}

.hero-edit-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    margin-top: 4px;
    border: 1px solid rgba(255, 255, 255, 0.28);
    border-radius: 999px;
    background: rgba(15, 15, 15, 0.28);
    color: #ffffff;
    font-size: 1rem;
    line-height: 1;
    cursor: pointer;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s ease, transform 0.2s ease, background 0.2s ease;
}

body.admin-mode .hero-edit-button {
    opacity: 1;
    pointer-events: auto;
}

.hero-edit-button:hover {
    background: var(--orange);
    transform: translateY(-1px);
}

.section-copy-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
}

.section-edit-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    margin-top: 2px;
    border: 1px solid rgba(15, 15, 15, 0.12);
    border-radius: 999px;
    background: #f4efe8;
    color: var(--text);
    font-size: 1rem;
    line-height: 1;
    cursor: pointer;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s ease, transform 0.2s ease, background 0.2s ease, color 0.2s ease;
}

body.admin-mode .section-edit-button {
    opacity: 1;
    pointer-events: auto;
}

.section-edit-button:hover {
    background: var(--orange);
    color: #ffffff;
    transform: translateY(-1px);
}

.hero-visual {
    display: none;
}

.hero-actions {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 16px;
    margin-top: 44px;
}

.hero-button,
.topbar-action,
.filter-chip,
.add-button,
.checkout-button {
    transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.hero-button:hover,
.topbar-action:hover,
.filter-chip:hover,
.add-button:hover,
.checkout-button:hover {
    transform: translateY(-2px);
}

.hero-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 58px;
    padding: 0 34px;
    border: 1px solid transparent;
    border-radius: 999px;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 0.95rem;
    font-weight: 600;
    letter-spacing: 0.01em;
    text-transform: none;
    transition:
        transform 0.24s ease,
        box-shadow 0.3s ease,
        color 0.24s ease,
        background 0.24s ease,
        border-color 0.24s ease;
}

.hero-button-primary {
    background: #d8b26b;
    color: #15120d;
    border-color: rgba(216, 178, 107, 0.9);
    box-shadow: 0 18px 38px rgba(0, 0, 0, 0.24);
}

.hero-button-primary:hover {
    background: #f5f0e8;
    color: #12100d;
    border-color: rgba(245, 240, 232, 0.92);
    box-shadow: 0 22px 48px rgba(0, 0, 0, 0.28);
}

.hero-button-secondary {
    background: rgba(255, 255, 255, 0.08);
    color: #ffffff;
    border-color: rgba(255, 255, 255, 0.22);
    backdrop-filter: blur(10px);
    box-shadow: 0 18px 34px rgba(0, 0, 0, 0.18);
}

.hero-button-secondary:hover {
    background: rgba(255, 255, 255, 0.14);
    color: #d8b26b;
    border-color: rgba(216, 178, 107, 0.92);
    box-shadow: 0 22px 42px rgba(0, 0, 0, 0.24);
}

.button-shiny {
    --button-shiny-bg: rgba(18, 14, 11, 0.86);
    --button-shiny-bg-soft: rgba(37, 28, 19, 0.9);
    --button-shiny-fg: #f8f1e4;
    --button-shiny-highlight: #d8b26b;
    --button-shiny-highlight-soft: #fff1c9;
    --button-shiny-shadow: rgba(216, 178, 107, 0.18);
    position: relative;
    isolation: isolate;
    overflow: hidden;
    border: 1px solid transparent;
    background:
        linear-gradient(var(--button-shiny-bg), var(--button-shiny-bg)) padding-box,
        conic-gradient(
            from var(--button-shiny-angle),
            transparent 0deg,
            rgba(216, 178, 107, 0.1) 28deg,
            var(--button-shiny-highlight) 56deg,
            var(--button-shiny-highlight-soft) 70deg,
            var(--button-shiny-highlight) 88deg,
            rgba(216, 178, 107, 0.14) 112deg,
            transparent 142deg 360deg
        ) border-box;
    color: var(--button-shiny-fg);
    box-shadow:
        inset 0 0 0 1px rgba(255, 255, 255, 0.05),
        0 14px 30px rgba(0, 0, 0, 0.2);
    animation: buttonShinyAngle 3.2s linear infinite;
}

.button-shiny::before,
.button-shiny::after,
.button-shiny > span::before {
    content: "";
    pointer-events: none;
    position: absolute;
    inset: 0;
    border-radius: inherit;
}

.button-shiny::before {
    inset: 2px;
    background:
        radial-gradient(circle at 2px 2px, rgba(255, 255, 255, 0.55) 0.8px, transparent 1px) 0 0 / 12px 12px,
        linear-gradient(180deg, rgba(255, 255, 255, 0.06), transparent 65%);
    mask-image: conic-gradient(
        from calc(var(--button-shiny-angle) + 28deg),
        rgba(0, 0, 0, 0.95),
        transparent 12% 84%,
        rgba(0, 0, 0, 0.95)
    );
    opacity: 0.28;
}

.button-shiny::after {
    inset: -65%;
    background: linear-gradient(115deg, transparent 34%, rgba(255, 255, 255, 0.1) 48%, var(--button-shiny-highlight) 54%, transparent 66%);
    opacity: 0.42;
    mix-blend-mode: screen;
    animation: buttonShinySweep 5.6s linear infinite;
}

.button-shiny > span {
    position: relative;
    z-index: 1;
}

.button-shiny > span::before {
    inset: -24%;
    border-radius: inherit;
    box-shadow: inset 0 -1.1rem 2.2rem 0 var(--button-shiny-shadow);
    opacity: 0;
    transition: opacity 0.42s ease;
    animation: buttonShinyPulse 3.2s ease-in-out infinite;
}

.button-shiny:is(:hover, :focus-visible) {
    --button-shiny-highlight: #e5c98d;
    --button-shiny-highlight-soft: #fff8e6;
    color: #fffaf1;
    box-shadow:
        inset 0 0 0 1px rgba(255, 255, 255, 0.08),
        0 18px 38px rgba(0, 0, 0, 0.24);
}

.button-shiny:is(:hover, :focus-visible) > span::before {
    opacity: 1;
}

.topbar-action.button-shiny {
    --button-shiny-bg: rgba(12, 10, 8, 0.74);
    --button-shiny-bg-soft: rgba(31, 23, 16, 0.84);
    --button-shiny-shadow: rgba(216, 178, 107, 0.14);
    min-height: 42px;
    padding: 0 22px;
    color: #f0e5d1;
    backdrop-filter: blur(10px);
}

.topbar-action.button-shiny:hover,
.topbar-action.button-shiny:focus-visible {
    background:
        linear-gradient(var(--button-shiny-bg), var(--button-shiny-bg)) padding-box,
        conic-gradient(
            from var(--button-shiny-angle),
            transparent 0deg,
            rgba(216, 178, 107, 0.1) 28deg,
            var(--button-shiny-highlight) 56deg,
            var(--button-shiny-highlight-soft) 70deg,
            var(--button-shiny-highlight) 88deg,
            rgba(216, 178, 107, 0.14) 112deg,
            transparent 142deg 360deg
        ) border-box;
    border-color: transparent;
}

.hero-button-secondary.button-shiny {
    --button-shiny-bg: rgba(24, 18, 12, 0.62);
    --button-shiny-bg-soft: rgba(39, 27, 17, 0.86);
    --button-shiny-shadow: rgba(216, 178, 107, 0.18);
    color: #f9f2e8;
    backdrop-filter: blur(14px);
}

.hero-button-secondary.button-shiny:hover,
.hero-button-secondary.button-shiny:focus-visible {
    background:
        linear-gradient(var(--button-shiny-bg), var(--button-shiny-bg)) padding-box,
        conic-gradient(
            from var(--button-shiny-angle),
            transparent 0deg,
            rgba(216, 178, 107, 0.1) 28deg,
            var(--button-shiny-highlight) 56deg,
            var(--button-shiny-highlight-soft) 70deg,
            var(--button-shiny-highlight) 88deg,
            rgba(216, 178, 107, 0.14) 112deg,
            transparent 142deg 360deg
        ) border-box;
    color: #fffaf1;
    border-color: transparent;
}

@keyframes buttonShinyAngle {
    to {
        --button-shiny-angle: 360deg;
    }
}

@keyframes buttonShinySweep {
    to {
        transform: rotate(360deg);
    }
}

@keyframes buttonShinyPulse {
    0%,
    100% {
        transform: scale(1);
    }

    50% {
        transform: scale(1.08);
    }
}

.hero-scroll-indicator {
    position: absolute;
    left: 50%;
    bottom: 28px;
    z-index: 3;
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    color: rgba(255, 255, 255, 0.72);
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.28em;
    text-decoration: none;
    text-transform: uppercase;
    transform: translateX(-50%);
    animation: heroScrollBounce 2.4s ease-in-out infinite;
}

.hero-scroll-line {
    width: 1px;
    height: 34px;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.14));
}

.marquee {
    position: relative;
    overflow: hidden;
    padding: 28px 0;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    background: #1a0f0a;
    isolation: isolate;
}

.marquee::before {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background:
        linear-gradient(90deg, rgba(26, 15, 10, 1), rgba(26, 15, 10, 0) 12%),
        linear-gradient(270deg, rgba(26, 15, 10, 1), rgba(26, 15, 10, 0) 12%);
    z-index: 1;
}

.marquee::after {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background: radial-gradient(circle at center, rgba(200, 146, 42, 0.08), transparent 58%);
    z-index: 0;
}

.marquee-track {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    gap: 28px;
    width: max-content;
    animation: marquee-scroll 24s linear infinite;
}

.marquee-track span {
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: clamp(1.7rem, 3.4vw, 3rem);
    line-height: 1;
    text-transform: none;
    letter-spacing: -0.03em;
}

.marquee-item {
    color: rgba(245, 240, 232, 0.92);
    font-weight: 500;
    text-shadow: 0 10px 28px rgba(0, 0, 0, 0.28);
}

.marquee-item-green {
    color: rgba(245, 240, 232, 0.74);
}

.marquee-item-yellow {
    color: #c8922a;
}

.marquee-item-black {
    color: #ffffff;
}

.marquee-dot {
    color: rgba(200, 146, 42, 0.72);
    font-size: clamp(1.2rem, 2vw, 1.8rem);
    transform: translateY(-2px);
}

.section-shell {
    position: relative;
    width: var(--shell);
    margin: 0 auto;
    padding: 72px 0 0;
    isolation: isolate;
}

.menu-section,
.delivery-section,
.site-footer {
    overflow: hidden;
}

.menu-section::before {
    top: 108px;
    right: -120px;
    width: 320px;
    height: 320px;
    border-radius: 50%;
    background:
        radial-gradient(circle at 50% 50%, rgba(232, 84, 36, 0.14), rgba(232, 84, 36, 0.06) 42%, transparent 70%);
    filter: blur(12px);
    animation: menuGlowFloat 28s ease-in-out infinite alternate;
}

.menu-section::after {
    left: -80px;
    bottom: 60px;
    width: 260px;
    height: 260px;
    border-radius: 38% 62% 56% 44% / 50% 38% 62% 50%;
    background:
        radial-gradient(circle at 44% 44%, rgba(243, 216, 109, 0.2), rgba(243, 216, 109, 0.08) 46%, transparent 72%);
    filter: blur(8px);
    opacity: 0.8;
    animation: menuGlowFloatReverse 30s ease-in-out infinite alternate;
}

.menu-section {
    width: 100vw;
    max-width: none;
    margin-left: calc(50% - 50vw);
    margin-right: calc(50% - 50vw);
    scroll-margin-top: 110px;
    background:
        radial-gradient(circle at top center, rgba(200, 146, 42, 0.09), transparent 25%),
        radial-gradient(circle at 18% 26%, rgba(216, 178, 107, 0.12), transparent 10%),
        radial-gradient(circle at 86% 22%, rgba(232, 84, 36, 0.1), transparent 11%),
        radial-gradient(circle at 36% 74%, rgba(243, 216, 109, 0.09), transparent 12%),
        radial-gradient(circle at 74% 82%, rgba(216, 178, 107, 0.08), transparent 9%),
        linear-gradient(120deg, transparent 0%, rgba(216, 178, 107, 0.08) 28%, rgba(232, 84, 36, 0.06) 48%, transparent 72%),
        linear-gradient(180deg, #0d0d0d 0%, #120a07 100%);
    background-size: 120% 120%, 140% 140%, 150% 150%, 130% 130%, 145% 145%, 220% 220%, 100% 100%;
    animation: menuBackgroundDrift 24s ease-in-out infinite alternate;
    border-radius: 0;
    padding: 84px max(32px, calc((100vw - 1240px) / 2 + 32px)) 40px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-left: 0;
    border-right: 0;
    box-shadow: 0 24px 64px rgba(0, 0, 0, 0.2);
}

.delivery-section::before {
    top: 84px;
    left: -110px;
    width: 300px;
    height: 300px;
    border-radius: 44% 56% 60% 40% / 40% 44% 56% 60%;
    background:
        radial-gradient(circle at 40% 40%, rgba(35, 66, 32, 0.14), rgba(35, 66, 32, 0.05) 48%, transparent 74%);
    filter: blur(10px);
    animation: ambientFloat 18s ease-in-out infinite;
}

.delivery-section::after {
    right: -90px;
    bottom: 24px;
    width: 240px;
    height: 240px;
    border-radius: 50%;
    background:
        radial-gradient(circle at 50% 50%, rgba(232, 84, 36, 0.12), rgba(232, 84, 36, 0.04) 48%, transparent 72%);
    filter: blur(10px);
    animation: ambientPulse 15s ease-in-out infinite;
}

.delivery-section {
    width: 100vw;
    max-width: none;
    margin-left: calc(50% - 50vw);
    margin-right: calc(50% - 50vw);
    padding: 88px max(24px, calc((100vw - 1240px) / 2 + 16px)) 24px;
    background:
        radial-gradient(circle at top center, rgba(200, 146, 42, 0.08), transparent 26%),
        linear-gradient(180deg, #0d0d0d 0%, #160d09 100%);
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.delivery-easy-section {
    width: 100vw;
    max-width: none;
    margin-left: calc(50% - 50vw);
    margin-right: calc(50% - 50vw);
    padding: 88px max(24px, calc((100vw - 1240px) / 2 + 16px)) 48px;
    background:
        radial-gradient(circle at 50% 0%, rgba(216, 178, 107, 0.14), transparent 28%),
        radial-gradient(circle at 18% 30%, rgba(35, 66, 32, 0.16), transparent 22%),
        radial-gradient(circle at 82% 24%, rgba(232, 84, 36, 0.1), transparent 20%),
        linear-gradient(180deg, #15110f 0%, #1a120d 54%, #120d09 100%);
    color: #ffffff;
}

.delivery-easy-shell {
    width: min(1240px, 100%);
    margin: 0 auto;
}

.delivery-easy-head {
    display: grid;
    justify-items: center;
    gap: 12px;
    margin-bottom: 44px;
    text-align: center;
}

.delivery-easy-head h2 {
    margin: 0;
    padding-bottom: 0.12em;
    font-family: "Playfair Display", Georgia, serif;
    font-size: clamp(2rem, 4vw, 3.4rem);
    line-height: 1.1;
    letter-spacing: -0.03em;
    color: transparent;
    background-image: linear-gradient(90deg, #fff7df, #d8b26b, #ffefd0, #ffffff, #d8b26b);
    background-size: 300% 100%;
    background-position: 0% 50%;
    -webkit-background-clip: text;
    background-clip: text;
    animation: heroGradientShift 8s ease-in-out infinite alternate;
}

.delivery-easy-section .section-kicker {
    color: #c8922a;
}

.delivery-easy-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 24px;
}

.delivery-easy-card {
    display: grid;
    justify-items: center;
    gap: 18px;
    min-height: 280px;
    padding: 36px 28px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 28px;
    background: rgba(255, 255, 255, 0.05);
    text-align: center;
    backdrop-filter: blur(8px);
}

.delivery-easy-icon {
    display: grid;
    place-items: center;
    width: 72px;
    height: 72px;
    color: rgba(255, 255, 255, 0.96);
}

.delivery-easy-icon svg {
    width: 64px;
    height: 64px;
}

.delivery-easy-icon img {
    width: 64px;
    height: 64px;
    object-fit: contain;
    display: block;
}

.delivery-easy-card h3 {
    margin: 0;
    color: #ffffff;
    font-family: "Space Grotesk", "Inter", "Segoe UI", Arial, sans-serif;
    font-size: clamp(1.5rem, 2.2vw, 2rem);
    font-weight: 500;
    letter-spacing: -0.03em;
}

.delivery-easy-card p {
    margin: 0;
    color: #c8922a;
    font-size: 1.02rem;
    line-height: 1.65;
}

.delivery-head {
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 44px;
    text-align: center;
}

.delivery-head > div {
    display: grid;
    gap: 12px;
    width: 100%;
    max-width: 760px;
    justify-items: center;
    margin: 0 auto;
}

.delivery-section .section-kicker {
    color: #c8922a;
    font-size: 0.76rem;
    font-weight: 600;
    letter-spacing: 0.26em;
    text-transform: uppercase;
}

.delivery-section .section-head h2 {
    color: #111111;
    font-family: "Playfair Display", Georgia, serif;
    font-size: clamp(2.1rem, 4.3vw, 3.8rem);
    line-height: 1.04;
    letter-spacing: -0.03em;
    text-transform: none;
    text-align: center;
}

.about-grid,
.menu-layout,
.contact-grid {
    display: grid;
    gap: 24px;
}

.about-grid {
    grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
    align-items: stretch;
}

.about-copy h2,
.section-head h2,
.contact-copy h2 {
    margin: 0;
    font-size: clamp(2.3rem, 5vw, 4.2rem);
    line-height: 0.94;
    color: var(--text);
}

.about-copy p,
.dish-body p,
.order-note,
.step-card p,
.review-card p,
.contact-copy p {
    color: var(--text-soft);
    line-height: 1.7;
}

.about-copy p,
.contact-copy p {
    margin: 20px 0 0;
    max-width: 58ch;
}

.about-cards {
    display: grid;
    gap: 18px;
}

.about-card,
.menu-content,
.order-panel,
.dish-card,
.step-card,
.review-card,
.contact-card {
    border: 1px solid var(--line);
    border-radius: var(--radius-xl);
}

.about-card {
    padding: 28px;
    box-shadow: var(--shadow);
}

.about-card span,
.step-card span {
    display: block;
    margin-bottom: 10px;
    font-family: "Space Grotesk", "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 3rem;
    line-height: 0.9;
    text-transform: uppercase;
}

.about-card p {
    margin: 0;
    line-height: 1.7;
}

.about-card-dark {
    background: var(--green);
    color: #ffffff;
}

.about-card-accent {
    background: var(--yellow);
    color: var(--text);
}

.section-head {
    display: flex;
    align-items: end;
    justify-content: space-between;
    gap: 24px;
    margin-bottom: 24px;
}

.menu-section .section-head {
    align-items: center;
    justify-content: center;
    margin-bottom: 44px;
    text-align: center;
}

.menu-section .section-head > div {
    display: grid;
    gap: 12px;
    width: min(100%, 1120px);
    max-width: 1120px;
    justify-items: center;
}

.section-kicker {
    color: var(--orange);
}

.menu-section .section-kicker {
    color: #c8922a;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 0.76rem;
    font-weight: 600;
    letter-spacing: 0.26em;
    text-transform: uppercase;
}

.menu-section .section-head h2 {
    color: transparent;
    background-image: linear-gradient(90deg, #fff7df, #d8b26b, #ffefd0, #ffffff, #d8b26b);
    background-size: 300% 100%;
    background-position: 0% 50%;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: heroGradientShift 8s ease-in-out infinite alternate;
    font-family: "Playfair Display", Georgia, serif;
    font-size: clamp(2.2rem, 4.6vw, 4rem);
    line-height: 1.04;
    letter-spacing: -0.035em;
    text-transform: none;
    max-width: 1120px;
}

.section-link {
    color: var(--orange);
    font-size: 0.84rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    background: transparent;
    padding: 0;
    font-family: "JetBrains Mono", monospace;
}

.menu-layout {
    grid-template-columns: 1fr;
    align-items: start;
    gap: 20px;
}

.menu-admin-bar {
    display: none;
    justify-content: flex-end;
    margin-bottom: 16px;
}

body.admin-mode .menu-admin-bar {
    display: flex;
}

.menu-content,
.cart-drawer {
    padding: 28px;
    background: var(--surface);
    box-shadow: 0 16px 40px rgba(17, 17, 17, 0.06);
}

.menu-admin-bar {
    justify-content: flex-end;
    gap: 10px;
}

.menu-content {
    position: relative;
    overflow: hidden;
    background: transparent;
    padding: 0;
    border: 0;
    box-shadow: none;
}

.menu-content::before {
    display: none;
}

.admin-modal {
    position: fixed;
    top: 50%;
    left: 50%;
    z-index: 72;
    width: min(620px, calc(100% - 24px));
    max-height: calc(100vh - 40px);
    padding: 24px;
    overflow-y: auto;
    border: 1px solid var(--line);
    border-radius: 28px;
    background: #ffffff;
    box-shadow: 0 32px 80px rgba(15, 15, 15, 0.22);
    opacity: 0;
    pointer-events: none;
    transform: translate(-50%, -44%);
    transition: opacity 0.25s ease, transform 0.25s ease;
}

.checkout-modal {
    position: fixed;
    top: 50%;
    left: 50%;
    z-index: 72;
    width: min(1080px, calc(100% - 24px));
    max-height: calc(100vh - 32px);
    opacity: 0;
    pointer-events: none;
    transform: translate(-50%, -46%);
    transition: opacity 0.25s ease, transform 0.25s ease;
}

.checkout-modal.is-open {
    opacity: 1;
    pointer-events: auto;
    transform: translate(-50%, -50%);
}

.auth-modal {
    position: fixed;
    top: 50%;
    left: 50%;
    z-index: 72;
    width: min(620px, calc(100% - 24px));
    opacity: 0;
    pointer-events: none;
    transform: translate(-50%, -46%);
    transition: opacity 0.25s ease, transform 0.25s ease;
}

.auth-modal.is-open {
    opacity: 1;
    pointer-events: auto;
    transform: translate(-50%, -50%);
}

.auth-modal-shell {
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 32px;
    background:
        radial-gradient(circle at top right, rgba(200, 146, 42, 0.14), transparent 28%),
        radial-gradient(circle at left top, rgba(216, 178, 107, 0.08), transparent 26%),
        #0d0d0d;
    box-shadow: 0 36px 90px rgba(0, 0, 0, 0.48);
}

.auth-modal-shell::before {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent 24%);
    pointer-events: none;
}

.auth-modal-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 20px 0;
}

.auth-modal-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 42px;
    height: 42px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.04);
    color: rgba(245, 240, 232, 0.88);
    font: inherit;
    font-size: 1rem;
    cursor: pointer;
    transition: border-color 0.24s ease, color 0.24s ease, background 0.24s ease, transform 0.24s ease;
}

.auth-modal-icon:hover {
    background: rgba(200, 146, 42, 0.12);
    border-color: rgba(200, 146, 42, 0.32);
    color: #f8f1e4;
    transform: translateY(-1px);
}

.auth-modal-body {
    display: grid;
    gap: 22px;
    padding: 8px 32px 34px;
}

.checkout-switcher.auth-switcher {
    margin-bottom: 2px;
    padding: 6px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.03);
    grid-template-columns: repeat(2, minmax(0, 1fr));
}

.checkout-switcher.auth-switcher .checkout-switch {
    min-height: 48px;
    border-radius: 14px;
    background: transparent;
    color: rgba(245, 240, 232, 0.62);
    letter-spacing: 0.03em;
    box-shadow: none;
}

.checkout-switcher.auth-switcher .checkout-switch.is-active {
    background: linear-gradient(180deg, rgba(248, 241, 228, 0.96), rgba(236, 226, 208, 0.92));
    color: #16120d;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.18);
}

.checkout-switcher.auth-switcher .checkout-switch:hover {
    color: #f8f1e4;
}

.checkout-switcher.auth-switcher .checkout-switch:not(.is-active):hover {
    background: rgba(255, 255, 255, 0.04);
}

.auth-form {
    display: grid;
    gap: 20px;
}

.auth-form.is-hidden {
    display: none;
}

.auth-link-button {
    width: fit-content;
    padding: 0;
    border: 0;
    background: transparent;
    color: #d8b26b;
    font: inherit;
    font-size: 0.9rem;
    font-weight: 700;
    cursor: pointer;
}

.auth-link-button:hover {
    color: #f5f0e8;
}

.auth-copy {
    display: grid;
    gap: 10px;
    padding-bottom: 4px;
    text-align: left;
}

.auth-copy .section-kicker {
    margin: 0;
    color: rgba(255, 255, 255, 0.4);
    font-size: 0.78rem;
    font-weight: 500;
    line-height: 1;
    letter-spacing: 0.04em;
    text-transform: none;
}

.auth-copy h3,
.account-orders h3,
.account-summary-card strong {
    font-family: "Space Grotesk", "Inter", "Segoe UI", Arial, sans-serif;
    text-transform: uppercase;
}

.auth-copy h3 {
    margin: 0;
    font-family: "Playfair Display", Georgia, serif;
    font-size: clamp(2rem, 6vw, 3rem);
    font-weight: 600;
    line-height: 0.98;
    letter-spacing: -0.04em;
    text-transform: none;
    color: #f5f0e8;
}

#auth-login-form .auth-copy h3 {
    white-space: normal;
    font-size: clamp(2rem, 6vw, 3rem);
}

.auth-copy p,
.account-summary-card p,
.account-order-empty,
.account-order-meta,
.account-order-items {
    margin: 0;
    color: rgba(245, 240, 232, 0.62);
    line-height: 1.65;
}

.auth-consents {
    display: grid;
    gap: 12px;
    padding: 0;
    border: 0;
    border-radius: 0;
    background: transparent;
}

.auth-consent {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 14px 16px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.03);
    color: rgba(245, 240, 232, 0.68);
    font-size: 0.88rem;
    line-height: 1.45;
}

.auth-consent span {
    color: rgba(245, 240, 232, 0.68);
}

.auth-consent input {
    flex: 0 0 auto;
    width: 18px;
    height: 18px;
    margin-top: 1px;
    accent-color: #c8922a;
}

.auth-consent a {
    color: #d8b26b;
    font-weight: 700;
    text-decoration: none;
}

.auth-consent a:hover {
    color: #f5f0e8;
    text-decoration: none;
}

.auth-consents.is-attention {
    padding: 10px;
    border: 1px solid rgba(200, 146, 42, 0.5);
    border-radius: 22px;
    background: rgba(200, 146, 42, 0.08);
    box-shadow: 0 0 0 3px rgba(200, 146, 42, 0.1);
}

.auth-field {
    position: relative;
}

.auth-field.is-hidden,
.auth-submit.is-hidden {
    display: none;
}

.auth-field input {
    width: 100%;
    min-height: 54px;
    padding: 18px 0 10px;
    border: 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 0;
    background: transparent;
    color: #f5f0e8;
    font: inherit;
    font-size: 1rem;
    font-weight: 400;
    transition: border-color 0.24s ease, color 0.24s ease;
}

.auth-field-floating > span {
    position: absolute;
    left: 0;
    top: 18px;
    color: rgba(255, 255, 255, 0.4);
    font-size: 0.78rem;
    line-height: 1;
    letter-spacing: 0.04em;
    pointer-events: none;
    transition: top 0.2s ease, font-size 0.2s ease, color 0.2s ease;
}

.auth-field-floating input::placeholder {
    color: transparent;
}

.auth-field-floating input:focus + span,
.auth-field-floating input:not(:placeholder-shown) + span {
    top: -2px;
    font-size: 0.64rem;
    color: #c8922a;
}

.auth-field input:focus {
    outline: none;
    border-color: #c8922a;
    box-shadow: none;
}

.auth-submit {
    min-height: 56px;
    border: 0;
    border-radius: 18px;
    background: linear-gradient(90deg, #c8922a, #a0721c);
    color: #0d0d0d;
    font: inherit;
    font-size: 0.92rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    cursor: pointer;
    transition: transform 0.2s ease, opacity 0.2s ease, box-shadow 0.2s ease;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.28);
}

.auth-submit:hover {
    opacity: 0.92;
    transform: translateY(-1px);
}

.auth-submit-secondary {
    background: rgba(255, 255, 255, 0.06);
    color: #f5f0e8;
    box-shadow: none;
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.auth-submit-secondary:hover {
    background: rgba(255, 255, 255, 0.1);
}

.auth-submit:disabled {
    opacity: 0.7;
    cursor: wait;
    transform: none;
}

.auth-recovery-actions {
    display: grid;
    gap: 12px;
}

.auth-hint {
    min-height: 24px;
    color: #c8922a;
    font-size: 0.88rem;
    line-height: 1.45;
    text-align: left;
}

.auth-required-actions {
    display: grid;
    gap: 12px;
}

.account-modal {
    position: fixed;
    top: 0;
    right: 0;
    bottom: auto;
    z-index: 72;
    width: min(430px, 100%);
    height: 100vh;
    height: 100svh;
    height: 100dvh;
    max-height: 100vh;
    max-height: 100svh;
    max-height: 100dvh;
    padding: 0;
    background: transparent;
    transform: translateX(0);
    transition: transform 0.28s ease;
}

.account-modal.is-hidden {
    display: block;
    pointer-events: none;
    transform: translateX(100%);
}

.account-modal-shell {
    position: relative;
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
    overflow-y: auto;
    padding: 24px;
    padding-bottom: calc(24px + env(safe-area-inset-bottom));
    border: 0;
    border-radius: 0;
    background: var(--surface);
    box-shadow: -24px 0 48px rgba(15, 15, 15, 0.18);
    -webkit-overflow-scrolling: touch;
}

.account-modal-head {
    display: flex;
    align-items: start;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 14px;
    padding-right: 48px;
}

.account-modal-head h2 {
    margin: 6px 0 0;
    font-size: 1.45rem;
    line-height: 1.1;
}

.account-modal-close {
    position: absolute;
    top: 20px;
    right: 20px;
    z-index: 2;
}

.account-current-order,
.account-orders,
.account-profile-card,
.account-summary-card {
    backdrop-filter: blur(10px);
}

.account-current-order,
.account-profile-card {
    border: 1px solid var(--line);
    border-radius: 8px;
    background: #ffffff;
    box-shadow: 0 12px 30px rgba(17, 17, 17, 0.06);
    padding: 16px;
}

.account-current-order {
    margin-bottom: 12px;
}

.account-order-card-current {
    background:
        linear-gradient(180deg, rgba(255, 255, 255, 1), rgba(247, 241, 232, 0.92)),
        #ffffff;
}

.account-summary-card-highlight {
    background:
        radial-gradient(circle at top right, rgba(232, 84, 36, 0.12), transparent 42%),
        #ffffff;
}

.account-profile-copy {
    margin: 8px 0 12px;
    color: var(--text-soft);
    line-height: 1.45;
}

.account-phone-form {
    display: grid;
    gap: 10px;
}

.account-phone-hint {
    text-align: left;
    min-height: 18px;
    margin-top: 8px;
}

.account-modal .auth-field input {
    min-height: 48px;
    border-radius: 8px;
}

.account-modal .auth-submit {
    min-height: 44px;
    border-radius: 8px;
}

.account-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 10px;
    margin-bottom: 10px;
}

.account-summary-card,
.account-orders {
    border: 1px solid var(--line);
    border-radius: 8px;
    background: #ffffff;
    box-shadow: 0 12px 30px rgba(17, 17, 17, 0.06);
}

.account-summary-card {
    display: grid;
    gap: 6px;
    padding: 16px;
}

.account-summary-label {
    color: var(--orange);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-family: "JetBrains Mono", monospace;
}

.account-summary-card strong {
    font-size: clamp(1.5rem, 3.4vw, 2.25rem);
    line-height: 0.9;
    color: var(--green);
}

.account-orders {
    padding: 16px;
    margin-bottom: 10px;
}

.account-orders-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 12px;
}

.account-orders-head h3 {
    margin: 0;
    font-size: 1.2rem;
    color: var(--orange);
}

.account-refresh {
    background: var(--green);
}

.account-orders-list {
    display: grid;
    gap: 8px;
}

#catalog-search-results .order-line {
    border-color: rgba(15, 15, 15, 0.08);
    background: rgba(15, 15, 15, 0.03);
}

#catalog-search-results .order-line strong,
#catalog-search-results .order-line small {
    display: block;
    color: var(--text);
}

#catalog-search-results .order-line small {
    margin-top: 4px;
    color: var(--text-soft);
}

.account-order-card {
    display: grid;
    gap: 7px;
    padding: 12px;
    border: 1px solid rgba(15, 15, 15, 0.08);
    border-radius: 8px;
    background: #fbf8f2;
}

.account-order-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}

.account-order-status {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 28px;
    padding: 0 10px;
    border-radius: 8px;
    background: rgba(35, 66, 32, 0.12);
    color: var(--green);
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.account-order-status-preparing {
    background: rgba(232, 84, 36, 0.14);
    color: var(--orange);
}

.account-order-status-ready {
    background: rgba(35, 66, 32, 0.12);
    color: var(--green);
}

.order-admin-meta-grid {
    display: grid;
    gap: 8px;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.order-admin-meta-card {
    display: grid;
    gap: 4px;
    padding: 12px 14px;
    border: 1px solid rgba(15, 15, 15, 0.08);
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.72);
}

.order-admin-meta-card span {
    color: rgba(15, 15, 15, 0.6);
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.order-admin-meta-card strong {
    font-size: 1rem;
    color: var(--text);
}

.order-admin-actions {
    display: grid;
    gap: 12px;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: end;
}

.order-admin-actions .admin-field {
    gap: 8px;
}

.order-admin-items {
    color: var(--text-soft);
    line-height: 1.5;
}

.order-admin-hint {
    color: var(--text-soft);
    font-size: 0.92rem;
}

.checkout-modal-shell {
    display: block;
    max-height: inherit;
    overflow: hidden;
    border-radius: 32px;
    background: #ffffff;
    box-shadow: 0 36px 90px rgba(15, 15, 15, 0.28);
}

.checkout-modal-head h3,
.checkout-preview strong {
    font-family: "Space Grotesk", "Inter", "Segoe UI", Arial, sans-serif;
    text-transform: uppercase;
}

.checkout-modal-head h3 {
    margin: 6px 0 0;
    font-size: clamp(2rem, 3.5vw, 3.4rem);
    line-height: 0.92;
}

.checkout-modal-form-wrap {
    display: grid;
    grid-template-rows: auto 1fr;
    gap: 20px;
    max-height: inherit;
    padding: 30px;
    overflow-y: auto;
    overscroll-behavior: contain;
    -webkit-overflow-scrolling: touch;
    background:
        radial-gradient(circle at top right, rgba(217, 163, 95, 0.16), transparent 26%),
        #fffdf9;
}

.checkout-modal-head {
    display: flex;
    align-items: start;
    justify-content: space-between;
    gap: 16px;
}

.checkout-form {
    display: grid;
    gap: 18px;
}

.checkout-preview {
    display: grid;
    gap: 12px;
}

.checkout-preview-inline {
    grid-template-columns: repeat(3, minmax(0, 1fr));
}

.checkout-preview > div {
    display: grid;
    gap: 6px;
    padding: 16px 18px;
    border: 1px solid rgba(15, 15, 15, 0.08);
    border-radius: 20px;
    background: #f7f1e8;
}

.checkout-preview span {
    color: rgba(15, 15, 15, 0.62);
    font-size: 0.78rem;
    line-height: 1.45;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.checkout-preview strong {
    font-size: 1.45rem;
    letter-spacing: -0.03em;
    color: var(--text);
}

.checkout-order-list {
    display: grid;
    gap: 12px;
}

.checkout-order-list .order-empty,
.checkout-order-list .order-line {
    border-color: rgba(255, 255, 255, 0.08);
    background:
        radial-gradient(circle at top right, rgba(216, 178, 107, 0.12), transparent 28%),
        rgba(255, 255, 255, 0.03);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02);
}

.checkout-order-list .order-empty strong,
.checkout-order-list .order-line strong {
    color: #f5f0e8;
}

.checkout-order-list .order-empty p,
.checkout-order-list .order-line small {
    color: rgba(245, 240, 232, 0.62);
}

.order-line-qty {
    flex: 0 0 auto;
}

.checkout-order-list .qty-picker-ghost {
    border-color: rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.03);
}

.checkout-order-list .qty-picker-ghost .qty-button {
    background: rgba(255, 255, 255, 0.08);
    color: #f5f0e8;
}

.checkout-order-list .qty-picker-ghost .qty-button:hover {
    background: #c8922a;
    color: #0d0d0d;
}

.checkout-order-list .qty-picker-ghost .qty-value {
    color: #f5f0e8;
}

.checkout-order-list .order-remove-button {
    background: rgba(255, 255, 255, 0.08);
    color: #f5f0e8;
}

.checkout-order-list .order-remove-button:hover {
    background: rgba(232, 84, 36, 0.92);
    color: #ffffff;
}

.checkout-switcher {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    padding: 8px;
    border: 1px solid rgba(15, 15, 15, 0.08);
    border-radius: 20px;
    background: #f7f1e8;
}

.checkout-switch {
    min-height: 52px;
    border: 0;
    border-radius: 14px;
    background: transparent;
    color: rgba(15, 15, 15, 0.74);
    font: inherit;
    font-size: 0.88rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    cursor: pointer;
    transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}

.checkout-switch.is-active {
    background: #ffffff;
    color: var(--text);
    box-shadow: 0 12px 24px rgba(15, 15, 15, 0.08);
}

.checkout-switch:hover {
    transform: translateY(-1px);
}

.checkout-switch.is-disabled,
.checkout-switch:disabled {
    opacity: 0.42;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
}

.cart-checkout-mode {
    display: grid;
    gap: 10px;
    margin-bottom: 18px;
}

.cart-checkout-mode-label {
    color: rgba(255, 255, 255, 0.74);
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-family: "JetBrains Mono", monospace;
}

.cart-drawer .checkout-switcher {
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(255, 255, 255, 0.14);
}

.cart-checkout-switcher {
    margin-bottom: 18px;
}

.cart-drawer .checkout-switch {
    color: rgba(255, 255, 255, 0.76);
}

.cart-drawer .checkout-switch.is-active {
    background: #ffffff;
    color: var(--text);
}

.cart-checkout-note {
    margin: 0;
    color: rgba(255, 255, 255, 0.72);
    font-size: 0.84rem;
    line-height: 1.45;
}

.delivery-threshold {
    display: none !important;
}

.delivery-threshold-icon,
#delivery-threshold-amount,
#delivery-threshold-amount + span {
    display: none !important;
}

.checkout-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}

.checkout-field {
    display: grid;
    gap: 8px;
}

.checkout-field-wide {
    grid-column: 1 / -1;
}

.checkout-field span,
.checkout-label {
    color: rgba(15, 15, 15, 0.7);
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-family: "JetBrains Mono", monospace;
}

.checkout-field input {
    min-height: 54px;
    padding: 0 16px;
    border: 1px solid rgba(15, 15, 15, 0.12);
    border-radius: 16px;
    background: #ffffff;
    color: var(--text);
    font: inherit;
}

.checkout-field input:focus {
    outline: none;
    border-color: rgba(232, 84, 36, 0.46);
    box-shadow: 0 0 0 4px rgba(232, 84, 36, 0.12);
}

.checkout-delivery-fields {
    display: grid;
    gap: 14px;
}

.checkout-delivery-fields.is-hidden {
    display: none;
}

.checkout-switcher.is-hidden {
    display: none;
}

.checkout-payment {
    display: grid;
    gap: 10px;
}

.checkout-bonus-box {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 180px;
    gap: 14px;
    align-items: end;
    padding: 16px 18px;
    border: 1px solid rgba(15, 15, 15, 0.08);
    border-radius: 18px;
    background: #f7f1e8;
}

.checkout-bonus-copy {
    display: grid;
    gap: 8px;
}

.checkout-bonus-copy p {
    margin: 0;
    color: rgba(15, 15, 15, 0.68);
    line-height: 1.5;
}

.checkout-bonus-field {
    gap: 10px;
}

.checkout-bonus-stepper {
    display: grid;
    grid-template-columns: 42px minmax(0, 1fr) 42px;
    align-items: center;
    min-height: 54px;
    border: 1px solid rgba(15, 15, 15, 0.12);
    border-radius: 16px;
    background: #ffffff;
    overflow: hidden;
}

.checkout-bonus-button {
    width: 42px;
    height: 42px;
    border: 0;
    background: transparent;
    color: var(--text);
    font: inherit;
    font-size: 1.1rem;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.2s ease, color 0.2s ease;
}

.checkout-bonus-button:hover {
    background: rgba(232, 84, 36, 0.1);
    color: var(--orange);
}

.checkout-bonus-stepper input[type="number"] {
    width: 100%;
    min-width: 0;
    height: 54px;
    padding: 0 12px;
    border: 0;
    background: transparent;
    color: var(--text);
    font: inherit;
    font-size: 1rem;
    font-weight: 700;
    text-align: center;
    appearance: textfield;
    -moz-appearance: textfield;
}

.checkout-bonus-stepper input[type="number"]::-webkit-outer-spin-button,
.checkout-bonus-stepper input[type="number"]::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
}

.checkout-bonus-stepper input[type="number"]:focus {
    outline: none;
}

.checkout-note {
    padding: 16px 18px;
    border: 1px solid rgba(15, 15, 15, 0.08);
    border-radius: 18px;
    background: #f6efe7;
    color: rgba(15, 15, 15, 0.76);
    line-height: 1.5;
}

.checkout-consents {
    display: grid;
    gap: 10px;
    padding: 14px 16px;
    border: 1px solid rgba(15, 15, 15, 0.08);
    border-radius: 8px;
    background: #ffffff;
}

.checkout-consent {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    color: rgba(15, 15, 15, 0.76);
    font-size: 0.9rem;
    line-height: 1.35;
}

.checkout-consent input {
    flex: 0 0 auto;
    width: 18px;
    height: 18px;
    margin-top: 1px;
    accent-color: var(--green);
}

.checkout-consent a {
    color: var(--orange);
    font-weight: 700;
    text-decoration: none;
}

.checkout-consent a:hover {
    text-decoration: underline;
}

.checkout-consents.is-attention {
    border-color: rgba(232, 84, 36, 0.72);
    box-shadow: 0 0 0 3px rgba(232, 84, 36, 0.14);
}

.checkout-consent-popup {
    position: fixed;
    left: 50%;
    bottom: 28px;
    z-index: 130;
    width: min(420px, calc(100% - 24px));
    padding: 14px 16px;
    border-radius: 8px;
    background: var(--green);
    color: #ffffff;
    box-shadow: 0 18px 36px rgba(35, 66, 32, 0.28);
    font-size: 0.92rem;
    font-weight: 700;
    line-height: 1.35;
    text-align: center;
    opacity: 0;
    pointer-events: none;
    transform: translate(-50%, 14px);
    transition: opacity 0.2s ease, transform 0.2s ease;
}

.checkout-warning-popup {
    background: var(--orange);
    box-shadow: 0 18px 36px rgba(151, 62, 22, 0.28);
}

.checkout-consent-popup.is-visible {
    opacity: 1;
    transform: translate(-50%, 0);
}

.checkout-actions {
    display: flex;
    justify-content: flex-end;
}

.order-success-backdrop {
    position: fixed;
    inset: 0;
    z-index: 115;
    background: rgba(6, 5, 4, 0.72);
    backdrop-filter: blur(10px);
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.24s ease;
}

.order-success-backdrop.is-open {
    opacity: 1;
    pointer-events: auto;
}

.order-success-modal {
    position: fixed;
    top: 50%;
    left: 50%;
    z-index: 116;
    width: min(540px, calc(100% - 32px));
    opacity: 0;
    pointer-events: none;
    transform: translate(-50%, -48%);
    transition: opacity 0.24s ease, transform 0.24s ease;
}

.order-success-modal.is-open {
    opacity: 1;
    pointer-events: auto;
    transform: translate(-50%, -50%);
}

.order-success-shell {
    position: relative;
    display: grid;
    gap: 18px;
    padding: 30px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 30px;
    background:
        radial-gradient(circle at top right, rgba(200, 146, 42, 0.16), transparent 30%),
        radial-gradient(circle at left top, rgba(216, 178, 107, 0.08), transparent 26%),
        #0d0d0d;
    box-shadow: 0 36px 90px rgba(0, 0, 0, 0.42);
}

.order-success-close {
    position: absolute;
    top: 18px;
    right: 18px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 42px;
    height: 42px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.03);
    color: #f5f0e8;
    cursor: pointer;
}

.order-success-badge {
    color: rgba(216, 178, 107, 0.88);
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}

.order-success-shell h3 {
    margin: 0;
    color: #f5f0e8;
    font-family: "Playfair Display", Georgia, serif;
    font-size: clamp(2rem, 5vw, 3.1rem);
    font-weight: 600;
    line-height: 0.96;
    letter-spacing: -0.04em;
}

.order-success-shell p {
    margin: 0;
    color: rgba(245, 240, 232, 0.72);
    font-size: 1rem;
    line-height: 1.7;
}

.order-success-actions {
    display: flex;
    justify-content: flex-start;
}

.order-success-button.button-shiny {
    --button-shiny-bg: rgba(12, 10, 8, 0.92);
    --button-shiny-bg-soft: rgba(31, 23, 16, 0.92);
    --button-shiny-fg: #d8b26b;
    --button-shiny-highlight: #e5c98d;
    --button-shiny-highlight-soft: #fff8e6;
    --button-shiny-shadow: rgba(216, 178, 107, 0.18);
    min-height: 56px;
    padding: 0 24px;
    border-radius: 18px;
    font-size: 0.92rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    text-transform: none;
}

.checkout-submit {
    min-height: 58px;
    padding: 0 24px;
    border: 0;
    border-radius: 18px;
    background: linear-gradient(135deg, var(--orange), #f38a3d);
    color: #ffffff;
    font: inherit;
    font-size: 0.9rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    cursor: pointer;
    box-shadow: 0 20px 40px rgba(232, 84, 36, 0.26);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.checkout-submit:hover {
    transform: translateY(-2px);
    box-shadow: 0 24px 44px rgba(232, 84, 36, 0.32);
}

.admin-modal.is-open {
    opacity: 1;
    pointer-events: auto;
    transform: translate(-50%, -50%);
}

.admin-modal-head {
    display: flex;
    align-items: start;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 20px;
}

.admin-modal-head h3 {
    margin: 6px 0 0;
    font-family: "Space Grotesk", "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 2rem;
    line-height: 0.96;
    text-transform: uppercase;
}

.admin-close {
    width: 42px;
    height: 42px;
    border: 0;
    border-radius: 12px;
    background: #f3eee7;
    color: var(--text);
    font-size: 1.2rem;
    cursor: pointer;
}

.admin-form {
    display: grid;
    gap: 16px;
}

.admin-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}

.admin-field {
    display: grid;
    gap: 8px;
}

.admin-field span {
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-family: "JetBrains Mono", monospace;
}

.admin-field input,
.admin-field select,
.admin-field textarea {
    width: 100%;
    padding: 14px 16px;
    border: 1px solid rgba(15, 15, 15, 0.12);
    border-radius: 14px;
    background: #fbf8f2;
    color: var(--text);
    font: inherit;
}

.admin-field input[type="file"] {
    padding: 10px;
    cursor: pointer;
}

.admin-field input[type="file"]::file-selector-button {
    min-height: 42px;
    margin-right: 14px;
    padding: 0 18px;
    border: 0;
    border-radius: 8px;
    background: var(--green);
    color: #ffffff;
    font: inherit;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    cursor: pointer;
    transition: background 0.2s ease, transform 0.2s ease;
}

.admin-field input[type="file"]:hover::file-selector-button {
    background: var(--orange);
    transform: translateY(-1px);
}

.admin-field textarea {
    resize: vertical;
    min-height: 140px;
}

.category-admin-list {
    display: grid;
    gap: 12px;
}

.category-admin-row {
    display: grid;
    grid-template-columns: minmax(0, 180px) minmax(0, 1fr) auto;
    gap: 12px;
    align-items: center;
}

.category-admin-input {
    width: 100%;
    padding: 14px 16px;
    border: 1px solid rgba(15, 15, 15, 0.12);
    border-radius: 14px;
    background: #ffffff;
    color: var(--text);
}

.category-admin-remove {
    flex: 0 0 auto;
}

.admin-checkbox {
    grid-template-columns: 1fr auto;
    align-items: center;
    min-height: 54px;
    padding: 0 16px;
    border: 1px solid rgba(15, 15, 15, 0.12);
    border-radius: 14px;
    background: #fbf8f2;
}

.admin-checkbox input {
    width: 20px;
    height: 20px;
    margin: 0;
}

.admin-actions {
    display: flex;
    justify-content: space-between;
    gap: 12px;
}

.admin-actions-end {
    justify-content: flex-end;
}

.admin-save {
    min-height: 48px;
    padding: 0 22px;
    border: 0;
    border-radius: 14px;
    background: var(--orange);
    color: #ffffff;
    font: inherit;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    cursor: pointer;
    transition: transform 0.2s ease, background 0.2s ease;
}

.admin-save:hover {
    background: var(--green);
    transform: translateY(-2px);
}

.admin-save:disabled {
    opacity: 0.6;
    cursor: wait;
    transform: none;
}

.admin-delete {
    min-height: 48px;
    padding: 0 22px;
    border: 1px solid rgba(15, 15, 15, 0.12);
    border-radius: 14px;
    background: #fff3ef;
    color: #9f2d0f;
    font: inherit;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    cursor: pointer;
    transition: transform 0.2s ease, background 0.2s ease, color 0.2s ease;
}

.admin-delete:hover {
    background: #d9411b;
    color: #ffffff;
    transform: translateY(-2px);
}

.admin-delete.is-hidden {
    visibility: hidden;
    pointer-events: none;
}

.cart-drawer {
    background: var(--green);
    box-shadow: -24px 0 48px rgba(15, 15, 15, 0.18);
}

.filters {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 12px;
    margin-bottom: 34px;
}

.filter-chip {
    position: relative;
    overflow: hidden;
    min-height: 46px;
    padding: 0 20px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.03);
    color: rgba(245, 240, 232, 0.84);
    font: inherit;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 0.88rem;
    font-weight: 500;
    letter-spacing: 0.01em;
    text-transform: none;
    cursor: pointer;
    transition:
        border-color 0.24s ease,
        background 0.24s ease,
        color 0.24s ease,
        transform 0.24s ease;
    z-index: 0;
}

.filter-chip::before,
.filter-chip::after {
    content: "";
    position: absolute;
    left: 0;
    width: 100%;
    pointer-events: none;
    transition: all 0.3s ease;
}

.filter-chip::before {
    inset: 0;
    border-top: 0;
    border-bottom: 0;
    transform: scaleY(1.8);
    opacity: 0;
}

.filter-chip::after {
    top: 2px;
    bottom: 2px;
    background: linear-gradient(180deg, #d8b26b, #b88b3c);
    transform: scale(0);
    opacity: 0;
    transform-origin: top;
    z-index: -1;
}

.filter-chip:hover,
.filter-chip:focus-visible {
    border-color: rgba(216, 178, 107, 0.85);
    color: #16120d;
    transform: none;
}

.filter-chip:hover::before,
.filter-chip:focus-visible::before {
    transform: scaleY(1);
    opacity: 1;
}

.filter-chip:hover::after,
.filter-chip:focus-visible::after {
    transform: scale(1);
    opacity: 1;
}

.filter-chip.active {
    background: #c8922a;
    border-color: #c8922a;
    color: #0d0d0d;
}

.filter-chip.active::before,
.filter-chip.active::after {
    opacity: 0;
}

.menu-grid,
.steps-grid,
.reviews-grid {
    display: grid;
    gap: 18px;
}

.menu-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
}

.dish-card {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    padding: 0;
    background: #1a0f0a;
    border-color: rgba(255, 255, 255, 0.05);
    border-radius: 24px;
    transition:
        transform 0.32s ease,
        box-shadow 0.32s ease,
        border-color 0.32s ease;
}

.dish-card:hover {
    transform: translateY(-6px);
    border-color: rgba(200, 146, 42, 0.4);
    box-shadow: 0 0 30px rgba(200, 146, 42, 0.1);
}

.dish-card.is-hidden {
    display: none;
}

.dish-visual {
    position: relative;
    min-height: 240px;
    margin-bottom: 0;
    overflow: hidden;
    border-radius: 0;
    background:
        radial-gradient(circle at 50% 18%, rgba(200, 146, 42, 0.12), transparent 30%),
        linear-gradient(180deg, rgba(0, 0, 0, 0.18), rgba(0, 0, 0, 0.34)),
        linear-gradient(180deg, #24150f, #130b07);
}

.dish-visual::after {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(0, 0, 0, 0.14), rgba(0, 0, 0, 0.36));
    pointer-events: none;
}

.dish-image {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 0;
    transform: scale(1);
    transition: transform 0.7s ease;
}

.dish-card:hover .dish-image {
    transform: scale(1.1);
}

.dish-image.is-hidden,
.dish-plate.is-hidden {
    display: none;
}

.dish-badge {
    position: absolute;
    top: 14px;
    left: 14px;
    z-index: 1;
    padding: 8px 12px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.92);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-family: "JetBrains Mono", monospace;
}

.dish-plate {
    position: absolute;
    inset: 0;
    width: 182px;
    height: 182px;
    margin: auto;
    border-radius: 50%;
    background:
        radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.08) 0 20%, transparent 21%),
        radial-gradient(circle at 50% 50%, #f1dbc0 22%, #deb983 54%, #b06f42 100%);
    box-shadow:
        inset 0 10px 20px rgba(255, 255, 255, 0.24),
        inset 0 -14px 20px rgba(0, 0, 0, 0.16),
        0 22px 30px rgba(0, 0, 0, 0.14);
}

.dish-center {
    position: absolute;
    inset: 22%;
    border-radius: 50%;
    background:
        radial-gradient(circle at 45% 35%, color-mix(in srgb, var(--card-accent) 65%, #ffd462), color-mix(in srgb, var(--card-accent) 70%, #db5f28) 42%, #6c2810 100%);
}

.dish-body h3 {
    margin: 0 0 10px;
    font-family: "Playfair Display", Georgia, serif;
    font-size: 1.42rem;
    line-height: 1.05;
    color: #c8922a;
    text-transform: none;
    letter-spacing: -0.02em;
}

.dish-body p {
    margin: 0;
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.84rem;
    line-height: 1.65;
}

.dish-admin-row {
    display: flex;
    align-items: start;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 10px;
}

.dish-admin-row .dish-title {
    margin-bottom: 0;
}

.dish-edit-button {
    flex: 0 0 auto;
    min-height: 34px;
    padding: 0 12px;
    border: 1px solid rgba(15, 15, 15, 0.12);
    border-radius: 10px;
    background: #f4efe8;
    color: var(--text);
    font: inherit;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    cursor: pointer;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s ease, background 0.2s ease, color 0.2s ease;
}

body.admin-mode .dish-edit-button {
    opacity: 1;
    pointer-events: auto;
}

.dish-edit-button:hover {
    background: var(--orange);
    color: #ffffff;
}

.dish-body {
    padding: 24px 24px 0;
}

.dish-footer,
.order-summary,
.order-line,
.contact-line {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.dish-footer {
    align-items: end;
    padding: 22px 24px 24px;
    margin-top: auto;
}

.dish-price {
    color: #c8922a;
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.01em;
}

.dish-actions {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
}

.qty-picker {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    min-height: 44px;
    padding: 0 10px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.03);
}

.qty-picker-ghost {
    width: fit-content;
    border-color: rgba(255, 255, 255, 0.12);
    background: rgba(255, 255, 255, 0.06);
}

.qty-picker-ghost .qty-button {
    background: rgba(255, 255, 255, 0.12);
    color: #ffffff;
}

.qty-picker-ghost .qty-value {
    color: #ffffff;
}

.qty-button {
    width: 26px;
    height: 26px;
    border: 0;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.08);
    color: #ffffff;
    font: inherit;
    font-weight: 700;
    cursor: pointer;
}

.qty-value {
    min-width: 18px;
    text-align: center;
    font-size: 0.86rem;
    font-weight: 700;
    color: #ffffff;
}

.add-button,
.checkout-button {
    border: 0;
    cursor: pointer;
}

.add-button {
    position: relative;
    overflow: hidden;
    min-height: 44px;
    padding: 0 16px;
    border-radius: 12px;
    flex: 1 1 auto;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: transparent;
    color: #ffffff;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    text-transform: none;
    transition:
        background 0.3s ease,
        color 0.3s ease,
        border-color 0.3s ease,
        transform 0.24s ease;
    z-index: 0;
}

.add-button::before,
.add-button::after {
    content: "";
    position: absolute;
    left: 0;
    width: 100%;
    pointer-events: none;
    transition: all 0.3s ease;
}

.add-button::before {
    inset: 0;
    border-top: 0;
    border-bottom: 0;
    transform: scaleY(1.8);
    opacity: 0;
}

.add-button::after {
    top: 2px;
    bottom: 2px;
    background: linear-gradient(180deg, #d8b26b, #b88b3c);
    transform: scale(0);
    opacity: 0;
    transform-origin: top;
    z-index: -1;
}

.add-button:hover,
.add-button:focus-visible {
    color: #0d0d0d;
    border-color: rgba(216, 178, 107, 0.9);
}

.add-button:hover::before,
.add-button:focus-visible::before {
    transform: scaleY(1);
    opacity: 1;
}

.add-button:hover::after,
.add-button:focus-visible::after {
    transform: scale(1);
    opacity: 1;
}

.cart-drawer .section-kicker,
.order-note,
.order-summary span,
.order-empty p,
.order-line small {
    font-family: "JetBrains Mono", monospace;
    color: rgba(255, 255, 255, 0.72);
}

.cart-drawer h3 {
    margin: 0 0 10px;
    font-size: 2rem;
    color: #ffffff;
}

.order-note {
    margin: 0 0 18px;
}

.order-items {
    display: grid;
    gap: 12px;
    margin: 18px 0 20px;
    min-width: 0;
    overflow: visible;
}

.order-empty,
.order-line {
    min-width: 0;
    padding: 16px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.06);
}

.order-empty strong {
    display: block;
}

.order-empty strong,
.order-line strong,
.order-summary strong {
    color: #ffffff;
}

.order-line {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    align-items: start;
    gap: 14px;
}

.order-line-copy {
    width: 100%;
    min-width: 0;
    display: grid;
    gap: 6px;
}

.order-line-title,
.order-line-total {
    display: block;
    line-height: 1.24;
}

.order-line-title {
    white-space: normal;
    overflow-wrap: break-word;
    word-break: normal;
}

.order-empty p,
.order-line small {
    display: block;
    margin: 8px 0 0;
    line-height: 1.55;
    white-space: normal;
    overflow-wrap: break-word;
    word-break: normal;
}

.order-line-meta {
    margin: 0;
}

.order-line-actions {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    align-items: center;
    width: 100%;
    align-self: stretch;
    gap: 10px;
}

.order-line-total {
    min-width: 0;
    white-space: nowrap;
    text-align: right;
    justify-self: end;
}

.order-remove-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border: 0;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.14);
    color: #ffffff;
    cursor: pointer;
    transition: background 0.2s ease, transform 0.2s ease;
}

.order-remove-button:hover {
    background: rgba(232, 84, 36, 0.92);
    transform: translateY(-1px);
}

.order-summary {
    display: grid;
    grid-template-columns: 1fr;
    align-items: stretch;
    gap: 14px;
    padding: 18px 0;
    margin-bottom: 18px;
    border-top: 1px solid rgba(255, 255, 255, 0.14);
    border-bottom: 1px solid rgba(255, 255, 255, 0.14);
}

.order-summary > div {
    display: grid;
    gap: 8px;
}

.order-summary span {
    display: block;
    margin-bottom: 0;
}

.checkout-button {
    width: 100%;
    min-height: 54px;
    flex: 0 0 auto;
    margin-top: auto;
    border-radius: 14px;
    background: var(--yellow);
    color: var(--text);
    font-size: 0.84rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.checkout-button:disabled {
    background: rgba(245, 211, 94, 0.45);
    color: rgba(15, 15, 15, 0.52);
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
}

.cart-drawer {
    border-left: 1px solid rgba(255, 255, 255, 0.06);
    background:
        radial-gradient(circle at top right, rgba(200, 146, 42, 0.14), transparent 30%),
        radial-gradient(circle at left top, rgba(216, 178, 107, 0.08), transparent 26%),
        #0d0d0d;
    box-shadow: -32px 0 80px rgba(0, 0, 0, 0.42);
}

.cart-drawer .section-kicker {
    margin: 0 0 10px;
    color: rgba(255, 255, 255, 0.4);
    font-size: 0.78rem;
    font-weight: 500;
    line-height: 1;
    letter-spacing: 0.04em;
    text-transform: none;
}

.cart-drawer h3 {
    margin: 0 0 18px;
    font-family: "Playfair Display", Georgia, serif;
    font-size: clamp(2rem, 5vw, 2.8rem);
    font-weight: 600;
    line-height: 0.98;
    letter-spacing: -0.04em;
    text-transform: none;
    color: #f5f0e8;
}

.cart-checkout-mode {
    gap: 12px;
    margin-bottom: 18px;
}

.cart-checkout-mode-label {
    color: rgba(255, 255, 255, 0.4);
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: none;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
}

.cart-drawer .checkout-switcher {
    padding: 6px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.03);
}

.cart-drawer .checkout-switch {
    min-height: 48px;
    border-radius: 14px;
    color: rgba(245, 240, 232, 0.62);
    letter-spacing: 0.03em;
}

.cart-drawer .checkout-switch.is-active {
    background: linear-gradient(180deg, rgba(248, 241, 228, 0.96), rgba(236, 226, 208, 0.92));
    color: #16120d;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.18);
}

.cart-drawer .checkout-switch:not(.is-active):hover {
    background: rgba(255, 255, 255, 0.04);
    color: #f8f1e4;
}

.cart-checkout-note {
    color: rgba(245, 240, 232, 0.62);
    font-size: 0.92rem;
    line-height: 1.6;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
}

.order-empty,
.order-line {
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.03);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02);
}

.order-empty strong,
.order-line strong,
.order-summary strong {
    color: #f5f0e8;
}

.order-summary {
    gap: 16px;
    padding: 20px 0;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.order-summary > div {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    min-width: 0;
    gap: 8px;
    padding: 16px 18px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.03);
}

.order-summary span {
    color: rgba(255, 255, 255, 0.42);
    font-size: 0.76rem;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: none;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
}

.qty-picker-ghost {
    border-color: rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.02);
}

.qty-picker-ghost .qty-button {
    background: rgba(255, 255, 255, 0.08);
    color: #f5f0e8;
}

.qty-picker-ghost .qty-button:hover {
    background: #c8922a;
    color: #0d0d0d;
}

.qty-picker-ghost .qty-value {
    color: #f5f0e8;
}

.order-remove-button {
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.08);
}

.checkout-button {
    min-height: 56px;
    border-radius: 18px;
    background: linear-gradient(90deg, #c8922a, #a0721c);
    color: #0d0d0d;
    font-size: 0.92rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    text-transform: none;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.28);
}

.account-modal-shell,
.checkout-modal-shell {
    position: relative;
    border: 1px solid rgba(255, 255, 255, 0.06);
    background:
        radial-gradient(circle at top right, rgba(200, 146, 42, 0.14), transparent 30%),
        radial-gradient(circle at left top, rgba(216, 178, 107, 0.08), transparent 24%),
        #0d0d0d;
    box-shadow: 0 36px 90px rgba(0, 0, 0, 0.42);
}

.checkout-modal-shell {
    overflow: hidden;
    overscroll-behavior: contain;
    touch-action: pan-y;
}

.account-modal-shell {
    overflow-x: hidden;
    overflow-y: auto;
    overscroll-behavior: contain;
    -webkit-overflow-scrolling: touch;
}

.account-modal-shell::before,
.checkout-modal-shell::before {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent 24%);
    pointer-events: none;
}

.checkout-modal-head,
.account-modal-head {
    position: relative;
    z-index: 1;
}

.checkout-modal-head .section-kicker,
.account-modal-head .section-kicker,
.checkout-label,
.account-summary-label {
    margin: 0;
    color: rgba(255, 255, 255, 0.4);
    font-size: 0.78rem;
    font-weight: 500;
    line-height: 1;
    letter-spacing: 0.04em;
    text-transform: none;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
}

.checkout-modal-head h3,
.account-modal-head h2 {
    margin: 6px 0 0;
    font-family: "Playfair Display", Georgia, serif;
    font-size: clamp(2rem, 5vw, 3rem);
    font-weight: 600;
    line-height: 0.98;
    letter-spacing: -0.04em;
    text-transform: none;
    color: #f5f0e8;
}

.checkout-modal-form-wrap {
    position: relative;
    z-index: 1;
    background: transparent;
    padding: 30px 32px 34px;
    overflow-y: auto;
    overscroll-behavior-y: contain;
    overscroll-behavior-x: none;
    -webkit-overflow-scrolling: touch;
    touch-action: pan-y;
}

.checkout-modal-form-wrap,
.checkout-modal-form-wrap * {
    -webkit-tap-highlight-color: transparent;
}

.checkout-modal-form-wrap > *,
.checkout-form,
.checkout-form > *,
.checkout-order-list,
.checkout-order-list > *,
.checkout-bonus-box,
.checkout-preview,
.checkout-consents,
.checkout-actions {
    min-width: 0;
    touch-action: pan-y;
}

.checkout-form {
    gap: 22px;
}

.checkout-preview > div,
.checkout-bonus-box,
.account-summary-card,
.account-orders,
.account-current-order,
.account-profile-card,
.account-order-card,
.account-order-card-current,
.order-admin-meta-card {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.03);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02);
}

.checkout-preview span,
.checkout-bonus-copy p,
.checkout-consent span,
.account-summary-card p,
.account-order-empty,
.account-order-meta,
.account-order-items,
.order-admin-hint,
.order-admin-items,
.order-admin-meta-card span {
    color: rgba(245, 240, 232, 0.62);
}

.checkout-preview strong,
.account-summary-card strong,
.account-orders-head h3,
.account-order-card strong,
.order-admin-meta-card strong {
    color: #f5f0e8;
}

.checkout-bonus-stepper {
    border-color: rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.03);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02);
}

.checkout-bonus-button {
    color: #f5f0e8;
}

.checkout-bonus-button:hover {
    background: rgba(216, 178, 107, 0.16);
    color: #d8b26b;
}

.checkout-bonus-stepper input[type="number"] {
    color: #f5f0e8;
}

.checkout-switcher {
    padding: 6px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.03);
}

.checkout-switch {
    min-height: 48px;
    border-radius: 14px;
    color: rgba(245, 240, 232, 0.62);
    letter-spacing: 0.03em;
}

.checkout-switch.is-active {
    background: linear-gradient(180deg, rgba(248, 241, 228, 0.96), rgba(236, 226, 208, 0.92));
    color: #16120d;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.18);
}

.checkout-switch:not(.is-active):hover {
    background: rgba(255, 255, 255, 0.04);
    color: #f8f1e4;
}

.checkout-field {
    position: relative;
    gap: 0;
}

.checkout-field-floating > span {
    position: absolute;
    left: 0;
    top: 18px;
    color: rgba(255, 255, 255, 0.4);
    font-size: 0.78rem;
    line-height: 1;
    letter-spacing: 0.04em;
    pointer-events: none;
    transition: top 0.2s ease, font-size 0.2s ease, color 0.2s ease;
}

.checkout-field input {
    min-height: 54px;
    padding: 18px 0 10px;
    border: 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 0;
    background: transparent;
    color: #f5f0e8;
    font: inherit;
    transition: border-color 0.24s ease, color 0.24s ease;
}

.checkout-field-floating input::placeholder {
    color: transparent;
}

.checkout-field-floating input:focus + span,
.checkout-field-floating input:not(:placeholder-shown) + span {
    top: -2px;
    font-size: 0.64rem;
    color: #c8922a;
}

.checkout-field input:focus {
    border-color: #c8922a;
    box-shadow: none;
}

.checkout-consents {
    gap: 12px;
}

.checkout-consent {
    padding: 14px 16px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.03);
}

.checkout-consent input {
    accent-color: #c8922a;
}

.checkout-consent a {
    color: #d8b26b;
}

.checkout-submit,
.account-modal .auth-submit,
.account-refresh {
    min-height: 56px;
    border: 0;
    border-radius: 18px;
    background: linear-gradient(90deg, #c8922a, #a0721c);
    color: #0d0d0d;
    font-size: 0.92rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    text-transform: none;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.28);
}

.checkout-submit:hover,
.account-modal .auth-submit:hover,
.account-refresh:hover {
    opacity: 0.92;
    transform: translateY(-1px);
}

.account-modal-shell {
    border-left: 1px solid rgba(255, 255, 255, 0.06);
    background:
        radial-gradient(circle at top right, rgba(200, 146, 42, 0.14), transparent 30%),
        radial-gradient(circle at left top, rgba(216, 178, 107, 0.08), transparent 24%),
        #0d0d0d;
}

.account-modal-head {
    margin-bottom: 18px;
    padding-right: 56px;
}

.account-modal-close {
    width: 42px;
    height: 42px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.04);
    color: rgba(245, 240, 232, 0.88);
}

.account-modal-close:hover {
    background: rgba(200, 146, 42, 0.12);
    border-color: rgba(200, 146, 42, 0.32);
    color: #f8f1e4;
}

.account-grid {
    gap: 14px;
    margin-bottom: 14px;
}

.account-summary-card {
    gap: 8px;
    padding: 18px;
}

.account-summary-card strong {
    font-family: "Playfair Display", Georgia, serif;
    font-size: clamp(1.9rem, 5vw, 2.5rem);
    font-weight: 600;
    line-height: 0.95;
}

.account-orders,
.account-current-order,
.account-profile-card {
    padding: 18px;
}

.account-orders-head h3 {
    font-family: "Playfair Display", Georgia, serif;
    font-size: 1.55rem;
    font-weight: 600;
    color: #f5f0e8;
}

.account-modal .auth-field input {
    min-height: 54px;
    padding: 18px 0 10px;
    border: 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 0;
    background: transparent;
    color: #f5f0e8;
}

.account-modal .auth-field input:focus {
    border-color: #c8922a;
}

.account-phone-hint {
    color: #c8922a;
}

#checkout-modal .admin-close,
.account-modal-close,
.cart-close {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 42px;
    height: 42px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.04);
    color: rgba(245, 240, 232, 0.88);
    font: inherit;
    font-size: 1rem;
    cursor: pointer;
    transition: border-color 0.24s ease, color 0.24s ease, background 0.24s ease, transform 0.24s ease;
}

#checkout-modal .admin-close:hover,
.account-modal-close:hover,
.cart-close:hover {
    background: rgba(200, 146, 42, 0.12);
    border-color: rgba(200, 146, 42, 0.32);
    color: #f8f1e4;
    transform: translateY(-1px);
}

#checkout-modal .checkout-consents {
    display: grid;
    gap: 12px;
    padding: 0;
    border: 0;
    border-radius: 0;
    background: transparent;
}

#checkout-modal .checkout-consent {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 16px 18px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.03);
    color: rgba(245, 240, 232, 0.68);
    font-size: 0.9rem;
    line-height: 1.45;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02);
}

#checkout-modal .checkout-consent span {
    color: rgba(245, 240, 232, 0.68);
}

#checkout-modal .checkout-consent input {
    flex: 0 0 auto;
    width: 18px;
    height: 18px;
    margin-top: 1px;
    accent-color: #c8922a;
}

#checkout-modal .checkout-consent a {
    color: #d8b26b;
    font-weight: 700;
    text-decoration: none;
}

#checkout-modal .checkout-consent a:hover {
    color: #f5f0e8;
    text-decoration: none;
}

#checkout-modal .checkout-consents.is-attention {
    padding: 10px;
    border: 1px solid rgba(200, 146, 42, 0.5);
    border-radius: 22px;
    background: rgba(200, 146, 42, 0.08);
    box-shadow: 0 0 0 3px rgba(200, 146, 42, 0.1);
}

#checkout-modal .checkout-payment {
    gap: 12px;
}

#checkout-modal .checkout-switcher {
    padding: 6px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.03);
}

#checkout-modal .checkout-switch {
    min-height: 48px;
    color: rgba(245, 240, 232, 0.62);
    background: transparent;
    box-shadow: none;
}

#checkout-modal .checkout-switch.is-active {
    background: linear-gradient(180deg, rgba(248, 241, 228, 0.96), rgba(236, 226, 208, 0.92));
    color: #16120d;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.18);
}

#checkout-modal .checkout-switch:not(.is-active):hover {
    background: rgba(255, 255, 255, 0.04);
    color: #f8f1e4;
}

.checkout-consent-popup,
.cart-toast {
    border: 1px solid rgba(216, 178, 107, 0.16);
    background:
        radial-gradient(circle at top right, rgba(216, 178, 107, 0.14), transparent 34%),
        #0d0d0d;
    color: #f5f0e8;
    box-shadow: 0 18px 42px rgba(0, 0, 0, 0.36);
}

.checkout-warning-popup {
    border-color: rgba(200, 146, 42, 0.28);
    background:
        radial-gradient(circle at top right, rgba(200, 146, 42, 0.18), transparent 34%),
        #120d09;
    color: #f5f0e8;
}

#catalog-search-results .order-line,
#orders-admin-results .order-line,
.account-orders-list .order-line,
.account-order-empty {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.03);
    color: rgba(245, 240, 232, 0.68);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02);
}

#account-current-order-card > .account-order-empty,
#account-orders-list > .account-order-empty {
    padding: 0;
    border: 0;
    border-radius: 0;
    background: transparent;
    box-shadow: none;
}

#catalog-search-results .order-line strong,
#orders-admin-results .order-line strong,
.account-orders-list .order-line strong {
    color: #f5f0e8;
}

#catalog-search-results .order-line small,
#orders-admin-results .order-line small,
.account-orders-list .order-line small {
    color: rgba(245, 240, 232, 0.58);
}

.account-order-status {
    background: rgba(200, 146, 42, 0.12);
    color: #d8b26b;
}

/* Admin theme refresh */
.menu-admin-bar {
    align-items: center;
    gap: 12px;
}

.menu-admin-bar .admin-toggle {
    min-height: 46px;
    padding: 0 18px;
    border: 1px solid rgba(216, 178, 107, 0.18);
    border-radius: 999px;
    background:
        radial-gradient(circle at top right, rgba(216, 178, 107, 0.1), transparent 34%),
        linear-gradient(180deg, rgba(16, 13, 10, 0.94), rgba(11, 9, 7, 0.98));
    color: rgba(245, 240, 232, 0.92);
    box-shadow:
        inset 0 0 0 1px rgba(255, 255, 255, 0.03),
        0 16px 32px rgba(0, 0, 0, 0.22);
}

.menu-admin-bar .admin-toggle:hover,
.menu-admin-bar .admin-toggle.is-active {
    border-color: rgba(216, 178, 107, 0.32);
    background:
        radial-gradient(circle at top right, rgba(216, 178, 107, 0.16), transparent 34%),
        linear-gradient(180deg, rgba(20, 16, 12, 0.96), rgba(12, 10, 8, 0.98));
    color: #f8f1e4;
}

.menu-admin-bar .admin-toggle-accent,
.menu-admin-bar .admin-toggle-accent:hover {
    color: #d8b26b;
}

.admin-modal {
    position: fixed;
    border-color: rgba(216, 178, 107, 0.14);
    background:
        radial-gradient(circle at top right, rgba(216, 178, 107, 0.12), transparent 28%),
        radial-gradient(circle at left top, rgba(255, 255, 255, 0.04), transparent 24%),
        linear-gradient(180deg, #15110f 0%, #0d0d0d 100%);
    color: #f5f0e8;
    box-shadow:
        0 36px 90px rgba(0, 0, 0, 0.42),
        inset 0 1px 0 rgba(255, 255, 255, 0.02);
    scrollbar-color: rgba(216, 178, 107, 0.48) rgba(255, 255, 255, 0.04);
}

.admin-modal .section-kicker {
    margin: 0 0 10px;
    color: rgba(216, 178, 107, 0.72);
}

.admin-modal-head {
    margin-bottom: 22px;
}

.admin-modal-head h3 {
    color: #f5f0e8;
    font-family: "Playfair Display", Georgia, serif;
    font-size: clamp(2rem, 4vw, 2.6rem);
    font-weight: 500;
    line-height: 0.98;
    letter-spacing: -0.04em;
    text-transform: none;
}

.admin-close {
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.04);
    color: rgba(245, 240, 232, 0.88);
    transition: border-color 0.24s ease, color 0.24s ease, background 0.24s ease, transform 0.24s ease;
}

.admin-close:hover {
    background: rgba(200, 146, 42, 0.12);
    border-color: rgba(200, 146, 42, 0.32);
    color: #f8f1e4;
    transform: translateY(-1px);
}

.admin-form {
    gap: 18px;
}

.admin-field span {
    color: rgba(216, 178, 107, 0.72);
    font-size: 0.74rem;
}

.admin-field input,
.admin-field select,
.admin-field textarea,
.category-admin-input {
    border-color: rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.03);
    color: #f5f0e8;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02);
}

.admin-field input::placeholder,
.admin-field textarea::placeholder,
.category-admin-input::placeholder {
    color: rgba(245, 240, 232, 0.34);
}

.admin-field input:focus,
.admin-field select:focus,
.admin-field textarea:focus,
.category-admin-input:focus {
    outline: none;
    border-color: rgba(216, 178, 107, 0.38);
    box-shadow: 0 0 0 4px rgba(216, 178, 107, 0.12);
}

.admin-field select {
    color-scheme: dark;
}

.admin-field input[type="file"]::file-selector-button {
    border-radius: 999px;
    background: linear-gradient(180deg, rgba(248, 241, 228, 0.96), rgba(236, 226, 208, 0.92));
    color: #16120d;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.18);
}

.admin-field input[type="file"]:hover::file-selector-button {
    background: linear-gradient(180deg, #f8f1e4, #e6d8c0);
}

.category-admin-row,
.admin-checkbox {
    border-color: rgba(255, 255, 255, 0.08);
}

.admin-checkbox {
    background: rgba(255, 255, 255, 0.03);
}

.admin-checkbox input {
    accent-color: #d8b26b;
}

.admin-actions {
    align-items: center;
    flex-wrap: wrap;
}

.admin-modal .topbar-action,
.admin-save,
.admin-delete {
    min-height: 50px;
    padding: 0 22px;
    border-radius: 999px;
    font-size: 0.8rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.admin-modal .topbar-action {
    border-color: rgba(216, 178, 107, 0.24);
    color: rgba(245, 240, 232, 0.88);
}

.admin-modal .topbar-action:hover,
.admin-modal .topbar-action:focus-visible {
    border-color: rgba(216, 178, 107, 0.4);
    background: rgba(216, 178, 107, 0.12);
    color: #f8f1e4;
}

.admin-save {
    background: linear-gradient(180deg, rgba(248, 241, 228, 0.96), rgba(236, 226, 208, 0.92));
    color: #16120d;
    box-shadow: 0 14px 26px rgba(0, 0, 0, 0.22);
}

.admin-save:hover {
    background: linear-gradient(180deg, #f8f1e4, #e6d8c0);
    color: #16120d;
    transform: translateY(-2px);
}

.admin-save:disabled {
    background: rgba(245, 240, 232, 0.26);
    color: rgba(245, 240, 232, 0.46);
}

.admin-delete {
    border-color: rgba(232, 84, 36, 0.24);
    background: rgba(232, 84, 36, 0.08);
    color: #ffb09a;
}

.admin-delete:hover {
    background: #d9411b;
    color: #ffffff;
}

#catalog-search-results,
#orders-admin-results {
    display: grid;
    gap: 14px;
}

#catalog-search-results .order-line,
#orders-admin-results .order-line,
.account-orders-list .order-line,
.account-order-empty {
    border-radius: 20px;
    background:
        radial-gradient(circle at top right, rgba(216, 178, 107, 0.1), transparent 24%),
        rgba(255, 255, 255, 0.03);
}

#catalog-search-results .order-line {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 18px;
}

#catalog-search-results .order-line > div {
    display: grid;
    gap: 6px;
}

#catalog-search-results .order-line small {
    font-family: "JetBrains Mono", monospace;
}

.admin-search-result-label {
    color: rgba(216, 178, 107, 0.72);
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
}

.admin-search-result-action {
    flex: 0 0 auto;
}

.order-admin-meta-card {
    border-color: rgba(255, 255, 255, 0.08);
    background:
        radial-gradient(circle at top right, rgba(216, 178, 107, 0.1), transparent 26%),
        rgba(255, 255, 255, 0.03);
}

.order-admin-meta-card span,
.order-admin-items,
.order-admin-hint {
    color: rgba(245, 240, 232, 0.62);
}

.order-admin-meta-card strong {
    color: #f5f0e8;
}

.order-admin-actions {
    gap: 14px;
}

.account-order-status-preparing {
    background: rgba(200, 146, 42, 0.16);
    color: #f1cf8a;
}

.account-order-status-ready {
    background: rgba(216, 178, 107, 0.14);
    color: #d8b26b;
}

.steps-grid {
    grid-template-columns: none;
}

.delivery-track {
    width: min(1240px, 100%);
    margin: 0 auto;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 24px;
    padding: 0;
}

.step-card {
    min-width: 0;
    height: 100%;
    position: relative;
    padding: 32px;
    background: #1a0f0a;
    color: #ffffff;
    border-color: rgba(255, 255, 255, 0.05);
    border-radius: 24px;
    box-shadow: none;
}

.delivery-card {
    overflow: hidden;
}

.delivery-card-quote {
    position: absolute;
    top: 18px;
    right: 22px;
    color: rgba(255, 255, 255, 0.06);
    font-family: "Playfair Display", Georgia, serif;
    font-size: 4rem;
    line-height: 1;
}

.delivery-card-rating {
    display: inline-flex;
    gap: 4px;
    margin-bottom: 18px;
    color: #c8922a;
    font-size: 0.95rem;
}

.delivery-card-rating span {
    display: inline;
    margin: 0;
    color: inherit;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: inherit;
    line-height: 1;
    text-transform: none;
}

.delivery-card-text {
    margin: 0 0 24px;
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.95rem;
    font-weight: 300;
    line-height: 1.75;
}

.delivery-card-meta {
    display: flex;
    align-items: center;
    gap: 14px;
}

.delivery-card-index {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: rgba(200, 146, 42, 0.12);
    color: #c8922a;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 0.9rem;
    font-weight: 700;
    letter-spacing: 0.08em;
}

.delivery-card-author {
    display: grid;
    gap: 4px;
}

.step-card span {
    color: var(--yellow);
}

.step-card h3 {
    margin: 0;
    color: #ffffff;
    font-size: 0.94rem;
    font-weight: 600;
    letter-spacing: 0.01em;
    line-height: 1.2;
    text-transform: none;
}

.delivery-card-author span {
    display: block;
    margin: 0;
    color: rgba(255, 255, 255, 0.42);
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: none;
}

.delivery-head h2,
.delivery-section .section-head h2 {
    color: #f5f0e8;
}

.step-card p {
    margin: 0;
    color: rgba(255, 255, 255, 0.86);
}

.reviews-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
}

.review-card {
    padding: 24px;
    background: var(--surface);
}

.review-stars {
    margin-bottom: 12px;
    color: var(--orange);
    font-size: 0.88rem;
    letter-spacing: 0.16em;
}

.review-card p {
    margin: 0;
}

.review-card strong {
    display: block;
    margin-top: 18px;
    font-size: 1.2rem;
}

.contact-grid {
    grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
    align-items: start;
    padding-bottom: 64px;
}

.contact-card {
    padding: 28px;
    background: var(--orange);
    color: #ffffff;
    box-shadow: var(--shadow);
}

.contact-card h3 {
    margin: 0 0 18px;
    font-size: 2rem;
    color: #ffffff;
}

.contact-line {
    padding: 16px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.18);
}

.contact-line:last-child {
    border-bottom: 0;
}

.site-footer {
    position: relative;
    border-top: 1px solid rgba(200, 146, 42, 0.2);
    background: #0d0d0d;
}

.site-footer::before {
    top: -40px;
    right: 10%;
    width: 220px;
    height: 220px;
    border-radius: 50%;
    background:
        radial-gradient(circle at 50% 50%, rgba(200, 146, 42, 0.16), rgba(200, 146, 42, 0.03) 52%, transparent 72%);
    filter: blur(10px);
    animation: ambientPulse 16s ease-in-out infinite;
}

.site-footer::after {
    left: -40px;
    bottom: -30px;
    width: 220px;
    height: 220px;
    border-radius: 40% 60% 58% 42% / 44% 42% 58% 56%;
    background:
        radial-gradient(circle at 40% 40%, rgba(200, 146, 42, 0.1), rgba(200, 146, 42, 0.02) 48%, transparent 74%);
    filter: blur(10px);
    animation: ambientFloat 18s ease-in-out infinite;
}

.site-footer-inner {
    display: grid;
    grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.9fr) minmax(0, 0.9fr) minmax(260px, 1fr);
    gap: 40px;
    align-items: start;
    max-width: 1240px;
    margin: 0 auto;
    padding: 64px 24px 48px;
}

.site-footer-logo {
    color: #c8922a;
    text-decoration: none;
    font-family: "Playfair Display", Georgia, serif;
    font-size: 2rem;
    font-weight: 500;
    line-height: 0.95;
    text-transform: none;
    letter-spacing: -0.04em;
}

.site-footer-copy {
    max-width: 34ch;
    margin: 14px 0 0;
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.8rem;
    font-weight: 300;
    line-height: 1.8;
}

.site-footer-social {
    display: flex;
    gap: 12px;
    margin-top: 22px;
}

.site-footer-social-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    padding: 0;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 999px;
    background: transparent;
    color: rgba(255, 255, 255, 0.62);
    text-decoration: none;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 0.72rem;
    font-weight: 500;
    cursor: pointer;
    transition: color 0.24s ease, border-color 0.24s ease, transform 0.24s ease;
}

.site-footer-social-link:hover {
    color: #c8922a;
    border-color: #c8922a;
    transform: translateY(-1px);
}

.site-footer-column {
    display: grid;
    gap: 14px;
}

.site-footer-heading {
    margin: 0;
    color: #c8922a;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 0.92rem;
    font-weight: 500;
}

.site-footer-links {
    display: grid;
    gap: 12px;
}

.site-footer-links a {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: flex-start;
    align-self: flex-start;
    justify-self: start;
    width: fit-content;
    max-width: 100%;
    overflow: hidden;
    padding: 8px 14px;
    border-radius: 14px;
    color: rgba(255, 255, 255, 0.72);
    text-decoration: none;
    font-size: 0.78rem;
    font-weight: 300;
    line-height: 1.5;
    transition: color 0.3s ease;
    z-index: 0;
}

.site-footer-links a::before,
.site-footer-links a::after {
    content: "";
    position: absolute;
    left: 0;
    width: 100%;
    pointer-events: none;
    transition: all 0.3s ease;
}

.site-footer-links a::before {
    inset: 0;
    transform: scaleY(1.9);
    opacity: 0;
}

.site-footer-links a::after {
    top: 2px;
    bottom: 2px;
    border-radius: 12px;
    background: linear-gradient(180deg, #d8b26b, #b88b3c);
    transform: scale(0);
    opacity: 0;
    transform-origin: top;
    z-index: -1;
}

.site-footer-links a:hover,
.site-footer-links a:focus-visible {
    color: #16120d;
}

.site-footer-links a:hover::before,
.site-footer-links a:focus-visible::before {
    transform: scaleY(1);
    opacity: 1;
}

.site-footer-links a:hover::after,
.site-footer-links a:focus-visible::after {
    transform: scale(1);
    opacity: 1;
}

.site-footer-copyright a {
    color: inherit;
    font-weight: 700;
    text-decoration: underline;
    text-underline-offset: 3px;
}

.site-footer-meta {
    display: grid;
    gap: 8px;
    justify-items: start;
    text-align: left;
}

.site-footer-label {
    color: rgba(255, 255, 255, 0.34);
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 0.66rem;
    font-weight: 500;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-top: 6px;
}

.site-footer-meta strong {
    color: #ffffff;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 0.82rem;
    font-weight: 500;
    line-height: 1.55;
}

.site-footer-phone,
.site-footer-map-trigger {
    color: rgba(255, 255, 255, 0.72);
    text-decoration: none;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 0.82rem;
    font-weight: 400;
    line-height: 1.55;
    transition: color 0.2s ease, transform 0.2s ease;
}

.site-footer-map-trigger {
    padding: 0;
    border: 0;
    background: transparent;
    cursor: pointer;
    text-align: right;
}

.site-footer-phone:hover,
.site-footer-map-trigger:hover {
    color: #c8922a;
    transform: translateY(-1px);
}

.site-footer-bottom {
    max-width: 1240px;
    margin: 0 auto;
    padding: 24px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 12px 24px;
}

.site-footer-copyright {
    margin: 0;
    color: rgba(255, 255, 255, 0.4);
    font-size: 0.66rem;
    font-weight: 300;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}

.site-footer-credit {
    padding-top: 0;
}

.legal-page-body {
    min-height: 100vh;
    background:
        radial-gradient(circle at top right, rgba(216, 178, 107, 0.12), transparent 22%),
        radial-gradient(circle at left top, rgba(232, 84, 36, 0.08), transparent 24%),
        linear-gradient(180deg, #090909 0%, #120a07 46%, #0c0c0c 100%);
    color: #f5f0e8;
}

.legal-page-header {
    position: sticky;
    top: 0;
    z-index: 50;
    padding: 16px 20px 0;
    background: linear-gradient(180deg, rgba(9, 9, 9, 0.86), rgba(9, 9, 9, 0));
    backdrop-filter: blur(16px);
}

.legal-page-header-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    width: min(1240px, 100%);
    margin: 0 auto;
    padding: 14px 20px;
    border: 1px solid rgba(216, 178, 107, 0.16);
    border-radius: 999px;
    background: linear-gradient(180deg, rgba(18, 14, 11, 0.9), rgba(12, 10, 8, 0.88));
    box-shadow: 0 18px 44px rgba(0, 0, 0, 0.18);
}

.legal-page-brand,
.legal-page-back {
    text-decoration: none;
}

.legal-page-brand {
    flex: 0 0 auto;
    color: #d8b26b;
    font-family: "Playfair Display", Georgia, serif;
    font-size: 1.6rem;
    font-weight: 500;
    letter-spacing: -0.04em;
    text-transform: none;
}

.legal-page-nav {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1 1 auto;
    gap: 12px;
    min-width: 0;
}

.legal-page-nav a {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    padding: 10px 16px;
    border-radius: 14px;
    color: rgba(245, 240, 232, 0.78);
    text-decoration: none;
    font-size: 0.84rem;
    font-weight: 300;
    letter-spacing: 0.06em;
    transition: color 0.3s ease;
    z-index: 0;
}

.legal-page-nav a::before,
.legal-page-nav a::after {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    transition: all 0.3s ease;
}

.legal-page-nav a::before {
    transform: scaleY(1.9);
    opacity: 0;
}

.legal-page-nav a::after {
    inset: 2px 0;
    border-radius: 12px;
    background: linear-gradient(180deg, #d8b26b, #b88b3c);
    transform: scale(0);
    opacity: 0;
    transform-origin: top;
    z-index: -1;
}

.legal-page-nav a:hover,
.legal-page-nav a:focus-visible {
    color: #16120d;
}

.legal-page-nav a:hover::before,
.legal-page-nav a:focus-visible::before {
    transform: scaleY(1);
    opacity: 1;
}

.legal-page-nav a:hover::after,
.legal-page-nav a:focus-visible::after {
    transform: scale(1);
    opacity: 1;
}

.legal-page-back {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 auto;
}

.legal-page-main {
    padding: 0 0 72px;
}

.legal-page-hero {
    position: relative;
    overflow: hidden;
    padding: 152px 24px 56px;
}

.legal-page-hero::before,
.legal-page-hero::after {
    content: "";
    position: absolute;
    pointer-events: none;
}

.legal-page-hero::before {
    top: 36px;
    right: -140px;
    width: 360px;
    height: 360px;
    border-radius: 50%;
    background: radial-gradient(circle at center, rgba(216, 178, 107, 0.22), transparent 66%);
    filter: blur(10px);
}

.legal-page-hero::after {
    left: -100px;
    bottom: -40px;
    width: 300px;
    height: 300px;
    border-radius: 50%;
    background: radial-gradient(circle at center, rgba(232, 84, 36, 0.16), transparent 70%);
    filter: blur(12px);
}

.legal-page-hero-shell,
.legal-page-shell {
    width: min(1240px, calc(100% - 32px));
    margin: 0 auto;
}

.legal-page-hero-shell {
    display: grid;
    gap: 22px;
}

.legal-page-hero-shell .section-kicker {
    margin-bottom: 0;
    color: rgba(255, 248, 236, 0.74);
}

.legal-page-hero-shell h1 {
    margin: 0;
    max-width: 12ch;
    color: #f5f0e8;
    font-family: "Playfair Display", Georgia, serif;
    font-size: clamp(3.1rem, 7vw, 5.6rem);
    line-height: 0.94;
    font-weight: 500;
    letter-spacing: -0.045em;
}

.legal-page-hero-shell p {
    max-width: 64ch;
    margin: 0;
    color: rgba(245, 240, 232, 0.72);
    font-size: 1rem;
    line-height: 1.8;
}

.legal-page-highlights {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
}

.legal-page-highlight,
.legal-page-aside-card,
.legal-document {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 28px;
    background:
        radial-gradient(circle at top right, rgba(216, 178, 107, 0.12), transparent 26%),
        rgba(255, 255, 255, 0.03);
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.03),
        0 24px 60px rgba(0, 0, 0, 0.2);
}

.legal-page-highlight {
    display: grid;
    gap: 12px;
    padding: 20px 22px;
}

.legal-page-highlight-label,
.legal-page-aside-label,
.legal-document-head span {
    color: rgba(216, 178, 107, 0.72);
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}

.legal-page-highlight strong,
.legal-document-head strong {
    color: #f5f0e8;
    font-size: 1rem;
    font-weight: 500;
    line-height: 1.5;
}

.legal-page-highlight a {
    color: inherit;
    text-decoration: none;
}

.legal-page-grid {
    display: grid;
    grid-template-columns: minmax(260px, 320px) minmax(0, 1fr);
    gap: 22px;
    align-items: start;
}

.legal-page-aside {
    position: sticky;
    top: 112px;
    display: grid;
    gap: 18px;
}

.legal-page-aside-card {
    display: grid;
    gap: 12px;
    padding: 22px;
}

.legal-page-aside-card strong {
    color: #f5f0e8;
    font-size: 1rem;
    font-weight: 500;
    line-height: 1.45;
}

.legal-page-aside-card p {
    margin: 0;
    color: rgba(245, 240, 232, 0.62);
    font-size: 0.92rem;
    line-height: 1.7;
}

.legal-page-aside-links {
    display: grid;
    gap: 10px;
}

.legal-page-aside-links a,
.legal-page-map-trigger,
.legal-page-phone {
    color: rgba(245, 240, 232, 0.86);
    text-decoration: none;
    font-size: 0.9rem;
    line-height: 1.6;
    transition: color 0.24s ease, transform 0.24s ease;
}

.legal-page-aside-links a:hover,
.legal-page-map-trigger:hover,
.legal-page-phone:hover {
    color: #d8b26b;
    transform: translateY(-1px);
}

.legal-document {
    padding: 28px;
}

.legal-document-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding-bottom: 18px;
    margin-bottom: 18px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.legal-document-text {
    margin: 0;
    white-space: pre-wrap;
    word-break: break-word;
    color: rgba(245, 240, 232, 0.88);
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 0.98rem;
    line-height: 1.75;
}

.footer-map-modal {
    width: min(980px, calc(100% - 24px));
}

.footer-map-modal-wrap {
    display: grid;
    gap: 22px;
    padding: 28px;
    background:
        radial-gradient(circle at top center, rgba(200, 146, 42, 0.12), transparent 28%),
        linear-gradient(180deg, #15110f 0%, #0d0d0d 100%);
    color: #f5f0e8;
}

.footer-map-modal .checkout-modal-head h3 {
    margin: 8px 0 0;
    color: #f5f0e8;
    font-family: "Playfair Display", Georgia, serif;
    font-size: 1.7rem;
    font-weight: 500;
    letter-spacing: -0.03em;
}

.footer-map-modal .checkout-modal-head .section-kicker {
    color: #c8922a;
}

.footer-map-card {
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 24px;
    background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.02)),
        rgba(255, 255, 255, 0.02);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.footer-map-card::before {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background:
        linear-gradient(90deg, rgba(255, 255, 255, 0.06) 1px, transparent 1px),
        linear-gradient(180deg, rgba(255, 255, 255, 0.06) 1px, transparent 1px);
    background-size: 28px 28px;
    mask-image: linear-gradient(135deg, rgba(0, 0, 0, 0.32), transparent 70%);
    opacity: 0.16;
}

.footer-map-card-grid {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 18px;
    padding: 20px 22px;
}

.footer-map-card-copy {
    display: grid;
    gap: 6px;
}

.footer-map-card-label {
    color: rgba(255, 255, 255, 0.42);
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 0.68rem;
    font-weight: 500;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}

.footer-map-card-copy strong {
    color: #f5f0e8;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 0.88rem;
    font-weight: 500;
    line-height: 1.55;
}

.delivery-info-modal {
    width: min(560px, calc(100% - 24px));
}

.delivery-info-modal .checkout-modal-head {
    align-items: flex-start;
}

.delivery-info-list {
    display: grid;
    gap: 14px;
}

.delivery-info-item {
    display: grid;
    gap: 8px;
    padding: 18px 20px;
    border: 1px solid rgba(216, 178, 107, 0.16);
    border-radius: 18px;
    background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02)),
        rgba(255, 255, 255, 0.03);
}

.delivery-info-item span {
    color: rgba(245, 240, 232, 0.68);
    font-size: 0.86rem;
    line-height: 1.45;
}

.delivery-info-item strong {
    color: #d8b26b;
    font-size: 1.35rem;
    font-weight: 700;
    line-height: 1.1;
}

.footer-map-frame {
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 24px;
    background:
        radial-gradient(circle at center, rgba(200, 146, 42, 0.08), transparent 56%),
        #14110f;
    min-height: 420px;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.04),
        0 20px 40px rgba(0, 0, 0, 0.24);
}

.footer-map-frame iframe {
    display: block;
    width: 100%;
    height: 420px;
    border: 0;
    filter: saturate(0.86) contrast(1.02) brightness(0.94);
}

.contact-line span {
    font-family: "Space Grotesk", "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 1.2rem;
    text-transform: uppercase;
}

@keyframes marquee-scroll {
    from {
        transform: translateX(0);
    }

    to {
        transform: translateX(-50%);
    }
}

@keyframes hero-image-float {
    0%,
    100% {
        transform: translateY(0) rotate(-2deg);
    }

    50% {
        transform: translateY(-10px) rotate(-1deg);
    }
}

@keyframes hero-badge-bounce {
    0%,
    100% {
        transform: translateY(0);
    }

    50% {
        transform: translateY(-10px);
    }
}

@keyframes hero-shadow-float {
    0%,
    100% {
        transform: scale(1);
        opacity: 0.22;
    }

    50% {
        transform: scale(0.96);
        opacity: 0.16;
    }
}

@media (max-width: 1100px) {
    .about-grid,
    .steps-grid,
    .reviews-grid,
    .contact-grid,
    .site-footer-inner {
        grid-template-columns: 1fr;
    }

    .site-footer-inner {
        gap: 28px;
    }

    .section-head {
        align-items: start;
        flex-direction: column;
    }

    .menu-section .section-head {
        align-items: center;
        justify-content: center;
        text-align: center;
    }

    .menu-section .section-head > div {
        justify-items: center;
    }
}

@media (max-width: 820px) {
    html {
        background: #0f110e;
    }

    .page-preloader-shell,
    .topbar-wrap.is-scrolled,
    .hero-overlay,
    .hero-badge-pill,
    .hero-button-secondary,
    .nav-links,
    .cart-drawer,
    .checkout-modal-shell,
    .auth-modal-body,
    .account-modal-shell {
        backdrop-filter: none;
        -webkit-backdrop-filter: none;
    }

    .hero-background-image {
        filter: brightness(1.02) contrast(1.02) saturate(1.04);
    }

    .hero-badge-pill,
    .hero-kicker,
    .hero h1,
    .hero-address,
    .hero h2 > span,
    .hero-actions,
    .hero-scroll-indicator span:first-child,
    .reveal-on-scroll,
    .reveal-on-scroll.is-visible {
        filter: none;
    }

    .menu-section,
    .menu-section::before,
    .menu-section::after,
    .delivery-section::before,
    .delivery-section::after,
    .site-footer::before,
    .site-footer::after,
    .button-shiny,
    .button-shiny::before,
    .button-shiny::after,
    .hero-scroll-indicator,
    .page-preloader-icon-wrap::before,
    .page-preloader-icon {
        animation: none;
    }

    .menu-section::before,
    .menu-section::after,
    .delivery-section::before,
    .delivery-section::after,
    .site-footer::before,
    .site-footer::after {
        filter: none;
        opacity: 0.35;
    }

    .auth-field input,
    .checkout-field input,
    .admin-field input,
    .admin-field select,
    .admin-field textarea,
    .category-admin-input {
        font-size: 16px;
    }

    .menu-section {
        padding: 68px 18px 28px;
        border-radius: 0;
    }

    .delivery-section {
        padding: 72px 18px 20px;
    }

    .delivery-easy-section {
        padding: 72px 18px 28px;
    }

    .delivery-easy-grid {
        gap: 18px;
    }

    .delivery-easy-card {
        min-height: 250px;
        padding: 28px 22px;
    }

    .delivery-track {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 18px;
    }

    .step-card {
        padding: 26px;
    }

    .topbar-wrap {
        padding: env(safe-area-inset-top) 18px 0;
        border-bottom-color: transparent;
        background: transparent;
        box-shadow: none;
    }

    .topbar-wrap.is-scrolled {
        background: rgba(8, 8, 8, 0.46);
        border-bottom-color: transparent;
        box-shadow: none;
    }

    .topbar {
        min-height: 74px;
    }

    .hero-inner {
        min-height: 100vh;
        padding: 126px 18px 104px;
        width: 100%;
        max-width: 100%;
        text-align: center;
    }

    .hero-badge-pill {
        margin-bottom: 16px;
        padding: 9px 15px;
        font-size: 0.68rem;
        letter-spacing: 0.14em;
    }

    .hero-background-image {
        transform: translate(-50%, -50%) scale(1.005);
        filter: brightness(1.02) contrast(1.02) saturate(1.06);
    }

    .hero-kicker {
        max-width: 100%;
        margin-bottom: 14px;
        font-size: 0.78rem;
        letter-spacing: 0.16em;
        line-height: 1.45;
        text-align: center;
        text-wrap: balance;
    }

    .hero h1 {
        font-size: clamp(3.35rem, 15vw, 5.2rem);
        line-height: 1;
        letter-spacing: 0;
    }

    .hero-address {
        width: min(100%, 34rem);
        font-size: 0.96rem;
        line-height: 1.65;
        max-width: 100%;
        text-align: center;
        text-wrap: balance;
    }

    .hero h2 {
        width: min(100%, 38rem);
        max-width: 100%;
        margin-top: 22px;
        margin-left: auto;
        margin-right: auto;
        padding-bottom: 0;
        font-size: clamp(1.4rem, 6.4vw, 2.2rem);
        line-height: 1.14;
        letter-spacing: 0;
        text-align: center;
        transform: none;
    }

    .hero h2 > span {
        display: block;
        width: 100%;
        max-width: 100%;
        text-align: center;
        white-space: normal;
        text-wrap: balance;
        -webkit-hyphens: none;
        hyphens: none;
        overflow-wrap: break-word;
        word-break: normal;
        transform: none;
    }

    .hero-actions {
        width: 100%;
        gap: 12px;
        margin-top: 28px;
    }

    .hero-button {
        width: 100%;
        min-height: 54px;
        padding: 0 24px;
    }

    .hero-scroll-indicator {
        bottom: 20px;
        font-size: 0.62rem;
    }

    .hero-scroll-line {
        height: 26px;
    }

    .menu-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .cart-drawer {
        top: auto;
        right: 0;
        bottom: 0;
        left: 0;
        width: 100%;
        max-width: 100%;
        height: min(88dvh, 88svh);
        max-height: min(88dvh, 88svh);
        min-height: 0;
        border-radius: 28px 28px 0 0;
        box-shadow: 0 -24px 56px rgba(0, 0, 0, 0.34);
        transform: translateY(100%);
    }

    .cart-drawer.is-open {
        transform: translateY(0);
    }

    .cart-drawer-shell {
        padding: 18px;
        padding-bottom: calc(32px + env(safe-area-inset-bottom));
    }

    .dish-footer {
        flex-direction: column;
        align-items: stretch;
    }

    .site-footer-inner {
        padding: 52px 18px 36px;
    }

    .site-footer-bottom {
        padding: 20px 18px;
        flex-direction: column;
        align-items: flex-start;
    }

    .site-footer-meta {
        justify-items: start;
        text-align: left;
    }

    .site-footer-social {
        margin-top: 18px;
    }

    .site-footer-map-trigger {
        text-align: left;
    }

    .dish-actions {
        justify-content: space-between;
        flex-wrap: wrap;
    }

    .dish-footer {
        align-items: stretch;
    }

    .add-button {
        width: 100%;
    }

    .floating-tools {
        right: 12px;
        gap: 8px;
        top: 104px;
    }

    body.mobile-menu-open .floating-tools {
        opacity: 0;
        transform: translateY(-16px);
        pointer-events: none;
    }

    .floating-tool {
        width: 68px;
        height: 68px;
    }

    .floating-tool-pill {
        width: auto;
        height: 52px;
        padding: 0 16px;
        gap: 8px;
    }

    .floating-tool-pill span {
        font-size: 0.76rem;
    }

    .floating-tool-menu-start {
        right: 12px;
        bottom: 16px;
    }

    #menu-start-trigger {
        right: 12px;
        bottom: calc(16px + env(safe-area-inset-bottom));
        min-height: 52px;
        padding: 0 16px;
        gap: 8px;
    }

    .topbar-wrap.is-menu-open {
        bottom: 0;
        padding: env(safe-area-inset-top) 14px 0;
    }

    .topbar {
        position: relative;
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 8px;
        min-height: 74px;
        padding: 0;
        border-radius: 0;
    }

    .topbar-wrap.is-menu-open .topbar {
        min-height: 100dvh;
        min-height: 100svh;
        align-content: start;
        padding: 0;
    }

    .topbar-wrap::before {
        content: "";
        position: fixed;
        inset: 0;
        z-index: 39;
        background:
            radial-gradient(circle at top right, rgba(216, 178, 107, 0.14), transparent 26%),
            rgba(6, 6, 6, 0.52);
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.28s ease;
    }

    .topbar-wrap.is-menu-open::before {
        opacity: 1;
        pointer-events: auto;
    }

    .topbar-burger {
        display: inline-grid;
        place-items: center;
        position: relative;
        z-index: 45;
        width: 36px;
        height: 36px;
        justify-self: end;
        flex: 0 0 36px;
    }

    .topbar-burger span {
        width: 15px;
    }

    .brand {
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .topbar.is-menu-open .brand {
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
    }

    .nav-links,
    .topbar-controls {
        display: flex;
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
    }

    .nav-links {
        position: fixed;
        top: 0;
        right: 0;
        bottom: 0;
        left: auto;
        z-index: 40;
        width: min(82vw, 340px);
        flex-direction: column;
        align-items: stretch;
        justify-content: flex-start;
        gap: 14px;
        padding: calc(102px + env(safe-area-inset-top)) 22px 156px;
        border-left: 1px solid rgba(216, 178, 107, 0.18);
        background:
            linear-gradient(180deg, rgba(216, 178, 107, 0.12), transparent 30%),
            rgba(13, 13, 13, 0.97);
        backdrop-filter: blur(18px);
        box-shadow: -28px 0 72px rgba(0, 0, 0, 0.36);
        transform: translateX(calc(100% + 28px));
        transition:
            opacity 0.28s ease,
            visibility 0.28s ease,
            transform 0.34s cubic-bezier(0.22, 1, 0.36, 1);
    }

    .nav-links a {
        width: 100%;
        justify-content: flex-start;
        padding: 14px 0;
        border: 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 0;
        background: transparent;
        text-align: left;
        color: #f5f0e8;
        font-family: "Playfair Display", Georgia, serif;
        font-size: clamp(1.45rem, 7vw, 1.95rem);
        font-weight: 400;
        letter-spacing: -0.02em;
        text-transform: none;
    }

    .nav-links a::before,
    .nav-links a::after {
        display: none;
    }

    .topbar-controls {
        position: absolute;
        right: 18px;
        left: auto;
        bottom: calc(12px + env(safe-area-inset-bottom));
        z-index: 41;
        transform: translateY(18px);
        justify-content: stretch;
        width: min(296px, calc(82vw - 44px));
        gap: 8px;
        transition: opacity 0.28s ease, visibility 0.28s ease, transform 0.28s ease;
    }

    .topbar.is-menu-open .nav-links,
    .topbar.is-menu-open .topbar-controls {
        opacity: 1;
        visibility: visible;
        pointer-events: auto;
    }

    .topbar.is-menu-open .nav-links {
        transform: translateX(0);
    }

    .topbar.is-menu-open .topbar-controls {
        position: fixed;
        right: 18px;
        left: auto;
        bottom: calc(12px + env(safe-area-inset-bottom));
        transform: translateY(0);
    }

    .topbar-controls .admin-toggle,
    .topbar-controls .topbar-action {
        width: 100%;
        min-height: 50px;
        border-color: #d8b26b;
        background: #d8b26b;
        color: #12100d;
        box-shadow: none;
    }

    .order-empty,
    .order-summary > div,
    .checkout-button {
        width: 100%;
    }

    .order-summary > div {
        padding: 15px 16px;
    }

    .order-empty p {
        font-size: 0.9rem;
    }

    .cart-toast {
        right: 12px;
        bottom: calc(84px + env(safe-area-inset-bottom));
    }

    .admin-grid {
        grid-template-columns: 1fr;
    }

    .category-admin-row {
        grid-template-columns: 1fr;
    }

    .checkout-modal-form-wrap {
        padding: 24px;
    }

    .account-grid {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 620px) {
    .site-footer-inner {
        padding: 42px 14px 28px;
        gap: 24px;
    }

    .site-footer-logo {
        font-size: 1.7rem;
    }

    .site-footer-bottom {
        padding: 18px 14px 22px;
        gap: 10px;
    }

    .menu-section {
        padding: 58px 14px 20px;
        border-radius: 0;
    }

    .delivery-section {
        padding: 58px 14px 18px;
    }

    .delivery-easy-section {
        padding: 58px 14px 18px;
    }

    .delivery-easy-head {
        margin-bottom: 28px;
    }

    .delivery-easy-grid {
        grid-template-columns: 1fr;
        gap: 14px;
    }

    .delivery-easy-card {
        min-height: 0;
        padding: 24px 18px;
        border-radius: 22px;
    }

    .delivery-easy-card h3 {
        font-size: 1.4rem;
    }

    .delivery-easy-card p {
        font-size: 0.95rem;
    }

    .step-card {
        padding: 22px;
    }

    .delivery-track {
        grid-template-columns: 1fr;
    }

    .menu-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
    }

    .topbar-controls {
        right: 14px;
        bottom: calc(8px + env(safe-area-inset-bottom));
        width: min(292px, calc(82vw - 28px));
    }

    .topbar.is-menu-open .topbar-controls {
        right: 14px;
        bottom: calc(8px + env(safe-area-inset-bottom));
    }

    .order-empty {
        display: grid;
        gap: 10px;
        align-content: start;
    }

    .order-line {
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        align-items: start;
        gap: 10px;
    }

    .order-line-copy {
        gap: 4px;
        width: 100%;
    }

    .order-line-actions {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr) auto;
        align-items: center;
        width: 100%;
        gap: 8px;
    }

    .order-empty strong,
    .order-empty p,
    .order-line-title,
    .order-line-meta,
    .order-summary span,
    .order-summary strong {
        margin: 0;
        white-space: normal;
        overflow-wrap: anywhere;
        word-break: break-word;
    }

    .order-empty strong,
    .order-line-title,
    .order-summary strong {
        display: block;
        line-height: 1.28;
    }

    .order-empty p,
    .order-line-meta,
    .order-summary span {
        line-height: 1.5;
    }

    .order-line-total {
        min-width: 0;
        white-space: nowrap;
        font-size: 0.98rem;
        line-height: 1.1;
        text-align: right;
    }

    .order-remove-button {
        width: 26px;
        height: 26px;
        border-radius: 999px;
    }

    .order-summary {
        gap: 12px;
    }

    .order-summary > div {
        gap: 6px;
    }

    .dish-card {
        border-radius: 18px;
    }

    .dish-visual {
        min-height: 118px;
    }

    .dish-badge {
        top: 10px;
        left: 10px;
        padding: 6px 9px;
        font-size: 0.58rem;
    }

    .dish-body {
        display: grid;
        align-content: start;
        gap: 2px;
        padding: 10px 10px 0;
        min-height: 88px;
    }

    .dish-body h3 {
        display: -webkit-box;
        overflow: hidden;
        margin-bottom: 0;
        font-size: 0.96rem;
        line-height: 1;
        min-height: 1.95em;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }

    .dish-body p {
        display: -webkit-box;
        overflow: hidden;
        margin-top: 0;
        font-size: 0.68rem;
        line-height: 1.35;
        min-height: 1.85em;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }

    .dish-footer {
        justify-content: flex-start;
        padding: 10px;
        gap: 6px;
        margin-top: 0;
    }

    .dish-price {
        font-size: 0.82rem;
    }

    .dish-actions {
        align-items: stretch;
        gap: 6px;
    }

    .qty-picker {
        min-height: 34px;
        padding: 0 7px;
        gap: 6px;
    }

    .qty-button {
        width: 20px;
        height: 20px;
        font-size: 0.76rem;
    }

    .qty-value {
        min-width: 12px;
        font-size: 0.72rem;
    }

    .add-button {
        min-height: 32px;
        padding: 0 8px;
        font-size: 0.68rem;
    }

    .hero h2 {
        width: 100%;
        text-align: center;
    }

    .hero h2 > span:first-child {
        transform: none;
    }

    .dish-admin-row {
        flex-direction: column;
    }

    .admin-modal {
        padding: 18px;
        transform: translate(-50%, -50%);
        transition: opacity 0.2s ease;
    }

    .checkout-modal {
        width: calc(100% - 16px);
        max-height: calc(100vh - 16px);
        max-height: calc(100svh - 16px);
        max-height: calc(100dvh - 16px);
        transform: translateX(-50%);
        transition: opacity 0.2s ease;
    }

    .checkout-modal-form-wrap {
        padding: 18px;
    }

    #checkout-modal {
        top: 8px;
        bottom: 8px;
        height: calc(100vh - 16px);
        height: calc(100svh - 16px);
        height: calc(100dvh - 16px);
        max-height: none;
        transform: translateX(-50%);
    }

    #checkout-modal.is-open {
        transform: translateX(-50%);
    }

    .admin-modal.is-open,
    .auth-modal,
    .auth-modal.is-open {
        transform: translate(-50%, -50%);
        transition: opacity 0.2s ease;
    }

    #checkout-modal .checkout-modal-shell,
    #checkout-modal .checkout-modal-form-wrap {
        height: 100%;
        max-height: none;
    }

    .footer-map-modal-wrap {
        padding: 18px;
    }

    .footer-map-card-grid {
        grid-template-columns: 1fr;
        padding: 16px 16px 18px;
        gap: 14px;
    }

    .footer-map-frame,
    .footer-map-frame iframe {
        min-height: 320px;
        height: 320px;
    }

    .checkout-grid {
        grid-template-columns: 1fr;
    }

    .checkout-preview-inline,
    .checkout-switcher {
        grid-template-columns: 1fr;
    }

    .checkout-bonus-box {
        grid-template-columns: 1fr;
    }

    .auth-modal-body,
    .account-orders {
        padding: 18px;
    }

    .auth-modal {
        width: calc(100% - 16px);
    }

    .auth-copy h3 {
        font-size: clamp(1.8rem, 9vw, 2.4rem);
    }

    .checkout-actions {
        justify-content: flex-start;
    }

    .order-success-modal {
        width: calc(100% - 16px);
    }

    .order-success-shell {
        padding: 24px 18px 20px;
        border-radius: 26px;
    }

    .account-modal {
        width: min(430px, 100%);
        height: 100svh;
        height: 100dvh;
        max-height: 100svh;
        max-height: 100dvh;
        padding: 0;
    }

    .account-modal-shell {
        width: 100%;
        max-height: none;
        padding: 18px;
        padding-bottom: calc(18px + env(safe-area-inset-bottom));
    }

    .account-modal-head {
        padding-right: 44px;
    }

    .account-modal-head h2 {
        font-size: 1.25rem;
    }

    .account-modal-close {
        top: 16px;
        right: 16px;
    }

.account-orders-head,
.account-order-head {
    flex-direction: column;
    align-items: flex-start;
}
}

@media (max-width: 980px) {
    .legal-page-header {
        padding: 12px 14px 0;
    }

    .legal-page-header-inner {
        border-radius: 28px;
        padding: 16px 18px;
        align-items: flex-start;
        flex-wrap: wrap;
    }

    .legal-page-nav {
        order: 3;
        width: 100%;
        justify-content: flex-start;
        flex-wrap: wrap;
        gap: 8px;
    }

    .legal-page-hero {
        padding: 136px 0 42px;
    }

    .legal-page-highlights,
    .legal-page-grid {
        grid-template-columns: 1fr;
    }

    .legal-page-aside {
        position: static;
        order: 2;
    }
}

@media (max-width: 620px) {
    .legal-page-body {
        overflow-x: hidden;
    }

    .legal-page-header {
        padding: calc(8px + env(safe-area-inset-top)) 10px 0;
        background: transparent;
        backdrop-filter: none;
        -webkit-backdrop-filter: none;
    }

    .legal-page-header-inner {
        align-items: center;
        flex-wrap: nowrap;
        gap: 10px;
        padding: 10px 12px;
        border-radius: 18px;
    }

    .legal-page-hero-shell,
    .legal-page-shell {
        width: min(100%, calc(100vw - 28px));
    }

    .legal-page-brand {
        min-width: 0;
        font-size: 1.35rem;
        white-space: nowrap;
    }

    .legal-page-nav a {
        padding: 10px 14px;
        font-size: 0.78rem;
        letter-spacing: 0.04em;
    }

    .legal-page-back {
        width: auto;
        min-height: 38px;
        padding: 0 14px;
        font-size: 0.78rem;
        white-space: nowrap;
    }

    .legal-page-main {
        padding-bottom: 42px;
    }

    .legal-page-hero {
        padding: 108px 14px 34px;
    }

    .legal-page-hero::before,
    .legal-page-hero::after {
        filter: none;
        opacity: 0.32;
    }

    .legal-page-hero-shell {
        gap: 14px;
    }

    .legal-page-hero-shell h1 {
        max-width: 100%;
        font-size: clamp(2.25rem, 12vw, 3.2rem);
        line-height: 1;
        letter-spacing: -0.035em;
        overflow-wrap: anywhere;
    }

    .legal-page-grid {
        gap: 14px;
    }

    .legal-page-aside {
        gap: 12px;
    }

    .legal-document,
    .legal-page-aside-card,
    .legal-page-highlight {
        border-radius: 20px;
        box-shadow: none;
    }

    .legal-page-aside-card,
    .legal-page-highlight {
        padding: 16px;
    }

    .legal-document {
        padding: 18px 16px;
    }

    .legal-document-head {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
        padding-bottom: 14px;
        margin-bottom: 14px;
    }

    .legal-document-text {
        font-size: 0.92rem;
        line-height: 1.65;
        overflow-wrap: anywhere;
    }
}

@media (max-width: 820px) {
    .menu-section {
        padding-left: 0;
        padding-right: 0;
    }

    .hero-inner {
        width: min(100%, calc(100vw - 28px));
        margin-inline: auto;
        padding-inline: 14px;
        align-items: center;
        text-align: center;
    }

    .hero-inner > * {
        margin-left: auto;
        margin-right: auto;
    }

    .menu-section .section-head,
    .menu-section .section-head > div {
        width: 100%;
        max-width: 100%;
        margin-left: auto;
        margin-right: auto;
        padding-left: 16px;
        padding-right: 16px;
        align-items: center;
        justify-items: center;
        justify-content: center;
        text-align: center;
    }

    .menu-section .section-kicker,
    .menu-section .section-head h2 {
        display: block;
        width: 100%;
        max-width: 100%;
        margin-left: auto;
        margin-right: auto;
        text-align: center;
        text-wrap: balance;
        overflow-wrap: break-word;
        word-break: normal;
    }

    .menu-section .section-head h2 {
        font-size: clamp(1.28rem, 5.4vw, 1.78rem);
        line-height: 1.18;
        letter-spacing: 0;
        text-align: center;
        text-align-last: center;
        text-wrap: balance;
        -webkit-hyphens: auto;
        hyphens: auto;
        overflow-wrap: break-word;
    }

    .floating-tools {
        top: 156px;
    }
}

```

## 📁 `static\files`

## 📁 `static\pic`

## 📁 `templates`

## 📄 `templates\index.html`

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Zamzam | Ресторан доставки восточной кухни</title>
    <meta
        name="description"
        content="Zamzam: авторские блюда, быстрая доставка и удобный онлайн-заказ."
    >
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/styles.css?v=20260619-delivery-easy-mobile-fix-1">
    <style>
        .site-footer-contact-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(150px, 1fr));
            column-gap: 46px;
            row-gap: 18px;
            width: max-content;
            max-width: 100%;
        }

        .site-footer-contact-item {
            display: grid;
            gap: 8px;
            align-content: start;
            min-width: 0;
        }

        .site-footer-contact-item .site-footer-map-trigger,
        .site-footer-contact-item .site-footer-phone {
            text-align: left;
        }

        .site-footer-contact-item .site-footer-phone,
        .site-footer-contact-item strong {
            white-space: nowrap;
        }

        .site-footer-contact-item .site-footer-map-trigger {
            white-space: nowrap;
        }

        #reservation-modal {
            width: min(420px, calc(100vw - 32px));
        }

        #reservation-modal .checkout-modal-shell {
            width: min(420px, calc(100vw - 32px));
        }

        #reservation-modal .footer-map-modal-wrap {
            padding: 28px;
        }

        .reservation-branch-list {
            display: grid;
            gap: 12px;
        }

        .reservation-branch-link {
            display: grid;
            gap: 4px;
            padding: 14px 16px;
            border: 1px solid rgba(216, 178, 107, 0.24);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.04);
            color: #fff;
            text-decoration: none;
        }

        .reservation-branch-link span {
            color: rgba(255, 255, 255, 0.72);
            font-size: 0.86rem;
        }

        .reservation-branch-link strong {
            color: #ffffff;
            font-size: 1rem;
        }

        @media (max-width: 640px) {
            .site-footer-contact-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body class="preloader-active">
    <div class="page-preloader" id="page-preloader" aria-hidden="true">
        <div class="page-preloader-shell">
            <div class="page-preloader-icon-wrap">
                <img class="page-preloader-icon" src="/static/pic/preloader-cloche.svg" alt="">
            </div>
            <strong class="page-preloader-title">Zamzam</strong>
            <span class="page-preloader-copy">Загружаем страницу</span>
        </div>
    </div>
    <div class="floating-tools">
        <button class="floating-tool floating-tool-neutral is-hidden" id="account-floating-trigger" type="button" aria-label="Открыть кабинет">
            <svg class="floating-tool-account-icon" width="18" height="20" viewBox="0 0 18 20" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <path d="M16.75 18.75C16.75 17.3544 16.75 16.6567 16.5778 16.0889C16.19 14.8105 15.1896 13.81 13.9112 13.4222C13.3434 13.25 12.6456 13.25 11.25 13.25H6.25003C4.85447 13.25 4.15668 13.25 3.58889 13.4222C2.31049 13.81 1.31007 14.8105 0.92227 16.0889C0.750031 16.6567 0.750031 17.3544 0.750031 18.75M13.25 5.25C13.25 7.73528 11.2353 9.75 8.75003 9.75C6.26475 9.75 4.25003 7.73528 4.25003 5.25C4.25003 2.76472 6.26475 0.75 8.75003 0.75C11.2353 0.75 13.25 2.76472 13.25 5.25Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </button>
        <button class="floating-tool floating-tool-accent" id="cart-toggle" type="button" aria-label="Открыть корзину">
            <svg class="floating-tool-cart-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <path d="M3.5 5.5H5.119C5.713 5.5 6.01 5.5 6.247 5.605C6.456 5.698 6.635 5.857 6.744 6.058C6.867 6.286 6.902 6.58 6.973 7.169L7.275 9.667C7.371 10.461 7.419 10.858 7.61 11.157C7.779 11.422 8.022 11.632 8.308 11.761C8.631 11.907 9.031 11.907 9.832 11.907H16.664C17.421 11.907 17.799 11.907 18.109 11.775C18.383 11.658 18.62 11.468 18.795 11.226C18.992 10.953 19.065 10.582 19.21 9.84L19.678 7.446C19.796 6.841 19.855 6.539 19.774 6.303C19.704 6.097 19.565 5.921 19.38 5.803C19.168 5.667 18.86 5.667 18.245 5.667H7.25" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M10 17.5C10 18.328 9.328 19 8.5 19C7.672 19 7 18.328 7 17.5C7 16.672 7.672 16 8.5 16C9.328 16 10 16.672 10 17.5Z" stroke="currentColor" stroke-width="1.6"/>
                <path d="M18 17.5C18 18.328 17.328 19 16.5 19C15.672 19 15 18.328 15 17.5C15 16.672 15.672 16 16.5 16C17.328 16 18 16.672 18 17.5Z" stroke="currentColor" stroke-width="1.6"/>
            </svg>
            <span class="floating-count" id="floating-count">0</span>
        </button>
    </div>
    <button class="floating-tool floating-tool-neutral floating-tool-pill floating-tool-menu-start is-hidden" id="menu-start-trigger" type="button" aria-label="Вернуться к началу меню">
        <svg class="floating-tool-arrow-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M12 18V6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M7 11L12 6L17 11" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>К началу</span>
    </button>

    <div class="cart-backdrop" id="cart-backdrop"></div>
    <div class="checkout-backdrop" id="checkout-backdrop"></div>
    <div class="checkout-backdrop" id="auth-backdrop"></div>
    <div class="checkout-backdrop" id="footer-map-backdrop"></div>
    <div class="checkout-backdrop" id="reservation-backdrop"></div>
    <div class="checkout-backdrop" id="delivery-info-backdrop"></div>
    <div class="admin-backdrop" id="admin-backdrop"></div>
    <aside class="cart-drawer" id="order-panel">
        <div class="cart-drawer-shell">
        <button class="cart-close" id="cart-close" type="button" aria-label="Закрыть корзину">x</button>
        <span class="section-kicker">Ваш заказ</span>
        <h3>Корзина</h3>

        <div class="cart-checkout-mode">
            <span class="cart-checkout-mode-label">Тип заказа</span>
            <div class="checkout-switcher cart-checkout-switcher" role="tablist" aria-label="Тип заказа в корзине">
                <button class="checkout-switch is-active" id="cart-checkout-type-pickup" type="button">Самовывоз</button>
                <button class="checkout-switch" id="cart-checkout-type-delivery" type="button">Доставка</button>
            </div>
            <p class="cart-checkout-note" id="cart-checkout-note" hidden></p>
        </div>

        <div class="cart-checkout-mode">
            <span class="cart-checkout-mode-label">Ресторан на:</span>
            <div class="checkout-switcher cart-checkout-switcher" role="tablist" aria-label="Филиал ресторана">
                <button class="checkout-switch is-active" id="cart-branch-malyshava" type="button">Малышева</button>
                <button class="checkout-switch" id="cart-branch-suh" type="button">Сухоложской</button>
            </div>
        </div>

        <div class="order-items" id="order-items">
            <div class="order-empty">
                <strong>Пока пусто</strong>
                <p>Добавьте блюда из каталога, и заказ появится здесь.</p>
            </div>
        </div>

        <div class="order-summary">
            <div>
                <span>Блюда</span>
                <strong id="items-count">0</strong>
            </div>
            <div id="cutlery-summary-item">
                <span>Приборы</span>
                <div class="qty-picker qty-picker-ghost" data-cutlery-picker>
                    <button class="qty-button" id="cutlery-decrease" type="button" data-cutlery-action="decrease">-</button>
                    <span class="qty-value" id="cutlery-count">0</span>
                    <button class="qty-button" id="cutlery-increase" type="button" data-cutlery-action="increase">+</button>
                </div>
            </div>
            <div>
                <span>Сумма заказа</span>
                <strong id="total-price">0 руб.</strong>
            </div>
        </div>

        <button class="checkout-button" id="checkout-button">Оформить заказ</button>
        </div>
    </aside>
    <section class="checkout-modal" id="checkout-modal" aria-hidden="true">
        <div class="checkout-modal-shell">
            <div class="checkout-modal-form-wrap">
                <div class="checkout-modal-head">
                    <div>
                        <span class="section-kicker">Детали заказа</span>
                        <h3>Оформить сейчас</h3>
                    </div>
                    <button class="admin-close" id="checkout-close" type="button" aria-label="Закрыть оформление">x</button>
                </div>

                <form class="checkout-form" id="checkout-form">
                    <div class="checkout-grid">
                        <label class="checkout-field checkout-field-floating">
                            <input id="checkout-name" type="text" maxlength="120" placeholder=" " required>
                            <span>Имя</span>
                        </label>

                        <label class="checkout-field checkout-field-floating">
                            <input id="checkout-phone" type="tel" maxlength="32" placeholder=" " required>
                            <span>Телефон</span>
                        </label>
                    </div>

                    <div class="checkout-delivery-fields is-hidden" id="checkout-delivery-fields">
                        <div class="checkout-grid">
                            <label class="checkout-field checkout-field-floating">
                                <input id="checkout-address" type="text" maxlength="255" placeholder=" " list="checkout-address-suggestions">
                                <span>Улица</span>
                                <datalist id="checkout-address-suggestions"></datalist>
                            </label>

                            <label class="checkout-field checkout-field-floating">
                                <input id="checkout-house" type="text" maxlength="64" placeholder=" ">
                                <span>Дом</span>
                            </label>
                        </div>

                        <div class="checkout-grid">
                            <label class="checkout-field checkout-field-floating">
                                <input id="checkout-flat" type="text" maxlength="64" placeholder=" ">
                                <span>Квартира / офис</span>
                            </label>

                            <label class="checkout-field checkout-field-floating">
                                <input id="checkout-entrance" type="text" maxlength="64" placeholder=" ">
                                <span>Подъезд / этаж</span>
                            </label>
                        </div>

                        <div class="checkout-grid">
                            <label class="checkout-field checkout-field-wide checkout-field-floating">
                                <input id="checkout-comment" type="text" maxlength="255" placeholder=" ">
                                <span>Комментарий курьеру</span>
                            </label>
                        </div>
                    </div>

                    <div class="checkout-preview checkout-preview-inline">
                        <div>
                            <span>Блюда</span>
                            <strong id="checkout-preview-items">0</strong>
                        </div>
                        <div>
                            <span>Приборы</span>
                            <strong id="checkout-preview-cutlery">0</strong>
                        </div>
                        <div>
                            <span>К оплате</span>
                            <strong id="checkout-preview-total">0 руб.</strong>
                        </div>
                    </div>

                    <div class="checkout-order-list" id="checkout-preview-lines">
                        <div class="order-empty">
                            <strong>Пока пусто</strong>
                            <p>Добавьте блюда из каталога, и они появятся перед подтверждением заказа.</p>
                        </div>
                    </div>

                    <div class="checkout-bonus-box">
                        <div class="checkout-bonus-copy">
                            <span class="checkout-label">Списание бонусов</span>
                            <p id="checkout-bonus-balance-text">Доступно бонусов: 0</p>
                        </div>
                        <label class="checkout-field checkout-bonus-field">
                            <span>Сколько списать</span>
                            <div class="checkout-bonus-stepper">
                                <button class="checkout-bonus-button" id="checkout-bonus-decrease" type="button" aria-label="Уменьшить списание бонусов">-</button>
                                <input id="checkout-bonus-spent" type="number" min="0" max="0" value="0" inputmode="numeric">
                                <button class="checkout-bonus-button" id="checkout-bonus-increase" type="button" aria-label="Увеличить списание бонусов">+</button>
                            </div>
                        </label>
                    </div>





                    <div class="checkout-consents">
                        <label class="checkout-consent">
                            <input id="checkout-oferta-consent" type="checkbox" required>
                            <span>Ознакомлен и соглашаюсь с <a href="/oferta" target="_blank" rel="noopener">офертой</a></span>
                        </label>
                        <label class="checkout-consent">
                            <input id="checkout-policy-consent" type="checkbox" required>
                            <span>Ознакомлен и соглашаюсь с <a href="/policy" target="_blank" rel="noopener">политикой конфиденциальности</a></span>
                        </label>
                    </div>

                    <div class="checkout-actions">
                        <button class="checkout-submit" id="checkout-submit" type="submit">Подтвердить и оплатить заказ</button>
                    </div>
                </form>
            </div>
        </div>
    </section>
    <section class="auth-modal" id="auth-modal" aria-hidden="true">
        <div class="auth-modal-shell">
            <div class="auth-modal-head">
                <button class="auth-modal-icon" id="auth-back" type="button" aria-label="Назад">&#8592;</button>
                <button class="auth-modal-icon" id="auth-close" type="button" aria-label="Закрыть">x</button>
            </div>

            <div class="auth-modal-body">
                <div class="checkout-switcher auth-switcher" role="tablist" aria-label="Режим авторизации">
                    <button class="checkout-switch is-active" id="auth-tab-login" type="button" onclick="if(window.setZamzamAuthMode){window.setZamzamAuthMode('login');}else{(function(){var loginForm=document.getElementById('auth-login-form');var registerForm=document.getElementById('auth-register-form');var loginTab=document.getElementById('auth-tab-login');var registerTab=document.getElementById('auth-tab-register');if(loginForm){loginForm.classList.remove('is-hidden');}if(registerForm){registerForm.classList.add('is-hidden');}if(loginTab){loginTab.classList.add('is-active');}if(registerTab){registerTab.classList.remove('is-active');}})();}">Войти</button>
                    <button class="checkout-switch" id="auth-tab-register" type="button" onclick="if(window.setZamzamAuthMode){window.setZamzamAuthMode('register');}else{(function(){var loginForm=document.getElementById('auth-login-form');var registerForm=document.getElementById('auth-register-form');var loginTab=document.getElementById('auth-tab-login');var registerTab=document.getElementById('auth-tab-register');if(loginForm){loginForm.classList.add('is-hidden');}if(registerForm){registerForm.classList.remove('is-hidden');}if(loginTab){loginTab.classList.remove('is-active');}if(registerTab){registerTab.classList.add('is-active');}})();}">Регистрация</button>
                </div>

                <form class="auth-form" id="auth-login-form">
                    <div class="auth-copy">
                        <span class="section-kicker">Личный кабинет</span>
                        <h3>Вход в Zamzam</h3>
                        <p>Введите номер телефона и пароль, чтобы посмотреть бонусы, историю заказов и быстро оформить доставку.</p>
                    </div>

                    <label class="auth-field auth-field-floating">
                        <input id="auth-phone" type="tel" maxlength="32" placeholder=" " required>
                        <span>Телефон</span>
                    </label>

                    <label class="auth-field auth-field-floating">
                        <input id="auth-password" type="password" maxlength="128" placeholder=" " required>
                        <span>Пароль</span>
                    </label>

                    <button class="auth-link-button" id="auth-forgot-password" type="button">Забыли пароль?</button>
                    <button class="auth-submit" id="auth-login-submit" type="submit">Войти</button>
                </form>

                <form class="auth-form is-hidden" id="auth-register-form">
                    <div class="auth-copy">
                        <span class="section-kicker">Создать профиль</span>
                        <h3>Регистрация</h3>
                        <p>Укажите имя, номер телефона и придумайте пароль, чтобы сохранить бонусы и получать статус заказов.</p>
                    </div>

                    <label class="auth-field auth-field-floating">
                        <input id="auth-register-name" type="text" maxlength="120" placeholder=" ">
                        <span>Ваше имя</span>
                    </label>

                    <label class="auth-field auth-field-floating">
                        <input id="auth-register-phone" type="tel" maxlength="32" placeholder=" " required>
                        <span>Телефон</span>
                    </label>

                    <label class="auth-field auth-field-floating">
                        <input id="auth-register-email" type="email" maxlength="255" placeholder=" " required>
                        <span>Email</span>
                    </label>

                    <label class="auth-field auth-field-floating">
                        <input id="auth-register-password" type="password" maxlength="128" placeholder=" " required>
                        <span>Пароль не менее 6 символов</span>
                    </label>

                    <div class="auth-consents" id="auth-register-consents">
                        <label class="auth-consent">
                            <input id="auth-register-oferta-consent" type="checkbox" required>
                            <span>Ознакомлен и соглашаюсь с <a href="/oferta" target="_blank" rel="noopener">офертой</a></span>
                        </label>
                        <label class="auth-consent">
                            <input id="auth-register-policy-consent" type="checkbox" required>
                            <span>Ознакомлен и соглашаюсь с <a href="/policy" target="_blank" rel="noopener">политикой конфиденциальности</a></span>
                        </label>
                    </div>

                    <button class="auth-submit" id="auth-register-submit" type="submit">Зарегистрироваться</button>
                </form>

                <form class="auth-form is-hidden" id="auth-recovery-form">
                    <div class="auth-copy">
                        <span class="section-kicker">Восстановление доступа</span>
                        <h3>Сброс пароля</h3>
                        <p>Укажите email, который был добавлен при регистрации. Мы отправим код восстановления.</p>
                    </div>

                    <label class="auth-field auth-field-floating">
                        <input id="auth-recovery-email" type="email" maxlength="255" placeholder=" " required>
                        <span>Email</span>
                    </label>

                    <label class="auth-field auth-field-floating is-hidden" id="auth-recovery-token-field">
                        <input id="auth-recovery-token" type="text" maxlength="6" inputmode="numeric" pattern="[0-9]{6}" placeholder=" ">
                        <span>Код из письма</span>
                    </label>

                    <label class="auth-field auth-field-floating is-hidden" id="auth-recovery-password-field">
                        <input id="auth-recovery-password" type="password" maxlength="128" placeholder=" ">
                        <span>Новый пароль</span>
                    </label>

                    <div class="auth-recovery-actions">
                        <button class="auth-submit" id="auth-recovery-submit" type="submit">Отправить код</button>
                        <button class="auth-submit auth-submit-secondary is-hidden" id="auth-reset-submit" type="button">Сменить пароль</button>
                    </div>
                </form>

                <div class="auth-hint" id="auth-hint"></div>
            </div>
        </div>
    </section>
    <section class="auth-modal" id="auth-required-modal" aria-hidden="true">
        <div class="auth-modal-shell">
            <div class="auth-modal-head">
                <div></div>
                <button class="auth-modal-icon" id="auth-required-close" type="button" aria-label="Закрыть">x</button>
            </div>

            <div class="auth-modal-body">
                <div class="auth-copy">
                    <h3>Сначала войдите в кабинет</h3>
                    <p>Чтобы оформить заказ, сначала нужно войти в аккаунт или зарегистрироваться. Это займет меньше минуты.</p>
                </div>

                <div class="auth-required-actions">
                    <button class="auth-submit" id="auth-required-login" type="button">Войти</button>
                    <button class="auth-submit auth-submit-secondary" id="auth-required-register" type="button">Зарегистрироваться</button>
                </div>
            </div>
        </div>
    </section>
    <section class="checkout-modal footer-map-modal" id="footer-map-modal" aria-hidden="true">
        <div class="checkout-modal-shell">
            <div class="footer-map-modal-wrap">
                <div class="checkout-modal-head">
                    <div>
                        <span class="section-kicker">Мы находимся</span>
                        <h3 id="footer-map-location-title">ул. Малышева, д. 28</h3>
                    </div>
                </div>

                <div class="footer-map-card">
                    <div class="footer-map-card-grid">
                        <div class="footer-map-card-copy">
                            <span class="footer-map-card-label">Адрес</span>
                            <strong id="footer-map-location-address">Екатеринбург, ул. Малышева, д. 28</strong>
                        </div>
                        <div class="footer-map-card-copy">
                            <span class="footer-map-card-label">Режим работы</span>
                            <strong>Пн - Вс • 10:00 - 23:00</strong>
                        </div>
                    </div>
                </div>

                <div class="footer-map-frame">
                    <iframe
                        title="Карта Zamzam"
                        src="https://www.google.com/maps?q=%D0%B3.%20%D0%95%D0%BA%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%BD%D0%B1%D1%83%D1%80%D0%B3,%20%D1%83%D0%BB.%20%D0%9C%D0%B0%D0%BB%D1%8B%D1%88%D0%B5%D0%B2%D0%B0,%20%D0%B4.28&output=embed"
                        loading="lazy"
                        referrerpolicy="no-referrer-when-downgrade"
                        allowfullscreen>
                    </iframe>
                </div>
            </div>
        </div>
    </section>
    <section class="checkout-modal footer-map-modal" id="reservation-modal" aria-hidden="true">
        <div class="checkout-modal-shell">
            <div class="footer-map-modal-wrap">
                <div class="checkout-modal-head">
                    <div>
                        <span class="section-kicker">Бронирование</span>
                        <h3>Выберите ресторан</h3>
                    </div>
                    <button class="admin-close" id="reservation-close" type="button" aria-label="Закрыть выбор ресторана">x</button>
                </div>

                <div class="reservation-branch-list">
                    <a class="reservation-branch-link button-shiny" href="tel:+79827505455">
                        <span>ул. Малышева, д. 28</span>
                        <strong>+7 982 750-54-55</strong>
                    </a>
                    <a class="reservation-branch-link button-shiny" href="tel:+79530420044">
                        <span>ул. Сухоложская, д. 5/1</span>
                        <strong>+7 (953) 042-00-44</strong>
                    </a>
                </div>
            </div>
        </div>
    </section>
    <section class="checkout-modal footer-map-modal delivery-info-modal" id="delivery-info-modal" aria-hidden="true">
        <div class="checkout-modal-shell">
            <div class="footer-map-modal-wrap delivery-info-modal-wrap">
                <div class="checkout-modal-head">
                    <div>
                        <span class="section-kicker">Доставка</span>
                        <h3>Условия доставки</h3>

                    </div>
                    <button class="admin-close" id="delivery-info-close" type="button" aria-label="Закрыть условия доставки">x</button>
                </div>

                <div class="delivery-info-list">
                   <div class="delivery-info-item">

                        <span>Бесплатная доставка при заказе от</span>
                        <strong>5 000 руб.</strong>
                    </div>

                </div>
            </div>
        </div>
    </section>
    <section class="admin-modal" id="admin-modal" aria-hidden="true">
        <div class="admin-modal-head">
            <div>
                <span class="section-kicker">Админка</span>
                <h3 id="admin-modal-title">Редактирование карточки</h3>
            </div>
            <button class="admin-close" id="admin-close" type="button" aria-label="Закрыть форму">x</button>
        </div>

        <form class="admin-form" id="admin-form">
            <input id="admin-item-id" type="hidden">
            <input id="admin-item-version" type="hidden">

            <label class="admin-field">
                <span>Название</span>
                <input id="admin-title" type="text" maxlength="255" required>
            </label>

            <label class="admin-field">
                <span>Описание</span>
                <textarea id="admin-description" rows="5" maxlength="4000" required></textarea>
            </label>

            <div class="admin-grid">
                <label class="admin-field">
                    <span>Цена</span>
                    <input id="admin-price" type="number" min="0" max="1000000" readonly>
                </label>

                <label class="admin-field">
                    <span>Категория на сайте</span>
                    <select id="admin-category" required></select>
                </label>
            </div>

            <label class="admin-field">
                <span>Фото</span>
                <input id="admin-image" type="file" accept="image/png,image/jpeg,image/webp">
            </label>

            <div class="admin-actions admin-actions-end">
                <button class="admin-delete is-hidden" id="admin-delete" type="button">Удалить с сайта</button>
                <button class="admin-save" id="admin-save" type="submit">Сохранить</button>
            </div>
        </form>
    </section>
    <section class="admin-modal" id="hero-admin-modal" aria-hidden="true">
        <div class="admin-modal-head">
            <div>
                <span class="section-kicker">Админка</span>
                <h3>Редактирование hero-секции</h3>
            </div>
            <button class="admin-close" id="hero-admin-close" type="button" aria-label="Закрыть форму">x</button>
        </div>

        <form class="admin-form" id="hero-admin-form">
            <label class="admin-field">
                <span>Верхняя строка</span>
                <input id="hero-admin-kicker" type="text" maxlength="255" required>
            </label>

            <label class="admin-field">
                <span>Главный заголовок</span>
                <input id="hero-admin-title" type="text" maxlength="255" required>
            </label>

            <label class="admin-field">
                <span>Описание</span>
                <textarea id="hero-admin-address" rows="4" maxlength="500" required></textarea>
            </label>

            <div class="admin-grid">
                <label class="admin-field">
                    <span>Подзаголовок 1</span>
                    <input id="hero-admin-subtitle-primary" type="text" maxlength="255" required>
                </label>

                <label class="admin-field">
                    <span>Подзаголовок 2</span>
                    <input id="hero-admin-subtitle-secondary" type="text" maxlength="255" required>
                </label>
            </div>

            <div class="admin-actions admin-actions-end">
                <button class="admin-save" id="hero-admin-save" type="submit">Сохранить</button>
            </div>
        </form>
    </section>
    <section class="admin-modal" id="menu-section-admin-modal" aria-hidden="true">
        <div class="admin-modal-head">
            <div>
                <span class="section-kicker">Админка</span>
                <h3 id="menu-section-admin-modal-title">Редактирование блока меню</h3>
            </div>
            <button class="admin-close" id="menu-section-admin-close" type="button" aria-label="Закрыть форму">x</button>
        </div>

        <form class="admin-form" id="menu-section-admin-form">
            <label class="admin-field">
                <span>Надпись</span>
                <input id="menu-section-admin-kicker" type="text" maxlength="255" required>
            </label>

            <label class="admin-field">
                <span>Заголовок</span>
                <textarea id="menu-section-admin-title" rows="4" maxlength="500" required></textarea>
            </label>

            <div class="admin-actions admin-actions-end">
                <button class="admin-save" id="menu-section-admin-save" type="submit">Сохранить</button>
            </div>
        </form>
    </section>
    <section class="admin-modal" id="menu-categories-admin-modal" aria-hidden="true">
        <div class="admin-modal-head">
            <div>
                <span class="section-kicker">Админка</span>
                <h3>Категории блюд</h3>
            </div>
            <button class="admin-close" id="menu-categories-admin-close" type="button" aria-label="Закрыть форму">x</button>
        </div>

        <form class="admin-form" id="menu-categories-admin-form">
            <div class="category-admin-list" id="menu-categories-admin-list"></div>

            <div class="admin-actions">
                <button class="topbar-action topbar-action-button" id="menu-categories-admin-add" type="button">Добавить категорию</button>
                <button class="admin-save" id="menu-categories-admin-save" type="submit">Сохранить</button>
            </div>
        </form>
    </section>
    <section class="admin-modal" id="catalog-admin-modal" aria-hidden="true">
        <div class="admin-modal-head">
            <div>
                <span class="section-kicker">Админка</span>
                <h3>Добавить товар из iiko</h3>
            </div>
            <button class="admin-close" id="catalog-admin-close" type="button" aria-label="Закрыть форму">x</button>
        </div>

        <div class="admin-form">
            <label class="admin-field">
                <span>Поиск по названию из iiko</span>
                <input id="catalog-search-input" type="text" maxlength="255" placeholder="Введите название товара">
            </label>

            <div class="admin-actions admin-actions-end">
                <button class="admin-save" id="catalog-search-submit" type="button">Найти</button>
            </div>

            <div class="account-orders-list" id="catalog-search-results">
                <div class="account-order-empty">Начните поиск товара из iiko.</div>
            </div>
        </div>
    </section>
    <section class="admin-modal" id="orders-admin-modal" aria-hidden="true">
        <div class="admin-modal-head">
            <div>
                <span class="section-kicker">Админка</span>
                <h3>Управление заказами</h3>
            </div>
            <button class="admin-close" id="orders-admin-close" type="button" aria-label="Закрыть форму">x</button>
        </div>

        <div class="admin-form">
            <label class="admin-field">
                <span>Поиск по номеру телефона</span>
                <input id="orders-admin-phone" type="tel" maxlength="32" placeholder="+7">
            </label>

            <div class="admin-actions">
                <button class="topbar-action topbar-action-button" id="orders-admin-refresh" type="button">Показать последние</button>
                <button class="admin-save" id="orders-admin-search" type="button">Найти заказы</button>
            </div>

            <div class="account-orders-list" id="orders-admin-results">
                <div class="account-order-empty">Здесь появятся последние заказы и статусы для управления.</div>
            </div>
        </div>
    </section>
    <header class="topbar-wrap" id="navbar">
        <nav class="topbar">
            <a class="brand" href="#hero">Zamzam</a>
            <button class="topbar-burger" id="topbar-burger" type="button" aria-label="Открыть меню" aria-expanded="false">
                <span></span>
                <span></span>
                <span></span>
            </button>

            <div class="nav-links">
                <a href="#about">О нас</a>
                <a href="#menu">Меню</a>
                <a href="#delivery-info" data-delivery-info-open>Доставка</a>
                <a href="#footer">Контакты</a>
            </div>

            <div class="topbar-controls">
                <button class="topbar-action topbar-action-button button-shiny" id="cart-open-topbar" type="button" onclick="(function(){var modal=document.getElementById('auth-modal');var backdrop=document.getElementById('auth-backdrop');var loginForm=document.getElementById('auth-login-form');var registerForm=document.getElementById('auth-register-form');var loginTab=document.getElementById('auth-tab-login');var registerTab=document.getElementById('auth-tab-register');var hint=document.getElementById('auth-hint');if(registerForm){registerForm.classList.add('is-hidden');}if(loginForm){loginForm.classList.remove('is-hidden');}if(loginTab){loginTab.classList.add('is-active');}if(registerTab){registerTab.classList.remove('is-active');}if(hint){hint.textContent='';hint.style.color='';}if(backdrop){backdrop.classList.add('is-open');}if(modal){modal.classList.add('is-open');modal.setAttribute('aria-hidden','false');}document.body.classList.add('admin-open');})();"><span>Войти</span></button>
            </div>
        </nav>
    </header>

    <main>
        <section class="account-modal is-hidden" id="account" aria-hidden="true">
            <div class="account-modal-shell">
                <div class="section-head account-modal-head">
                    <div>
                    <span class="section-kicker">Личный кабинет</span>
                    <h2>Ваши бонусы и актуальный статус заказа.</h2>
                    </div>
                </div>

            <button class="admin-close account-modal-close" id="account-close" type="button" aria-label="Закрыть кабинет">x</button>
            <div class="account-grid">
                <article class="account-summary-card">
                    <span class="account-summary-label">Бонусы</span>
                    <strong id="account-bonus-balance">0</strong>
                    <p id="account-user-phone">Телефон не подтвержден.</p>
                </article>

                <article class="account-summary-card">
                    <span class="account-summary-label">Статус заказа</span>
                    <strong id="account-order-status">Заказов пока нет</strong>
                    <p id="account-orders-count">Активных заказов: 0</p>
                </article>
            </div>

            <section class="account-current-order">
                <div class="account-orders-head">
                    <h3>Текущий заказ</h3>
                    <button class="topbar-action topbar-action-button account-refresh" id="account-current-refresh" type="button">Обновить</button>
                </div>
                <div id="account-current-order-card">
                    <div class="account-order-empty">Активного заказа пока нет.</div>
                </div>
            </section>

            <div class="account-orders">
                <div class="account-orders-head">
                    <h3>История заказов</h3>
                    <button class="topbar-action topbar-action-button account-refresh" id="account-history-refresh" type="button">Обновить</button>
                </div>
                <div class="account-orders-list" id="account-orders-list">
                    <div class="account-order-empty">После первого подтвержденного заказа история появится здесь.</div>
                </div>
            </div>

            <section class="account-profile-card">
                <form class="account-phone-form" id="account-phone-form">
                    <label class="auth-field auth-field-floating">
                        <input id="account-phone-input" type="tel" maxlength="32" placeholder=" " required>
                        <span>Телефон</span>
                    </label>
                    <button class="auth-submit" id="account-phone-submit" type="submit">Сохранить номер</button>
                </form>
                <div class="auth-hint account-phone-hint" id="account-phone-hint"></div>
            </section>
                </div>
        </section>

        <section class="hero" id="hero">
            <div class="hero-media" aria-hidden="true">
                <video
                    class="hero-background-image"
                    data-desktop-src="/static/files/screen_1778050798162.mp4"
                    data-mobile-src="/static/files/IMG_2455 (online-video-cutter.com).mp4"
                    autoplay
                    muted
                    loop
                    playsinline
                    preload="auto"
                ></video>
            </div>
            <div class="hero-overlay"></div>

            <div class="hero-inner">
                <div class="hero-badge-pill">
                    <span class="hero-badge-dot" aria-hidden="true"></span>
                    Ресторан и доставка
                </div>

                <span class="hero-kicker">Восточная • Кавказская • Авторская кухня</span>

                <h1>Zamzam</h1>

                <p class="hero-address">
                    Доставка по городу, ресторанная подача и быстрый онлайн-заказ
                </p>

                <h2>
                    <span>Яркая восточная кухня с характером</span>
                    <span>Сервис современного уровня</span>
                </h2>

                <div class="hero-actions">
                    <a class="hero-button hero-button-primary" href="#menu">Смотреть меню</a>
                    <button class="hero-button hero-button-secondary button-shiny" id="cart-open-hero" type="button"><span>Забронировать стол</span></button>
                </div>
            </div>

            <a class="hero-scroll-indicator" href="#menu" aria-label="Прокрутить ниже">
                <span>МЕНЮ</span>
                <span class="hero-scroll-line" aria-hidden="true"></span>
            </a>
        </section>

        <section class="delivery-easy-section" aria-labelledby="delivery-easy-title">
            <div class="delivery-easy-shell">
                <div class="delivery-easy-head">
                    <h2 id="delivery-easy-title">Оформим доставку в пару шагов</h2>
                </div>

                <div class="delivery-easy-grid">
                    <article class="delivery-easy-card">
                        <div class="delivery-easy-icon" aria-hidden="true">
                            <img src="/static/pic/div2.svg" alt="" loading="lazy" decoding="async">
                        </div>
                        <h3>Вызовите Яндекс курьера</h3>
                        <p>ул. Малышева, 28 или Сухоложская 5/1<br>доставка по Екатеринбургу</p>
                    </article>

                    <article class="delivery-easy-card">
                        <div class="delivery-easy-icon" aria-hidden="true">
                            <img src="/static/pic/div1.svg" alt="" loading="lazy" decoding="async">
                        </div>
                        <h3>Мы передадим ему заказ</h3>
                        <p>На любую сумму</p>
                    </article>
                </div>
            </div>
        </section>

        <section class="menu-section section-shell" id="menu">
            <div class="section-head">
                <div>
                    <span class="section-kicker">Наше меню</span>
                    <h2>Наша кухня - это богатое сочетание традиций, ароматов и вкусов, которые передаются из поколения в поколение.</h2>
                </div>

            </div>

            <div class="menu-layout">
                <div class="menu-admin-bar">
                    <button class="admin-toggle" id="menu-categories-open" type="button">Категории</button>
                    <button class="admin-toggle admin-toggle-accent" id="catalog-search-open" type="button">Добавить товар из iiko</button>
                </div>
                <div class="menu-content">
                    <div class="filters" id="filters">
                        <button class="filter-chip active" data-filter="all">Все блюда</button>
                        {% for category in menu_categories %}
                        <button class="filter-chip" data-filter="{{ category.value }}">{{ category.label }}</button>
                        {% endfor %}
                    </div>

                    <div class="menu-grid" id="menu-grid">
                        {% for item in menu_items %}
                        <article
                            class="dish-card"
                            data-category="{{ item.category }}"
                            data-item-id="{{ item.id }}"
                            data-item-version="{{ item.version }}"
                            data-item-is-active="{{ 'true' if item.is_active else 'false' }}"
                            data-image-path="{{ item.image_path or '' }}"
                            style="--card-accent: {{ item.accent }}"
                        >
                            <div class="dish-visual">
                                <img
                                    class="dish-image{% if not item.image_path %} is-hidden{% endif %}"
                                    src="{% if item.image_path %}/static/{{ item.image_path }}{% endif %}"
                                    alt="{{ item.title }}"
                                    loading="lazy"
                                    decoding="async"
                                >
                                <div class="dish-plate{% if item.image_path %} is-hidden{% endif %}">
                                    <div class="dish-center"></div>
                                </div>
                            </div>

                            <div class="dish-body">
                                <div class="dish-admin-row">
                                    <h3 class="dish-title">{{ item.title }}</h3>
                                    <button class="dish-edit-button" type="button">Редактировать</button>
                                </div>
                                <p class="dish-description">{{ item.description }}</p>
                            </div>

                            <div class="dish-footer">
                                <strong class="dish-price">{{ item.price }} руб.</strong>
                                <div class="dish-actions">
                                    <div class="qty-picker" data-qty-picker>
                                        <button class="qty-button" type="button" data-qty-action="decrease">-</button>
                                        <span class="qty-value" data-qty-value>1</span>
                                        <button class="qty-button" type="button" data-qty-action="increase">+</button>
                                    </div>
                                    <button
                                        class="add-button"
                                        data-id="{{ item.id }}"
                                        data-title="{{ item.title }}"
                                        data-price="{{ item.price }}"
                                    >
                                        Добавить
                                    </button>
                                </div>
                            </div>
                        </article>
                        {% endfor %}
                    </div>
                </div>

            </div>
        </section>

        <section class="delivery-section section-shell" id="delivery">
            <div class="section-head delivery-head">
                <div>
                    <span class="section-kicker">Доставка</span>
                    <h2>Путь к заказу остался простым: выбрать, собрать, получить.</h2>
                </div>
            </div>

            <div class="steps-grid delivery-track">
                {% for step in steps %}
                <article class="step-card delivery-card">
                    <div class="delivery-card-quote" aria-hidden="true">”</div>
                    <div class="delivery-card-rating" aria-hidden="true">
                        <span>★</span><span>★</span><span>★</span><span>★</span><span>★</span>
                    </div>
                    <p class="delivery-card-text">{{ step.text }}</p>
                    <div class="delivery-card-meta">
                        <div class="delivery-card-index">0{{ loop.index }}</div>
                        <div class="delivery-card-author">
                            <h3>{{ step.title }}</h3>
                            <span>Этап доставки</span>
                        </div>
                    </div>
                </article>
                {% endfor %}
            </div>
        </section>






    </main>

    <footer class="site-footer" id="footer">
        <div class="site-footer-inner">
            <div class="site-footer-brand">
                <a class="site-footer-logo" href="#hero">Zamzam.</a>
                <p class="site-footer-copy">Восточная кухня, быстрая доставка и аккуратная ресторанная подача каждый день.</p>
            </div>

            <div class="site-footer-column">
                <h4 class="site-footer-heading">Навигация</h4>
                <div class="site-footer-links">
                    <a href="#hero">Главная</a>
                    <a href="#menu">Меню</a>
                    <a href="#delivery-info" data-delivery-info-open>Доставка</a>

                </div>
            </div>

            <div class="site-footer-column">
                <h4 class="site-footer-heading">Документы</h4>
                <div class="site-footer-links">
                    <a href="/policy">Политика конфиденциальности</a>
                    <a href="/oferta">Оферта</a>
                </div>
            </div>

            <div class="site-footer-column site-footer-meta">
                <h4 class="site-footer-heading">Контакты</h4>
                <div class="site-footer-contact-grid">
                    <div class="site-footer-contact-item">
                        <span class="site-footer-label">Адрес</span>
                        <button class="site-footer-map-trigger" id="footer-map-open" type="button" data-map-src="https://www.google.com/maps?q=%D0%B3.%20%D0%95%D0%BA%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%BD%D0%B1%D1%83%D1%80%D0%B3,%20%D1%83%D0%BB.%20%D0%9C%D0%B0%D0%BB%D1%8B%D1%88%D0%B5%D0%B2%D0%B0,%20%D0%B4.%2028&amp;output=embed" data-map-title="ул. Малышева, д. 28" data-map-address="Екатеринбург, ул. Малышева, д. 28" style="text-align:left;">ул. Малышева, д. 28</button>
                        <span class="site-footer-label">Телефон</span>
                        <a class="site-footer-phone" href="tel:+79827505455">+7 982 750-54-55</a>
                        <span class="site-footer-label">Режим работы</span>
                        <strong>Пн - Вс • 10:00 - 23:00</strong>
                    </div>
                    <div class="site-footer-contact-item">
                        <span class="site-footer-label">Адрес</span>
                        <button class="site-footer-map-trigger" id="footer-map-open-footer" type="button" data-map-src="https://www.google.com/maps?q=%D0%B3.%20%D0%95%D0%BA%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%BD%D0%B1%D1%83%D1%80%D0%B3,%20%D1%83%D0%BB.%20%D0%A1%D1%83%D1%85%D0%BE%D0%BB%D0%BE%D0%B6%D1%81%D0%BA%D0%B0%D1%8F,%20%D0%B4.%205%2F1&amp;output=embed" data-map-title="ул. Сухоложская, д. 5/1" data-map-address="Екатеринбург, ул. Сухоложская, д. 5/1" style="text-align:left;">ул. Сухоложская, д. 5/1</button>
                        <span class="site-footer-label">Телефон</span>
                        <a class="site-footer-phone" href="tel:+79530420044">+7 (953) 042-00-44</a>
                        <span class="site-footer-label">Режим работы</span>
                        <strong>Пн - Вс • 10:00 - 00:00</strong>
                    </div>
                </div>
            </div>
        </div>

        <div class="site-footer-bottom">
            <p class="site-footer-copyright">© 2026 Zamzam. Все права защищены.</p>
            <p class="site-footer-copyright site-footer-credit">Сайт разработан компанией <a href="https://blackphantom.ru/" target="_blank" rel="noopener noreferrer">BlackPhantom</a>.</p>
        </div>
    </footer>

    <script defer src="/static/app.js?v=20260628-delivery-fields-1"></script>
    <script defer src="/static/catalog-admin.js?v=20260506-hero-mobile-fix-2"></script>
    <script defer src="/static/account.js?v=20260628-delivery-fields-1"></script>
    <script defer src="/static/orders-admin.js?v=20260627-iiko-address-suggest-4"></script>
    <script>
        (function () {
            const preloader = document.getElementById("page-preloader");
            const topbarWrap = document.querySelector(".topbar-wrap");
            const topbar = document.querySelector(".topbar");
            const topbarBurger = document.getElementById("topbar-burger");
            const heroVideo = document.querySelector(".hero-background-image");
            const deliveryInfoModal = document.getElementById("delivery-info-modal");
            const deliveryInfoBackdrop = document.getElementById("delivery-info-backdrop");
            const deliveryInfoClose = document.getElementById("delivery-info-close");
            const footerMapBackdrop = document.getElementById("footer-map-backdrop");
            const footerMapModal = document.getElementById("footer-map-modal");
            const footerMapClose = document.getElementById("footer-map-close");
            const footerMapFrame = footerMapModal ? footerMapModal.querySelector("iframe") : null;
            const footerMapLocationTitle = document.getElementById("footer-map-location-title");
            const footerMapLocationAddress = document.getElementById("footer-map-location-address");
            const reservationOpen = document.getElementById("cart-open-hero");
            const reservationBackdrop = document.getElementById("reservation-backdrop");
            const reservationModal = document.getElementById("reservation-modal");
            const reservationClose = document.getElementById("reservation-close");

            function openDeliveryInfoModal(event) {
                event?.preventDefault();
                setMobileMenuOpen(false);
                deliveryInfoBackdrop?.classList.add("is-open");
                deliveryInfoModal?.classList.add("is-open");
                deliveryInfoModal?.setAttribute("aria-hidden", "false");
                document.body.classList.add("admin-open");
            }

            function closeDeliveryInfoModal() {
                deliveryInfoBackdrop?.classList.remove("is-open");
                deliveryInfoModal?.classList.remove("is-open");
                deliveryInfoModal?.setAttribute("aria-hidden", "true");
                document.body.classList.remove("admin-open");
            }

            function openFooterMapModal(event) {
                if (!footerMapBackdrop || !footerMapModal) {
                    return;
                }

                const trigger = event.currentTarget;
                if (trigger instanceof HTMLElement) {
                    const mapSrc = trigger.getAttribute("data-map-src");
                    const mapTitle = trigger.getAttribute("data-map-title");
                    const mapAddress = trigger.getAttribute("data-map-address");

                    if (mapSrc && footerMapFrame) {
                        footerMapFrame.src = mapSrc;
                    }
                    if (mapTitle && footerMapLocationTitle) {
                        footerMapLocationTitle.textContent = mapTitle;
                    }
                    if (mapAddress && footerMapLocationAddress) {
                        footerMapLocationAddress.textContent = mapAddress;
                    }
                    if (footerMapFrame) {
                        footerMapFrame.title = "Карта Zamzam: " + (mapAddress || mapTitle || "адрес");
                    }
                }

                footerMapBackdrop.classList.add("is-open");
                footerMapModal.classList.add("is-open");
                footerMapModal.setAttribute("aria-hidden", "false");
                document.body.classList.add("admin-open");
            }

            function closeFooterMapModal() {
                footerMapBackdrop?.classList.remove("is-open");
                footerMapModal?.classList.remove("is-open");
                footerMapModal?.setAttribute("aria-hidden", "true");
                document.body.classList.remove("admin-open");
            }

            function openReservationModal() {
                reservationBackdrop?.classList.add("is-open");
                reservationModal?.classList.add("is-open");
                reservationModal?.setAttribute("aria-hidden", "false");
                document.body.classList.add("admin-open");
            }

            function closeReservationModal() {
                reservationBackdrop?.classList.remove("is-open");
                reservationModal?.classList.remove("is-open");
                reservationModal?.setAttribute("aria-hidden", "true");
                document.body.classList.remove("admin-open");
            }

            function setMobileMenuOpen(isOpen) {
                topbar?.classList.toggle("is-menu-open", isOpen);
                topbarWrap?.classList.toggle("is-menu-open", isOpen);
                document.body.classList.toggle("mobile-menu-open", isOpen);
                topbarBurger?.setAttribute("aria-expanded", String(Boolean(isOpen)));

                if (isOpen) {
                    window.setZamzamCartDrawerOpen?.(false);
                }
            }

            window.setZamzamMobileMenuOpen = setMobileMenuOpen;

            function syncTopbarScrolled() {
                topbarWrap?.classList.toggle("is-scrolled", window.scrollY > 24);
            }

            function hidePreloader() {
                if (preloader) {
                    preloader.classList.add("is-hidden");
                }
                document.body.classList.remove("preloader-active");
            }

            function playHeroVideo() {
                if (!heroVideo || typeof heroVideo.play !== "function") {
                    return;
                }

                heroVideo.muted = true;
                heroVideo.play().catch(function () {});
            }

            function syncHeroVideoSource() {
                if (!heroVideo) {
                    return;
                }

                const mobileSource = heroVideo.dataset.mobileSrc || "";
                const desktopSource = heroVideo.dataset.desktopSrc || heroVideo.getAttribute("src") || "";
                const nextSource = window.matchMedia("(max-width: 820px)").matches ? mobileSource : desktopSource;

                if (nextSource && heroVideo.getAttribute("src") !== nextSource) {
                    heroVideo.setAttribute("src", nextSource);
                    heroVideo.load();
                    playHeroVideo();
                }
            }

            topbarBurger?.addEventListener("click", function () {
                setMobileMenuOpen(!topbar?.classList.contains("is-menu-open"));
            });

            document.querySelectorAll("[data-delivery-info-open]").forEach(function (item) {
                item.addEventListener("click", openDeliveryInfoModal);
            });
            document.querySelectorAll("#footer-map-open, #footer-map-open-footer").forEach(function (item) {
                item.addEventListener("click", openFooterMapModal);
            });
            reservationOpen?.addEventListener("click", openReservationModal);

            deliveryInfoClose?.addEventListener("click", closeDeliveryInfoModal);
            deliveryInfoBackdrop?.addEventListener("click", closeDeliveryInfoModal);
            footerMapClose?.addEventListener("click", closeFooterMapModal);
            footerMapBackdrop?.addEventListener("click", closeFooterMapModal);
            reservationClose?.addEventListener("click", closeReservationModal);
            reservationBackdrop?.addEventListener("click", closeReservationModal);

            topbarWrap?.addEventListener("click", function (event) {
                if (!topbar?.classList.contains("is-menu-open")) {
                    return;
                }

                if (event.target === topbarWrap) {
                    setMobileMenuOpen(false);
                }
            });

            topbar?.querySelectorAll(".nav-links a, .topbar-controls button").forEach(function (item) {
                item.addEventListener("click", function () {
                    setMobileMenuOpen(false);
                });
            });

            document.addEventListener("DOMContentLoaded", function () {
                syncTopbarScrolled();
                syncHeroVideoSource();
                playHeroVideo();
                window.setTimeout(hidePreloader, 120);
            });

            window.addEventListener("load", function () {
                window.setTimeout(hidePreloader, 120);
            });

            window.addEventListener("resize", function () {
                syncHeroVideoSource();
                playHeroVideo();

                if (window.innerWidth > 820) {
                    setMobileMenuOpen(false);
                }
            });

            document.addEventListener("keydown", function (event) {
                if (event.key === "Escape") {
                    setMobileMenuOpen(false);
                    closeDeliveryInfoModal();
                    closeFooterMapModal();
                    closeReservationModal();
                }
            });

            window.addEventListener("scroll", syncTopbarScrolled, { passive: true });
        })();
    </script>
</body>
</html>

```

## 📄 `templates\oferta.html`

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Zamzam | Оферта</title>
    <meta name="description" content="Оферта Zamzam">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/styles.css?v=20260519-legal-mobile-fix-1">
</head>
<body class="legal-page-body preloader-active">
    <div class="page-preloader" id="page-preloader" aria-hidden="true">
        <div class="page-preloader-shell">
            <div class="page-preloader-icon-wrap">
                <img class="page-preloader-icon" src="/static/pic/preloader-cloche.svg" alt="">
            </div>
            <strong class="page-preloader-title">Zamzam</strong>
            <span class="page-preloader-copy">Загружаем страницу</span>
        </div>
    </div>

    <div class="checkout-backdrop" id="footer-map-backdrop"></div>

    <header class="legal-page-header">
        <div class="legal-page-header-inner">
            <a class="legal-page-brand" href="/">Zamzam.</a>

            <a class="legal-page-back button-shiny" href="/"><span>На главную</span></a>
        </div>
    </header>

    <main class="legal-page-main">
        <section class="legal-page-hero">
            <div class="legal-page-hero-shell">
                <span class="section-kicker">Документы</span>
                <h1>Оферта</h1>



            </div>
        </section>

        <section class="legal-page-shell">
            <div class="legal-page-grid">
                <aside class="legal-page-aside">
                    <article class="legal-page-aside-card">
                        <span class="legal-page-aside-label">Раздел</span>
                        <strong>Оферта и условия сервиса</strong>
                        <p>Документ фиксирует правила покупки, доставки, оплаты и оформления заказа через сайт Zamzam.</p>
                    </article>

                    <article class="legal-page-aside-card">
                        <span class="legal-page-aside-label">Навигация</span>
                        <div class="legal-page-aside-links">
                            <a href="/">На главную</a>
                            <a href="/#menu">Открыть меню</a>
                            <a href="/policy">Перейти к политике</a>
                        </div>
                    </article>

                    <article class="legal-page-aside-card">
                        <span class="legal-page-aside-label">Контакты</span>
                        <button class="site-footer-map-trigger legal-page-map-trigger" id="footer-map-open" type="button" data-map-src="https://www.google.com/maps?q=%D0%B3.%20%D0%95%D0%BA%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%BD%D0%B1%D1%83%D1%80%D0%B3,%20%D1%83%D0%BB.%20%D0%9C%D0%B0%D0%BB%D1%8B%D1%88%D0%B5%D0%B2%D0%B0,%20%D0%B4.%2028&amp;output=embed" data-map-label="Ресторан на Малышева" data-map-address="Екатеринбург, ул. Малышева, д. 28" style="text-align:left;">Екатеринбург, ул. Малышева, д. 28</button>
                        <a class="site-footer-phone legal-page-phone" href="tel:+79827505455">+7 982 750-54-55</a>
                        <button class="site-footer-map-trigger legal-page-map-trigger" id="footer-map-open-footer" type="button" data-map-src="https://www.google.com/maps?q=%D0%B3.%20%D0%95%D0%BA%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%BD%D0%B1%D1%83%D1%80%D0%B3,%20%D1%83%D0%BB.%20%D0%A1%D1%83%D1%85%D0%BE%D0%BB%D0%BE%D0%B6%D1%81%D0%BA%D0%B0%D1%8F,%20%D0%B4.%205%2F1&amp;output=embed" data-map-label="Ресторан на Сухоложской" data-map-address="Екатеринбург, ул. Сухоложская, д. 5/1" style="text-align:left;">Екатеринбург, ул. Сухоложская, д. 5/1</button>
                        <a class="site-footer-phone legal-page-phone" href="tel:+79530420044">+7 (953) 042-00-44</a>
                    </article>
                </aside>

                <article class="legal-document">
                    <div class="legal-document-head">
                        <span class="legal-page-aside-label">Текст документа</span>
                        <strong>Актуальная редакция</strong>
                    </div>
                    <pre class="legal-document-text">{{ oferta_text }}</pre>
                </article>
            </div>
        </section>
    </main>

    <section class="checkout-modal footer-map-modal" id="footer-map-modal" aria-hidden="true">
    <div class="checkout-modal-shell">
        <div class="footer-map-modal-wrap">
            <div class="checkout-modal-head">
                <div>
                    <span class="section-kicker">Мы находимся</span>
                    <h3>Адреса ресторанов</h3>
                </div>
                <button
                    class="admin-close"
                    id="footer-map-close"
                    type="button"
                    aria-label="Закрыть карту"
                >
                    x
                </button>
            </div>

            <div class="footer-map-card">
                <div class="footer-map-card-grid">
                    <div class="footer-map-card-copy">
                        <span class="footer-map-card-label" id="footer-map-location-label">Ресторан на Малышева</span>
                        <strong id="footer-map-location-address">Екатеринбург, ул. Малышева, д. 28</strong>
                    </div>


                    <div class="footer-map-card-copy">
                        <span class="footer-map-card-label">Режим работы</span>
                        <strong>Пн – Вс • 10:00 – 23:00</strong>
                    </div>
                </div>
            </div>

            <div class="footer-map-frame">
                <iframe
                    title="Карта Zamzam на улице Малышева"
                    src="https://www.google.com/maps?q=%D0%B3.%20%D0%95%D0%BA%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%BD%D0%B1%D1%83%D1%80%D0%B3,%20%D1%83%D0%BB.%20%D0%9C%D0%B0%D0%BB%D1%8B%D1%88%D0%B5%D0%B2%D0%B0,%20%D0%B4.28&output=embed"
                    loading="lazy"
                    referrerpolicy="no-referrer-when-downgrade"
                    allowfullscreen
                ></iframe>
            </div>
        </div>
    </div>
</section>



    <script>
        (function () {
            const preloader = document.getElementById("page-preloader");

            function hidePreloader() {
                if (preloader) {
                    preloader.classList.add("is-hidden");
                }
                document.body.classList.remove("preloader-active");
            }

            window.addEventListener("load", function () {
                window.setTimeout(hidePreloader, 120);
            });
        })();
    </script>

    <script>
        (function () {
            const footerMapBackdrop = document.getElementById("footer-map-backdrop");
            const footerMapModal = document.getElementById("footer-map-modal");
            const footerMapTriggers = document.querySelectorAll("#footer-map-open, #footer-map-open-footer");
            const footerMapClose = document.getElementById("footer-map-close");
            const footerMapFrame = footerMapModal ? footerMapModal.querySelector("iframe") : null;
            const footerMapLocationLabel = document.getElementById("footer-map-location-label");
            const footerMapLocationAddress = document.getElementById("footer-map-location-address");

            function closeFooterMapModal() {
                if (footerMapBackdrop) {
                    footerMapBackdrop.classList.remove("is-open");
                }
                if (footerMapModal) {
                    footerMapModal.classList.remove("is-open");
                    footerMapModal.setAttribute("aria-hidden", "true");
                }
                document.body.classList.remove("admin-open");
            }

            function openFooterMapModal(event) {
                if (!footerMapBackdrop || !footerMapModal) {
                    return;
                }
                const trigger = event.currentTarget;
                if (footerMapFrame && trigger instanceof HTMLElement) {
                    const mapSrc = trigger.getAttribute("data-map-src");
                    const mapLabel = trigger.getAttribute("data-map-label");
                    const mapAddress = trigger.getAttribute("data-map-address");
                    if (mapSrc) {
                        footerMapFrame.src = mapSrc;
                    }
                    if (mapLabel && footerMapLocationLabel) {
                        footerMapLocationLabel.textContent = mapLabel;
                    }
                    if (mapAddress && footerMapLocationAddress) {
                        footerMapLocationAddress.textContent = mapAddress;
                    }
                    footerMapFrame.title = "Карта Zamzam: " + (mapAddress || trigger.textContent.trim());
                }
                footerMapBackdrop.classList.add("is-open");
                footerMapModal.classList.add("is-open");
                footerMapModal.setAttribute("aria-hidden", "false");
                document.body.classList.add("admin-open");
            }

            footerMapTriggers.forEach(function (trigger) {
                trigger.addEventListener("click", openFooterMapModal);
            });
            footerMapClose && footerMapClose.addEventListener("click", closeFooterMapModal);
            footerMapBackdrop && footerMapBackdrop.addEventListener("click", closeFooterMapModal);
            document.addEventListener("keydown", function (event) {
                if (event.key === "Escape" && footerMapModal && footerMapModal.classList.contains("is-open")) {
                    closeFooterMapModal();
                }
            });
        })();
    </script>
</body>
</html>

```

## 📄 `templates\policy.html`

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Zamzam | Политика конфиденциальности</title>
    <meta name="description" content="Политика конфиденциальности Zamzam">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/styles.css?v=20260519-legal-mobile-fix-1">
</head>
<body class="legal-page-body preloader-active">
    <div class="page-preloader" id="page-preloader" aria-hidden="true">
        <div class="page-preloader-shell">
            <div class="page-preloader-icon-wrap">
                <img class="page-preloader-icon" src="/static/pic/preloader-cloche.svg" alt="">
            </div>
            <strong class="page-preloader-title">Zamzam</strong>
            <span class="page-preloader-copy">Загружаем страницу</span>
        </div>
    </div>

    <div class="checkout-backdrop" id="footer-map-backdrop"></div>

    <header class="legal-page-header">
        <div class="legal-page-header-inner">
            <a class="legal-page-brand" href="/">Zamzam.</a>

            <a class="legal-page-back button-shiny" href="/"><span>На главную</span></a>
        </div>
    </header>

    <main class="legal-page-main">
        <section class="legal-page-hero">
            <div class="legal-page-hero-shell">
                <span class="section-kicker">Документы</span>
                <h1>Политика конфиденциальности</h1>



            </div>
        </section>

        <section class="legal-page-shell">
            <div class="legal-page-grid">
                <aside class="legal-page-aside">


                    <article class="legal-page-aside-card">
                        <span class="legal-page-aside-label">Быстрые ссылки</span>
                        <div class="legal-page-aside-links">
                            <a href="/">На главную</a>
                            <a href="/#menu">Открыть меню</a>
                            <a href="/oferta">Перейти к оферте</a>
                        </div>
                    </article>

                    <article class="legal-page-aside-card">
                        <span class="legal-page-aside-label">Контакты</span>
                        <button class="site-footer-map-trigger legal-page-map-trigger" id="footer-map-open" type="button" data-map-src="https://www.google.com/maps?q=%D0%B3.%20%D0%95%D0%BA%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%BD%D0%B1%D1%83%D1%80%D0%B3,%20%D1%83%D0%BB.%20%D0%9C%D0%B0%D0%BB%D1%8B%D1%88%D0%B5%D0%B2%D0%B0,%20%D0%B4.%2028&amp;output=embed" data-map-label="Ресторан на Малышева" data-map-address="Екатеринбург, ул. Малышева, д. 28" style="text-align:left;">Екатеринбург, ул. Малышева, д. 28</button>
                        <a class="site-footer-phone legal-page-phone" href="tel:+79827505455">+7 982 750-54-55</a>
                        <button class="site-footer-map-trigger legal-page-map-trigger" id="footer-map-open-footer" type="button" data-map-src="https://www.google.com/maps?q=%D0%B3.%20%D0%95%D0%BA%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%BD%D0%B1%D1%83%D1%80%D0%B3,%20%D1%83%D0%BB.%20%D0%A1%D1%83%D1%85%D0%BE%D0%BB%D0%BE%D0%B6%D1%81%D0%BA%D0%B0%D1%8F,%20%D0%B4.%205%2F1&amp;output=embed" data-map-label="Ресторан на Сухоложской" data-map-address="Екатеринбург, ул. Сухоложская, д. 5/1" style="text-align:left;">Екатеринбург, ул. Сухоложская, д. 5/1</button>
                        <a class="site-footer-phone legal-page-phone" href="tel:+79530420044">+7 (953) 042-00-44</a>
                    </article>
                </aside>

                <article class="legal-document">
                    <div class="legal-document-head">
                        <span class="legal-page-aside-label">Текст документа</span>
                        <strong>Актуальная редакция</strong>
                    </div>
                    <pre class="legal-document-text">{{ policy_text }}</pre>
                </article>
            </div>
        </section>
    </main>

    <section class="checkout-modal footer-map-modal" id="footer-map-modal" aria-hidden="true">
    <div class="checkout-modal-shell">
        <div class="footer-map-modal-wrap">
            <div class="checkout-modal-head">
                <div>
                    <span class="section-kicker">Мы находимся</span>
                    <h3>Адреса ресторанов</h3>
                </div>
                <button
                    class="admin-close"
                    id="footer-map-close"
                    type="button"
                    aria-label="Закрыть карту"
                >
                    x
                </button>
            </div>

            <div class="footer-map-card">
                <div class="footer-map-card-grid">
                    <div class="footer-map-card-copy">
                        <span class="footer-map-card-label">Ресторан на Малышева</span>
                        <strong>Екатеринбург, ул. Малышева, д. 28</strong>
                    </div>

                    <div class="footer-map-card-copy">
                        <span class="footer-map-card-label">Ресторан на Сухоложской</span>
                        <strong>Екатеринбург, ул. Сухоложская, д. 5/1</strong>
                        <a href="tel:+79530420044">+7 (953) 042-00-44</a>
                    </div>

                    <div class="footer-map-card-copy">
                        <span class="footer-map-card-label">Режим работы</span>
                        <strong>Пн – Вс • 10:00 – 23:00</strong>
                    </div>
                </div>
            </div>

            <div class="footer-map-frame">
                <iframe
                    title="Карта Zamzam на улице Малышева"
                    src="https://www.google.com/maps?q=%D0%B3.%20%D0%95%D0%BA%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%BD%D0%B1%D1%83%D1%80%D0%B3,%20%D1%83%D0%BB.%20%D0%9C%D0%B0%D0%BB%D1%8B%D1%88%D0%B5%D0%B2%D0%B0,%20%D0%B4.28&output=embed"
                    loading="lazy"
                    referrerpolicy="no-referrer-when-downgrade"
                    allowfullscreen
                ></iframe>
            </div>
        </div>
    </div>
</section>



    <script>
        (function () {
            const preloader = document.getElementById("page-preloader");

            function hidePreloader() {
                if (preloader) {
                    preloader.classList.add("is-hidden");
                }
                document.body.classList.remove("preloader-active");
            }

            window.addEventListener("load", function () {
                window.setTimeout(hidePreloader, 120);
            });
        })();
    </script>

    <script>
        (function () {
            const footerMapBackdrop = document.getElementById("footer-map-backdrop");
            const footerMapModal = document.getElementById("footer-map-modal");
            const footerMapTriggers = document.querySelectorAll("#footer-map-open, #footer-map-open-footer");
            const footerMapClose = document.getElementById("footer-map-close");

            function closeFooterMapModal() {
                if (footerMapBackdrop) {
                    footerMapBackdrop.classList.remove("is-open");
                }
                if (footerMapModal) {
                    footerMapModal.classList.remove("is-open");
                    footerMapModal.setAttribute("aria-hidden", "true");
                }
                document.body.classList.remove("admin-open");
            }

            function openFooterMapModal() {
                if (!footerMapBackdrop || !footerMapModal) {
                    return;
                }
                footerMapBackdrop.classList.add("is-open");
                footerMapModal.classList.add("is-open");
                footerMapModal.setAttribute("aria-hidden", "false");
                document.body.classList.add("admin-open");
            }

            footerMapTriggers.forEach(function (trigger) {
                trigger.addEventListener("click", openFooterMapModal);
            });
            footerMapClose && footerMapClose.addEventListener("click", closeFooterMapModal);
            footerMapBackdrop && footerMapBackdrop.addEventListener("click", closeFooterMapModal);
            document.addEventListener("keydown", function (event) {
                if (event.key === "Escape" && footerMapModal && footerMapModal.classList.contains("is-open")) {
                    closeFooterMapModal();
                }
            });
        })();
    </script>
</body>
</html>

```
