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
    price: Optional[int] = Field(default=None, ge=0, le=1_000_000)
    category: Optional[str] = Field(default=None, min_length=1, max_length=64)
    accent: Optional[str] = Field(default=None, min_length=3, max_length=32)
    badge: Optional[str] = Field(default=None, max_length=128)
    image_path: Optional[str] = Field(default=None, max_length=255)
    sort_order: Optional[int] = Field(default=None, ge=0, le=100_000)
    is_active: Optional[bool] = None


class MenuItemDelete(BaseModel):
    version: int = Field(..., ge=1)


class MenuItemRead(MenuItemBase):
    id: int
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MenuItemsPage(BaseModel):
    items: list[MenuItemRead]
    total: int
    limit: int
    offset: int


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
