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
