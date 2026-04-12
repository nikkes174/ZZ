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
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Catalog products are managed by iiko and cannot be deleted manually.",
    )
