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
