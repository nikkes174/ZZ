import os


os.environ.setdefault("DB_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("API_IIKO", "test")
os.environ.setdefault("IIKO_ORGANIZATION_ID", "00000000-0000-0000-0000-000000000001")
os.environ.setdefault("TERMINAL_ID_GROUP_MALYSHAVA", "00000000-0000-0000-0000-000000000002")
