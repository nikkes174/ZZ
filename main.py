from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.orders import router as orders_router
from backend.orders.migrations import ensure_order_bonus_columns
from backend.redactor import router as redactor_router
from backend.redactor.router import load_hero_content
from backend.redactor.crud import SqlAlchemyMenuItemRepository
from backend.redactor.schemas import MenuItemCreate
from backend.redactor.service import MenuItemService
from backend.user import router as user_router
from db import AsyncSessionLocal, init_db


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


MENU_ITEMS = [
    {
        "title": "Томлёная говядина Zamzam",
        "description": "Мраморная говядина, демиглас, картофельный крем и соус из печёного чеснока.",
        "price": 1290,
        "category": "signature",
        "badge": "Хит вечера",
        "accent": "#d9a35f",
        "sort_order": 10,
    },
    {
        "title": "Сёмга на углях",
        "description": "Филе сёмги, молодые овощи, лимонный гель и травяное масло.",
        "price": 1180,
        "category": "seafood",
        "badge": "Свежий улов",
        "accent": "#5ab6a6",
        "sort_order": 20,
    },
    {
        "title": "Ризотто с белыми грибами",
        "description": "Кремовая текстура, выдержанный пармезан и трюфельный штрих.",
        "price": 910,
        "category": "signature",
        "badge": "Премиум comfort",
        "accent": "#b98d62",
        "sort_order": 30,
    },
    {
        "title": "Поке с тунцом блюфин",
        "description": "Рис для суши, тунец, авокадо, манго, эдамаме и пикантный соус.",
        "price": 860,
        "category": "bowls",
        "badge": "Лёгкий выбор",
        "accent": "#6da4ff",
        "sort_order": 40,
    },
    {
        "title": "Бургер Black Angus",
        "description": "Бриошь, котлета dry-aged, чеддер, айоли и фирменный BBQ.",
        "price": 970,
        "category": "grill",
        "badge": "Сытный фаворит",
        "accent": "#ef7b5c",
        "sort_order": 50,
    },
    {
        "title": "Десерт Фисташковое облако",
        "description": "Нежный мусс, малина, белый шоколад и хрустящий слой пралине.",
        "price": 540,
        "category": "dessert",
        "badge": "Финальный акцент",
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


async def _seed_menu_items() -> None:
    async with AsyncSessionLocal() as session:
        service = MenuItemService(repository=SqlAlchemyMenuItemRepository(session))
        await service.ensure_seed_data([MenuItemCreate(**item) for item in MENU_ITEMS])


async def _load_menu_items() -> list[dict[str, object]]:
    async with AsyncSessionLocal() as session:
        service = MenuItemService(repository=SqlAlchemyMenuItemRepository(session))
        page = await service.list_items(limit=100, offset=0, include_inactive=False)
        return [item.model_dump(mode="json") for item in page.items]


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    await ensure_order_bonus_columns()
    await _seed_menu_items()
    yield


app = FastAPI(
    title="Zamzam",
    description="Ресторан доставки восточной кухни",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(redactor_router)
app.include_router(user_router)
app.include_router(orders_router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "hero_content": load_hero_content(),
            "menu_items": await _load_menu_items(),
            "features": FEATURES,
            "steps": STEPS,
            "reviews": REVIEWS,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8083)
