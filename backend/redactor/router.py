from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from backend.redactor.depencises import get_menu_item_service
from backend.redactor.schemas import (
    HeroContentRead,
    HeroContentUpdate,
    MenuSectionContentRead,
    MenuSectionContentUpdate,
    MenuItemCreate,
    MenuItemDelete,
    MenuItemRead,
    MenuItemsPage,
    MenuItemUpdate,
)
from backend.redactor.service import (
    MenuItemConflictError,
    MenuItemNotFoundError,
    MenuItemService,
)

router = APIRouter(prefix="/api/redactor/menu-items", tags=["redactor"])

BASE_DIR = Path(__file__).resolve().parents[2]
STATIC_FILES_DIR = BASE_DIR / "static" / "files"
HERO_CONTENT_FILE = BASE_DIR / "files" / "hero-content.json"
MENU_SECTION_CONTENT_FILE = BASE_DIR / "files" / "menu-section-content.json"
DELIVERY_SECTION_CONTENT_FILE = BASE_DIR / "files" / "delivery-section-content.json"
CONTACT_SECTION_CONTENT_FILE = BASE_DIR / "files" / "contact-section-content.json"
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

DEFAULT_HERO_CONTENT = HeroContentRead(
    kicker="Восточная • Кавказская • Авторская кухня",
    title="Zamzam",
    address="Доставка по городу, ресторанная подача и быстрый онлайн-заказ",
    subtitle_primary="Яркая восточная кухня с характером,",
    subtitle_secondary="Сервис современного уровня",
)

DEFAULT_MENU_SECTION_CONTENT = MenuSectionContentRead(
    kicker="Наше меню",
    title="Соберите заказ в визуале из эталонного шаблона, но с нашей продуктовой логикой.",
)
DEFAULT_DELIVERY_SECTION_CONTENT = MenuSectionContentRead(
    kicker="Доставка",
    title="Путь к заказу остался простым: выбрать, собрать, получить.",
)

DEFAULT_CONTACT_SECTION_CONTENT = MenuSectionContentRead(
    kicker="Контакты",
    title="Работаем каждый день и держим быструю доставку в центре внимания.",
)


def _resolve_image_file_path(image_path: str | None) -> Path | None:
    if not image_path:
        return None

    candidate = STATIC_FILES_DIR / Path(image_path).name
    try:
        candidate.resolve().relative_to(STATIC_FILES_DIR.resolve())
    except ValueError:
        return None
    return candidate


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


@router.get("/hero-content", response_model=HeroContentRead)
async def get_hero_content() -> HeroContentRead:
    return load_hero_content()


@router.patch("/hero-content", response_model=HeroContentRead)
async def update_hero_content(payload: HeroContentUpdate) -> HeroContentRead:
    return save_hero_content(payload)


@router.get("/menu-section-content", response_model=MenuSectionContentRead)
async def get_menu_section_content() -> MenuSectionContentRead:
    return load_menu_section_content()


@router.patch("/menu-section-content", response_model=MenuSectionContentRead)
async def update_menu_section_content(payload: MenuSectionContentUpdate) -> MenuSectionContentRead:
    return save_menu_section_content(payload)


@router.get("/delivery-section-content", response_model=MenuSectionContentRead)
async def get_delivery_section_content() -> MenuSectionContentRead:
    return load_delivery_section_content()


@router.patch("/delivery-section-content", response_model=MenuSectionContentRead)
async def update_delivery_section_content(payload: MenuSectionContentUpdate) -> MenuSectionContentRead:
    return save_delivery_section_content(payload)


@router.get("/contact-section-content", response_model=MenuSectionContentRead)
async def get_contact_section_content() -> MenuSectionContentRead:
    return load_contact_section_content()


@router.patch("/contact-section-content", response_model=MenuSectionContentRead)
async def update_contact_section_content(payload: MenuSectionContentUpdate) -> MenuSectionContentRead:
    return save_contact_section_content(payload)


@router.get("", response_model=MenuItemsPage)
async def list_menu_items(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    include_inactive: bool = Query(default=False),
    service: MenuItemService = Depends(get_menu_item_service),
) -> MenuItemsPage:
    return await service.list_items(
        limit=limit,
        offset=offset,
        include_inactive=include_inactive,
    )


@router.get("/{item_id}", response_model=MenuItemRead)
async def get_menu_item(
    item_id: int,
    service: MenuItemService = Depends(get_menu_item_service),
) -> MenuItemRead:
    try:
        return await service.get_item(item_id)
    except MenuItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found") from exc


@router.post("", response_model=MenuItemRead, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    payload: MenuItemCreate,
    service: MenuItemService = Depends(get_menu_item_service),
) -> MenuItemRead:
    return await service.create_item(payload)


@router.patch("/{item_id}", response_model=MenuItemRead)
async def update_menu_item(
    item_id: int,
    payload: MenuItemUpdate,
    service: MenuItemService = Depends(get_menu_item_service),
) -> MenuItemRead:
    try:
        return await service.update_item(item_id, payload)
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
    service: MenuItemService = Depends(get_menu_item_service),
) -> MenuItemRead:
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
    file_name = f"menu-item-{item_id}-{uuid4().hex}{extension}"
    target_path = STATIC_FILES_DIR / file_name

    try:
        target_path.write_bytes(content)
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
    service: MenuItemService = Depends(get_menu_item_service),
) -> MenuItemRead:
    try:
        item = await service.delete_item(item_id, payload)
        image_path = _resolve_image_file_path(item.image_path)
        if image_path is not None:
            image_path.unlink(missing_ok=True)
        return item
    except MenuItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found") from exc
    except MenuItemConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Menu item was changed concurrently. Reload and retry.",
        ) from exc
