from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from app_logging import configure_application_logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.auth import router as auth_router
from backend.orders import router as orders_router
from backend.orders.crud import SqlAlchemyOrderRepository
from backend.orders.migrations import ensure_order_bonus_columns
from backend.orders.service import IikoOrderStatusSyncService
from backend.payment.router import router as payment_router
from backend.iiko_manager.client import IikoApiClient
from backend.iiko_manager.repository import IikoCatalogRepository
from backend.iiko_manager.service import IikoCatalogSyncService
from backend.redactor import router as redactor_router
from backend.redactor.router import load_hero_content, load_menu_categories
from backend.redactor.crud import SqlAlchemyMenuItemRepository
from backend.redactor.migrations import ensure_menu_item_iiko_columns
from backend.redactor.service import MenuItemService
from backend.user import router as user_router
from backend.user.migrations import ensure_user_auth_columns, sync_admin_users_from_env
from config import (
    API_IIKO,
    IIKO_BASE_URL,
    IIKO_ORGANIZATION_ID,
    IIKO_ORDER_STATUS_SYNC_INTERVAL_SECONDS,
    IIKO_ORDER_STATUS_SYNC_LIMIT,
    IIKO_ORDER_TIMEOUT_SECONDS,
    IIKO_SYNC_INTERVAL_SECONDS,
    IIKO_SYNC_TIMEOUT_SECONDS,
    TERMINAL_ID_GROUP,
)
from db import AsyncSessionLocal, init_db


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
configure_application_logging()
logger = logging.getLogger(__name__)
OFERTA_TEXT_PATH = BASE_DIR / "files" / "legal" / "oferta.txt"
POLICY_TEXT_PATH = BASE_DIR / "files" / "legal" / "politic.txt"


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
        page = await service.list_items(limit=100, offset=0, include_inactive=False)
        logger.info("Loaded %s active iiko menu items for storefront.", len(page.items))
        if not page.items:
            logger.warning("Storefront has zero active iiko menu items.")
        return [item.model_dump(mode="json") for item in page.items]


async def _sync_iiko_catalog() -> None:
    logger.info("Starting iiko catalog sync.")
    if not API_IIKO:
        raise RuntimeError("API_IIKO is required because iiko is the only source of truth for catalog data.")
    if not TERMINAL_ID_GROUP:
        raise RuntimeError("TERMINAL_ID_GROUP is required because iiko is the only source of truth for catalog data.")

    async with AsyncSessionLocal() as session:
        service = IikoCatalogSyncService(
            client=IikoApiClient(
                api_login=API_IIKO,
                base_url=IIKO_BASE_URL,
                timeout_seconds=IIKO_SYNC_TIMEOUT_SECONDS,
            ),
            repository=IikoCatalogRepository(session),
            terminal_group_id=TERMINAL_ID_GROUP,
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


@asynccontextmanager
async def lifespan(_: FastAPI):
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
    await _sync_iiko_catalog()
    stop_event = asyncio.Event()
    sync_task = asyncio.create_task(_run_iiko_sync_loop(stop_event))
    order_status_sync_task = asyncio.create_task(_run_iiko_order_status_sync_loop(stop_event))
    try:
        logger.info("Application startup completed.")
        yield
    finally:
        logger.info("Application shutdown initiated.")
        stop_event.set()
        for task in (sync_task, order_status_sync_task):
            task.cancel()
        await asyncio.gather(sync_task, order_status_sync_task, return_exceptions=True)
        logger.info("Application shutdown completed.")


app = FastAPI(
    title="Zamzam",
    description="   ",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(redactor_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(orders_router)
app.include_router(payment_router)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    body = await request.body()
    logger.warning(
        "Request validation failed. method=%s path=%s errors=%s body=%s",
        request.method,
        request.url.path,
        exc.errors(),
        body.decode("utf-8", errors="replace")[:2000],
    )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


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

    uvicorn.run("main:app", host="127.0.0.1", port=8011)
