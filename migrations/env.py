# migrations/env.py
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from alembic import context
import asyncio

from app.settings import get_settings
from src.base.adapters.sqlalchemydb.database import Base

# Import all models for autogenerate to detect them
import src.base.adapters.sqlalchemydb.models
import src.users.adapters.sqlalchemydb.models
import src.files.adapters.sqlalchemydb.models
import src.messaging.adapters.sqlalchemydb.models

config = context.config
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)
fileConfig(config.config_file_name)
target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    # This is the sync section executed inside run_sync
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():  # <-- IMPORTANT
        context.run_migrations()  # <-- IMPORTANT


def run_migrations_online():
    engine: AsyncEngine = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
        future=True,
    )

    async def run():
        async with engine.begin() as conn:  # <-- IMPORTANT
            await conn.run_sync(do_run_migrations)

    asyncio.run(run())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
